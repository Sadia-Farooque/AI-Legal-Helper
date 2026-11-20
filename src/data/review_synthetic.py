"""Task A3: Automated quality checks for the synthetic incident stories.

Checks every row of data/processed/synthetic.csv and writes:
  - docs/A3_review_log.md                        (all check results)
  - data/processed/synthetic_review_sample.csv   (stratified sample for MANUAL review;
                                                  fill the `verdict` column: ok / fix / delete)

Checks
  1. Schema: K3 columns present, sections are valid labels, 307 never used (decision D5)
  2. Label leakage: legal terms or section numbers that give the answer away
  3. Length: too short (< 10 words) or too long (> 100 words)
  4. Duplicates: exact duplicates and near-duplicates (TF-IDF cosine >= 0.85)
  5. Language tag: Roman Urdu rows must contain Urdu function words; English rows must not be mostly Urdu
  6. Balance: stories per section and language

Run:  python -m src.data.review_synthetic            (checks; creates the sample only if it does not exist yet)
      python -m src.data.review_synthetic --summary --reviewer "..."  (summarise the filled-in sample)
"""

import argparse
import csv
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SYN_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "synthetic.csv")
LABELS_JSON = os.path.join(PROJECT_ROOT, "src", "labels.json")
LOG_MD = os.path.join(PROJECT_ROOT, "docs", "A3_review_log.md")
SAMPLE_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "synthetic_review_sample.csv")

K3 = ["id", "text", "sections", "primary_section", "language", "source", "split"]
SAMPLE_PER_SECTION = 3
NEAR_DUP_THRESHOLD = 0.85

# Legal vocabulary a citizen would not normally use, and which names the answer.
LEAK_TERMS = [
    r"\bsection\b", r"\bsec\.", r"\bu/s\b", r"\bppc\b", r"\bipc\b", r"\bpenal code\b",
    r"\bqatl\b", r"qatl-i", r"\bshajjah\b", r"\bjurh\b", r"\bdacoity\b",
    r"breach of trust", r"\btrespass", r"\bdefamation\b", r"\bdefame", r"\bextortion\b",
    r"misappropriat", r"\bintimidation\b", r"\bwrongful", r"\bcognizable\b", r"\bculpable\b",
    r"\b(302|307|319|324|337|339|340|354|363|365|379|380|382|384|392|395|403|406|411|420|441|447|448|489|500|506|509)\b(?!\s*(rupees|rs|lakh|hazaar|thousand))",
]
LEAK_RE = [re.compile(p, re.I) for p in LEAK_TERMS]
URDU_MARKERS = {"hai", "hain", "ne", "ka", "ki", "ke", "ko", "se", "mein", "aur", "nahi", "tha", "thi", "thay",
                "kar", "diya", "gaya", "gayi", "raha", "rahi", "wala", "wale", "mera", "meri", "mere"}


def load_rows(path=SYN_CSV):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_schema(rows, labels):
    problems = []
    for r in rows:
        missing = [c for c in K3 if c not in r or r[c] == ""]
        if missing:
            problems.append((r.get("id"), f"missing {missing}"))
            continue
        secs = json.loads(r["sections"])
        bad = [s for s in secs if s not in labels]
        if bad:
            problems.append((r["id"], f"unknown sections {bad}"))
        if "307" in secs:
            problems.append((r["id"], "uses 307 (not a citizen-facing PPC offence, see D5)"))
        if r["primary_section"] not in secs:
            problems.append((r["id"], "primary_section not in sections"))
        if r["language"] not in {"en", "roman_ur"}:
            problems.append((r["id"], f"bad language {r['language']}"))
    return problems


def check_leaks(rows):
    hits = []
    for r in rows:
        found = [p.pattern for p in LEAK_RE if p.search(r["text"])]
        if found:
            hits.append((r["id"], found))
    return hits


def check_length(rows, lo=10, hi=100):
    return [(r["id"], len(r["text"].split())) for r in rows if not lo <= len(r["text"].split()) <= hi]


def check_duplicates(rows):
    exact = [k for k, c in Counter(r["text"].strip().lower() for r in rows).items() if c > 1]
    near = []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        texts = [r["text"] for r in rows]
        X = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True).fit_transform(texts)
        S = cosine_similarity(X)
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if S[i, j] >= NEAR_DUP_THRESHOLD:
                    near.append((rows[i]["id"], rows[j]["id"], round(float(S[i, j]), 3)))
    except ImportError:
        near = None
    return exact, near


def check_language(rows):
    wrong = []
    for r in rows:
        toks = re.findall(r"[a-z]+", r["text"].lower())
        share = sum(t in URDU_MARKERS for t in toks) / max(len(toks), 1)
        if r["language"] == "roman_ur" and share < 0.10:
            wrong.append((r["id"], "tagged roman_ur but few Urdu words", round(share, 2)))
        if r["language"] == "en" and share > 0.25:
            wrong.append((r["id"], "tagged en but mostly Urdu", round(share, 2)))
    return wrong


def balance(rows):
    table = defaultdict(Counter)
    for r in rows:
        for s in json.loads(r["sections"]):
            table[s][r["language"]] += 1
    return table


