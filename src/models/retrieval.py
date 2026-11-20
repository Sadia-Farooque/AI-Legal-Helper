"""
src/models/retrieval.py
Thin adapter exposing the B4 retrieval classifier under the K4 model contract
path expected by src/evaluate.py:
  --model retrieval  →  importlib.import_module("src.models.retrieval")

All logic lives in src/retrieval.py.  This file is intentionally a one-liner
proxy so evaluate.py can discover it via its standard src.models.* import path.
"""

from src.retrieval import predict_scores  # re-export — satisfies K4 contract

__all__ = ["predict_scores"]
