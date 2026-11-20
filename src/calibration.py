"""Task A6: Calibration (Platt scaling of the top-1 confidence) and the abstain ("not sure, consult a lawyer") threshold.

Why: a model that says 0.9 should be right about 90% of the time. Raw classifier scores are usually
over- or under-confident, and the app must know when to abstain instead of guessing.

Method (per model)
1. Validation scores on the synthetic (citizen-style) validation rows, converted to logits z.
2. Platt scaling of the TOP-1 decision: score = sigmoid(a * z + b), with a > 0 and b fitted so that
   the confidence of the top-ranked section matches how often it is actually correct (log-loss on
   (top-1 logit, correct?) pairs). Applying the same (a, b) to every section keeps the ranking unchanged.
   Why not plain temperature scaling over all 30 labels: about 29 of 30 label-cells are negatives,
   so that fit mostly learns to be confident about "not this section" and made the top-1 confidence
   WORSE (first run: ECE 0.254 -> 0.260 for LR, 0.125 -> 0.239 for DistilBERT). The calibration
   objective must match how the score is used: the app shows and thresholds the top-1 confidence.
   2-fold cross-fitting: (a, b) is fitted on one half and tested on the other, so the reported ECE
   is not measured on the data it was fitted on.
3. ECE (expected calibration error, 10 bins) of the top-1 confidence, before and after.
4. Abstain threshold: the lowest confidence t such that top-1 accuracy on the answered cases is at
   least TARGET_ACCURACY. Below t the app shows "not sure, consult a lawyer" instead of sections.
5. Plots: reliability diagram and accuracy-vs-coverage curve -> results/figures/

Run:  python -m src.calibration --model tfidf_lr        (also tfidf_svm, tfidf_nb, distilbert)
Output: results/calibration_<model>.json (+ figures). The K4 wrappers read (a, b) from it.
"""

import argparse
import csv
import json
import os
import sys
from functools import lru_cache

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DATASET = os.path.join(PROJECT_ROOT, "data", "processed", "dataset.csv")
RESULTS = os.path.join(PROJECT_ROOT, "results")
FIG_DIR = os.path.join(RESULTS, "figures")
TARGET_ACCURACY = 0.85
EPS = 1e-6


def calibration_path(model_name):
    return os.path.join(RESULTS, f"calibration_{model_name}.json")


@lru_cache(maxsize=None)
def load_calibration(model_name):
    """(a, b) for score = sigmoid(a * logit + b); (1, 0) = uncalibrated."""
    p = calibration_path(model_name)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        return float(d.get("a", 1.0)), float(d.get("b", 0.0))
    return 1.0, 0.0


def calibrate_score(model_name, raw):
    """Calibrate one raw score in [0,1] with the stored (a, b)."""
    a, b = load_calibration(model_name)
    if (a, b) == (1.0, 0.0):
        return raw
    return float(apply(to_logits(raw), a, b))


