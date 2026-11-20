"""Task A4: TF-IDF + Logistic Regression / Linear SVM / Naive Bayes multi-label classifiers.

Features : word TF-IDF (1-2 grams) + character TF-IDF (2-5 grams, word-boundary). Character n-grams
           make the model robust to Roman Urdu spelling variation and typos.
Classifier: one-vs-rest, one binary classifier per PPC section, class_weight="balanced" for LR/SVM
           because ILSI is highly imbalanced (302 has 435 cases, 384 has 10).
Selection : small grid search; the best setting per model type is chosen on the SYNTHETIC validation
           rows (citizen-style text is what the app will see), by top-3 recall then micro-F1.

Run:
  python -m src.models.classical --grid        # grid search, saves the best LR / SVM / NB models
  python -m src.models.classical --ablation    # data-source ablation with the best LR setting
"""

import argparse
import csv
import json
import os
import sys
import time
import warnings

import joblib
import numpy as np
from scipy.special import expit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.metrics import per_section_f1, ranking_metrics  # noqa: E402
from src.preprocess import normalize  # noqa: E402

DATASET = os.path.join(PROJECT_ROOT, "data", "processed", "dataset.csv")
LABELS_JSON = os.path.join(PROJECT_ROOT, "src", "labels.json")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
DOC_MD = os.path.join(PROJECT_ROOT, "docs", "A4_results.md")

warnings.filterwarnings("ignore", message="Label .* is present in all training examples")
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.multiclass")

GRID = {
        "lr": [{"C": c} for c in (1.0, 4.0, 16.0, 64.0)],
    "svm": [{"C": c} for c in (0.1, 0.5, 1.0)],
    "nb": [{"alpha": a} for a in (0.1, 0.3, 1.0)],
}


def label_names():
    with open(LABELS_JSON, "r", encoding="utf-8") as f:
        return list(json.load(f).keys())


def load_dataset(path=DATASET):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def features():
    return FeatureUnion([
        ("word", TfidfVectorizer(preprocessor=normalize, ngram_range=(1, 2), min_df=2,
                                 sublinear_tf=True, max_features=60000)),
        ("char", TfidfVectorizer(preprocessor=normalize, analyzer="char_wb", ngram_range=(2, 5),
                                 min_df=2, sublinear_tf=True, max_features=120000)),
    ])


def make_model(kind, params):
    if kind == "lr":
        clf = LogisticRegression(C=params["C"], class_weight="balanced", max_iter=2000, solver="liblinear")
    elif kind == "svm":
        clf = LinearSVC(C=params["C"], class_weight="balanced")
    elif kind == "nb":
        clf = ComplementNB(alpha=params["alpha"])
    else:
        raise ValueError(kind)
    return Pipeline([("tfidf", features()), ("ovr", OneVsRestClassifier(clf))])


def raw_scores(pipe, texts):
    """Scores in [0,1] for every label. SVM margins are squashed with a sigmoid (A6 calibrates them)."""
    ovr = pipe.named_steps["ovr"]
    X = pipe.named_steps["tfidf"].transform(texts)
    if hasattr(ovr.estimators_[0], "predict_proba") and not isinstance(ovr.estimators_[0], LinearSVC):
        return ovr.predict_proba(X)
    return expit(ovr.decision_function(X))


class TrainedModel:
    """Bundles pipeline + label binarizer and exposes the K4 contract."""

    def __init__(self, kind, params, pipe, mlb):
        self.kind, self.params, self.pipe, self.mlb = kind, params, pipe, mlb

    def scores(self, texts):
        return raw_scores(self.pipe, texts)

    def predict_scores(self, text):
        s = self.scores([text or ""])[0]
        out = {lab: float(round(v, 6)) for lab, v in zip(self.mlb.classes_, s)}
        if not (text or "").strip():
            out = {lab: 0.0 for lab in out}
        return out


def fit(kind, params, rows, labels):
    mlb = MultiLabelBinarizer(classes=labels)
    Y = mlb.fit_transform([json.loads(r["sections"]) for r in rows])
    pipe = make_model(kind, params)
    pipe.fit([r["text"] for r in rows], Y)
    return TrainedModel(kind, params, pipe, mlb)


def evaluate_on(model, rows):
    if not rows:
        return None
    Y = model.mlb.transform([json.loads(r["sections"]) for r in rows])
    return ranking_metrics(Y, model.scores([r["text"] for r in rows]))


def val_subsets(rows):
    val = [r for r in rows if r["split"] == "val"]
    syn = [r for r in val if r["source"] == "synthetic"]
    return {
        "synthetic_all": syn,
        "synthetic_en": [r for r in syn if r["language"] == "en"],
        "synthetic_roman_ur": [r for r in syn if r["language"] == "roman_ur"],
        "ilsi": [r for r in val if r["source"] == "ilsi"],
    }


