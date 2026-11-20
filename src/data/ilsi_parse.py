"""Task A2: Parse the LeSICiN / ILSI dataset into the K3 CSV format with PPC labels.

Input : data/raw/ilsi/{train,dev,test}.jsonl   (one case per line: id, text=[sentences], labels=[IPC sections])
        data/raw/ilsi/label_vocab.json         (the IPC sections ILSI covers)
        data/mapping/ipc_ppc_map.csv           (Task A1: which IPC section feeds which PPC label)
Output: data/processed/ilsi_clean.csv          (K3 schema + audit columns)
        docs/A2_ilsi_report.md                 (coverage and class-count report)

Key design decisions
1. Labels are mapped ONLY through the A1 table (rows with use_ilsi=yes). IPC sections that
   mean a different offence in Pakistan (e.g. IPC 324 = hurt by weapon) are dropped, never renamed.
2. Statute mentions ("u/s 302 IPC", "Section 379") are masked to [SEC] so the model cannot
   learn the answer from the citation itself (label leakage).
3. Lines that are not valid JSON (e.g. the last line of a partly downloaded file) are skipped and counted.
4. Long judgments are truncated to the first MAX_WORDS words after masking; the full length is kept
   in n_words_full for the truncation analysis in A4.

Run:  python -m src.data.ilsi_parse
"""

import csv
import json
import os
import re
import sys
from collections import Counter

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "ilsi")
MAP_CSV = os.path.join(PROJECT_ROOT, "data", "mapping", "ipc_ppc_map.csv")
LABELS_JSON = os.path.join(PROJECT_ROOT, "src", "labels.json")
OUT_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "ilsi_clean.csv")
REPORT_MD = os.path.join(PROJECT_ROOT, "docs", "A2_ilsi_report.md")

SPLIT_FILES = ["train.jsonl", "dev.jsonl", "test.jsonl"]
MAX_WORDS = 400
MIN_WORDS = 20

K3_COLUMNS = ["id", "text", "sections", "primary_section", "language", "source", "split"]
AUDIT_COLUMNS = ["orig_ipc_labels", "dropped_ipc_labels", "ilsi_file", "n_words_full", "n_masked"]

# ---------------------------------------------------------------- label handling

_LABEL_RE = re.compile(r"(\d{1,3})\s*[-_ ]?\s*([A-Za-z])?(?![A-Za-z])")


