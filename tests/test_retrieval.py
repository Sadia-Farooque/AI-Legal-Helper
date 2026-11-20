"""
tests/test_retrieval.py
Task B4 — Automated integrity tests for src/retrieval.py
Run with: python tests/test_retrieval.py

Tests:
  T1  — predict_scores() returns dict with exactly 30 keys
  T2  — all scores are floats in [0.0, 1.0]
  T3  — scores sum to 1.0 ± 0.001 (valid probability distribution)
  T4  — murder scenario: '302' in top-3
  T5  — cheque fraud scenario: '489-F' in top-3
  T6  — kidnapping ransom scenario: '365-A' in top-3
  T7  — robbery scenario: '392' in top-3
  T8  — empty string returns valid dict (no crash, all zeros or valid dist)
  T9  — Roman Urdu input does not raise exception
  T10 — models/section_embeddings.npy exists, shape (30, 384)
  T11 — models/section_ids.json has exactly 30 entries matching labels.json
  T12 — top_k_sections() returns ranked list with correct fields
"""

import json
import math
import os
import sys

import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

PASS = "✅ PASS"
FAIL = "❌ FAIL"

# Semantic test cases: (description, must_appear_in_top3)
SEMANTIC_CASES = [
    (
        "The accused shot and killed the complainant's brother during a land dispute. The deceased was hit by multiple bullets.",
        "302",
        "Murder scenario → PPC 302 (Qatl-i-Amd)",
    ),
    (
        "My employer gave me a cheque but it bounced. He issued it knowing the account had no money and deceived me.",
        "489-F",
        "Cheque fraud scenario → PPC 489-F",
    ),
    (
        "Armed men stopped our vehicle at gunpoint, abducted my son, and demanded ten million rupees ransom for his release.",
        "365-A",
        "Kidnapping for ransom → PPC 365-A",
    ),
    (
        "Three men stopped me on the road, threatened me with a pistol, and snatched my mobile phone and wallet.",
        "392",
        "Armed robbery on road → PPC 392",
    ),
]


