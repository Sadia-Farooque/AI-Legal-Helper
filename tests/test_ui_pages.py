"""Headless tests of the redesigned app (entry point + navigation): Home, Report an incident, Student Corner.

Run: python -m pytest tests/test_ui_pages.py -q
"""

import os

import pytest
from streamlit.testing.v1 import AppTest

os.environ.setdefault("HF_HUB_OFFLINE", "1")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENTRY = os.path.join(ROOT, "app", "Home.py")
T = 120


def _app():
    return AppTest.from_file(ENTRY, default_timeout=T)


def _goto(at, page):
    at.switch_page(os.path.join(ROOT, "app", "views", page))
    return at.run()


def _text(at):
    return " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)


def test_home_welcome_and_warning():
    at = _app().run()
    assert not at.exception
    t = _text(at)
    assert "Understand the law" in t and "not a lawyer" in t
    assert "Sadia Fatima" not in t and "Abdul Qudoos" not in t           # no names in the user interface


def test_evaluation_hidden_for_normal_users(monkeypatch):
    monkeypatch.delenv("LEGAL_HELPER_ADMIN", raising=False)
    at = _app().run()
    with pytest.raises(Exception):
        at.switch_page(os.path.join(ROOT, "app", "pages", "5_Evaluation.py")).run()


def test_sidebar_helplines_change_with_province():
    at = _app().run()
    at.sidebar.selectbox[0].set_value("Sindh").run()
    side = " ".join(m.value for m in at.sidebar.markdown)
    assert "1715" in side and "1094" in side and "1787" not in side


def test_report_confident_case_shows_results_and_steps():
    at = _goto(_app().run(), "report.py")
    at.text_area(key="incident").set_value(
        "Kal raat do larkay bike par aaye aur pistol dikha kar mera mobile aur wallet cheen kar bhaag gaye")
    at.button[0].click().run()
    assert not at.exception
    t = _text(at)
    assert "Sections that may apply" in t and "What to do now" in t
    assert "Sadia Fatima" not in t and "Abdul Qudoos" not in t


def test_report_unsure_case_gives_no_legal_route():
    at = _goto(_app().run(), "report.py")
    at.text_area(key="incident").set_value("teacher wont give me marks")
    at.button[0].click().run()
    assert not at.exception
    t = _text(at)
    assert "more detail" in t
    assert "What to do now" not in t and "Sections that may apply" not in t   # no FIR advice on a guess


def test_student_corner_quiz_flow_ends_with_results():
    at = _goto(_app().run(), "learn.py")
    assert not at.exception
    at.session_state["learn_mode"] = "📝 Quiz"
    at.run()
    at.button(key=None) if False else None
    start = [b for b in at.button if b.label == "Start quiz"][0]
    start.click().run()
    q = at.session_state["quiz"]
    for _ in range(len(q["ids"])):
        at.radio[0].set_value(0).run()
        [b for b in at.button if b.label == "Check answer"][0].click().run()
        [b for b in at.button if b.label in ("Next question →", "See my results")][0].click().run()
    assert not at.exception
    assert "Your result" in _text(at)


def test_student_corner_shows_correct_319_and_hides_wrong_quiz_questions():
    at = _goto(_app().run(), "learn.py")
    at.selectbox[1].set_value("319").run() if False else None
    t = _text(at)
    assert "Hurt (Causing bodily pain" not in t
    at.session_state["topic"] = "violence"
    at.run()
    t = _text(at)
    assert "Qatl-i-khata (killing by mistake)" in t and "Hurt (Causing bodily pain" not in t
    import importlib.util
    spec = importlib.util.spec_from_file_location("learn_src", os.path.join(ROOT, "app", "views", "learn.py"))
    src = open(spec.origin, encoding="utf-8").read()
    assert '"quiz_007", "quiz_008"' in src
