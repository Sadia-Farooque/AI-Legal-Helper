"""Shared Evaluation Framework adhering to K6 and K7 contracts.
Usage:
    python src/evaluate.py --model stub_model --test-data data/test/stub_test.csv
"""

import argparse
import csv
import importlib
import json
import os
import sys
from typing import Callable, Dict, List, Set

# Ensure project root is in sys.path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

def parse_sections(raw_sections: str) -> Set[str]:
    """Parse sections field formatted as semicolon-delimited or JSON string."""
    if not raw_sections:
        return set()
    raw = str(raw_sections).strip()
    if raw.startswith("[") and raw.endswith("]"):
        try:
            return set(json.loads(raw))
        except Exception:
            pass
    return {s.strip() for s in raw.replace(",", ";").split(";") if s.strip()}

def evaluate_predictions(
    predict_fn: Callable[[str], Dict[str, float]],
    test_csv_path: str,
    top_k: int = 3,
    threshold: float = 0.5
) -> Dict[str, Dict[str, float]]:
    """Evaluates a predict_scores model against a test dataset CSV.
    Computes top-1 accuracy, top-3 recall, micro-F1, macro-F1 across languages.
    """
    if not os.path.exists(test_csv_path):
        raise FileNotFoundError(f"Test CSV not found: {test_csv_path}")

    records = []
    with open(test_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    if not records:
        raise ValueError(f"No records found in {test_csv_path}")

    # Metrics storage per language category ('all', 'en', 'roman_ur')
    subsets = {
        "all": records,
        "en": [r for r in records if r.get("language") == "en"],
        "roman_ur": [r for r in records if r.get("language") == "roman_ur"]
    }

    results = {}

    for lang, rows in subsets.items():
        if not rows:
            continue

        n_samples = len(rows)
        top1_hits = 0
        topk_hits = 0

        # Multi-label F1 trackers
        true_positives = 0
        false_positives = 0
        false_negatives = 0

        # Per-section counts for macro-F1
        section_stats: Dict[str, Dict[str, int]] = {}

        for row in rows:
            text = row.get("text", "")
            true_sections = parse_sections(row.get("sections", ""))
            primary = row.get("primary_section", "").strip()
            if primary:
                true_sections.add(primary)

            scores = predict_fn(text)
            # Sort sections descending by score
            ranked_sections = [k for k, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)]

            top1_pred = ranked_sections[0] if ranked_sections else None
            topk_preds = set(ranked_sections[:top_k])

            # Top-1 accuracy (hit if top prediction is among true sections)
            if top1_pred and top1_pred in true_sections:
                top1_hits += 1

            # Top-k recall (hit if any of top-k predictions is in true sections)
            if any(pred in true_sections for pred in topk_preds):
                topk_hits += 1

            # Threshold-based or top-k positive predictions for multi-label F1
            pred_positives = {sec for sec, score in scores.items() if score >= threshold}
            if not pred_positives:
                pred_positives = set(ranked_sections[:top_k])

            for sec in pred_positives:
                if sec in true_sections:
                    true_positives += 1
                else:
                    false_positives += 1

            for sec in true_sections:
                if sec not in pred_positives:
                    false_negatives += 1

                # Track per-section
                if sec not in section_stats:
                    section_stats[sec] = {"tp": 0, "fp": 0, "fn": 0}
                if sec in pred_positives:
                    section_stats[sec]["tp"] += 1
                else:
                    section_stats[sec]["fn"] += 1

        # Calculate metrics
        top1_acc = round(top1_hits / n_samples, 4)
        topk_rec = round(topk_hits / n_samples, 4)

        # Micro F1
        micro_precision = true_positives / (true_positives + false_positives + 1e-9)
        micro_recall = true_positives / (true_positives + false_negatives + 1e-9)
        micro_f1 = round(2 * micro_precision * micro_recall / (micro_precision + micro_recall + 1e-9), 4)

        # Macro F1
        section_f1s = []
        for sec, stat in section_stats.items():
            tp, fp, fn = stat["tp"], stat["fp"], stat["fn"]
            prec = tp / (tp + fp + 1e-9)
            rec = tp / (tp + fn + 1e-9)
            f1 = 2 * prec * rec / (prec + rec + 1e-9)
            section_f1s.append(f1)
        macro_f1 = round(sum(section_f1s) / (len(section_f1s) + 1e-9), 4) if section_f1s else 0.0

        results[lang] = {
            "samples": float(n_samples),
            "top1_accuracy": top1_acc,
            f"top{top_k}_recall": topk_rec,
            "micro_f1": micro_f1,
            "macro_f1": macro_f1
        }

    return results

def save_results(results: Dict[str, Dict[str, float]], model_name: str, output_dir: str = "results") -> str:
    """Saves evaluation metrics following the K6 results contract:
    columns: metric, language, value.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"{model_name}.csv")

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "language", "value"])
        for lang, metrics in results.items():
            for metric, val in metrics.items():
                writer.writerow([metric, lang, val])

    return out_file

def main():
    parser = argparse.ArgumentParser(description="AI Legal Helper Evaluation Engine")
    parser.add_argument("--model", type=str, default="stub_model", help="Model name inside src.models")
    parser.add_argument("--test-data", type=str, default="data/test/stub_test.csv", help="Test CSV path")
    parser.add_argument("--top-k", type=int, default=3, help="Top-K recall threshold")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory to save CSV results")
    args = parser.parse_args()

    # Import predictor dynamically
    mod = importlib.import_module(f"src.models.{args.model}")
    if not hasattr(mod, "predict_scores"):
        raise AttributeError(f"Model module {args.model} does not expose predict_scores(text)")

    print(f"Evaluating model '{args.model}' on '{args.test_data}'...")
    results = evaluate_predictions(mod.predict_scores, args.test_data, top_k=args.top_k)

    print("\n--- Evaluation Summary ---")
    for lang, metrics in results.items():
        print(f"\nLanguage: [{lang.upper()}] (Samples: {int(metrics['samples'])})")
        for k, v in metrics.items():
            if k != "samples":
                print(f"  {k:15}: {v:.4f}")

    saved_path = save_results(results, args.model, args.output_dir)
    print(f"\nResults successfully written to: {saved_path}")

if __name__ == "__main__":
    main()
