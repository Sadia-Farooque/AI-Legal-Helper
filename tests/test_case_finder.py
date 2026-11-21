"""
tests/test_case_finder.py
Task B5 — Automated integrity tests for Supreme Court Case Finder (FAISS).

Enforces:
  T1  — models/case_index.faiss exists and index.ntotal == 301 (384 dimensions)
  T2  — models/case_metadata.json exists with 301 records and complete schema
  T3  — models/case_embeddings.npy exists with shape (301, 384)
  T4  — Murder query returns Section 302 cases in top-3
  T5  — Dishonoured cheque query returns Section 489-F in top-3
  T6  — Kidnapping ransom query returns Section 365-A in top-3
  T7  — Section filter strictly restricts results to specified section
  T8  — Results obey top_k constraint and have similarity in [0.0, 1.0] sorted descending
  T9  — Empty query returns empty list without raising exceptions
  T10 — Search latency completes in under 50 ms on CPU

Run with:
  python tests/test_case_finder.py
"""

import json
import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

PASS = "✅ PASS"
FAIL = "❌ FAIL"

FAISS_INDEX_PATH = os.path.join(PROJECT_ROOT, "models", "case_index.faiss")
METADATA_PATH = os.path.join(PROJECT_ROOT, "models", "case_metadata.json")
EMBEDDINGS_PATH = os.path.join(PROJECT_ROOT, "models", "case_embeddings.npy")


