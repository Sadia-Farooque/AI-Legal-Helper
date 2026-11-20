"""Track A metrics for multi-label section prediction (used for validation, ablation and calibration).

Unlike the shared src/evaluate.py, per-section false positives ARE counted here, so macro-F1 is a
true macro-F1 (the shared script currently only counts TP and FN per section; reported in PR).
"""

import numpy as np
from sklearn.metrics import f1_score


def ranking_metrics(Y_true, scores, k=3, threshold=0.5):
    """Y_true, scores: arrays (n_samples, n_labels). Returns a dict of metrics."""
    Y_true = np.asarray(Y_true)
    scores = np.asarray(scores)
    order = np.argsort(-scores, axis=1)
    has = Y_true.sum(axis=1) > 0
    top1 = Y_true[np.arange(len(Y_true)), order[:, 0]] > 0
    topk = np.array([Y_true[i, order[i, :k]].any() for i in range(len(Y_true))])
    pred = (scores >= threshold).astype(int)
    empty = pred.sum(axis=1) == 0                       # always predict at least the top-1 label
    pred[np.where(empty)[0], order[empty, 0]] = 1
    labels_present = np.where(Y_true.sum(axis=0) > 0)[0]
    return {
        "samples": int(has.sum()),
        "top1_accuracy": round(float(top1[has].mean()), 4) if has.any() else 0.0,
        f"top{k}_recall": round(float(topk[has].mean()), 4) if has.any() else 0.0,
        "micro_f1": round(float(f1_score(Y_true, pred, average="micro", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(Y_true[:, labels_present], pred[:, labels_present],
                                         average="macro", zero_division=0)), 4),
    }


def per_section_f1(Y_true, scores, label_names, threshold=0.5):
    Y_true = np.asarray(Y_true)
    scores = np.asarray(scores)
    order = np.argsort(-scores, axis=1)
    pred = (scores >= threshold).astype(int)
    empty = pred.sum(axis=1) == 0
    pred[np.where(empty)[0], order[empty, 0]] = 1
    f1s = f1_score(Y_true, pred, average=None, zero_division=0)
    support = Y_true.sum(axis=0)
    return {name: (round(float(f), 4), int(s)) for name, f, s in zip(label_names, f1s, support)}
