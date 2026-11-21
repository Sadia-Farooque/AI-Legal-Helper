"""K4 wrapper for the J2 hybrid model: predict_scores(text) -> {section: score}.

Uses the weight w chosen on validation by `python -m src.hybrid` (results/hybrid.json).
Scores are a ranking distribution (they sum to 1), not calibrated probabilities.
"""

import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.hybrid import combine, labels, lr_scores, retrieval_scores  # noqa: E402


def predict_scores(text):
    L = labels()
    if not (text or "").strip():
        return {l: 0.0 for l in L}
    with open(os.path.join(_ROOT, "results", "hybrid.json"), encoding="utf-8") as f:
        w = json.load(f)["chosen_w"]
    s = combine(lr_scores([text]), retrieval_scores([text], L), w)[0]
    return {l: float(round(v, 6)) for l, v in zip(L, s)}
