"""
tests/test_quiz_bank.py
Task B6 — Automated integrity test suite for data/content/quiz_bank.json.

Asserts:
  T1  — File exists, non-empty, and parses as valid JSON list
  T2  — Total question count >= 60
  T3  — Complete schema: all 10 required fields present in every record
  T4  — All question IDs are unique (no duplicates)
  T5  — Complete statutory coverage: all 30 PPC sections represented >= 2 times
  T6  — Exactly 4 distinct options per question
  T7  — correct_index in [0..3] and corresponds to target_section
  T8  — Difficulty tiering distribution (easy, medium, hard all populated)
  T9  — Substantive length thresholds (scenario >= 100 chars, explanation >= 80 chars)
  T10 — Confusable group IDs adhere to referential integrity with confusable_groups.json

Run with:
  python tests/test_quiz_bank.py
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QUIZ_JSON_PATH = os.path.join(PROJECT_ROOT, "data", "content", "quiz_bank.json")
LABELS_PATH = os.path.join(PROJECT_ROOT, "src", "labels.json")
CONFUSABLE_PATH = os.path.join(PROJECT_ROOT, "data", "content", "confusable_groups.json")

REQUIRED_FIELDS = {
    "id",
    "category",
    "difficulty",
    "confusable_group_id",
    "target_section",
    "scenario",
    "options",
    "correct_index",
    "legal_elements_tested",
    "explanation",
}

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def run_all():
    failures = []

    # --- T1: File existence & JSON parsing ---
    print("T1: File exists and parses as JSON list")
    if not os.path.exists(QUIZ_JSON_PATH):
        print(f"  {FAIL}: {QUIZ_JSON_PATH} missing")
        sys.exit(1)
    try:
        with open(QUIZ_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            failures.append("T1: root element is not a JSON list")
            print(f"  {FAIL}: type={type(data)}")
        else:
            print(f"  {PASS}: {QUIZ_JSON_PATH} parsed cleanly ({len(data)} items)")
    except Exception as e:
        print(f"  {FAIL}: JSON parse error: {e}")
        sys.exit(1)

    # --- T2: Question count >= 60 ---
    print("T2: Minimum 60 scenario questions")
    if len(data) < 60:
        failures.append(f"T2: only {len(data)} questions found, expected >= 60")
        print(f"  {FAIL}: count={len(data)}")
    else:
        print(f"  {PASS}: {len(data)} questions found")

    # --- T3: Complete schema ---
    print("T3: All 10 required fields present in every question")
    missing_fields = []
    for q in data:
        missing = REQUIRED_FIELDS - set(q.keys())
        if missing:
            missing_fields.append((q.get("id", "unknown"), missing))
    if missing_fields:
        failures.append(f"T3: {len(missing_fields)} records missing fields: {missing_fields[:3]}")
        print(f"  {FAIL}: missing fields in {len(missing_fields)} records")
    else:
        print(f"  {PASS}: all {len(data)} records conform to 10-field canonical schema")

    # --- T4: Unique IDs ---
    print("T4: Question IDs are unique")
    ids = [q["id"] for q in data]
    dups = len(ids) - len(set(ids))
    if dups > 0:
        failures.append(f"T4: {dups} duplicate question IDs detected")
        print(f"  {FAIL}: {dups} duplicates")
    else:
        print(f"  {PASS}: all {len(ids)} question IDs are strictly unique")

    # --- T5: Statutory coverage (all 30 sections >= 2 times) ---
    print("T5: 100% coverage of all 30 PPC sections (>= 2 questions each)")
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)
    all_sections = set(labels.keys())

    counts = {}
    for q in data:
        t = q.get("target_section", "")
        counts[t] = counts.get(t, 0) + 1

    missing_sections = all_sections - set(counts.keys())
    underrepresented = {s: counts[s] for s in counts if counts[s] < 2}

    if missing_sections:
        failures.append(f"T5: missing target sections: {missing_sections}")
        print(f"  {FAIL}: missing sections {missing_sections}")
    elif underrepresented:
        failures.append(f"T5: sections with <2 questions: {underrepresented}")
        print(f"  {FAIL}: underrepresented sections {underrepresented}")
    else:
        print(f"  {PASS}: all 30 target sections represented >= 2 times (mean={len(data)/30:.1f})")

    # --- T6: Exactly 4 distinct options ---
    print("T6: Exactly 4 unique options per question")
    bad_options = []
    for q in data:
        opts = q.get("options", [])
        if not isinstance(opts, list) or len(opts) != 4 or len(set(opts)) != 4:
            bad_options.append(q["id"])
    if bad_options:
        failures.append(f"T6: {len(bad_options)} questions have invalid options: {bad_options[:3]}")
        print(f"  {FAIL}: {len(bad_options)} questions failed options cardinality/uniqueness")
    else:
        print(f"  {PASS}: all questions have exactly 4 unique options")

    # --- T7: correct_index in [0..3] and references target_section ---
    print("T7: correct_index in [0..3] and option references target_section")
    mismatches = []
    for q in data:
        idx = q.get("correct_index", -1)
        opts = q.get("options", [])
        target = q.get("target_section", "")
        if not (isinstance(idx, int) and 0 <= idx < len(opts)):
            mismatches.append((q["id"], "out_of_range"))
            continue
        correct_opt = opts[idx]
        if target not in correct_opt:
            mismatches.append((q["id"], f"target '{target}' not in '{correct_opt}'"))
    if mismatches:
        failures.append(f"T7: {len(mismatches)} questions have mismatched correct_index: {mismatches[:3]}")
        print(f"  {FAIL}: {len(mismatches)} mismatches")
    else:
        print(f"  {PASS}: all correct_index entries valid and correspond to target_section")

    # --- T8: Difficulty tiering ---
    print("T8: Difficulty tier distribution (easy >= 15, medium >= 25, hard >= 10)")
    diffs = {}
    for q in data:
        d = q.get("difficulty", "unknown")
        diffs[d] = diffs.get(d, 0) + 1
    easy_c = diffs.get("easy", 0)
    med_c = diffs.get("medium", 0)
    hard_c = diffs.get("hard", 0)

    if easy_c < 15 or med_c < 25 or hard_c < 10:
        failures.append(f"T8: difficulty counts insufficient: easy={easy_c}, medium={med_c}, hard={hard_c}")
        print(f"  {FAIL}: distribution {diffs}")
    else:
        print(f"  {PASS}: easy={easy_c}, medium={med_c}, hard={hard_c} (total={len(data)})")

    # --- T9: Substantive length thresholds ---
    print("T9: Substantive text length (scenario >= 100 chars, explanation >= 80 chars)")
    short_scenarios = [q["id"] for q in data if len(q.get("scenario", "").strip()) < 100]
    short_explanations = [q["id"] for q in data if len(q.get("explanation", "").strip()) < 80]
    if short_scenarios or short_explanations:
        failures.append(f"T9: short text: scenarios={len(short_scenarios)}, explanations={len(short_explanations)}")
        print(f"  {FAIL}: short text detected")
    else:
        avg_s = sum(len(q["scenario"]) for q in data) // len(data)
        avg_e = sum(len(q["explanation"]) for q in data) // len(data)
        print(f"  {PASS}: all scenarios >= 100 chars (avg {avg_s}), explanations >= 80 chars (avg {avg_e})")

    # --- T10: Confusable groups referential integrity ---
    print("T10: Confusable group referential integrity")
    with open(CONFUSABLE_PATH, "r", encoding="utf-8") as f:
        conf_groups = json.load(f)
    valid_group_ids = {g["group_id"] for g in conf_groups}

    bad_group_refs = []
    for q in data:
        gid = q.get("confusable_group_id")
        if gid is not None and gid not in valid_group_ids:
            bad_group_refs.append((q["id"], gid))

    if bad_group_refs:
        failures.append(f"T10: {len(bad_group_refs)} invalid group references: {bad_group_refs[:3]}")
        print(f"  {FAIL}: invalid group refs {bad_group_refs}")
    else:
        print(f"  {PASS}: all referenced confusable_group_ids exist in confusable_groups.json")

    # --- Summary ---
    print()
    print("=" * 65)
    if failures:
        print(f"RESULT: {len(failures)} test(s) FAILED:")
        for f in failures:
            print(f"  ❌ {f}")
        sys.exit(1)
    else:
        print(f"RESULT: All 10 tests PASSED ✅ (Task B6 Quiz Bank Verified)")
    print("=" * 65)


if __name__ == "__main__":
    run_all()
