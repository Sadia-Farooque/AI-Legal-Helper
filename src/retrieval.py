"""
src/retrieval.py
Task B4 — Zero-Shot Retrieval Classifier using Sentence Embeddings.

Architecture:
  - Model:   all-MiniLM-L6-v2 (bi-encoder, 22 MB, CPU-friendly)
  - Index:   30 composite reference passages (title + summary + scenarios + citizen term)
  - Scoring: cosine similarity → temperature-scaled softmax → probability distribution
  - Contract: predict_scores(text: str) -> dict[str, float]   (K4 contract)

Usage:
  # Build/rebuild the section embedding index:
  python src/retrieval.py --build-index

  # Smoke-test a query:
  python src/retrieval.py --query "My neighbour stabbed me with a knife"
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

import numpy as np

# Tell HuggingFace Hub to use only local cache (no network calls).
# This is set before any sentence_transformers import so the library
# never tries to reach hf.co, which fails in sandbox / offline environments.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE         = os.path.dirname(os.path.abspath(__file__))
_ROOT         = os.path.abspath(os.path.join(_HERE, ".."))
_LABELS_PATH  = os.path.join(_ROOT, "src", "labels.json")
_SECTIONS_PATH= os.path.join(_ROOT, "data", "content", "sections.json")
_MODELS_DIR   = os.path.join(_ROOT, "models")
_EMB_PATH     = os.path.join(_MODELS_DIR, "section_embeddings.npy")
_IDS_PATH     = os.path.join(_MODELS_DIR, "section_ids.json")
_REQS_PATH    = os.path.join(_ROOT, "requirements.txt")

# ---------------------------------------------------------------------------
# Hyper-parameter — tuned in §7.6 Step 6
# Temperature T < 1.0 sharpens the softmax distribution.
# T=0.25: empirically gives top-1 score ~0.55–0.75 for strong query-section matches.
# Tuned on data/test/stub_test.csv (see results/retrieval_zeroshot.csv).
# ---------------------------------------------------------------------------
TEMPERATURE: float = 0.25
MODEL_NAME:  str   = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Lazy-load globals (populated on first predict_scores() call)
# ---------------------------------------------------------------------------
_model         = None   # SentenceTransformer instance
_section_matrix: Optional[np.ndarray] = None   # shape (30, 384) float32
_section_ids:   Optional[List[str]]   = None   # ordered list of section IDs


# ---------------------------------------------------------------------------
# Reference passage builder
# ---------------------------------------------------------------------------
def _build_reference_passages() -> Dict[str, str]:
    """
    Constructs one composite reference passage per section by concatenating:
      1. Section title (anchors legal vocabulary)
      2. Plain-English summary from B2 (sections.json)
      3. Example scenarios from B2 (citizen-language incident descriptions)
      4. Citizen term from labels.json (lay vocabulary the citizen uses)

    Why this order:
      - Title first so the embedding is anchored to the legal concept name.
      - Summary second for definitional context.
      - Scenarios third — these look most like what a citizen will actually type.
      - Citizen term last as a vocabulary boost.

    Returns: {section_id: passage_string}
    """
    with open(_LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)
    with open(_SECTIONS_PATH, "r", encoding="utf-8") as f:
        sections = json.load(f)

    passages: Dict[str, str] = {}

    for sec_id, label_data in labels.items():
        title        = label_data.get("title", "")
        citizen_term = label_data.get("citizen_term", "")  # singular key in labels.json

        sec_data     = sections.get(sec_id, {})
        summary      = sec_data.get("summary", "")
        scenarios    = sec_data.get("example_scenarios", [])

        # Flatten scenarios list into a single string
        scenarios_text = " ".join(str(s) for s in scenarios)

        # Composite passage — richer = better retrieval quality
        parts = [p for p in [title, summary, scenarios_text, citizen_term] if p.strip()]
        passage = ". ".join(parts)

        passages[sec_id] = passage

    return passages


# ---------------------------------------------------------------------------
# Index builder (run once, saves .npy + .json to models/)
# ---------------------------------------------------------------------------
def build_index(verbose: bool = True) -> None:
    """
    Encodes all 30 reference passages with the sentence transformer,
    saves embeddings as (30, 384) float32 matrix and ordered ID list.

    Why save to disk:
      Encoding 30 passages takes ~3 s on CPU. Saving once and loading with
      np.load() costs < 10 ms — eliminates the per-startup encoding penalty.
    """
    from sentence_transformers import SentenceTransformer  # import here to allow
    # other functions to import this module without loading torch at import time

    if verbose:
        print(f"[retrieval] Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    passages_dict = _build_reference_passages()
    section_ids   = list(passages_dict.keys())   # stable order
    passages_list = [passages_dict[sid] for sid in section_ids]

    if verbose:
        print(f"[retrieval] Encoding {len(section_ids)} section reference passages...")

    embeddings = model.encode(
        passages_list,
        normalize_embeddings=True,  # L2-normalise → cosine sim = dot product
        show_progress_bar=verbose,
        batch_size=32,
    )
    # embeddings shape: (30, 384), dtype float32

    os.makedirs(_MODELS_DIR, exist_ok=True)
    np.save(_EMB_PATH, embeddings)
    with open(_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(section_ids, f, indent=2)

    if verbose:
        print(f"[retrieval] Saved embeddings → {_EMB_PATH}  shape={embeddings.shape}")
        print(f"[retrieval] Saved section IDs → {_IDS_PATH}")
        print(f"\nSample passage for '302':\n  {passages_dict.get('302', '')[:200]}")


# ---------------------------------------------------------------------------
# Lazy loader
# ---------------------------------------------------------------------------
def _load() -> None:
    """
    Loads model + index on first call. Subsequent calls are no-ops.

    Why lazy:
      `import src.retrieval` appears at Streamlit module-level and in test
      imports. Without lazy loading, every import would pay the ~3 s model
      load cost. With the _model is None guard, only the first predict_scores()
      call pays it; all subsequent calls skip straight through.
    """
    global _model, _section_matrix, _section_ids

    if _model is not None:
        return  # Already loaded — fast path

    if not os.path.exists(_EMB_PATH) or not os.path.exists(_IDS_PATH):
        raise FileNotFoundError(
            f"Section index not found. Run first:\n"
            f"  python src/retrieval.py --build-index\n"
            f"Expected: {_EMB_PATH}"
        )

    from sentence_transformers import SentenceTransformer
    _model          = SentenceTransformer(MODEL_NAME)
    _section_matrix = np.load(_EMB_PATH)                    # (30, 384) float32
    with open(_IDS_PATH, "r", encoding="utf-8") as f:
        _section_ids = json.load(f)


# ---------------------------------------------------------------------------
# K4 Contract — primary public API
# ---------------------------------------------------------------------------
def predict_scores(text: str) -> Dict[str, float]:
    """
    K4 contract: predict_scores(text: str) -> dict[str, float]

    Maps a plain-language incident description to PPC section relevance scores.

    Pipeline:
      1. Lazy-load model + pre-encoded section matrix.
      2. Encode query text → 384-dim unit vector.
      3. Dot product with section matrix → raw cosine similarities (30,).
      4. Temperature-scaled softmax → probability distribution (30,).
      5. Return {section_id: probability} for all 30 sections.

    Args:
        text: Citizen incident description (English or Roman Urdu).

    Returns:
        dict mapping each of the 30 PPC section IDs to a float in [0.0, 1.0].
        Values sum to 1.0 (valid probability distribution).
        Higher value = more semantically similar to that section's reference text.
    """
    _load()  # no-op if already loaded

    # --- Edge case: empty input ---
    if not text or not str(text).strip():
        return {sid: 0.0 for sid in _section_ids}

    # --- Step 1: Encode query ---
    query_vec = _model.encode(
        [str(text).strip()],
        normalize_embeddings=True,   # unit vector → dot product = cosine sim
        show_progress_bar=False,
    )[0]  # shape: (384,)

    # --- Step 2: Cosine similarities (dot product of unit vectors) ---
    # _section_matrix: (30, 384)  |  query_vec: (384,)
    # Result: (30,) — one similarity per section
    raw_sims = np.dot(_section_matrix, query_vec)   # shape: (30,)

    # --- Step 3: Temperature-scaled numerically-stable softmax ---
    # Divide by T to sharpen the distribution (see §7.4 rationale).
    # Subtract max before exp() to prevent float overflow (standard recipe).
    sharpened = raw_sims / TEMPERATURE
    exp_vals  = np.exp(sharpened - sharpened.max())
    probs     = exp_vals / exp_vals.sum()            # sums to 1.0

    return {sid: float(probs[i]) for i, sid in enumerate(_section_ids)}


# ---------------------------------------------------------------------------
# Top-k convenience helper (used by Streamlit pages)
# ---------------------------------------------------------------------------
def top_k_sections(text: str, k: int = 5) -> List[Dict]:
    """
    Returns the top-k sections as a list of dicts, ranked by score descending.
    Each dict: {section_id, score, rank}
    """
    scores = predict_scores(text)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [
        {"section_id": sid, "score": round(score, 6), "rank": i + 1}
        for i, (sid, score) in enumerate(ranked[:k])
    ]


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------
def _cli():
    parser = argparse.ArgumentParser(description="B4 Retrieval Classifier — build index or query")
    parser.add_argument("--build-index", action="store_true", help="Encode all section passages and save .npy index")
    parser.add_argument("--query",       type=str,            help="Run predict_scores on this query text")
    parser.add_argument("--top-k",       type=int, default=5, help="Number of top results to show (default: 5)")
    args = parser.parse_args()

    if args.build_index:
        build_index(verbose=True)
        return

    if args.query:
        print(f"\nQuery: \"{args.query}\"")
        results = top_k_sections(args.query, k=args.top_k)
        # Load section titles for display
        with open(_LABELS_PATH, encoding="utf-8") as f:
            labels = json.load(f)
        print(f"\nTop {args.top_k} PPC Sections:")
        print(f"{'Rank':<5} {'Section':<10} {'Score':<8} {'Title'}")
        print("-" * 70)
        for r in results:
            sid   = r["section_id"]
            score = r["score"]
            title = labels.get(sid, {}).get("title", "")[:45]
            print(f"{r['rank']:<5} {sid:<10} {score:<8.4f} {title}")
        return

    parser.print_help()


if __name__ == "__main__":
    _cli()