def to_logits(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sigmoid(z):
    return expit(z)


def _top1(Y, z):
    idx = z.argmax(axis=1)
    return z[np.arange(len(z)), idx], (Y[np.arange(len(Y)), idx] > 0).astype(float)


def fit_platt(Y, z):
    """Fit (a, b) for p = sigmoid(a*z + b) on the top-1 logit vs top-1 correctness. a is kept > 0."""
    zt, c = _top1(Y, z)

    def loss(params):
        a, b = np.exp(params[0]), params[1]
        p = np.clip(sigmoid(a * zt + b), EPS, 1 - EPS)
        return float(-(c * np.log(p) + (1 - c) * np.log(1 - p)).mean() + 1e-3 * params[0] ** 2)

    res = minimize(loss, x0=[0.0, 0.0], method="Nelder-Mead")
    return float(np.exp(res.x[0])), float(res.x[1])


def apply(z, a, b):
    return sigmoid(a * z + b)


def top1_conf_correct(Y, p):
    idx = p.argmax(axis=1)
    conf = p[np.arange(len(p)), idx]
    correct = Y[np.arange(len(Y)), idx] > 0
    return conf, correct


def ece(conf, correct, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi) if lo > 0 else (conf >= lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(total)


def coverage_curve(conf, correct, Y, p, k=3):
    order = np.argsort(-p, axis=1)
    topk = np.array([Y[i, order[i, :k]].any() for i in range(len(Y))])
    out = []
    for t in np.round(np.arange(0.0, 1.0001, 0.05), 2):
        m = conf >= t
        out.append({"threshold": float(t), "coverage": float(m.mean()),
                    "top1_accuracy": float(correct[m].mean()) if m.any() else None,
                    "top3_recall": float(topk[m].mean()) if m.any() else None})
    return out


def choose_threshold(curve, target=TARGET_ACCURACY):
    ok = [c for c in curve if c["top1_accuracy"] is not None and c["top1_accuracy"] >= target]
    return min(ok, key=lambda c: c["threshold"]) if ok else max(
        (c for c in curve if c["top1_accuracy"] is not None), key=lambda c: c["top1_accuracy"])


def val_rows(source="synthetic"):
    with open(DATASET, "r", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["split"] == "val" and r["source"] == source]


def get_val_logits(model_name, rows, labels):
    """Returns (Y, z) for the validation rows."""
    L2I = {l: i for i, l in enumerate(labels)}
    Y = np.zeros((len(rows), len(labels)))
    for i, r in enumerate(rows):
        for s in json.loads(r["sections"]):
            Y[i, L2I[s]] = 1
    if model_name == "distilbert":
        path = os.path.join(RESULTS, "distilbert_val_scores.csv")
        with open(path, "r", encoding="utf-8") as f:
            saved = {r["id"]: r for r in csv.DictReader(f)}
        z = np.array([[float(saved[r["id"]][l]) for l in labels] for r in rows])
    else:
        import joblib
        from src.models.classical import TrainedModel  # noqa: F401
        m = joblib.load(os.path.join(PROJECT_ROOT, "models", f"{model_name}.joblib"))
        assert list(m.mlb.classes_) == labels
        z = to_logits(m.scores([r["text"] for r in rows]))
    return Y, z


def plot(model_name, before, after, curve, thr):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    os.makedirs(FIG_DIR, exist_ok=True)
    paths = []
    fig, ax = plt.subplots(figsize=(5, 5))
    for (conf, corr), name in [(before, "before"), (after, "after")]:
        edges = np.linspace(0, 1, 11)
        xs, ys = [], []
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (conf >= lo) & (conf <= hi)
            if m.any():
                xs.append(conf[m].mean()); ys.append(corr[m].mean())
        ax.plot(xs, ys, marker="o", label=f"{name} (ECE {ece(conf, corr):.3f})")
    ax.plot([0, 1], [0, 1], "--", color="grey", label="perfect")
    ax.set_xlabel("confidence of top-1 section"); ax.set_ylabel("observed accuracy")
    ax.set_title(f"Reliability: {model_name}"); ax.legend()
    p = os.path.join(FIG_DIR, f"reliability_{model_name}.png"); fig.savefig(p, dpi=120, bbox_inches="tight"); plt.close(fig)
    paths.append(p)
    fig, ax = plt.subplots(figsize=(6, 4))
    c = [x for x in curve if x["top1_accuracy"] is not None]
    ax.plot([x["coverage"] for x in c], [x["top1_accuracy"] for x in c], marker=".", label="top-1 accuracy")
    ax.plot([x["coverage"] for x in c], [x["top3_recall"] for x in c], marker=".", label="top-3 recall")
    ax.axvline(thr["coverage"], ls="--", color="grey", label=f"abstain below {thr['threshold']:.2f}")
    ax.set_xlabel("coverage (share of cases answered)"); ax.set_ylabel("score on answered cases")
    ax.set_title(f"Accuracy vs coverage: {model_name}"); ax.legend()
    p = os.path.join(FIG_DIR, f"coverage_{model_name}.png"); fig.savefig(p, dpi=120, bbox_inches="tight"); plt.close(fig)
    paths.append(p)
    return paths


def calibrate(model_name, seed=42):
    with open(os.path.join(PROJECT_ROOT, "src", "labels.json"), "r", encoding="utf-8") as f:
        labels = list(json.load(f).keys())
    rows = val_rows()
    Y, z = get_val_logits(model_name, rows, labels)
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(rows)); a, b = idx[: len(idx) // 2], idx[len(idx) // 2:]
    cross_ece = []
    for fit_i, test_i in [(a, b), (b, a)]:
        ca, cb = fit_platt(Y[fit_i], z[fit_i])
        cross_ece.append(ece(*top1_conf_correct(Y[test_i], apply(z[test_i], ca, cb))))
    A, B = fit_platt(Y, z)                          # final (a, b) on all validation rows
    p_before, p_after = sigmoid(z), apply(z, A, B)
    before, after = top1_conf_correct(Y, p_before), top1_conf_correct(Y, p_after)
    curve = coverage_curve(*after, Y, p_after)
    thr = choose_threshold(curve)
    out = {
        "model": model_name, "n_val": len(rows), "method": "platt_top1", "a": round(A, 4), "b": round(B, 4),
        "ece_before": round(ece(*before), 4), "ece_after": round(ece(*after), 4),
        "ece_after_crossfit": round(float(np.mean(cross_ece)), 4),
        "abstain_threshold": thr["threshold"], "target_top1_accuracy": TARGET_ACCURACY,
        "coverage_at_threshold": round(thr["coverage"], 4),
        "top1_accuracy_at_threshold": round(thr["top1_accuracy"], 4),
        "top3_recall_at_threshold": round(thr["top3_recall"], 4),
        "curve": curve,
    }
    os.makedirs(RESULTS, exist_ok=True)
    with open(calibration_path(model_name), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    figs = plot(model_name, before, after, curve, thr)
    return out, figs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="tfidf_lr", help="tfidf_lr | tfidf_svm | tfidf_nb | distilbert")
    a = ap.parse_args()
    out, figs = calibrate(a.model)
    print(f"{a.model}: a={out['a']} b={out['b']}  ECE {out['ece_before']} -> {out['ece_after']} "
          f"(cross-fit {out['ece_after_crossfit']})")
    print(f"abstain below {out['abstain_threshold']}: answers {out['coverage_at_threshold']:.0%} of cases, "
          f"top-1 acc {out['top1_accuracy_at_threshold']:.3f}, top-3 recall {out['top3_recall_at_threshold']:.3f}")
    for p in figs:
        print("figure ->", os.path.relpath(p, PROJECT_ROOT))


if __name__ == "__main__":
    main()
