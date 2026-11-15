import json
import os

def test_labels_file_exists_and_is_valid():
    labels_path = os.path.join(os.path.dirname(__file__), "..", "src", "labels.json")
    assert os.path.exists(labels_path), "src/labels.json does not exist"
    
    with open(labels_path, "r", encoding="utf-8") as f:
        labels = json.load(f)
        
    assert isinstance(labels, dict), "Labels should be a dictionary"
    assert 25 <= len(labels) <= 40, f"Expected 25 to 40 labels, got {len(labels)}"
    
    for section_id, info in labels.items():
        assert info["section"] == section_id
        assert "title" in info and len(info["title"]) > 0
        assert "category" in info
        assert "citizen_term" in info
        assert "confusable_with" in info and isinstance(info["confusable_with"], list)
        assert "in_ilsi" in info and isinstance(info["in_ilsi"], bool)

if __name__ == "__main__":
    test_labels_file_exists_and_is_valid()
    print("All label tests passed successfully!")