def grid_search(rows, labels):
    train = [r for r in rows if r["split"] == "train"]
    subsets = val_subsets(rows)
    log, best = [], {}
    for kind, grid in GRID.items():
        for params in grid:
            t0 = time.time()
            model = fit(kind, params, train, labels)
            res = {name: evaluate_on(model, sub) for name, sub in subsets.items()}
            key = res["synthetic_all"]
            log.append({"model": kind, "params": json.dumps(params), "seconds": round(time.time() - t0, 1),
                        **{f"{name}_{m}": v for name, r in res.items() if r for m, v in r.items() if m != "samples"}})
            score = (key["top3_recall"], key["micro_f1"])
            print(f"{kind:4s} {params}  syn top3={key['top3_recall']:.3f} microF1={key['micro_f1']:.3f} "
                  f"macroF1={key['macro_f1']:.3f}")
            if kind not in best or score > best[kind][0]:
                best[kind] = (score, params, model, res)
    return log, best


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def save_k6(res, name):
    """Validation results in the K6 format (metric, language, value)."""
    out = []
    for subset, r in res.items():
        if r:
            for m, v in r.items():
                out.append({"metric": m, "language": subset, "value": v})
    write_csv(os.path.join(RESULTS_DIR, f"{name}_val.csv"), out)


def run_grid():
    rows, labels = load_dataset(), label_names()
    log, best = grid_search(rows, labels)
    write_csv(os.path.join(RESULTS_DIR, "tfidf_grid.csv"), log)
    os.makedirs(MODELS_DIR, exist_ok=True)
    md = ["# A4 Results: TF-IDF baselines", "", "Generated by `python -m src.models.classical --grid`.",
          "Validation = grouped 20% split (`src/data/make_splits.py`). Model selection uses the synthetic "
          "(citizen-style) validation rows. Metrics from `src/metrics.py` (true macro-F1).", "",
          "## Best setting per model", "",
          "| Model | Params | Subset | Top-1 | Top-3 recall | Micro-F1 | Macro-F1 | n |", "|---|---|---|---|---|---|---|---|"]
    for kind, (_, params, model, res) in best.items():
        joblib.dump(model, os.path.join(MODELS_DIR, f"tfidf_{kind}.joblib"))
        save_k6(res, f"tfidf_{kind}")
        for subset, r in res.items():
            if r:
                md.append(f"| {kind} | {params} | {subset} | {r['top1_accuracy']} | {r['top3_recall']} | "
                          f"{r['micro_f1']} | {r['macro_f1']} | {r['samples']} |")
    # per-section F1 of the best LR on synthetic val
    _, _, lr, _ = best["lr"]
    syn = val_subsets(rows)["synthetic_all"]
    Y = lr.mlb.transform([json.loads(r["sections"]) for r in syn])
    ps = per_section_f1(Y, lr.scores([r["text"] for r in syn]), labels)
    md += ["", "## Per-section F1, best LR, synthetic validation", "", "| Section | F1 | Support |", "|---|---|---|"]
    md += [f"| {s} | {f} | {n} |" for s, (f, n) in ps.items() if n > 0]
    md += ["", "Full grid: `results/tfidf_grid.csv`. Saved models: `models/tfidf_{lr,svm,nb}.joblib` (not in git).", ""]
    with open(DOC_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Best models saved to models/, summary -> {os.path.relpath(DOC_MD, PROJECT_ROOT)}")


def run_ablation():
    """Same model (best LR from the grid), trained on different data sources, evaluated on the same val rows."""
    rows, labels = load_dataset(), label_names()
    best_lr = joblib.load(os.path.join(MODELS_DIR, "tfidf_lr.joblib"))
    params = best_lr.params
    train = [r for r in rows if r["split"] == "train"]
    subsets = val_subsets(rows)
    configs = {
        "synthetic_only": [r for r in train if r["source"] == "synthetic"],
        "ilsi_only": [r for r in train if r["source"] == "ilsi"],
        "synthetic_plus_ilsi": train,
    }
    out = []
    for name, tr in configs.items():
        model = fit("lr", params, tr, labels)
        for subset, sub in subsets.items():
            r = evaluate_on(model, sub)
            if r:
                out.append({"train_data": name, "n_train": len(tr), "eval_subset": subset, **r})
                print(f"{name:20s} -> {subset:20s} top3={r['top3_recall']:.3f} microF1={r['micro_f1']:.3f}")
    write_csv(os.path.join(RESULTS_DIR, "ablation.csv"), out)
    md = ["", "## Ablation: which training data helps? (best LR setting)", "",
          "| Train data | n train | Eval subset | Top-1 | Top-3 recall | Micro-F1 | Macro-F1 |", "|---|---|---|---|---|---|---|"]
    md += [f"| {o['train_data']} | {o['n_train']} | {o['eval_subset']} | {o['top1_accuracy']} | {o['top3_recall']} | "
           f"{o['micro_f1']} | {o['macro_f1']} |" for o in out]
    with open(DOC_MD, "a", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"-> results/ablation.csv, appended to {os.path.relpath(DOC_MD, PROJECT_ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--ablation", action="store_true")
    a = ap.parse_args()
    if a.grid:
        run_grid()
    if a.ablation:
        run_ablation()
    if not (a.grid or a.ablation):
        ap.print_help()


if __name__ == "__main__":
    # Re-import under the package name so saved models reference src.models.classical.TrainedModel
    # (not __main__.TrainedModel), otherwise they could not be loaded by the app or evaluate.py.
    from src.models import classical as _classical
    _classical.main()
