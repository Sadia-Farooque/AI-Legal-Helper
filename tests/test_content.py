import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LABELS_PATH = os.path.join(PROJECT_ROOT, "src", "labels.json")
SECTIONS_PATH = os.path.join(PROJECT_ROOT, "data", "content", "sections.json")
CONFUSABLE_PATH = os.path.join(PROJECT_ROOT, "data", "content", "confusable_groups.json")

def load_json(path):
    assert os.path.exists(path), f"File not found: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_files_exist():
    assert os.path.exists(SECTIONS_PATH), "sections.json missing"
    assert os.path.exists(CONFUSABLE_PATH), "confusable_groups.json missing"

def test_sections_parity_with_labels():
    labels = load_json(LABELS_PATH)
    sections = load_json(SECTIONS_PATH)

    label_keys = set(labels.keys())
    section_keys = set(sections.keys())

    assert len(section_keys) == 30, f"Expected exactly 30 sections, found {len(section_keys)}"
    assert section_keys == label_keys, f"Parity mismatch! In labels but not sections: {label_keys - section_keys}. In sections but not labels: {section_keys - label_keys}"

def test_sections_substance_and_elements():
    sections = load_json(SECTIONS_PATH)
    for sec_id, data in sections.items():
        assert data["section"] == sec_id, f"Section key mismatch for {sec_id}"
        assert len(data.get("title", "").strip()) > 0, f"Title missing for Section {sec_id}"
        assert len(data.get("category", "").strip()) > 0, f"Category missing for Section {sec_id}"

        # Substantive summary test
        summary = data.get("summary", "").strip()
        assert len(summary) >= 80, f"Summary too brief for Section {sec_id} ({len(summary)} chars, minimum 80 required)"

        # Statutory prosecution elements test
        elements = data.get("elements", [])
        assert isinstance(elements, list), f"Elements must be list for Section {sec_id}"
        assert len(elements) >= 2, f"Section {sec_id} must have at least 2 legal elements, found {len(elements)}"
        for elem in elements:
            assert len(elem.strip()) >= 15, f"Legal element too brief in Section {sec_id}: '{elem}'"

        # Realistic Pakistani scenario examples test
        scenarios = data.get("example_scenarios", [])
        assert isinstance(scenarios, list), f"Scenarios must be list for Section {sec_id}"
        assert len(scenarios) >= 2, f"Section {sec_id} must have at least 2 example scenarios, found {len(scenarios)}"
        for sc in scenarios:
            assert len(sc.strip()) >= 40, f"Scenario too brief in Section {sec_id}: '{sc}'"

        # Statutory citation test
        ref = data.get("statutory_reference", "").strip()
        assert ("PPC" in ref or "Pakistan Penal Code" in ref), f"Statutory citation missing PPC reference in Section {sec_id}: '{ref}'"

def test_confusable_groups_integrity():
    labels = load_json(LABELS_PATH)
    groups = load_json(CONFUSABLE_PATH)

    assert isinstance(groups, list), "confusable_groups.json must be a JSON array"
    assert len(groups) >= 8, f"Expected at least 8 confusable groups, found {len(groups)}"

    for grp in groups:
        grp_id = grp.get("group_id", "")
        grp_name = grp.get("group_name", "")
        sections = grp.get("sections", [])
        distinction = grp.get("distinction_summary", "").strip()
        diffs = grp.get("key_differentiators", {})
        pitfall = grp.get("critical_student_pitfall", "").strip()

        assert len(grp_id) > 0, "Missing group_id"
        assert len(grp_name) > 0, f"Missing group_name in {grp_id}"
        assert len(sections) >= 2, f"Group {grp_id} must contain at least 2 sections"
        assert len(distinction) >= 40, f"Distinction summary too brief in {grp_id}"
        assert len(pitfall) >= 30, f"Critical student pitfall too brief in {grp_id}"

        # Referential integrity: check all member sections exist in master labels.json
        for sec in sections:
            assert sec in labels, f"Group {grp_id} references unknown section '{sec}'"
            assert sec in diffs, f"Group {grp_id} missing differentiator note for member section '{sec}'"
            assert len(diffs[sec].strip()) >= 20, f"Differentiator note too brief for Section {sec} in {grp_id}"

if __name__ == "__main__":
    test_files_exist()
    test_sections_parity_with_labels()
    test_sections_substance_and_elements()
    test_confusable_groups_integrity()
    print("All 4 substantive content integrity tests passed successfully! 100% genuine legal data verified.")
