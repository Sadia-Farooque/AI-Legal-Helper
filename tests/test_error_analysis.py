"""
tests/test_error_analysis.py — Automated Test Suite for Task B8 (Evaluation & Error Analysis)

Verifies:
1. Error analysis engine computes per-class metrics, confusion pairs, and failure logs.
2. Metrics adhere to bounds [0.0, 1.0].
3. Streamlit app/pages/5_Evaluation.py renders cleanly without exceptions.
"""

import json
import os
import sys
import unittest
from streamlit.testing.v1 import AppTest

# Set HuggingFace offline mode for fast headless runs
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.error_analysis import run_error_analysis
from src.models.stub_model import predict_scores as stub_predict

TEST_CSV = os.path.join(PROJECT_ROOT, "data", "test", "stub_test.csv")
LABELS_PATH = os.path.join(PROJECT_ROOT, "src", "labels.json")
EVAL_PAGE = os.path.join(PROJECT_ROOT, "app", "pages", "5_Evaluation.py")


class TestErrorAnalysis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analysis = run_error_analysis(stub_predict, TEST_CSV, top_k=3)

    def test_01_schema_conformance(self):
        """Verify run_error_analysis returns all expected top-level keys."""
        expected_keys = {"summary", "per_class", "confusion_pairs", "failures"}
        self.assertTrue(expected_keys.issubset(set(self.analysis.keys())), f"Missing keys in analysis: {self.analysis.keys()}")

    def test_02_summary_bounds(self):
        """Verify summary metrics are mathematically valid."""
        summary = self.analysis["summary"]
        self.assertEqual(summary["total_samples"], 20)
        self.assertGreaterEqual(summary["top1_accuracy"], 0.0)
        self.assertLessEqual(summary["top1_accuracy"], 1.0)
        self.assertGreaterEqual(summary["top3_recall"], 0.0)
        self.assertLessEqual(summary["top3_recall"], 1.0)
        self.assertGreaterEqual(summary["macro_f1"], 0.0)
        self.assertLessEqual(summary["macro_f1"], 1.0)

    def test_03_per_class_integrity(self):
        """Verify all 30 target sections exist in per-class metrics."""
        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            target_sections = set(json.load(f).keys())

        per_class = self.analysis["per_class"]
        self.assertEqual(set(per_class.keys()), target_sections, "Per-class sections do not match labels.json")

        for sec, stats in per_class.items():
            self.assertIn("precision", stats)
            self.assertIn("recall", stats)
            self.assertIn("f1", stats)
            self.assertIn("support", stats)
            self.assertGreaterEqual(stats["precision"], 0.0)
            self.assertGreaterEqual(stats["recall"], 0.0)
            self.assertGreaterEqual(stats["f1"], 0.0)

    def test_04_confusion_pairs_sorted(self):
        """Verify confusion pairs are correctly ranked descending by frequency."""
        pairs = self.analysis["confusion_pairs"]
        self.assertIsInstance(pairs, list)
        if len(pairs) > 1:
            counts = [p["count"] for p in pairs]
            self.assertEqual(counts, sorted(counts, reverse=True), "Confusion pairs not sorted descending by count")

    def test_05_failure_log_attributes(self):
        """Verify failure cases record essential diagnostic attributes."""
        failures = self.analysis["failures"]
        self.assertIsInstance(failures, list)
        for fail in failures:
            self.assertIn("id", fail)
            self.assertIn("text", fail)
            self.assertIn("primary_section", fail)
            self.assertIn("predicted_top1", fail)
            self.assertIn("topk_predictions", fail)
            self.assertIsInstance(fail["topk_predictions"], list)

    def test_06_evaluation_dashboard_renders(self):
        """Verify app/pages/5_Evaluation.py renders headlessly without exceptions."""
        at = AppTest.from_file(EVAL_PAGE, default_timeout=25).run()
        self.assertFalse(at.exception, f"Evaluation dashboard crashed: {at.exception}")
        self.assertGreaterEqual(len(at.tabs), 4, "Evaluation dashboard should have at least 4 tabs")


if __name__ == "__main__":
    unittest.main()
