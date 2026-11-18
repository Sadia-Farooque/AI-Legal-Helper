"""Stub model implementation adhering to K4 model contract:
predict_scores(text: str) -> dict[str, float]
"""

import json
import os
import random
import hashlib
from typing import Dict

# Locate labels.json relative to this file
_LABELS_PATH = os.path.join(os.path.dirname(__file__), "..", "labels.json")

def _load_sections():
    if os.path.exists(_LABELS_PATH):
        with open(_LABELS_PATH, "r", encoding="utf-8") as f:
            return list(json.load(f).keys())
    # Fallback default 30 sections if file not loaded
    return [
        "302", "307", "319", "324", "337-A", "337-F", "339", "340",
        "354", "354A", "363", "365", "365-A", "379", "380", "382",
        "384", "392", "395", "403", "406", "411", "420", "441",
        "447", "448", "489-F", "500", "506", "509"
    ]

_SECTIONS = _load_sections()

def predict_scores(text: str) -> Dict[str, float]:
    """Generates predicted probability scores for all PPC sections.
    Adheres strictly to the shared K4 model contract:
    Returns {section_id: score} where 0.0 <= score <= 1.0.
    """
    if not text or not text.strip():
        return {sec: 0.0 for sec in _SECTIONS}

    # Deterministic pseudo-random generation based on text hash for reproducible testing
    seed = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)

    # Pick 2-3 prominent sections to give high confidence
    num_peaks = rng.randint(1, 3)
    peak_sections = rng.sample(_SECTIONS, num_peaks)

    scores = {}
    for sec in _SECTIONS:
        if sec in peak_sections:
            scores[sec] = round(rng.uniform(0.65, 0.95), 4)
        else:
            scores[sec] = round(rng.uniform(0.01, 0.25), 4)

    return scores

if __name__ == "__main__":
    test_text = "Two men snatched my mobile phone on a motorcycle."
    output = predict_scores(test_text)
    print(f"Total sections evaluated: {len(output)}")
    top_3 = sorted(output.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"Top 3 predicted sections: {top_3}")
