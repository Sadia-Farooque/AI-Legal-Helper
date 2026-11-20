"""Tests for Task A7 explanations. Uses a tiny keyword "model", so no trained model is needed.
Run: python -m pytest tests/test_explain.py -q
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.explain import explain, highlight_html  # noqa: E402

LABELS = list(json.load(open(os.path.join(os.path.dirname(__file__), "..", "src", "labels.json"),
                             encoding="utf-8")).keys())


def keyword_model(text):
    t = text.lower()
    s = {l: 0.05 for l in LABELS}
    s["392"] = 0.9 if "pistol" in t else 0.1
    s["379"] = 0.6 if "stolen" in t else 0.05
    return s


def test_lime_finds_the_trigger_word():
    words = explain("two men showed a pistol and took my phone", keyword_model, section="392",
                    num_samples=200)
    top_word, top_weight = words[0]
    assert top_word == "pistol" and top_weight > 0


def test_default_section_is_top_prediction():
    words = explain("my bike was stolen outside the mosque", keyword_model, num_samples=200)
    assert words[0][0] == "stolen"


def test_highlight_html_marks_words_and_escapes():
    out = highlight_html("pistol <b>", [("pistol", 0.5)])
    assert "rgba(46,160,67" in out and "&lt;b&gt;" in out