def normalize_ipc_label(raw):
    """Turn any ILSI label spelling into a bare IPC section id.

    'Section 302' -> '302', 'Section_364A' -> '364A', 'IPC_354-B' -> '354B', '379' -> '379'.
    Returns None if no section number is found.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    text = re.sub(r"(?i)\b(indian\s+penal\s+code|ipc|section|sec\.?|s\.)\b", " ", text)
    m = _LABEL_RE.search(text)
    if not m:
        return None
    num, letter = m.group(1), (m.group(2) or "")
    return f"{int(num)}{letter.upper()}"


def load_ipc_to_ppc(map_csv=MAP_CSV):
    """IPC section id -> PPC label, built only from A1 rows with use_ilsi == yes."""
    mapping = {}
    with open(map_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["use_ilsi"] != "yes":
                continue
            for ipc in row["ilsi_source_sections"].split(";"):
                ipc = ipc.strip()
                if ipc:
                    if ipc in mapping:
                        raise ValueError(f"IPC {ipc} mapped twice in A1 table")
                    mapping[ipc] = row["ppc_section"]
    return mapping


def map_labels(raw_labels, ipc_to_ppc):
    """Return (ppc_labels_sorted_unique, kept_ipc, dropped_ipc)."""
    ppc, kept, dropped = [], [], []
    for raw in raw_labels or []:
        ipc = normalize_ipc_label(raw)
        if ipc is None:
            continue
        if ipc in ipc_to_ppc:
            kept.append(ipc)
            if ipc_to_ppc[ipc] not in ppc:
                ppc.append(ipc_to_ppc[ipc])
        else:
            dropped.append(ipc)
    return ppc, kept, dropped

# ---------------------------------------------------------------- text handling

_NUM = r"\d{1,3}\s*-?\s*[A-Za-z]?(?![A-Za-z0-9])"
_JOIN = r"(?:\s*(?:/|,|&|and|r/w|read\s+with)\s*(?:sections?\s*)?)"
_STATUTE_RE = re.compile(
    rf"(?i)\b(?:under\s+)?(?:sections?|secs?\.?|u/s\.?|u/ss\.?|s\.)\s*{_NUM}(?:{_JOIN}{_NUM})*"
    r"(?:\s*(?:of\s+the\s+)?(?:I\.?\s?P\.?\s?C\.?|Indian\s+Penal\s+Code|Penal\s+Code))?"
)
_CODE_RE = re.compile(r"(?i)\b(?:I\.\s?P\.\s?C\.?|IPC|Indian\s+Penal\s+Code)\b")


def mask_statutes(text):
    """Replace statute citations with [SEC]. Returns (masked_text, n_replacements)."""
    text, n1 = _STATUTE_RE.subn(" [SEC] ", text)
    text, n2 = _CODE_RE.subn(" [SEC] ", text)
    text = re.sub(r"(\[SEC\]\s*)+", "[SEC] ", text)
    return re.sub(r"\s+", " ", text).strip(), n1 + n2


def build_text(sentences):
    if isinstance(sentences, str):
        sentences = [sentences]
    full = " ".join(str(s).strip() for s in sentences if str(s).strip())
    masked, n_masked = mask_statutes(full)
    words = masked.split()
    return " ".join(words[:MAX_WORDS]), len(words), n_masked

# ---------------------------------------------------------------- main pipeline


def read_jsonl(path, stats):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stats["lines"] += 1
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                stats["bad_lines"] += 1


def parse(raw_dir=RAW_DIR, map_csv=MAP_CSV, labels_json=LABELS_JSON):
    ipc_to_ppc = load_ipc_to_ppc(map_csv)
    with open(labels_json, "r", encoding="utf-8") as f:
        valid_ppc = set(json.load(f))
    bad = set(ipc_to_ppc.values()) - valid_ppc
    if bad:
        raise ValueError(f"A1 table maps to PPC labels not in labels.json: {bad}")

    stats = Counter()
    file_stats = {}
    raw_label_examples = Counter()
    dropped_counter = Counter()
    rows, seen_ids = [], set()

    for fname in SPLIT_FILES:
        path = os.path.join(raw_dir, fname)
        if not os.path.exists(path):
            file_stats[fname] = "missing"
            continue
        fs = Counter()
        for doc in read_jsonl(path, fs):
            labels = doc.get("labels") or []
            for l in labels:
                raw_label_examples[str(l)] += 1
            ppc, kept, dropped = map_labels(labels, ipc_to_ppc)
            dropped_counter.update(dropped)
            if not ppc:
                fs["no_mapped_label"] += 1
                continue
            text, n_words, n_masked = build_text(doc.get("text", []))
            if n_words < MIN_WORDS:
                fs["too_short"] += 1
                continue
            doc_id = f"ilsi_{doc.get('id', fs['lines'])}"
            if doc_id in seen_ids:
                fs["duplicate_id"] += 1
                continue
            seen_ids.add(doc_id)
            fs["kept"] += 1
            stats["masked_total"] += n_masked
            rows.append({
                "id": doc_id,
                "text": text,
                "sections": json.dumps(ppc),
                "primary_section": ppc[0],
                "language": "en",
                "source": "ilsi",
                "split": "train",
                "orig_ipc_labels": ";".join(normalize_ipc_label(l) or str(l) for l in labels),
                "dropped_ipc_labels": ";".join(dropped),
                "ilsi_file": fname,
                "n_words_full": n_words,
                "n_masked": n_masked,
            })
        file_stats[fname] = fs
    return rows, file_stats, raw_label_examples, dropped_counter, ipc_to_ppc, stats


def vocab_coverage(raw_dir, ipc_to_ppc):
    """Which IPC sources from the A1 table exist in ILSI's label vocabulary at all."""
    path = os.path.join(raw_dir, "label_vocab.json")
    if not os.path.exists(path):
        return None, None
    with open(path, "r", encoding="utf-8") as f:
        vocab = json.load(f)
    keys = vocab.keys() if isinstance(vocab, dict) else vocab
    in_vocab = {normalize_ipc_label(k) for k in keys} - {None}
    return in_vocab, sorted(set(ipc_to_ppc) - in_vocab, key=lambda s: (int(re.sub(r"\D", "", s)), s))


