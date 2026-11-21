"""Tests for Task A8 (src/analyzer.py).

Logic tests use a fake model, so they always run. Behaviour tests use the real trained model
(models/tfidf_lr.joblib) and are skipped if it has not been trained on this machine.
Run: python -m pytest tests/test_analyzer.py -q
"""

import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from src.analyzer import analyze, detect_language  # noqa: E402

LABELS = list(json.load(open(os.path.join(ROOT, "src", "labels.json"), encoding="utf-8")).keys())
HAS_MODEL = os.path.exists(os.path.join(ROOT, "models", "tfidf_lr.joblib"))


def fake(top):
    def fn(text):
        s = {l: 0.01 for l in LABELS}
        s.update(top)
        return s
    return fn


# ---------- logic (always run)

def test_empty_input():
    assert analyze("   ")["status"] == "empty"


def test_urdu_script_is_flagged():
    assert analyze("میرا موبائل چھین لیا", predict_fn=fake({"392": 0.9}))["status"] == "urdu_script"


def test_abstains_below_threshold():
    r = analyze("something happened", predict_fn=fake({"379": 0.40}), threshold=0.7)
    assert r["status"] == "abstain" and r["results"][0]["section"] == "379"


def test_ok_above_threshold_with_legal_facts():
    r = analyze("two men snatched my phone", predict_fn=fake({"392": 0.95, "379": 0.3}), threshold=0.7)
    assert r["status"] == "ok"
    top = r["results"][0]
    assert top["section"] == "392" and top["cognizable"] != "unknown" and top["punishment"]


def test_441_merged_into_447_and_307_hidden():
    r = analyze("x", predict_fn=fake({"441": 0.9, "447": 0.8, "307": 0.95}), threshold=0.5)
    secs = [c["section"] for c in r["results"]]
    assert "441" not in secs and "307" not in secs and secs[0] == "447"


def test_confusable_note_for_theft_vs_dwelling():
    r = analyze("x", predict_fn=fake({"379": 0.8, "380": 0.7}), threshold=0.5)
    assert r["confusable"] and r["confusable"]["a"] == "379" and r["confusable"]["b_text"]


def test_language_detection():
    assert detect_language("do larkay bike par aaye aur mobile cheen liya") == "roman_ur"
    assert detect_language("two men on a bike snatched my phone") == "en"


# ---------- behaviour with the real model

needs_model = pytest.mark.skipif(not HAS_MODEL, reason="models/tfidf_lr.joblib not trained on this machine")


def top3(text):
    return [c["section"] for c in analyze(text)["results"]]


@needs_model
def test_theft():
    assert {"379", "380"} & set(top3("someone stole my motorcycle from outside the mosque during jummah prayer"))


@needs_model
def test_harassment():
    assert {"509", "354"} & set(top3("a man in my office keeps sending me vulgar messages and making dirty comments"))


@needs_model
def test_fraud():
    assert "420" in top3("an agent took 5 lakh from my brother for a job in dubai and the visa was fake")


@needs_model
def test_roman_urdu_snatching():
    assert top3("do larkay bike par aaye aur pistol dikha kar mera mobile cheen liya")[0] == "392"


@needs_model
def test_non_crime_abstains():
    """Was an expected failure before calibration; now passes (D13: 16/16 non-crime test messages abstain)."""
    assert analyze("my landlord is not fixing the kitchen tap and the paint is old")["status"] == "abstain"
