"""Crime gate (D30), EXPERIMENTAL, NOT USED BY THE APP: is this message about a crime at all?

The 30-section classifier has no "not a crime" option: it must always pick one of the 30 offences, and the
abstain threshold alone does not stop everyday complaints from getting a confident wrong answer (found in the
hands-on check: "my landlord wont return my deposit" -> 337-F bodily injury at 78%).

This gate is a separate binary TF-IDF + logistic regression model:
  positive = citizen-style crime messages (data/processed/dataset.csv, source "synthetic", train split)
  negative = everyday non-crime problems (data/processed/non_crime.csv, train split: rent, salary, marks,
             shopping, family, bills, services, legal questions)
Both sides are in the same chat style, so the gate learns the content, not the writing style. Court texts are
left out for the same reason. If P(crime) < GATE_THRESHOLD (0.5, fixed before testing) the app says the message
does not look like a crime instead of naming a section. The 30-section model itself is unchanged.

Result (D30): best validation setting (character n-grams, C=4) passes 98% of crime messages but stops only 82%
of non-crime ones, and it would wrongly block "my landlord beat me when I asked for my deposit" (0.46). With only
112 non-crime training messages it cannot separate such cases, so it is NOT connected to the app. It needs several
hundred varied (ideally real) non-crime messages first; the real-message form collects them (D28).

The gate trains in a few seconds on first use (no saved weights needed).
Run  python -m src.models.crime_gate  for its validation and J1 test results (-> results/crime_gate.json).
"""

import csv
import json
import os
import threading
from functools import lru_cache

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASET = os.path.join(PROJECT_ROOT, "data", "processed", "dataset.csv")
NON_CRIME = os.path.join(PROJECT_ROOT, "data", "processed", "non_crime.csv")
OUT_JSON = os.path.join(PROJECT_ROOT, "results", "crime_gate.json")
GATE_THRESHOLD = 0.5
_LOCK = threading.Lock()


def _rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def training_data(split="train"):
    crime = [r["text"] for r in _rows(DATASET) if r["source"] == "synthetic" and r["split"] == split]
    other = [r["text"] for r in _rows(NON_CRIME) if r["split"] == split]
    return crime + other, [1] * len(crime) + [0] * len(other)


@lru_cache(maxsize=1)
def _gate():
    with _LOCK:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from src.preprocess import normalize
        X, y = training_data("train")
        model = Pipeline([("tfidf", TfidfVectorizer(preprocessor=normalize, analyzer="char_wb", ngram_range=(3, 5),
                                                    min_df=2, sublinear_tf=True)),
                          ("lr", LogisticRegression(C=4.0, class_weight="balanced", max_iter=2000,
                                                    solver="liblinear"))])
        model.fit(X, y)
        return model


def crime_probability(text):
    return float(_gate().predict_proba([text or ""])[0][1])


def is_crime(text, threshold=GATE_THRESHOLD):
    return crime_probability(text) >= threshold


def _rates(texts, crime):
    p = _gate().predict_proba(texts)[:, 1]
    passed = (p >= GATE_THRESHOLD)
    return {"n": len(texts), ("passed_as_crime" if crime else "stopped_as_not_crime"):
            round(float(passed.mean() if crime else (~passed).mean()), 4)}


def main():
    Xv, yv = training_data("val")
    test = _rows(os.path.join(PROJECT_ROOT, "data", "test", "test_sf.csv"))
    oos = _rows(os.path.join(PROJECT_ROOT, "data", "test", "out_of_scope_sf.csv"))
    res = {
        "threshold": GATE_THRESHOLD,
        "val_crime": _rates([x for x, y in zip(Xv, yv) if y == 1], True),
        "val_non_crime": _rates([x for x, y in zip(Xv, yv) if y == 0], False),
        "test_crime_J1": _rates([r["text"] for r in test], True),
        "test_non_crime_J1": _rates([r["text"] for r in oos], False),
        "test_real_messages": _rates([r["text"] for r in test if r["source"] == "real"], True),
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    for k, v in res.items():
        print(f"{k:22s} {v}")
    print("->", os.path.relpath(OUT_JSON, PROJECT_ROOT))


if __name__ == "__main__":
    main()
