"""Task A4: Build the combined training dataset with a grouped, stratified train/val split.

Input : data/processed/synthetic.csv, data/processed/ilsi_clean.csv
Output: data/processed/dataset.csv   (K3 columns + group_id)

Rules
- Grouped: all rows sharing a group_id go to the same split, so near-identical stories can never
  appear in both train and val (K3 split rule 2). Synthetic stories carry a group_id; each ILSI case
  is its own group.
- Stratified: within each primary_section, about VAL_FRACTION of the groups go to val, so every
  label appears in validation.
- Real or held-out test data never enters this file (K3 split rule 1).

Run:  python -m src.data.make_splits
"""

import csv
import os
import random
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCES = [os.path.join(PROJECT_ROOT, "data", "processed", "synthetic.csv"),
           os.path.join(PROJECT_ROOT, "data", "processed", "ilsi_clean.csv")]
# Added later (A2b, A3b). They are split separately so the original train/val rows above stay exactly the same,
# which keeps before/after comparisons fair: chat stories get their own grouped split (same rule and seed);
# Supreme Court of Pakistan rows keep the split already assigned in sc_clean.csv.
EXTRA_SPLIT = [os.path.join(PROJECT_ROOT, "data", "processed", "synthetic_chat.csv")]
EXTRA_KEEP = [os.path.join(PROJECT_ROOT, "data", "processed", "sc_facts.csv")]
OUT_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "dataset.csv")
COLUMNS = ["id", "text", "sections", "primary_section", "language", "source", "split", "group_id"]
VAL_FRACTION = 0.2
SEED = 42


def load(paths=SOURCES):
    rows = []
    for p in paths:
        if not os.path.exists(p):
            print(f"warning: {p} not found, skipped")
            continue
        with open(p, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r["group_id"] = r.get("group_id") or r["id"]
                rows.append({c: r.get(c, "") for c in COLUMNS})
    return rows


def grouped_split(rows, val_fraction=VAL_FRACTION, seed=SEED):
    rng = random.Random(seed)
    groups = defaultdict(list)
    for r in rows:
        groups[r["group_id"]].append(r)
    by_label = defaultdict(list)
    for gid, members in groups.items():
        by_label[(members[0]["source"], members[0]["primary_section"])].append(gid)
    val_groups = set()
    for key in sorted(by_label):
        gids = sorted(by_label[key])
        rng.shuffle(gids)
        n_val = max(1, round(len(gids) * val_fraction)) if len(gids) >= 3 else 0
        val_groups.update(gids[:n_val])
    for r in rows:
        r["split"] = "val" if r["group_id"] in val_groups else "train"
    return rows


def main():
    rows = grouped_split(load())
    rows += grouped_split(load(EXTRA_SPLIT))
    rows += load(EXTRA_KEEP)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    for src in sorted({r["source"] for r in rows}):
        tr = sum(r["source"] == src and r["split"] == "train" for r in rows)
        va = sum(r["source"] == src and r["split"] == "val" for r in rows)
        print(f"{src:10s} train {tr:5d}  val {va:4d}")
    print(f"-> {os.path.relpath(OUT_CSV, PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
