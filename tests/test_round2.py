"""Checks for the round 2 data (A2b Supreme Court of Pakistan facts, A3b Roman Urdu chat stories) and the
safety floor of the abstain threshold."""

import csv
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
LABELS = set(json.load(open(P("src", "labels.json"), encoding="utf-8")))


def _rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_chat_stories_are_valid():
    rows = _rows(P("data", "processed", "synthetic_chat.csv"))
    assert len(rows) == 280
    for r in rows:
        secs = json.loads(r["sections"])
        assert secs and set(secs) <= LABELS and "307" not in secs
        assert r["primary_section"] == secs[0] and r["language"] == "roman_ur"


def test_chat_stories_do_not_copy_the_test_set():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    chat = [r["text"] for r in _rows(P("data", "processed", "synthetic_chat.csv"))]
    test = [r["text"] for f in ("test_sf.csv", "out_of_scope_sf.csv") for r in _rows(P("data", "test", f))]
    v = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit(chat + test)
    assert cosine_similarity(v.transform(chat), v.transform(test)).max() < 0.6


def test_supreme_court_facts_have_no_section_numbers():
    rows = _rows(P("data", "processed", "sc_facts.csv"))
    assert len(rows) > 100
    leak = re.compile(r"\b(302|324|420|489|506|PPC|P\.P\.C)\b")
    assert not [r["id"] for r in rows if leak.search(r["text"])]
    assert {r["source"] for r in rows} == {"sc_pk"}


def test_no_test_rows_in_training_data():
    test_ids = {r["id"] for f in ("test_sf.csv", "out_of_scope_sf.csv") for r in _rows(P("data", "test", f))}
    assert not test_ids & {r["id"] for r in _rows(P("data", "processed", "dataset.csv"))}


def test_abstain_threshold_never_below_safety_floor():
    for m in ("tfidf_lr", "tfidf_svm", "tfidf_nb"):
        cal = json.load(open(P("results", f"calibration_{m}.json"), encoding="utf-8"))
        assert cal["abstain_threshold"] >= 0.70


def test_non_crime_messages_do_not_copy_the_test_set():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    nc = [r["text"] for r in _rows(P("data", "processed", "non_crime.csv"))]
    test = [r["text"] for f in ("test_sf.csv", "out_of_scope_sf.csv") for r in _rows(P("data", "test", f))]
    v = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit(nc + test)
    assert cosine_similarity(v.transform(nc), v.transform(test)).max() < 0.5
