"""Retrain the saved TF-IDF models on the current data/processed/dataset.csv WITHOUT a new grid search.

Used after adding data (round 2: Roman Urdu chat stories A3b + Supreme Court of Pakistan facts A2b). The
hyperparameters stay the ones chosen by the A4 grid search (results/tfidf_grid.csv), so the before/after
comparison measures only the effect of the data. Then run calibration and the J1 test again:

    python -m src.data.make_splits
    python -m src.models.retrain
    python -m src.calibration --model tfidf_lr      (and tfidf_svm, tfidf_nb)
    python -m src.evaluate_test
"""

import csv
import json
import os

import joblib

from src.models.classical import fit, label_names, load_dataset

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def best_params(kind):
    with open(os.path.join(PROJECT_ROOT, "results", "tfidf_grid.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["model"] == kind]
    best = max(rows, key=lambda r: (float(r["synthetic_all_top3_recall"]), float(r["synthetic_all_micro_f1"])))
    return json.loads(best["params"])


def main():
    rows, labels = load_dataset(), label_names()
    train = [r for r in rows if r["split"] == "train"]
    for kind in ("lr", "svm", "nb"):
        params = best_params(kind)
        model = fit(kind, params, train, labels)
        path = os.path.join(PROJECT_ROOT, "models", f"tfidf_{kind}.joblib")
        joblib.dump(model, path)
        print(f"tfidf_{kind}: {params}, trained on {len(train)} rows -> {os.path.relpath(path, PROJECT_ROOT)}")


if __name__ == "__main__":
    from src.models import retrain as _r      # pickle under the package name (see classical.py)
    _r.main()
