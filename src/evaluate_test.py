"""Evaluation of all Track A models on the held-out J1 test set (step 3.2).

Test data (never used for training, model selection or calibration):
  data/test/test_sf.csv          crime descriptions: ChatGPT-written (source=llm_test, a DIFFERENT generator from
                                 the training stories) + real people (source=real)
  data/test/out_of_scope_sf.csv  non-crime everyday problems: the model should ABSTAIN on these

Reports for every model: top-1 / top-3 / micro-F1 / macro-F1 overall, by language and by source;
the abstain trade-off at the A6 threshold (coverage, accuracy on answered cases); and the abstain rate on
non-crime text. Writes results/test_<model>.csv (K6 format) and docs/J1_results.md.

Run:  python -m src.evaluate_test
"""

import csv
import importlib
import json
import os
import sys
from collections import Counter

import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.metrics import per_section_f1, ranking_metrics  # noqa: E402

TEST = os.path.join(PROJECT_ROOT, "data", "test", "test_sf.csv")
OOS = os.path.join(PROJECT_ROOT, "data", "test", "out_of_scope_sf.csv")
RESULTS = os.path.join(PROJECT_ROOT, "results")
DOC = os.path.join(PROJECT_ROOT, "docs", "J1_results.md")
MODELS = ["tfidf_lr", "tfidf_svm", "tfidf_nb", "distilbert"]


def labels():
    with open(os.path.join(PROJECT_ROOT, "src", "labels.json"), encoding="utf-8") as f:
        return list(json.load(f).keys())


def load(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def scorer(name):
    """Return f(texts) -> calibrated score array (n, n_labels), or None if the model is unavailable here."""
    try:
        if name == "distilbert":
            from src.calibration import apply, load_calibration
            from src.models.distilbert_model import _load, logits
            _load()                                  # fails here if torch/transformers or the weights are missing
            a, b = load_calibration("distilbert")
            return lambda texts: apply(np.vstack([logits(texts[i:i + 32]) for i in range(0, len(texts), 32)]), a, b)
        mod = importlib.import_module(f"src.models.{name}")
        mod._model()
        return mod.predict_scores_batch
    except Exception as e:  # missing weights or torch
        print(f"skip {name}: {type(e).__name__}: {e}")
        return None


def threshold(name):
    p = os.path.join(RESULTS, f"calibration_{name}.json")
    return json.load(open(p))["abstain_threshold"] if os.path.exists(p) else 0.5


def evaluate(name, score_fn, rows, oos, L):
    Y = np.array([[1 if l in json.loads(r["sections"]) else 0 for l in L] for r in rows])
    S = score_fn([r["text"] for r in rows])
    subsets = {"all": range(len(rows))}
    for key in ("language", "source"):
        for v in sorted({r[key] for r in rows}):
            subsets[v] = [i for i, r in enumerate(rows) if r[key] == v]
    res = {k: ranking_metrics(Y[list(idx)], S[list(idx)]) for k, idx in subsets.items() if len(idx)}
    t = threshold(name)
    conf = S.max(axis=1)
    top1_ok = Y[np.arange(len(Y)), S.argmax(axis=1)] > 0
    ans = conf >= t
    res["abstain"] = {"threshold": t, "coverage": round(float(ans.mean()), 4),
                      "top1_accuracy_answered": round(float(top1_ok[ans].mean()), 4) if ans.any() else None}
    if oos:
        So = score_fn([r["text"] for r in oos])
        res["out_of_scope"] = {"samples": len(oos), "abstain_rate": round(float((So.max(axis=1) < t).mean()), 4)}
    errors = Counter((L[int(np.where(Y[i])[0][0])], L[int(S[i].argmax())])
                     for i in range(len(rows)) if not top1_ok[i])
    return res, per_section_f1(Y, S, L), errors


def main():
    L, rows, oos = labels(), load(TEST), (load(OOS) if os.path.exists(OOS) else [])
    all_res, best = {}, None
    for name in MODELS:
        fn = scorer(name)
        if fn is None:
            continue
        res, ps, err = evaluate(name, fn, rows, oos, L)
        all_res[name] = (res, ps, err)
        out = [{"metric": m, "language": sub, "value": v} for sub, r in res.items() for m, v in r.items()]
        with open(os.path.join(RESULTS, f"test_{name}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["metric", "language", "value"]); w.writeheader(); w.writerows(out)
        a = res["all"]
        print(f"{name:10s} top1={a['top1_accuracy']:.3f} top3={a['top3_recall']:.3f} microF1={a['micro_f1']:.3f} "
              f"| RU top1={res.get('roman_ur', {}).get('top1_accuracy', 0):.3f} "
              f"| answers {res['abstain']['coverage']:.0%} at top1 {res['abstain']['top1_accuracy_answered']} "
              f"| non-crime abstain {res.get('out_of_scope', {}).get('abstain_rate', 'n/a')}")
    src = Counter(r["source"] for r in rows); lang = Counter(r["language"] for r in rows)
    D = ["# J1 Results: held-out test set", "",
         f"Generated by `python -m src.evaluate_test`. Test set: {len(rows)} crime descriptions "
         f"({lang['en']} English, {lang['roman_ur']} Roman Urdu; {src['llm_test']} written by ChatGPT, a different "
         f"generator from the training stories, and {src['real']} by real people) + {len(oos)} non-crime descriptions. "
         "None of it was used for training, model selection or calibration. Construction and label checks: "
         "`docs/J1_test_set.md`.", "",
         "## Main results", "",
         "| Model | Top-1 | Top-3 recall | Micro-F1 | Macro-F1 | Roman Urdu top-1 | Answers (coverage) | Top-1 when answering | Non-crime abstain rate |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, (res, _, _) in all_res.items():
        a, ru, ab, oo = res["all"], res.get("roman_ur", {}), res["abstain"], res.get("out_of_scope", {})
        D.append(f"| {name} | {a['top1_accuracy']} | {a['top3_recall']} | {a['micro_f1']} | {a['macro_f1']} | "
                 f"{ru.get('top1_accuracy', '-')} | {ab['coverage']:.0%} | {ab['top1_accuracy_answered']} | "
                 f"{oo.get('abstain_rate', '-')} |")
    if "tfidf_lr" in all_res:
        res, ps, err = all_res["tfidf_lr"]
        D += ["", "## TF-IDF + LR (the app's model) by subset", "", "| Subset | n | Top-1 | Top-3 | Micro-F1 |", "|---|---|---|---|---|"]
        for k, r in res.items():
            if "samples" in r and "top1_accuracy" in r:
                D.append(f"| {k} | {r['samples']} | {r['top1_accuracy']} | {r['top3_recall']} | {r['micro_f1']} |")
        D += ["", "## Per-section F1 (TF-IDF + LR)", "", "| Section | F1 | Support |", "|---|---|---|"]
        D += [f"| {s} | {f} | {n} |" for s, (f, n) in ps.items() if n]
        D += ["", "## Most frequent top-1 confusions (true → predicted)", "", "| True | Predicted | Count |", "|---|---|---|"]
        D += [f"| {a} | {b} | {c} |" for (a, b), c in err.most_common(12)]
    D.append("")
    with open(DOC, "w", encoding="utf-8") as f:
        f.write("\n".join(D))
    print("->", os.path.relpath(DOC, PROJECT_ROOT))


if __name__ == "__main__":
    main()
