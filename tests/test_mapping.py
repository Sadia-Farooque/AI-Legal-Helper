"""Validation tests for Task A1: IPC-to-PPC mapping table (data/mapping/ipc_ppc_map.csv).

These tests stop Indian (IPC) section numbers from leaking into the Pakistani (PPC)
label space when ILSI training data is mapped in Task A2.

Run:  python tests/test_mapping.py     (or)    pytest tests/test_mapping.py
"""

import csv
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAP_CSV = os.path.join(PROJECT_ROOT, "data", "mapping", "ipc_ppc_map.csv")
LABELS_JSON = os.path.join(PROJECT_ROOT, "src", "labels.json")

EXPECTED_COLUMNS = [
    "ppc_section", "ppc_title", "ipc_equivalent", "ilsi_source_sections",
    "status", "use_ilsi", "notes", "source", "date_checked",
]
VALID_STATUS = {
    "Same", "Changed-compatible", "Mapped (different number)",
    "Not in IPC", "Label error", "Label conflict",
}
# Statuses for which ILSI data is safe to use
USABLE_STATUS = {"Same", "Changed-compatible", "Mapped (different number)"}


def load_rows():
    with open(MAP_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_labels():
    with open(LABELS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def ilsi_sources(row):
    return [s.strip() for s in row["ilsi_source_sections"].split(";") if s.strip()]


def test_file_and_columns():
    assert os.path.exists(MAP_CSV), f"Mapping file missing: {MAP_CSV}"
    with open(MAP_CSV, "r", encoding="utf-8") as f:
        headers = next(csv.reader(f))
    assert headers == EXPECTED_COLUMNS, f"Header mismatch: {headers}"


def test_parity_with_labels():
    rows, labels = load_rows(), load_labels()
    mapped = [r["ppc_section"] for r in rows]
    assert len(mapped) == len(set(mapped)), "Duplicate PPC section rows"
    assert set(mapped) == set(labels), (
        f"Missing: {set(labels) - set(mapped)}  Extra: {set(mapped) - set(labels)}"
    )


def test_status_and_flags_are_consistent():
    for r in load_rows():
        sec = r["ppc_section"]
        assert r["status"] in VALID_STATUS, f"{sec}: bad status {r['status']}"
        assert r["use_ilsi"] in {"yes", "no"}, f"{sec}: use_ilsi must be yes/no"
        assert r["notes"].strip(), f"{sec}: every decision needs a note"
        if r["use_ilsi"] == "yes":
            assert r["status"] in USABLE_STATUS, f"{sec}: uses ILSI but status is {r['status']}"
            assert ilsi_sources(r), f"{sec}: uses ILSI but lists no IPC source sections"
        else:
            assert not ilsi_sources(r), f"{sec}: use_ilsi=no but IPC sources listed"


def test_no_ipc_section_feeds_two_ppc_labels():
    """One ILSI case label must map to exactly one PPC label, or training labels become ambiguous."""
    seen = {}
    for r in load_rows():
        for ipc in ilsi_sources(r):
            assert ipc not in seen, f"IPC {ipc} mapped to both PPC {seen[ipc]} and {r['ppc_section']}"
            seen[ipc] = r["ppc_section"]


def test_known_ipc_ppc_traps():
    """Hard-coded legal checks: same number, different offence in the two codes."""
    by_sec = {r["ppc_section"]: r for r in load_rows()}
    all_sources = {ipc for r in by_sec.values() for ipc in ilsi_sources(r)}

    # IPC 324 = hurt by dangerous weapon; PPC 324 = attempted qatl-i-amd (IPC 307)
    assert "324" not in all_sources, "IPC 324 (hurt by weapon) must never be used as training data"
    assert ilsi_sources(by_sec["324"]) == ["307"], "PPC 324 must take ILSI cases from IPC 307"

    # IPC 319 = hurt; PPC 319 = qatl-i-khata
    assert "319" not in all_sources and "323" not in all_sources, "IPC hurt sections must not be mapped"

    # Pakistan-only or restructured sections take no ILSI data
    for sec in ["307", "337-A", "337-F", "354A", "489-F"]:
        assert by_sec[sec]["use_ilsi"] == "no", f"PPC {sec} must not use ILSI data"

    # Kidnapping for ransom: IPC 364A -> PPC 365-A
    assert ilsi_sources(by_sec["365-A"]) == ["364A"]


if __name__ == "__main__":
    test_file_and_columns()
    test_parity_with_labels()
    test_status_and_flags_are_consistent()
    test_no_ipc_section_feeds_two_ppc_labels()
    test_known_ipc_ppc_traps()
    print("All 5 mapping tests passed.")
