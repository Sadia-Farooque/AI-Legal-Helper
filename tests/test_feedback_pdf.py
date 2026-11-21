"""Tests for Extra 2 (PDF export) and Extra 3 (feedback). Run: python -m pytest tests/test_feedback_pdf.py -q"""

import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import feedback  # noqa: E402
from src.pdf_export import build_pdf  # noqa: E402

RES = {"status": "ok", "threshold": 0.7,
       "results": [{"section": "392", "name": "Robbery", "score": 0.91, "cognizable": "Cognizable",
                    "bailable": "Non-bailable", "compoundable": "Non-compoundable", "punishment": "3-10 years",
                    "summary": "Theft with force or threat."}],
       "guide": {"general": [("Register an FIR", "Go to the **police station**.")]}}


def test_feedback_consent_controls_text(tmp_path, monkeypatch):
    monkeypatch.delenv("FEEDBACK_GITHUB_TOKEN", raising=False)
    path = tmp_path / "fb.csv"
    for consent in (False, True):
        rec = feedback.make_record("no", ["392"], ["379"], "lawyer", "wrong section", "my bike was stolen",
                                   consent, "tfidf_lr", "ok")
        out = feedback.submit(rec, path=str(path))
        assert out["issue_url"] is None                      # no token -> no GitHub call
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert len(rows) == 2 and rows[0]["incident_text"] == "" and rows[1]["incident_text"] == "my bike was stolen"
    assert json.loads(rows[1]["correct_sections"]) == ["379"]


def test_issue_body_includes_text_only_with_consent():
    with_text = feedback.make_record("partly", ["392"], ["392", "506"], "law student", "", "snatched", True, "m", "ok")
    without = feedback.make_record("partly", ["392"], ["392", "506"], "law student", "", "snatched", False, "m", "ok")
    assert "snatched" in feedback.issue_body(with_text) and "snatched" not in feedback.issue_body(without)


def test_pdf_basic_and_with_complaint():
    pdf = build_pdf("two men snatched my phone", RES, complaint_en="To, The SHO ...", helplines=[
        {"number": "15", "name": "Police emergency", "area": "All Pakistan"}])
    assert pdf[:4] == b"%PDF" and len(pdf) > 1000


def test_pdf_with_urdu_never_crashes():
    pdf = build_pdf("x", RES, complaint_ur="بخدمت جناب ایس ایچ او صاحب")
    assert pdf[:4] == b"%PDF"


def test_rtl_lines_stay_on_the_page():
    """Regression test: every Urdu line must start inside the page (bug: lines drifted right, off the page)."""
    import io
    import src.pdf_export as P
    pdfplumber = __import__("pytest").importorskip("pdfplumber")
    old = (P.URDU_TEST, P.CANDIDATES)
    P.URDU_TEST, P.CANDIDATES = "بجن", [P.latin_font()]      # stand-in font with basic Arabic letters
    try:
        pdf = P.build_pdf("x", RES, complaint_ur="\n".join(["بخدمت جناب"] * 8 + ["", "عنوان: درخواست"]))
    finally:
        P.URDU_TEST, P.CANDIDATES = old
    page = pdfplumber.open(io.BytesIO(pdf)).pages[-1]
    words = page.extract_words()
    assert len(words) >= 18 and all(w["x1"] <= page.width + 1 for w in words)