def write_outputs(rows, file_stats, raw_label_examples, dropped_counter, ipc_to_ppc, stats, raw_dir=RAW_DIR):
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=K3_COLUMNS + AUDIT_COLUMNS)
        w.writeheader()
        w.writerows(rows)

    with open(LABELS_JSON, "r", encoding="utf-8") as f:
        labels = json.load(f)
    counts = Counter(s for r in rows for s in json.loads(r["sections"]))
    in_vocab, missing_sources = vocab_coverage(raw_dir, ipc_to_ppc)
    n_multi = sum(1 for r in rows if len(json.loads(r["sections"])) > 1)
    lengths = sorted(r["n_words_full"] for r in rows) or [0]

    L = ["# A2 Report: ILSI parsing and IPC-to-PPC label mapping", "",
         "Generated by `python -m src.data.ilsi_parse`. Source: LeSICiN / ILSI dataset "
         "(Paul, Goyal & Ghosh, AAAI 2022; Zenodo record 6053791; licence CC BY 4.0).", "",
         "## 1. Files read", "",
         "| File | Lines | Invalid JSON lines | No mapped PPC label | Too short | Kept |",
         "|---|---|---|---|---|---|"]
    for fname, fs in file_stats.items():
        if fs == "missing":
            L.append(f"| {fname} | missing | | | | |")
        else:
            L.append(f"| {fname} | {fs['lines']} | {fs['bad_lines']} | {fs['no_mapped_label']} | {fs['too_short']} | {fs['kept']} |")
    L += ["", "Note: the raw files are partial downloads (the Zenodo transfer was interrupted). JSONL stores one case per line, "
          "so every complete line is a valid case; only the final cut-off line is invalid and is skipped.", "",
          "## 2. Output", "",
          f"- Cases kept: **{len(rows)}**",
          f"- Cases with more than one PPC label: **{n_multi}**",
          f"- Statute mentions masked as `[SEC]`: **{stats['masked_total']}** (label-leakage prevention)",
          f"- Words per case before truncation: median **{lengths[len(lengths)//2]}**, max {lengths[-1]}; "
          f"truncated to the first {MAX_WORDS} words",
          "", "## 3. Examples of raw ILSI label strings", "",
          ", ".join(f"`{k}`" for k, _ in raw_label_examples.most_common(12)) or "(none)",
          "", "## 4. Coverage of the A1 mapping in ILSI's label vocabulary", ""]
    if in_vocab is None:
        L.append("label_vocab.json not found.")
    else:
        L.append(f"ILSI vocabulary size: {len(in_vocab)} IPC sections.")
        L.append(f"A1 source sections **not** in the ILSI vocabulary (these PPC labels get no ILSI data): "
                 f"{', '.join(missing_sources) if missing_sources else 'none'}")
    L += ["", "## 5. Cases per PPC label (ILSI only)", "",
          "| PPC | Title | ILSI cases |", "|---|---|---|"]
    for sec, meta in labels.items():
        title = meta.get("title", "") if isinstance(meta, dict) else ""
        L.append(f"| {sec} | {title} | {counts.get(sec, 0)} |")
    L += ["", "## 6. Most frequent IPC labels that were dropped (not used for any PPC label)", "",
          "| IPC | Times dropped |", "|---|---|"]
    for ipc, c in dropped_counter.most_common(15):
        L.append(f"| {ipc} | {c} |")
    L += ["", "IPC 34 (common intention) and other procedural or out-of-scope sections are dropped by design. "
          "IPC 324 must appear here, never in the PPC counts (A1 trap: hurt by weapon is not attempted murder).", ""]
    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return counts


def main():
    if not os.path.isdir(RAW_DIR):
        sys.exit(f"Raw ILSI folder not found: {RAW_DIR}")
    result = parse()
    counts = write_outputs(*result)
    rows, file_stats = result[0], result[1]
    print(f"Kept {len(rows)} ILSI cases -> {os.path.relpath(OUT_CSV, PROJECT_ROOT)}")
    for fname, fs in file_stats.items():
        print(f"  {fname}: {fs if fs == 'missing' else dict(fs)}")
    print("Cases per PPC label:", dict(sorted(counts.items(), key=lambda kv: -kv[1])))
    print(f"Report -> {os.path.relpath(REPORT_MD, PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
