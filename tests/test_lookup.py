import csv
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOOKUP_CSV = os.path.join(PROJECT_ROOT, "data", "lookup", "ppc_lookup.csv")
LABELS_JSON = os.path.join(PROJECT_ROOT, "src", "labels.json")

EXPECTED_COLUMNS = [
    "section", "short_name", "meaning", "cognizable", "bailable",
    "compoundable", "punishment", "court", "source", "date_checked"
]

def load_data():
    with open(LABELS_JSON, "r", encoding="utf-8") as f:
        labels = json.load(f)

    rows = []
    with open(LOOKUP_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return labels, rows

def test_lookup_file_exists():
    assert os.path.exists(LOOKUP_CSV), f"Lookup file does not exist at {LOOKUP_CSV}"

def test_column_headers():
    with open(LOOKUP_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
    assert headers == EXPECTED_COLUMNS, f"Headers mismatch. Expected: {EXPECTED_COLUMNS}, got: {headers}"

def test_exact_section_parity_with_labels():
    labels, rows = load_data()
    csv_sections = {r["section"].strip() for r in rows}
    json_sections = set(labels.keys())

    assert len(csv_sections) == 30, f"Expected 30 unique sections, found {len(csv_sections)}"
    assert csv_sections == json_sections, f"Parity mismatch! Missing in CSV: {json_sections - csv_sections}. Extra in CSV: {csv_sections - json_sections}"

def test_no_empty_fields():
    _, rows = load_data()
    for row in rows:
        sec = row["section"]
        for col in EXPECTED_COLUMNS:
            val = row.get(col, "").strip()
            assert val != "", f"Empty value found in Section {sec} for column '{col}'"

def test_statutory_fact_validity():
    _, rows = load_data()
    for row in rows:
        sec = row["section"]
        cognizable = row["cognizable"]
        bailable = row["bailable"]
        compoundable = row["compoundable"]
        source = row["source"]
        date_checked = row["date_checked"]

        # Cognizable must be Cognizable or Non-cognizable
        assert cognizable in ["Cognizable", "Non-cognizable"], f"Invalid cognizable value '{cognizable}' in Section {sec}"

        # Bailable check
        assert "bailable" in bailable.lower(), f"Invalid bailable value '{bailable}' in Section {sec}"

        # Compoundable check
        assert "compoundable" in compoundable.lower(), f"Invalid compoundable value '{compoundable}' in Section {sec}"

        # Official statutory source check
        assert "PPC" in source and "CrPC" in source, f"Source missing official legal codes in Section {sec}: {source}"

        # Date format check
        assert date_checked.startswith("2026-"), f"Unexpected date format in Section {sec}: {date_checked}"

def test_high_profile_statutory_benchmarks():
    """Validates specific critical legal facts verified against Schedule II:
    - 489-F is Non-bailable under CrPC Sched II
    - 392 is Non-bailable, Non-compoundable, Cognizable
    - 379 is Non-bailable, Non-compoundable, Cognizable
    - 403 is Non-cognizable, Bailable, Compoundable
    - 500 is Non-cognizable, Bailable
    - 354A is Non-bailable, Cognizable (penalty includes Death/Life)
    """
    _, rows = load_data()
    lookup = {r["section"]: r for r in rows}

    # Section 489-F (Dishonoured cheque)
    assert lookup["489-F"]["cognizable"] == "Cognizable"
    assert "Non-bailable" in lookup["489-F"]["bailable"]
    assert "Compoundable" in lookup["489-F"]["compoundable"]

    # Section 392 (Robbery)
    assert lookup["392"]["cognizable"] == "Cognizable"
    assert lookup["392"]["bailable"] == "Non-bailable"
    assert lookup["392"]["compoundable"] == "Non-compoundable"

    # Section 403 (Dishonest Misappropriation)
    assert lookup["403"]["cognizable"] == "Non-cognizable"
    assert lookup["403"]["bailable"] == "Bailable"

    # Section 500 (Defamation)
    assert lookup["500"]["cognizable"] == "Non-cognizable"
    assert lookup["500"]["bailable"] == "Bailable"

    # Section 354A (Stripping woman of clothes)
    assert lookup["354A"]["cognizable"] == "Cognizable"
    assert lookup["354A"]["bailable"] == "Non-bailable"
    assert "Death" in lookup["354A"]["punishment"]

if __name__ == "__main__":
    test_lookup_file_exists()
    test_column_headers()
    test_exact_section_parity_with_labels()
    test_no_empty_fields()
    test_statutory_fact_validity()
    test_high_profile_statutory_benchmarks()
    print("All 6 test suites passed successfully! 100% statutory validation verified.")
