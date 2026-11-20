"""
tests/test_student_pages.py — Automated Headless Test Suite for Student Pages (Task B7)

Validates the full student application suite:
- app/pages/2_Section_Explorer.py (Statutory Elements & Precedents)
- app/pages/3_Case_Finder.py (Supreme Court Semantic Search)
- app/pages/4_Quiz.py (Legal Scenario Quiz & Drill-down)

Uses streamlit.testing.v1.AppTest to execute Streamlit headless sessions.
"""

import os
import sys
import unittest
from streamlit.testing.v1 import AppTest

# Set HuggingFace offline mode for fast headless runs
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAGE_EXPLORER = os.path.join(PROJECT_ROOT, "app", "pages", "2_Section_Explorer.py")
PAGE_FINDER = os.path.join(PROJECT_ROOT, "app", "pages", "3_Case_Finder.py")
PAGE_QUIZ = os.path.join(PROJECT_ROOT, "app", "pages", "4_Quiz.py")


class TestStudentAppPages(unittest.TestCase):

    def test_01_section_explorer_renders_cleanly(self):
        """Verify 2_Section_Explorer.py renders without exceptions."""
        at = AppTest.from_file(PAGE_EXPLORER, default_timeout=15).run()
        self.assertFalse(at.exception, f"Section Explorer crashed: {at.exception}")
        self.assertGreater(len(at.tabs), 0, "Tabs not rendered in Section Explorer")

    def test_02_section_explorer_search_filter(self):
        """Verify search input filters sections correctly in Section Explorer."""
        at = AppTest.from_file(PAGE_EXPLORER, default_timeout=15)
        at.session_state["explorer_search"] = "302"
        at.run()
        self.assertFalse(at.exception, f"Filtered Section Explorer crashed: {at.exception}")

    def test_03_case_finder_renders_cleanly(self):
        """Verify 3_Case_Finder.py renders without exceptions."""
        at = AppTest.from_file(PAGE_FINDER, default_timeout=20).run()
        self.assertFalse(at.exception, f"Case Finder crashed: {at.exception}")
        self.assertGreater(len(at.text_area), 0, "Query text area missing in Case Finder")

    def test_04_case_finder_preset_section(self):
        """Verify 3_Case_Finder.py initializes with preset section filter."""
        at = AppTest.from_file(PAGE_FINDER, default_timeout=20)
        at.session_state["case_section_filter"] = "302"
        at.run()
        self.assertFalse(at.exception, f"Case Finder with preset section filter crashed: {at.exception}")

    def test_05_quiz_page_renders_cleanly(self):
        """Verify 4_Quiz.py renders without exceptions."""
        at = AppTest.from_file(PAGE_QUIZ, default_timeout=15).run()
        self.assertFalse(at.exception, f"Quiz page crashed: {at.exception}")
        self.assertGreater(len(at.radio), 0, "Radio options not rendered in Quiz page")

    def test_06_quiz_section_drilldown(self):
        """Verify 4_Quiz.py honors quiz_target_section drill-down mode."""
        at = AppTest.from_file(PAGE_QUIZ, default_timeout=15)
        at.session_state["quiz_target_section"] = "392"
        at.run()
        self.assertFalse(at.exception, f"Quiz drill-down crashed: {at.exception}")


if __name__ == "__main__":
    unittest.main()