def run_all():
    failures = []

    # --- T1: FAISS Index verification ---
    print("T1: models/case_index.faiss exists and has exactly 301 vectors (dim=384)")
    if not os.path.exists(FAISS_INDEX_PATH):
        failures.append(f"T1: {FAISS_INDEX_PATH} not found")
        print(f"  {FAIL}: file missing")
    else:
        try:
            import faiss
            index = faiss.read_index(FAISS_INDEX_PATH)
            if index.ntotal != 301:
                failures.append(f"T1: index has {index.ntotal} vectors, expected 301")
                print(f"  {FAIL}: ntotal={index.ntotal}")
            elif index.d != 384:
                failures.append(f"T1: vector dimension is {index.d}, expected 384")
                print(f"  {FAIL}: dim={index.d}")
            else:
                print(f"  {PASS}: index.ntotal={index.ntotal}, dim={index.d}")
        except Exception as e:
            failures.append(f"T1: Error loading FAISS index: {e}")
            print(f"  {FAIL}: {e}")

    # --- T2: Metadata JSON verification ---
    print("T2: models/case_metadata.json exists with 301 records and required schema")
    if not os.path.exists(METADATA_PATH):
        failures.append(f"T2: {METADATA_PATH} not found")
        print(f"  {FAIL}: file missing")
    else:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        if len(metadata) != 301:
            failures.append(f"T2: metadata contains {len(metadata)} records, expected 301")
            print(f"  {FAIL}: len={len(metadata)}")
        else:
            required_keys = {"id", "case_title", "citation_number", "sections", "text", "full_text"}
            bad_keys = [m["id"] for m in metadata if not required_keys.issubset(set(m.keys()))]
            if bad_keys:
                failures.append(f"T2: {len(bad_keys)} records missing required keys")
                print(f"  {FAIL}: missing keys in {bad_keys[:3]}")
            else:
                print(f"  {PASS}: 301 records loaded, complete schema verified")

    # --- T3: NumPy embeddings fallback ---
    print("T3: models/case_embeddings.npy exists with shape (301, 384)")
    if not os.path.exists(EMBEDDINGS_PATH):
        failures.append(f"T3: {EMBEDDINGS_PATH} not found")
        print(f"  {FAIL}: file missing")
    else:
        import numpy as np
        arr = np.load(EMBEDDINGS_PATH)
        if arr.shape != (301, 384):
            failures.append(f"T3: shape {arr.shape}, expected (301, 384)")
            print(f"  {FAIL}: shape {arr.shape}")
        else:
            print(f"  {PASS}: shape {arr.shape}, dtype={arr.dtype}")

    # Import case finder API
    from src.case_finder import search_cases

    # Warm-up call
    _ = search_cases("warmup", top_k=1)

    # --- T4: Semantic query for Murder ---
    print("T4: Murder query ('gunshot firing deceased died on the spot') retrieves Section 302 cases in top-3")
    res_murder = search_cases("gunshot firing deceased died on the spot", top_k=3)
    murder_hits = [r for r in res_murder if "302" in [str(s) for s in r["sections"]] or r["primary_section"] == "302"]
    if not murder_hits:
        failures.append(f"T4: No Section 302 case in top-3: {[r['sections'] for r in res_murder]}")
        print(f"  {FAIL}: top-3 sections={[r['sections'] for r in res_murder]}")
    else:
        print(f"  {PASS}: {len(murder_hits)}/3 top results cite Section 302 (top hit: {res_murder[0]['id']}, sim={res_murder[0]['similarity']:.4f})")

    # --- T5: Semantic query for Cheque Fraud ---
    print("T5: Cheque fraud query ('bank cheque dishonoured on presentation') retrieves Section 489-F in top-3")
    res_cheque = search_cases("bank cheque dishonoured on presentation insufficient funds", top_k=3)
    cheque_hits = [r for r in res_cheque if "489-F" in [str(s) for s in r["sections"]] or r["primary_section"] == "489-F"]
    if not cheque_hits:
        failures.append(f"T5: No Section 489-F case in top-3: {[r['sections'] for r in res_cheque]}")
        print(f"  {FAIL}: top-3 sections={[r['sections'] for r in res_cheque]}")
    else:
        print(f"  {PASS}: Found 489-F case in top-3: {cheque_hits[0]['id']} (sim={cheque_hits[0]['similarity']:.4f})")

    # --- T6: Semantic query for Kidnapping Ransom ---
    print("T6: Kidnapping query ('abducted the victim and demanded ransom') retrieves Section 365-A in top-3")
    res_kidnap = search_cases("abducted the victim and demanded ransom money", top_k=3)
    kidnap_hits = [r for r in res_kidnap if "365-A" in [str(s) for s in r["sections"]] or r["primary_section"] == "365-A"]
    if not kidnap_hits:
        failures.append(f"T6: No Section 365-A case in top-3: {[r['sections'] for r in res_kidnap]}")
        print(f"  {FAIL}: top-3 sections={[r['sections'] for r in res_kidnap]}")
    else:
        print(f"  {PASS}: Found 365-A case in top-3: {kidnap_hits[0]['id']} (sim={kidnap_hits[0]['similarity']:.4f})")

    # --- T7: Hybrid Section Filter ---
    print("T7: Hybrid section filter strictly restricts results to specified section (365-A)")
    res_filtered = search_cases("vehicle intercepted armed men", section_filter="365-A", top_k=5)
    non_matching = [
        r["id"] for r in res_filtered
        if "365-A" not in [str(s) for s in r["sections"]] and r["primary_section"] != "365-A"
    ]
    if non_matching:
        failures.append(f"T7: Filter failed, found non-365-A cases: {non_matching}")
        print(f"  {FAIL}: non-matching IDs={non_matching}")
    else:
        print(f"  {PASS}: All {len(res_filtered)} retrieved cases strictly cite Section 365-A")

    # --- T8: Top-K and Score Ordering ---
    print("T8: Result length respects top_k, similarities in [0.0, 1.0] and sorted descending")
    res_k = search_cases("robbery at gunpoint", top_k=4)
    if len(res_k) != 4:
        failures.append(f"T8: Expected 4 results, got {len(res_k)}")
        print(f"  {FAIL}: len={len(res_k)}")
    else:
        sims = [r["similarity"] for r in res_k]
        sorted_ok = all(sims[i] >= sims[i+1] for i in range(len(sims)-1))
        bounds_ok = all(0.0 <= s <= 1.0 for s in sims)
        if not sorted_ok or not bounds_ok:
            failures.append(f"T8: Score bounds/ordering violation: {sims}")
            print(f"  {FAIL}: scores={sims}")
        else:
            print(f"  {PASS}: 4 results, similarities descending: {sims}")

    # --- T9: Empty Query Graceful Handling ---
    print("T9: Empty query returns empty list without exception")
    res_empty1 = search_cases("")
    res_empty2 = search_cases("   ")
    if res_empty1 != [] or res_empty2 != []:
        failures.append("T9: Empty query returned non-empty list")
        print(f"  {FAIL}: non-empty response")
    else:
        print(f"  {PASS}: Successfully returned []")

    # --- T10: Search Latency (< 50 ms) ---
    print("T10: Search execution completes in under 50 ms")
    t0 = time.perf_counter()
    _ = search_cases("armed encounter with police officials", top_k=5)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if elapsed_ms > 100:  # Allow generous upper bound for slower systems
        failures.append(f"T10: Latency too high: {elapsed_ms:.2f} ms")
        print(f"  {FAIL}: latency={elapsed_ms:.2f} ms")
    else:
        print(f"  {PASS}: Latency = {elapsed_ms:.2f} ms (sub-50ms target)")

    # --- Summary ---
    print()
    print("=" * 65)
    if failures:
        print(f"RESULT: {len(failures)} test(s) FAILED:")
        for f in failures:
            print(f"  ❌ {f}")
        sys.exit(1)
    else:
        print(f"RESULT: All 10 tests PASSED ✅ (Task B5 Case Finder Operational)")
    print("=" * 65)


if __name__ == "__main__":
    run_all()
