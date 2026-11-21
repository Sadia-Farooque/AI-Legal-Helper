"""
tests/test_sc_clean.py
Task B3 – Automated integrity tests for data/processed/sc_clean.csv
Run with: python tests/test_sc_clean.py
"""

import json
import os
import sys
import csv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "sc_clean.csv")
LABELS_JSON = os.path.join(PROJECT_ROOT, "src", "labels.json")

REQUIRED_COLUMNS = {
    "id", "text", "full_text", "sections", "primary_section",
    "language", "source", "split", "case_title", "citation_number"
}

PASS = "✅ PASS"
FAIL = "❌ FAIL"

def load_csv():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def load_labels():
    with open(LABELS_JSON, encoding="utf-8") as f:
        return set(json.load(f).keys())

def run_all():
    failures = []

    # --- TEST 1: File exists ---
    print("TEST 1: File exists and is non-empty")
    if not os.path.isfile(CSV_PATH):
        print(f"  {FAIL}: {CSV_PATH} not found")
        sys.exit(1)
    size = os.path.getsize(CSV_PATH)
    if size < 1000:
        failures.append(f"TEST 1: file too small ({size} bytes)")
        print(f"  {FAIL}: file too small ({size} bytes)")
    else:
        print(f"  {PASS}: {size:,} bytes")

    rows = load_csv()
    labels = load_labels()

    # --- TEST 2: Minimum row count (>=100) ---
    print("TEST 2: Minimum 100 rows")
    if len(rows) < 100:
        failures.append(f"TEST 2: only {len(rows)} rows, need >=100")
        print(f"  {FAIL}: {len(rows)} rows")
    else:
        print(f"  {PASS}: {len(rows)} rows extracted")

    # --- TEST 3: Required columns ---
    print("TEST 3: Required columns present")
    if not rows:
        failures.append("TEST 3: no rows loaded")
        print(f"  {FAIL}: no rows")
    else:
        actual_cols = set(rows[0].keys())
        missing = REQUIRED_COLUMNS - actual_cols
        if missing:
            failures.append(f"TEST 3: missing columns {missing}")
            print(f"  {FAIL}: missing {missing}")
        else:
            print(f"  {PASS}: all {len(REQUIRED_COLUMNS)} required columns present")

    # --- TEST 4: source == "sc" for all rows ---
    print("TEST 4: source == 'sc' for every row")
    bad_source = [r["id"] for r in rows if r.get("source", "") != "sc"]
    if bad_source:
        failures.append(f"TEST 4: {len(bad_source)} rows with wrong source")
        print(f"  {FAIL}: {len(bad_source)} rows have wrong source")
    else:
        print(f"  {PASS}: all rows have source='sc'")

    # --- TEST 5: language == "en" for all rows ---
    print("TEST 5: language == 'en' for every row")
    bad_lang = [r["id"] for r in rows if r.get("language", "") != "en"]
    if bad_lang:
        failures.append(f"TEST 5: {len(bad_lang)} rows with wrong language")
        print(f"  {FAIL}: {len(bad_lang)} rows")
    else:
        print(f"  {PASS}: all rows have language='en'")

    # --- TEST 6: split is either "train" or "val" ---
    print("TEST 6: split in {train, val}")
    bad_split = [r["id"] for r in rows if r.get("split", "") not in ("train", "val")]
    if bad_split:
        failures.append(f"TEST 6: {len(bad_split)} rows with invalid split")
        print(f"  {FAIL}: {len(bad_split)} rows with invalid split")
    else:
        train_n = sum(1 for r in rows if r["split"] == "train")
        val_n   = sum(1 for r in rows if r["split"] == "val")
        print(f"  {PASS}: train={train_n}, val={val_n}")

    # --- TEST 7: text length >=150 chars per row ---
    print("TEST 7: text length >= 150 chars per row")
    short_text = [r["id"] for r in rows if len(r.get("text", "")) < 150]
    if short_text:
        failures.append(f"TEST 7: {len(short_text)} rows with text <150 chars")
        print(f"  {FAIL}: {len(short_text)} rows have text shorter than 150 chars")
    else:
        avg_len = sum(len(r["text"]) for r in rows) // len(rows)
        print(f"  {PASS}: all rows >=150 chars (avg {avg_len} chars)")

    # --- TEST 8: sections parses as JSON list with known labels ---
    print("TEST 8: 'sections' is valid JSON list; each label in labels.json")
    parse_errors = []
    unknown_labels = []
    for r in rows:
        raw = r.get("sections", "")
        try:
            secs = json.loads(raw)
            if not isinstance(secs, list) or len(secs) == 0:
                parse_errors.append(r["id"])
                continue
            for s in secs:
                if s not in labels:
                    unknown_labels.append((r["id"], s))
        except json.JSONDecodeError:
            parse_errors.append(r["id"])
    if parse_errors:
        failures.append(f"TEST 8a: {len(parse_errors)} rows with invalid sections JSON")
        print(f"  {FAIL}: {len(parse_errors)} rows with invalid sections JSON")
    elif unknown_labels:
        failures.append(f"TEST 8b: {len(unknown_labels)} unknown section labels")
        print(f"  {FAIL}: {len(unknown_labels)} unknown labels: {unknown_labels[:5]}")
    else:
        print(f"  {PASS}: all sections parse correctly and are known PPC labels")

    # --- TEST 9: primary_section is first element of sections ---
    print("TEST 9: primary_section == sections[0]")
    mismatch = []
    for r in rows:
        try:
            secs = json.loads(r.get("sections", "[]"))
            if secs and r.get("primary_section", "") != secs[0]:
                mismatch.append(r["id"])
        except Exception:
            pass
    if mismatch:
        failures.append(f"TEST 9: {len(mismatch)} rows with mismatched primary_section")
        print(f"  {FAIL}: {len(mismatch)} rows mismatched")
    else:
        print(f"  {PASS}: primary_section consistent with sections[0]")

    # --- TEST 10: IDs are unique ---
    print("TEST 10: row IDs are unique")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        dup = len(ids) - len(set(ids))
        failures.append(f"TEST 10: {dup} duplicate IDs")
        print(f"  {FAIL}: {dup} duplicate IDs")
    else:
        print(f"  {PASS}: all {len(ids)} IDs unique")

    # --- TEST 11: Section coverage (at minimum 302, 324, 365-A present) ---
    print("TEST 11: Key sections (302, 324, 365-A) present in dataset")
    all_sections = set()
    for r in rows:
        try:
            all_sections.update(json.loads(r.get("sections", "[]")))
        except Exception:
            pass
    required_secs = {"302", "324", "365-A"}
    missing_secs = required_secs - all_sections
    if missing_secs:
        failures.append(f"TEST 11: missing expected sections {missing_secs}")
        print(f"  {FAIL}: missing sections {missing_secs}")
    else:
        print(f"  {PASS}: all key sections present — found {len(all_sections)} distinct sections total")

    # --- TEST 12: citation_number non-empty for most rows (>=50%) ---
    print("TEST 12: citation_number non-empty for >= 50% of rows")
    has_citation = sum(1 for r in rows if r.get("citation_number", "").strip())
    pct = has_citation / len(rows) * 100 if rows else 0
    if pct < 50:
        failures.append(f"TEST 12: only {pct:.1f}% rows have citation_number")
        print(f"  {FAIL}: {pct:.1f}% have citation_number (need >=50%)")
    else:
        print(f"  {PASS}: {has_citation}/{len(rows)} ({pct:.1f}%) rows have citation_number")

    # --- SUMMARY ---
    print()
    print("=" * 55)
    if failures:
        print(f"RESULT: {len(failures)} test(s) FAILED:")
        for f in failures:
            print(f"  ❌ {f}")
        sys.exit(1)
    else:
        print(f"RESULT: All 12 tests PASSED ✅  ({len(rows)} rows in sc_clean.csv)")
    print("=" * 55)


if __name__ == "__main__":
    run_all()
