"""K4 wrapper for the Task A4 TF-IDF lr model: predict_scores(text) -> {section: score}.

Usage: python src/evaluate.py --model tfidf_lr --test-data <csv>
"""

import os
import sys

import joblib

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.calibration import calibrate_score  # noqa: E402
from src.models.classical import TrainedModel  # noqa: E402,F401  (needed to unpickle)

_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        _MODEL = joblib.load(os.path.join(_ROOT, "models", "tfidf_lr.joblib"))
    return _MODEL


def predict_scores(text):
    """Calibrated scores: sigmoid(a * logit + b), with (a, b) from results/calibration_tfidf_lr.json (A6)."""
    raw = _model().predict_scores(text)
    if not (text or "").strip():
        return raw
    return {s: round(calibrate_score("tfidf_lr", v), 6) for s, v in raw.items()}