def make_sample(rows, seed=42, force=False):
    """Write the manual-review sample. An existing sample (with verdicts) is never overwritten unless force=True."""
    if os.path.exists(SAMPLE_CSV) and not force:
        with open(SAMPLE_CSV, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    rng = random.Random(seed)
    by_sec = defaultdict(list)
    for r in rows:
        by_sec[r["primary_section"]].append(r)
    sample = []
    for sec in sorted(by_sec):
        group = by_sec[sec]
        en = [r for r in group if r["language"] == "en"]
        ur = [r for r in group if r["language"] == "roman_ur"]
        pick = rng.sample(en, min(2, len(en))) + rng.sample(ur, min(SAMPLE_PER_SECTION - 2, len(ur)))
        sample.extend(pick)
    with open(SAMPLE_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "sections", "language", "text", "verdict", "comment"])
        for r in sample:
            w.writerow([r["id"], r["sections"], r["language"], r["text"], "", ""])
    return sample


def write_log(rows, labels, results, sample_n):
    schema, leaks, lengths, (exact, near), lang = results
    bal = balance(rows)
    n_multi = sum(len(json.loads(r["sections"])) > 1 for r in rows)
    L = ["# A3 Review Log: synthetic incident stories", "",
         "Generated by `python -m src.data.review_synthetic`.", "",
         "## Summary", "",
         f"- Stories checked: **{len(rows)}** (English {sum(r['language']=='en' for r in rows)}, "
         f"Roman Urdu {sum(r['language']=='roman_ur' for r in rows)}; multi-offence {n_multi})",
         f"- Schema problems: **{len(schema)}**",
         f"- Label-leak hits (legal terms / section numbers in the text): **{len(leaks)}**",
         f"- Length out of range (10–100 words): **{len(lengths)}**",
         f"- Exact duplicates: **{len(exact)}**",
         f"- Near-duplicates (char TF-IDF cosine >= {NEAR_DUP_THRESHOLD}): "
         f"**{'not checked' if near is None else len(near)}**",
         f"- Language-tag problems: **{len(lang)}**",
         f"- Manual review sample: **{sample_n}** stories in `data/processed/synthetic_review_sample.csv`", ""]
    for title, items in [("Schema problems", schema), ("Label-leak hits", leaks), ("Length problems", lengths),
                         ("Near-duplicates", near or []), ("Language-tag problems", lang)]:
        if items:
            L += [f"## {title}", ""] + [f"- {it}" for it in items] + [""]
    L += ["## Stories per section", "", "| Section | Title | English | Roman Urdu | Total |", "|---|---|---|---|---|"]
    for sec, meta in labels.items():
        c = bal.get(sec, Counter())
        L.append(f"| {sec} | {meta.get('title','')} | {c['en']} | {c['roman_ur']} | {c['en']+c['roman_ur']} |")
    L += ["", "307 has 0 stories by design (decision D5).", ""]
    with open(LOG_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def summarise_manual(reviewer):
    with open(SAMPLE_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    v = Counter((r["verdict"] or "").strip().lower() for r in rows)
    lines = ["", "## Manual review result", "",
             f"Reviewer: {reviewer}. Sample: {len(rows)} stories (stratified: up to 2 English + 1 Roman Urdu per section, seed 42), "
             "judged against the per-section rules in docs/A3_generation_note.md. Fixes, including the dataset-wide "
             "sweep for the same error patterns, are listed in docs/A3_review_fixes.md.", "",
             f"- ok: **{v['ok']}**", f"- fix: **{v['fix']}**", f"- delete: **{v['delete']}**",
             f"- not reviewed: **{v['']}**", ""]
    for r in rows:
        if (r["verdict"] or "").strip().lower() in {"fix", "delete"}:
            lines.append(f"- {r['id']} ({r['verdict']}): {r['comment']}")
    with open(LOG_MD, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(dict(v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", action="store_true", help="summarise the filled manual-review sample")
    ap.add_argument("--reviewer", default="Sadia Fatima", help="who did the manual review (recorded in the log)")
    ap.add_argument("--resample", action="store_true", help="draw a new review sample (overwrites verdicts)")
    args = ap.parse_args()
    if args.summary:
        summarise_manual(args.reviewer)
        return
    rows = load_rows()
    with open(LABELS_JSON, "r", encoding="utf-8") as f:
        labels = json.load(f)
    results = (check_schema(rows, labels), check_leaks(rows), check_length(rows),
               check_duplicates(rows), check_language(rows))
    sample = make_sample(rows, force=args.resample)
    write_log(rows, labels, results, len(sample))
    schema, leaks, lengths, (exact, near), lang = results
    print(f"{len(rows)} stories | schema {len(schema)} | leaks {len(leaks)} | length {len(lengths)} | "
          f"exact dup {len(exact)} | near dup {'n/a' if near is None else len(near)} | language {len(lang)}")
    print(f"Log -> {os.path.relpath(LOG_MD, PROJECT_ROOT)} | sample of {len(sample)} -> "
          f"{os.path.relpath(SAMPLE_CSV, PROJECT_ROOT)}")
    if schema:
        sys.exit(1)


if __name__ == "__main__":
    main()
