"""K4 wrapper for the Task A4 TF-IDF lr model: predict_scores(text) -> {section: score}.

Usage: python src/evaluate.py --model tfidf_lr --test-data <csv>
"""

import os
import sys

import joblib

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.calibration import apply, calibrate_score, load_calibration, to_logits  # noqa: E402
from src.models.classical import TrainedModel  # noqa: E402,F401  (needed to unpickle)

_MODEL = None


_PATH = os.path.join(_ROOT, "models", "tfidf_lr.joblib")


def _best_params():
    """Best LR setting from the A4 grid search (results/tfidf_grid.csv); C=16 if the file is missing."""
    import csv
    try:
        with open(os.path.join(_ROOT, "results", "tfidf_grid.csv"), encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["model"] == "lr"]
        best = max(rows, key=lambda r: (float(r["synthetic_all_top3_recall"]), float(r["synthetic_all_micro_f1"])))
        import json
        return json.loads(best["params"])
    except Exception:  # noqa: BLE001
        return {"C": 16.0}


def _train_and_save():
    """Trained weights are not in git (27 MB). On a fresh clone or a cloud server, rebuild the model from the
    committed data (data/processed/dataset.csv, same grouped split) with the grid-search setting, then save it.
    Takes about a minute, once."""
    from src.models.classical import fit, label_names, load_dataset
    rows = [r for r in load_dataset() if r["split"] == "train"]
    model = fit("lr", _best_params(), rows, label_names())
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    joblib.dump(model, _PATH)
    return model


def _model():
    global _MODEL
    if _MODEL is None:
        _MODEL = joblib.load(_PATH) if os.path.exists(_PATH) else _train_and_save()
    return _MODEL


def predict_scores(text):
    """Calibrated scores: sigmoid(a * logit + b), with (a, b) from results/calibration_tfidf_lr.json (A6)."""
    raw = _model().predict_scores(text)
    if not (text or "").strip():
        return raw
    return {s: round(calibrate_score("tfidf_lr", v), 6) for s, v in raw.items()}


def predict_scores_batch(texts):
    """Calibrated scores for many texts at once: array (n_texts, n_labels) in labels.json order (used by LIME)."""
    m = _model()
    a, b = load_calibration("tfidf_lr")
    return apply(to_logits(m.scores(list(texts))), a, b)
