"""J2: Hybrid model = supervised TF-IDF + LR (Track A) combined with zero-shot retrieval (Track B, B4).

The two models are very different, so their mistakes may differ:
  - LR learned from 1,892 labelled texts (court cases + reviewed citizen stories), char n-grams handle Roman Urdu
  - Retrieval needs no labels: it compares the meaning of the text with each section's description (MiniLM)

Combination (per text):  hybrid = w * normalise(LR scores) + (1 - w) * retrieval probabilities
  - LR's calibrated per-section scores are divided by their sum so both are distributions over the 30 sections.
  - w is chosen on the VALIDATION set only (synthetic citizen stories), never on the test set.
  - Decision rule, fixed BEFORE looking at test results: the app switches to the hybrid only if it beats LR
    on validation top-3 recall by at least 2 points; otherwise LR stays (simpler, calibrated).

Run:  python -m src.hybrid
Output: results/hybrid.json, results/test_hybrid.csv (K6), docs/J2_hybrid.md
"""

import csv
import json
import os
import sys

import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.metrics import ranking_metrics  # noqa: E402

DATASET = os.path.join(PROJECT_ROOT, "data", "processed", "dataset.csv")
TEST = os.path.join(PROJECT_ROOT, "data", "test", "test_sf.csv")
OUT_JSON = os.path.join(PROJECT_ROOT, "results", "hybrid.json")
OUT_K6 = os.path.join(PROJECT_ROOT, "results", "test_hybrid.csv")
DOC = os.path.join(PROJECT_ROOT, "docs", "J2_hybrid.md")
WEIGHTS = [round(x, 1) for x in np.arange(0.0, 1.01, 0.1)]
ADOPT_MARGIN = 0.02


def labels():
    with open(os.path.join(PROJECT_ROOT, "src", "labels.json"), encoding="utf-8") as f:
        return list(json.load(f).keys())


def lr_scores(texts):
    from src.models.tfidf_lr import predict_scores_batch
    return predict_scores_batch(texts)


def retrieval_scores(texts, L):
    """B4 scores for many texts at once, re-ordered to labels.json order (same maths as src.retrieval.predict_scores)."""
    import src.retrieval as R
    R._load()
    q = R._model.encode([str(t).strip() for t in texts], normalize_embeddings=True, show_progress_bar=False,
                        batch_size=64)
    sims = q @ R._section_matrix.T / R.TEMPERATURE
    probs = np.exp(sims - sims.max(axis=1, keepdims=True))
    probs /= probs.sum(axis=1, keepdims=True)
    pos = {s: i for i, s in enumerate(R._section_ids)}
    return probs[:, [pos[l] for l in L]]


def combine(p_lr, p_ret, w):
    p_lr = p_lr / np.clip(p_lr.sum(axis=1, keepdims=True), 1e-9, None)
    return w * p_lr + (1 - w) * p_ret


def Y(rows, L):
    return np.array([[1 if l in json.loads(r["sections"]) else 0 for l in L] for r in rows])


def by_language(Ytrue, S, rows):
    out = {"all": ranking_metrics(Ytrue, S)}
    for lang in ("en", "roman_ur"):
        idx = [i for i, r in enumerate(rows) if r["language"] == lang]
        if idx:
            out[lang] = ranking_metrics(Ytrue[idx], S[idx])
    return out


