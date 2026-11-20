"""K4 wrapper for the Task A4 TF-IDF nb model: predict_scores(text) -> {section: score}.

Usage: python src/evaluate.py --model tfidf_nb --test-data <csv>
"""

import os
import sys

import joblib

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.calibration import load_temperature, sigmoid, to_logits  # noqa: E402
from src.models.classical import TrainedModel  # noqa: E402,F401  (needed to unpickle)

_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        _MODEL = joblib.load(os.path.join(_ROOT, "models", "tfidf_nb.joblib"))
    return _MODEL


def predict_scores(text):
    """Calibrated scores: sigmoid(logit / T), with T from results/calibration_tfidf_nb.json (A6)."""
    raw = _model().predict_scores(text)
    T = load_temperature("tfidf_nb")
    if T == 1.0 or not (text or "").strip():
        return raw
    return {s: float(round(sigmoid(to_logits(v) / T), 6)) for s, v in raw.items()}
