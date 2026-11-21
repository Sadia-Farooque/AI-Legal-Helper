"""A2b: Pakistani training data from Supreme Court of Pakistan criminal judgments (Track B's B3 corpus).

Input : data/processed/sc_clean.csv (301 judgments with the PPC sections they cite; split already assigned)
Output: data/processed/sc_facts.csv (K3 columns, source = "sc_pk")

For each judgment we keep only the passage that states the facts of the occurrence ("prosecution case",
"facts of the case", "allegation" ...), not the court header (judges, parties, lawyers), which carries no
incident information. Statute citations are masked to [SEC] as for ILSI, and any remaining bare section numbers
(e.g. "302", "489-F") and "PPC" are removed, so the model cannot read the answer from the text.
Judgments with no facts passage are skipped. The existing train/val split of sc_clean.csv is kept.

Run:  python -m src.data.sc_facts
"""

import csv
import os
import re

from src.data.ilsi_parse import mask_statutes

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IN_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "sc_clean.csv")
OUT_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "sc_facts.csv")
COLUMNS = ["id", "text", "sections", "primary_section", "language", "source", "split", "group_id"]

_START = re.compile(r"(prosecution case|prosecution story|facts of the case|brief facts|allegation against|"
                    r"allegations against|case of the prosecution|according to the (?:fir|crime report|complainant)|"
                    r"as per (?:the )?(?:fir|crime report)|the occurrence)", re.I)
_SECNUM = re.compile(r"\b(?:sections?|ss?\.|u/s)?\s*\d{3}(?:-?[A-Z])?(?:\s*(?:,|/|and|&)\s*\d{3}(?:-?[A-Z])?)*"
                     r"\s*(?:PPC|P\.P\.C\.?|of the (?:Pakistan )?Penal Code)", re.I)
_BARE = re.compile(r"\b(?:PPC|P\.P\.C\.?|Pakistan Penal Code|CrPC|Cr\.P\.C\.?)\b", re.I)
_LABELNUM = re.compile(r"\b(?:302|319|324|337|339|340|354|363|365|379|380|382|384|392|395|403|406|411|420|441|"
                       r"447|448|489|500|506|509)(?:-?[A-Z])?\b")
MAX_CHARS = 900


def facts_passage(full_text):
    m = _START.search(full_text or "")
    if not m:
        return None
    return re.sub(r"\s+", " ", full_text[m.start(): m.start() + MAX_CHARS]).strip()


def clean(text):
    text = _SECNUM.sub(" [SEC] ", text)
    text, _ = mask_statutes(text)
    text = _LABELNUM.sub(" [SEC] ", _BARE.sub(" ", text))
    return re.sub(r"(\[SEC\]\s*)+", "[SEC] ", re.sub(r"\s+", " ", text)).strip()


def main():
    out, skipped = [], 0
    with open(IN_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = facts_passage(r["full_text"])
            if not p or len(p) < 200:
                skipped += 1
                continue
            out.append({"id": r["id"], "text": clean(p), "sections": r["sections"],
                        "primary_section": r["primary_section"], "language": "en", "source": "sc_pk",
                        "split": r["split"], "group_id": r["id"]})
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    tr = sum(o["split"] == "train" for o in out)
    print(f"kept {len(out)} judgments (train {tr}, val {len(out) - tr}), skipped {skipped} without a facts passage")
    print(f"-> {os.path.relpath(OUT_CSV, PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
