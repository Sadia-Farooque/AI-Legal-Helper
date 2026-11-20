"""K4 wrapper for the Task A5 DistilBERT model: predict_scores(text) -> {section: score}.

Expects the folder downloaded from notebooks/A5_distilbert.ipynb at models/distilbert/
(config, weights, tokenizer, track_a_config.json). Not committed to git (too large).
If A6 has written a temperature into track_a_config.json, scores are calibrated:
score = sigmoid(logit / T).

Usage: python src/evaluate.py --model distilbert_model --test-data <csv>
"""

import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.preprocess import normalize  # noqa: E402

MODEL_DIR = os.path.join(_ROOT, "models", "distilbert")
_STATE = {}


def _load():
    if not _STATE:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        cfg = json.load(open(os.path.join(MODEL_DIR, "track_a_config.json"), encoding="utf-8"))
        _STATE.update(
            torch=torch, cfg=cfg,
            tok=AutoTokenizer.from_pretrained(MODEL_DIR),
            model=AutoModelForSequenceClassification.from_pretrained(MODEL_DIR).eval(),
        )
    return _STATE


def logits(texts):
    s = _load()
    enc = s["tok"]([normalize(t) for t in texts], truncation=True, max_length=s["cfg"]["max_len"],
                   padding=True, return_tensors="pt")
    with s["torch"].no_grad():
        return s["model"](**enc).logits.float().numpy()


def predict_scores(text):
    s = _load()
    labels = s["cfg"]["labels"]
    if not (text or "").strip():
        return {l: 0.0 for l in labels}
    import numpy as np
    z = logits([text])[0] / float(s["cfg"].get("temperature", 1.0))
    p = 1.0 / (1.0 + np.exp(-z))
    return {l: float(round(v, 6)) for l, v in zip(labels, p)}