def run_all():
    failures = []

    # --- T10: Embedding file exists and has correct shape ---
    print("T10: models/section_embeddings.npy exists and has shape (30, 384)")
    emb_path = os.path.join(PROJECT_ROOT, "models", "section_embeddings.npy")
    ids_path = os.path.join(PROJECT_ROOT, "models", "section_ids.json")
    if not os.path.exists(emb_path):
        print(f"  {FAIL}: {emb_path} not found — run: python src/retrieval.py --build-index")
        sys.exit(1)
    emb = np.load(emb_path)
    if emb.shape != (30, 384):
        failures.append(f"T10: embedding shape {emb.shape}, expected (30, 384)")
        print(f"  {FAIL}: shape {emb.shape}")
    else:
        print(f"  {PASS}: shape {emb.shape}, dtype={emb.dtype}")

    # --- T11: section_ids.json matches labels.json ---
    print("T11: section_ids.json has 30 entries matching labels.json")
    with open(os.path.join(PROJECT_ROOT, "src", "labels.json"), encoding="utf-8") as f:
        labels = json.load(f)
    with open(ids_path, encoding="utf-8") as f:
        section_ids = json.load(f)
    missing = set(labels.keys()) - set(section_ids)
    extra   = set(section_ids) - set(labels.keys())
    if len(section_ids) != 30 or missing or extra:
        failures.append(f"T11: id mismatch — missing={missing}, extra={extra}")
        print(f"  {FAIL}: ids={len(section_ids)}, missing={missing}, extra={extra}")
    else:
        print(f"  {PASS}: 30 IDs, all match labels.json")

    # Now import retrieval (after index check so errors are clear)
    from src.retrieval import predict_scores, top_k_sections

    # --- T1: Returns dict with exactly 30 keys ---
    print("T1: predict_scores() returns dict with exactly 30 keys")
    result = predict_scores("Someone was attacked on the street")
    if not isinstance(result, dict) or len(result) != 30:
        failures.append(f"T1: got {type(result)} with {len(result) if isinstance(result, dict) else '?'} keys")
        print(f"  {FAIL}: got {len(result) if isinstance(result, dict) else type(result)} keys")
    else:
        print(f"  {PASS}: 30 keys returned")

    # --- T2: All scores float in [0.0, 1.0] ---
    print("T2: All scores are floats in [0.0, 1.0]")
    bad_scores = [(k, v) for k, v in result.items() if not isinstance(v, float) or not (0.0 <= v <= 1.0)]
    if bad_scores:
        failures.append(f"T2: {len(bad_scores)} invalid scores: {bad_scores[:3]}")
        print(f"  {FAIL}: {len(bad_scores)} invalid scores")
    else:
        top3 = sorted(result.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"  {PASS}: all in [0,1]. Top-3: {[(s, round(v, 4)) for s,v in top3]}")

    # --- T3: Scores sum to 1.0 ± 0.001 ---
    print("T3: Scores sum to 1.0 ± 0.001")
    total = sum(result.values())
    if abs(total - 1.0) > 0.001:
        failures.append(f"T3: sum={total:.6f}, expected 1.0 ± 0.001")
        print(f"  {FAIL}: sum={total:.6f}")
    else:
        print(f"  {PASS}: sum={total:.6f}")

    # --- T4–T7: Semantic correctness ---
    for i, (query, expected_sec, description) in enumerate(SEMANTIC_CASES, start=4):
        test_id = f"T{i}"
        print(f"{test_id}: {description}")
        scores = predict_scores(query)
        top3_secs = [s for s, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]]
        if expected_sec in top3_secs:
            top_score = scores[expected_sec]
            print(f"  {PASS}: '{expected_sec}' in top-3 {top3_secs} (score={top_score:.4f})")
        else:
            top5 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
            rank = next((j+1 for j, (s, _) in enumerate(sorted(scores.items(), key=lambda x: x[1], reverse=True)) if s == expected_sec), "?")
            failures.append(f"{test_id}: '{expected_sec}' not in top-3. Rank={rank}. Top-5={[s for s,_ in top5]}")
            print(f"  {FAIL}: '{expected_sec}' not in top-3. Actual top-3={top3_secs}, rank={rank}")

    # --- T8: Empty string — no crash, valid output ---
    print("T8: Empty string input returns valid dict (no crash)")
    try:
        empty_result = predict_scores("")
        if not isinstance(empty_result, dict) or len(empty_result) != 30:
            failures.append("T8: empty input returned invalid structure")
            print(f"  {FAIL}: bad structure {type(empty_result)}")
        else:
            vals = list(empty_result.values())
            print(f"  {PASS}: returned 30-key dict. All zeros={all(v == 0.0 for v in vals)}")
    except Exception as e:
        failures.append(f"T8: exception on empty input: {e}")
        print(f"  {FAIL}: raised {type(e).__name__}: {e}")

    # --- T9: Roman Urdu input — no crash ---
    print("T9: Roman Urdu input does not raise exception")
    roman_urdu_queries = [
        "mujhe mara aur loot liya",             # "I was beaten and robbed"
        "usne meri zamin par qabza kar liya",    # "He seized my land illegally"
        "raat ko ghar mein ghus aaye",           # "They broke into the house at night"
    ]
    roman_failed = []
    for rq in roman_urdu_queries:
        try:
            rr = predict_scores(rq)
            if not isinstance(rr, dict) or len(rr) != 30:
                roman_failed.append(rq[:30])
        except Exception as e:
            roman_failed.append(f"'{rq[:30]}' → {e}")
    if roman_failed:
        failures.append(f"T9: Roman Urdu failures: {roman_failed}")
        print(f"  {FAIL}: {roman_failed}")
    else:
        print(f"  {PASS}: {len(roman_urdu_queries)} Roman Urdu queries handled without error")

    # --- T12: top_k_sections() returns correct structure ---
    print("T12: top_k_sections() returns ranked list with correct fields")
    try:
        topk = top_k_sections("someone was robbed at gunpoint", k=5)
        req_fields = {"section_id", "score", "rank"}
        ok = (
            isinstance(topk, list) and
            len(topk) == 5 and
            all(req_fields.issubset(set(r.keys())) for r in topk) and
            [r["rank"] for r in topk] == list(range(1, 6)) and
            topk[0]["score"] >= topk[-1]["score"]
        )
        if ok:
            print(f"  {PASS}: top-5 = {[r['section_id'] for r in topk]}, scores descending={topk[0]['score']:.4f}→{topk[-1]['score']:.4f}")
        else:
            failures.append("T12: top_k_sections() returned malformed structure")
            print(f"  {FAIL}: malformed output: {topk}")
    except Exception as e:
        failures.append(f"T12: exception: {e}")
        print(f"  {FAIL}: {e}")

    # --- Summary ---
    print()
    print("=" * 60)
    if failures:
        print(f"RESULT: {len(failures)} test(s) FAILED:")
        for f in failures:
            print(f"  ❌ {f}")
        sys.exit(1)
    else:
        print(f"RESULT: All 12 tests PASSED ✅")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
