"""Task A7: "Why this section?" word-level explanations with LIME.

LIME perturbs the input (removes random words), watches how the model's score for one section
changes, and fits a small linear model. The weights say which words pushed the score up (+) or
down (-). It works for ANY model exposing predict_scores, so the same code explains TF-IDF and DistilBERT.

    from src.explain import explain, highlight_html
    words = explain(text, predict_scores, section="392")   # [(word, weight), ...]
    html  = highlight_html(text, words)                    # for the Streamlit page

Run a demo:  python -m src.explain --model tfidf_lr "do larkay bike par aaye aur mobile cheen liya"
"""

import argparse
import html
import importlib
import json
import os
import re
import sys

import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _labels():
    with open(os.path.join(PROJECT_ROOT, "src", "labels.json"), "r", encoding="utf-8") as f:
        return list(json.load(f).keys())


def batch_fn(predict_scores, labels):
    """Adapt K4 predict_scores(text)->dict into LIME's classifier_fn(list[str]) -> array (n, n_labels)."""
    def fn(texts):
        return np.array([[predict_scores(t).get(l, 0.0) for l in labels] for t in texts])
    return fn


def explain(text, predict_scores, section=None, num_features=8, num_samples=300, seed=42, batch_predict=None):
    """Return [(word, weight)] for `section` (default: the top-scoring section), strongest first.

    batch_predict(list[str]) -> array (n, n_labels), if given, scores all LIME samples in one call (much faster).
    """
    from lime.lime_text import LimeTextExplainer
    labels = _labels()
    scores = predict_scores(text)
    if section is None:
        section = max(scores, key=scores.get)
    idx = labels.index(section)
    explainer = LimeTextExplainer(class_names=labels, bow=True, random_state=seed,
                                  split_expression=r"\W+")
    fn = batch_predict if batch_predict is not None else batch_fn(predict_scores, labels)
    exp = explainer.explain_instance(text, fn, labels=[idx],
                                     num_features=num_features, num_samples=num_samples)
    return exp.as_list(label=idx)


def highlight_html(text, weights, max_alpha=0.75):
    """Colour each word by its LIME weight: green = supports the section, red = against it."""
    w = {k.lower(): v for k, v in weights}
    top = max((abs(v) for v in w.values()), default=1.0) or 1.0
    out = []
    for token in re.split(r"(\W+)", text):
        v = w.get(token.lower())
        if v is None or not token.strip():
            out.append(html.escape(token))
            continue
        a = max_alpha * abs(v) / top
        colour = f"rgba(46,160,67,{a:.2f})" if v > 0 else f"rgba(218,54,51,{a:.2f})"
        out.append(f'<span style="background:{colour};border-radius:3px;padding:0 2px" '
                   f'title="{v:+.3f}">{html.escape(token)}</span>')
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="tfidf_lr")
    ap.add_argument("text")
    a = ap.parse_args()
    mod = importlib.import_module(f"src.models.{a.model}")
    scores = mod.predict_scores(a.text)
    top = sorted(scores.items(), key=lambda kv: -kv[1])[:3]
    print("top-3:", [(s, round(v, 3)) for s, v in top])
    for w, v in explain(a.text, mod.predict_scores, section=top[0][0]):
        print(f"  {w:15s} {v:+.3f}")


if __name__ == "__main__":
    main()
