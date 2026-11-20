"""
src/case_finder.py
Task B5 — Similar Case Finder using FAISS Vector Index.

Indexes and retrieves 301 Supreme Court of Pakistan criminal judgments
(mined in Task B3: data/processed/sc_clean.csv) using dense embeddings
and exact Inner Product (cosine) search.

Key Capabilities:
  - Sub-millisecond dense vector search via FAISS IndexFlatIP (384-dim).
  - Hybrid relational filtering by cited PPC section and minimum similarity.
  - Zero-redundancy shared embedding model (all-MiniLM-L6-v2 with offline mode).
  - Fallback resilience: pure NumPy dot product fallback if FAISS runtime is unavailable.

Usage:
  # 1. Build / rebuild the FAISS vector index & metadata:
  python src/case_finder.py --build-index

  # 2. Query precedents via CLI:
  python src/case_finder.py --query "gunshot firing during property dispute" --top-k 3
  python src/case_finder.py --query "ransom demand" --section 365-A --top-k 3
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

import numpy as np

# Ensure HuggingFace and Transformers run strictly offline from local cache
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# ---------------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_SC_CLEAN_CSV = os.path.join(_ROOT, "data", "processed", "sc_clean.csv")
_MODELS_DIR = os.path.join(_ROOT, "models")
_FAISS_INDEX_PATH = os.path.join(_MODELS_DIR, "case_index.faiss")
_METADATA_PATH = os.path.join(_MODELS_DIR, "case_metadata.json")
_EMBEDDINGS_NPY_PATH = os.path.join(_MODELS_DIR, "case_embeddings.npy")
_LABELS_PATH = os.path.join(_ROOT, "src", "labels.json")

MODEL_NAME: str = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Module-level singletons (lazy loaded on first search)
# ---------------------------------------------------------------------------
_model = None
_faiss_index = None
_case_metadata: Optional[List[Dict[str, Any]]] = None
_case_embeddings: Optional[np.ndarray] = None


# ---------------------------------------------------------------------------
# Document Packaging for Semantic Embedding
# ---------------------------------------------------------------------------
def format_case_passage(row: Dict[str, Any], sections_list: List[str]) -> str:
    """
    Constructs a domain-specific search passage from the case record.
    Packages title, citation, cited statutes, and isolated factual narrative
    into a dense 180-300 token passage optimal for all-MiniLM-L6-v2.
    """
    sections_str = ", ".join(f"PPC {s}" for s in sections_list) if sections_list else "Unspecified"
    title = str(row.get("case_title", "")).strip() or "Supreme Court of Pakistan"
    citation = str(row.get("citation_number", "")).strip()
    facts = str(row.get("text", "")).strip()

    parts = [
        f"Case: {title}",
        f"Citation: {citation}" if citation else "",
        f"Cited Sections: {sections_str}",
        f"Facts of Occurrence: {facts}"
    ]
    return ". ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Index Builder
# ---------------------------------------------------------------------------
def build_case_index(verbose: bool = True) -> None:
    """
    Encodes all 301 Supreme Court cases, generates the FAISS IndexFlatIP,
    and exports hydrated metadata to models/case_metadata.json.
    """
    import pandas as pd
    from sentence_transformers import SentenceTransformer

    if not os.path.exists(_SC_CLEAN_CSV):
        raise FileNotFoundError(f"Cleaned SC dataset not found at {_SC_CLEAN_CSV}. Run Task B3 first.")

    if verbose:
        print(f"[case_finder] Loading SC dataset from {_SC_CLEAN_CSV}...")
    df = pd.read_csv(_SC_CLEAN_CSV)
    n_cases = len(df)
    if verbose:
        print(f"[case_finder] Found {n_cases} criminal judgments.")

    # 1. Format passages and build metadata records
    passages = []
    metadata_list = []

    for idx, row in df.iterrows():
        raw_sections = row.get("sections", "[]")
        try:
            sections_list = json.loads(raw_sections) if isinstance(raw_sections, str) else list(raw_sections)
        except Exception:
            sections_list = [s.strip() for s in str(raw_sections).replace(";", ",").split(",") if s.strip()]

        passage = format_case_passage(row, sections_list)
        passages.append(passage)

        citation_raw = str(row.get("citation_number", "")).strip()
        citation_clean = "" if citation_raw.lower() in ("nan", "none", "") else citation_raw

        title_raw = str(row.get("case_title", "")).strip()
        title_clean = "Supreme Court of Pakistan" if title_raw.lower() in ("nan", "none", "versus", "") else title_raw

        record = {
            "index_id": idx,
            "id": str(row.get("id", f"sc_{idx+1:04d}")),
            "case_title": title_clean,
            "citation_number": citation_clean,
            "primary_section": str(row.get("primary_section", "")),
            "sections": sections_list,
            "text": str(row.get("text", "")),
            "full_text": str(row.get("full_text", "")),
            "split": str(row.get("split", "train")),
            "source": str(row.get("source", "sc")),
        }
        metadata_list.append(record)

    # 2. Compute embeddings
    if verbose:
        print(f"[case_finder] Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    if verbose:
        print(f"[case_finder] Encoding {n_cases} case passages (384 dimensions)...")
    embeddings = model.encode(
        passages,
        normalize_embeddings=True,  # L2 normalization -> dot product equals cosine similarity
        show_progress_bar=verbose,
        batch_size=32,
    )
    embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

    os.makedirs(_MODELS_DIR, exist_ok=True)

    # 3. Build & Save FAISS Index
    try:
        import faiss
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        faiss.write_index(index, _FAISS_INDEX_PATH)
        if verbose:
            print(f"[case_finder] FAISS IndexFlatIP written -> {_FAISS_INDEX_PATH} ({index.ntotal} vectors)")
    except Exception as e:
        if verbose:
            print(f"[case_finder] Warning: FAISS write encountered error: {e}. Relying on NumPy fallback.")

    # 4. Save NumPy fallback array and JSON metadata
    np.save(_EMBEDDINGS_NPY_PATH, embeddings)
    with open(_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"[case_finder] NumPy embeddings saved -> {_EMBEDDINGS_NPY_PATH} (shape: {embeddings.shape})")
        print(f"[case_finder] Metadata exported -> {_METADATA_PATH} ({len(metadata_list)} records)")
        print(f"\nSample Search Passage [0]:\n  {passages[0][:200]}...")


# ---------------------------------------------------------------------------
# Lazy Loader
# ---------------------------------------------------------------------------
def _load_index_and_model() -> None:
    """Loads embedding model, FAISS index (or NumPy backup), and metadata on demand."""
    global _model, _faiss_index, _case_metadata, _case_embeddings

    if _case_metadata is not None and (_faiss_index is not None or _case_embeddings is not None):
        return  # already initialized

    if not os.path.exists(_METADATA_PATH):
        raise FileNotFoundError(
            f"Case index artifacts not found. Please run first:\n"
            f"  python src/case_finder.py --build-index\n"
            f"Expected metadata file: {_METADATA_PATH}"
        )

    # Load metadata
    with open(_METADATA_PATH, "r", encoding="utf-8") as f:
        _case_metadata = json.load(f)

    # Load FAISS index if available
    if os.path.exists(_FAISS_INDEX_PATH):
        try:
            import faiss
            _faiss_index = faiss.read_index(_FAISS_INDEX_PATH)
        except Exception:
            _faiss_index = None

    # Load NumPy backup
    if os.path.exists(_EMBEDDINGS_NPY_PATH):
        _case_embeddings = np.load(_EMBEDDINGS_NPY_PATH)

    # Load embedding model
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer(MODEL_NAME)


# ---------------------------------------------------------------------------
# Search Engine API Contract
# ---------------------------------------------------------------------------
def search_cases(
    query: str,
    top_k: int = 5,
    section_filter: Optional[str] = None,
    min_similarity: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Semantically searches 301 Supreme Court of Pakistan judgments.

    Args:
        query: Factual scenario or legal proposition in plain language.
        top_k: Maximum number of precedents to return (default: 5).
        section_filter: Optional PPC section ID (e.g., '302', '365-A') to restrict results.
        min_similarity: Minimum cosine similarity threshold in [0.0, 1.0].

    Returns:
        List of dictionaries sorted by similarity descending:
        [
            {
                "id": "sc_0042",
                "similarity": 0.8245,
                "case_title": "Muhammad Akram vs. The State",
                "citation_number": "Criminal Appeal No. 10 of 2021",
                "primary_section": "392",
                "sections": ["392", "34"],
                "text": "The prosecution story in brief is that...",
                "full_text": "..."
            },
            ...
        ]
    """
    if not query or not str(query).strip():
        return []

    _load_index_and_model()

    # 1. Encode query vector with unit normalization
    query_str = str(query).strip()
    query_vec = _model.encode([query_str], normalize_embeddings=True, show_progress_bar=False)[0]
    query_vec = np.ascontiguousarray(query_vec, dtype=np.float32)

    total_cases = len(_case_metadata)
    # Fetch wider candidate pool if filtering is enabled
    candidate_k = total_cases if section_filter else min(top_k * 4, total_cases)

    # 2. Retrieve top nearest neighbors
    if _faiss_index is not None:
        scores_arr, indices_arr = _faiss_index.search(query_vec.reshape(1, -1), candidate_k)
        raw_scores = scores_arr[0]
        raw_indices = indices_arr[0]
    elif _case_embeddings is not None:
        raw_scores = np.dot(_case_embeddings, query_vec)
        raw_indices = np.argsort(raw_scores)[::-1][:candidate_k]
        raw_scores = raw_scores[raw_indices]
    else:
        raise RuntimeError("Neither FAISS index nor NumPy vector cache is available.")

    # 3. Apply hybrid relational filters and format results
    filtered_results = []
    clean_sec_filter = str(section_filter).strip().upper() if section_filter else None

    for sim, idx in zip(raw_scores, raw_indices):
        if idx < 0 or idx >= total_cases:
            continue
        sim_val = float(sim)
        if sim_val < min_similarity:
            continue

        case_item = _case_metadata[idx]

        if clean_sec_filter:
            case_sections = [str(s).upper() for s in case_item.get("sections", [])]
            primary_sec = str(case_item.get("primary_section", "")).upper()
            if clean_sec_filter not in case_sections and clean_sec_filter != primary_sec:
                continue

        result_dict = {
            "id": case_item["id"],
            "similarity": round(sim_val, 4),
            "case_title": case_item.get("case_title", "Supreme Court of Pakistan"),
            "citation_number": case_item.get("citation_number", ""),
            "primary_section": case_item.get("primary_section", ""),
            "sections": case_item.get("sections", []),
            "text": case_item.get("text", ""),
            "full_text": case_item.get("full_text", ""),
        }
        filtered_results.append(result_dict)

        if len(filtered_results) >= top_k:
            break

    return filtered_results


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def _cli():
    parser = argparse.ArgumentParser(description="Task B5: Supreme Court Similar Case Finder (FAISS)")
    parser.add_argument("--build-index", action="store_true", help="Build FAISS vector index from sc_clean.csv")
    parser.add_argument("--query", type=str, help="Search query or factual scenario")
    parser.add_argument("--section", type=str, default=None, help="Optional PPC section filter (e.g. 302, 365-A)")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results to return (default: 3)")
    args = parser.parse_args()

    if args.build_index:
        build_case_index(verbose=True)
        return

    if args.query:
        print(f"\n🔍 Query: \"{args.query}\"")
        if args.section:
            print(f"📌 Section Filter: PPC {args.section}")
        results = search_cases(args.query, top_k=args.top_k, section_filter=args.section)
        print(f"\nRetrieved {len(results)} Relevant Precedents:")
        print("=" * 80)
        for i, res in enumerate(results, 1):
            print(f"#{i} [{res['id']}] Similarity: {res['similarity']*100:.1f}%")
            print(f"   Citation: {res['citation_number'] or 'Registry Appeal'}")
            print(f"   Title:    {res['case_title']}")
            print(f"   Sections: {', '.join(res['sections'])}")
            print(f"   Facts:    {res['text'][:140]}...")
            print("-" * 80)
        return

    parser.print_help()


if __name__ == "__main__":
    _cli()
