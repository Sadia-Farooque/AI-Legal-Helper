"""Task A8: Incident analysis pipeline behind the Incident Analyzer page.

analyze(text) ->
  status        "ok" | "abstain" | "empty" | "urdu_script"
  language      "en" | "roman_ur"   (simple heuristic, for display and logging)
  results       top-3 sections: calibrated confidence + legal facts from the CrPC Schedule II lookup (B1)
                + summary/elements from sections.json (B2)
  confusable    how the top-1 differs from the next section when both are in a confusable group (B2)
  guide         next steps for the predicted sections (src/next_steps.py)

Model: calibrated TF-IDF + Logistic Regression (A4 + A6), chosen in decision D10 because it beat
DistilBERT on citizen and Roman Urdu text. Abstain rule: if the calibrated top-1 confidence is below the
A6 threshold, the app says it is not sure instead of guessing. Explanations (A7, LIME) are computed on
demand by the page because they are slower.
"""

import csv
import json
import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.next_steps import guidance  # noqa: E402

MODEL_NAME = "tfidf_lr"
LOOKUP_CSV = os.path.join(PROJECT_ROOT, "data", "lookup", "ppc_lookup.csv")
SECTIONS_JSON = os.path.join(PROJECT_ROOT, "data", "content", "sections.json")
GROUPS_JSON = os.path.join(PROJECT_ROOT, "data", "content", "confusable_groups.json")
CALIBRATION_JSON = os.path.join(PROJECT_ROOT, "results", f"calibration_{MODEL_NAME}.json")
DEFAULT_THRESHOLD = 0.70
MERGE = {"441": "447"}      # 441 defines and 447 punishes the same trespass: show as one result (D5)
NEVER_SHOW = {"307"}        # not a citizen-facing offence in the PPC (A1, D1)

_URDU_SCRIPT = re.compile(r"[؀-ۿ]")
_RU_MARKERS = {"hai", "hain", "ne", "ka", "ki", "ke", "ko", "se", "mein", "aur", "nahi", "tha", "thi", "kar",
               "diya", "gaya", "gayi", "raha", "mera", "meri", "mere", "wala", "liya", "bhai", "kal"}


def _load_csv_by(path, key):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return {r[key]: r for r in csv.DictReader(f)}


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


LOOKUP = _load_csv_by(LOOKUP_CSV, "section")
SECTIONS = _load_json(SECTIONS_JSON, {})
GROUPS = _load_json(GROUPS_JSON, [])
THRESHOLD = float(_load_json(CALIBRATION_JSON, {}).get("abstain_threshold", DEFAULT_THRESHOLD))


def detect_language(text):
    toks = re.findall(r"[a-z]+", text.lower())
    share = sum(t in _RU_MARKERS for t in toks) / max(len(toks), 1)
    return "roman_ur" if share >= 0.12 else "en"


def _predict(text):
    from src.models.tfidf_lr import predict_scores
    return predict_scores(text)


def _merge_and_rank(scores):
    s = dict(scores)
    for src, dst in MERGE.items():
        if src in s and dst in s:
            s[dst] = max(s[dst], s.pop(src))
    for k in NEVER_SHOW:
        s.pop(k, None)
    return sorted(s.items(), key=lambda kv: -kv[1])


def section_card(sec, score):
    lk = LOOKUP.get(sec, {})
    sj = SECTIONS.get(sec, {}) if isinstance(SECTIONS, dict) else {}
    return {
        "section": sec,
        "score": round(float(score), 4),
        "name": lk.get("short_name") or sj.get("title", f"Section {sec}"),
        "meaning": lk.get("meaning", ""),
        "summary": sj.get("summary", ""),
        "elements": sj.get("elements", []),
        "cognizable": lk.get("cognizable", "unknown"),
        "bailable": lk.get("bailable", "unknown"),
        "compoundable": lk.get("compoundable", "unknown"),
        "punishment": lk.get("punishment", ""),
        "court": lk.get("court", ""),
        "also_441": sec == "447",
    }


def confusable_note(sec_a, sec_b):
    for g in GROUPS:
        secs = g.get("sections", [])
        if sec_a in secs and sec_b in secs:
            d = g.get("key_differentiators", {})
            return {"group": g.get("group_name", ""), "a": sec_a, "b": sec_b,
                    "a_text": d.get(sec_a, ""), "b_text": d.get(sec_b, "")}
    return None


def analyze(text, predict_fn=None, threshold=None, k=3):
    text = (text or "").strip()
    if not text:
        return {"status": "empty"}
    if _URDU_SCRIPT.search(text) and not re.search(r"[A-Za-z]{3,}", text):
        return {"status": "urdu_script"}
    threshold = THRESHOLD if threshold is None else threshold
    ranked = _merge_and_rank((predict_fn or _predict)(text))
    top = ranked[:k]
    results = [section_card(s, v) for s, v in top]
    status = "ok" if top and top[0][1] >= threshold else "abstain"
    out = {
        "status": status,
        "language": detect_language(text),
        "threshold": threshold,
        "results": results,
        "confusable": confusable_note(top[0][0], top[1][0]) if len(top) > 1 else None,
        "guide": guidance([s for s, _ in top], LOOKUP),
    }
    return out


def compare_retrieval(text, k=3):
    """Top-k from Track B's zero-shot retrieval model (B4), for side-by-side comparison in the page.

    Returns (list[(section, score)], None) or (None, reason) if that model cannot run on this machine
    (it needs sentence-transformers and the cached all-MiniLM-L6-v2 model).
    """
    try:
        from src.retrieval import predict_scores as retrieval_scores
        ranked = _merge_and_rank(retrieval_scores(text))
        return ranked[:k], None
    except Exception as e:  # noqa: BLE001  (any missing dependency or index)
        return None, f"{type(e).__name__}: {e}"


# ---- Legal condition notes (display only: they never change the model's ranking or the test metrics) ----------
# PPC 354 and 354-A protect a woman by their wording. PPC 509 has two parts: (i) insulting the modesty of a
# woman, and (ii) sexual harassment of "the other person" (gender-neutral, Criminal Law (Amendment) Act 2010).
WOMEN_ONLY = {"354", "354A"}
_FEMALE_CUES = re.compile(
    r"\b(she|her|hers|woman|women|girl|girls|lady|ladies|wife|sister|daughter|mother|mom|mum|aunt|niece|bride|"
    r"female|widow|aurat|auraton|larki|larkee|larkiyon|behen|bahen|behan|beti|biwi|bivi|ammi|ami|maa|khala|"
    r"phuppo|phuphi|bhabhi|begum|baji|apa|rahi|gayi|karti|jaati|sakti)\b", re.I)


def legal_condition(section, text):
    """Plain-language condition a citizen must check before relying on a section, or None."""
    if section in WOMEN_ONLY:
        if _FEMALE_CUES.search(text or ""):
            return "Applies only when the victim is a woman."
        return ("Applies only when the victim is a woman. Your description does not say the victim is a woman, "
                "so check this before relying on it.")
    if section == "509":
        return ("Covers insulting a woman's modesty, and sexual harassment of anyone, including at work "
                "(s.509(ii)).")
    return None