def run(lr_fn=lr_scores, ret_fn=None):
    L = labels()
    ret_fn = ret_fn or (lambda texts: retrieval_scores(texts, L))
    with open(DATASET, encoding="utf-8") as f:
        val = [r for r in csv.DictReader(f) if r["split"] == "val" and r["source"] == "synthetic"]
    with open(TEST, encoding="utf-8") as f:
        test = list(csv.DictReader(f))
    Yv, Yt = Y(val, L), Y(test, L)
    lv, rv = lr_fn([r["text"] for r in val]), ret_fn([r["text"] for r in val])
    lt, rt = lr_fn([r["text"] for r in test]), ret_fn([r["text"] for r in test])

    grid = []
    for w in WEIGHTS:
        m = ranking_metrics(Yv, combine(lv, rv, w))
        grid.append({"w": w, **m})
    best = max(grid, key=lambda g: (g["top3_recall"], g["top1_accuracy"], g["w"]))
    w = best["w"]
    lr_val = next(g for g in grid if g["w"] == 1.0)
    adopt = best["top3_recall"] - lr_val["top3_recall"] >= ADOPT_MARGIN

    results = {
        "chosen_w": w, "adopt_in_app": bool(adopt), "adopt_rule": f"val top-3 gain >= {ADOPT_MARGIN}",
        "val_grid": grid,
        "val": {"lr": by_language(Yv, lv, val), "retrieval": by_language(Yv, rv, val),
                "hybrid": by_language(Yv, combine(lv, rv, w), val)},
        "test": {"lr": by_language(Yt, lt, test), "retrieval": by_language(Yt, rt, test),
                 "hybrid": by_language(Yt, combine(lt, rt, w), test)},
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    with open(OUT_K6, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f); wr.writerow(["metric", "language", "value"])
        for sub, m in results["test"]["hybrid"].items():
            for k, v in m.items():
                wr.writerow([k, sub, v])
    write_doc(results)
    return results


def write_doc(r):
    def row(name, d):
        a, ru = d["all"], d.get("roman_ur", {})
        return f"| {name} | {a['top1_accuracy']} | {a['top3_recall']} | {ru.get('top1_accuracy', '-')} | {ru.get('top3_recall', '-')} |"
    w = r["chosen_w"]
    D = ["# J2: Hybrid model (TF-IDF + LR × zero-shot retrieval)", "",
         "Generated by `python -m src.hybrid`.", "",
         "**Method.** hybrid = w × normalised LR scores + (1 − w) × retrieval probabilities. "
         "w = 1 is pure LR, w = 0 is pure retrieval. w was chosen on the synthetic **validation** set only; "
         f"the decision rule (adopt the hybrid only if validation top-3 improves by ≥ {ADOPT_MARGIN:.0%}) was fixed "
         "before the test set was scored.", "",
         f"**Chosen w = {w}.** Adopted in the app: **{'yes' if r['adopt_in_app'] else 'no, LR stays'}**.", "",
         "## Weight search (validation, synthetic citizen stories)", "",
         "| w | Top-1 | Top-3 recall |", "|---|---|---|"]
    D += [f"| {g['w']} | {g['top1_accuracy']} | {g['top3_recall']} |" for g in r["val_grid"]]
    for split in ("val", "test"):
        D += ["", f"## {'Validation' if split == 'val' else 'Held-out test (J1)'}", "",
              "| Model | Top-1 | Top-3 recall | Roman Urdu top-1 | Roman Urdu top-3 |", "|---|---|---|---|---|",
              row("TF-IDF + LR (Track A)", r[split]["lr"]), row("Retrieval, zero-shot (Track B)", r[split]["retrieval"]),
              row(f"Hybrid (w = {w})", r[split]["hybrid"])]
    D += ["", "Note: the hybrid produces a ranking, not calibrated probabilities. The app's confidence and "
          "abstain rule therefore always use the calibrated LR score (A6), even if the hybrid ordering is adopted.", ""]
    with open(DOC, "w", encoding="utf-8") as f:
        f.write("\n".join(D))


def main():
    r = run()
    for split in ("val", "test"):
        for name in ("lr", "retrieval", "hybrid"):
            a = r[split][name]["all"]; ru = r[split][name].get("roman_ur", {})
            print(f"{split:4s} {name:9s} top1={a['top1_accuracy']:.3f} top3={a['top3_recall']:.3f} "
                  f"RU top1={ru.get('top1_accuracy', 0):.3f}")
    print(f"chosen w={r['chosen_w']} | adopt in app: {r['adopt_in_app']}")
    print("->", os.path.relpath(DOC, PROJECT_ROOT))


if __name__ == "__main__":
    main()
