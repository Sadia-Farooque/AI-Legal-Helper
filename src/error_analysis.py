"""
src/error_analysis.py — Error Analysis & Diagnostic Engine (Task B8)

Computes granular per-class metrics, identifies off-diagonal confusion pairs,
and logs qualitative failure cases for AI Legal Helper classifiers.
"""

import argparse
import csv
import importlib
import json
import os
import sys
from typing import Any, Callable, Dict, List, Set

# Ensure project root is in sys.path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

LABELS_PATH = os.path.join(_PROJECT_ROOT, "src", "labels.json")
CONFUSABLE_PATH = os.path.join(_PROJECT_ROOT, "data", "content", "confusable_groups.json")


def parse_sections(raw_sections: str) -> Set[str]:
    """Parse sections field formatted as semicolon-delimited, comma-delimited, or JSON list."""
    if not raw_sections:
        return set()
    raw = str(raw_sections).strip()
    if raw.startswith("[") and raw.endswith("]"):
        try:
            return set(json.loads(raw))
        except Exception:
            pass
    return {s.strip() for s in raw.replace(",", ";").split(";") if s.strip()}


def load_confusable_map() -> Dict[str, str]:
    """Builds a mapping from (sec_a, sec_b) to the confusable group name if recognized."""
    mapping = {}
    if os.path.exists(CONFUSABLE_PATH):
        try:
            with open(CONFUSABLE_PATH, "r", encoding="utf-8") as f:
                groups = json.load(f)
                for g in groups:
                    g_name = g.get("group_name", "Statutory Boundary")
                    secs = g.get("sections", [])
                    for s1 in secs:
                        for s2 in secs:
                            if s1 != s2:
                                mapping[f"{s1} -> {s2}"] = g_name
        except Exception:
            pass
    return mapping


def run_error_analysis(
    predict_fn: Callable[[str], Dict[str, float]],
    test_csv_path: str,
    top_k: int = 3,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """Executes a diagnostic error analysis on a test dataset using predict_fn.

    Returns:
        dict containing:
            - 'summary': Overall performance counts & rates.
            - 'per_class': Per-section TP, FP, FN, Precision, Recall, F1, Support.
            - 'confusion_pairs': Most frequent (true_section -> predicted_section) misclassifications.
            - 'failures': Detailed records of all misclassified cases.
    """
    if not os.path.exists(test_csv_path):
        raise FileNotFoundError(f"Test CSV not found: {test_csv_path}")

    # Load known section labels
    all_sections = []
    if os.path.exists(LABELS_PATH):
        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            all_sections = sorted(list(json.load(f).keys()))

    confusable_map = load_confusable_map()

    records = []
    with open(test_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            records.append(r)

    if not records:
        raise ValueError(f"No records found in {test_csv_path}")

    total_samples = len(records)
    top1_correct = 0
    topk_correct = 0

    # Per-class counters
    class_stats = {
        sec: {"tp": 0, "fp": 0, "fn": 0, "support": 0} for sec in all_sections
    }

    confusion_counts: Dict[str, Dict[str, int]] = {}
    failures: List[Dict[str, Any]] = []

    for r in records:
        rec_id = r.get("id", "unknown")
        text = r.get("text", "")
        lang = r.get("language", "en")
        true_secs = parse_sections(r.get("sections", ""))
        primary = r.get("primary_section", "").strip()
        if primary:
            true_secs.add(primary)
        elif true_secs:
            primary = sorted(list(true_secs))[0]

        # Update support for true sections
        for s in true_secs:
            if s in class_stats:
                class_stats[s]["support"] += 1

        # Run inference
        scores = predict_fn(text)
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top1_pred = ranked[0][0] if ranked else None
        top1_conf = ranked[0][1] if ranked else 0.0
        topk_preds = [k for k, _ in ranked[:top_k]]

        # Top-1 Hit
        is_top1 = bool(top1_pred and top1_pred in true_secs)
        if is_top1:
            top1_correct += 1

        # Top-k Hit
        is_topk = any(p in true_secs for p in topk_preds)
        if is_topk:
            topk_correct += 1

        # Determine positive predictions for multi-label stats
        pred_positives = {sec for sec, sc in scores.items() if sc >= threshold}
        if not pred_positives:
            pred_positives = set(topk_preds)

        # Update per-class TP, FP, FN
        for s in all_sections:
            is_ground_truth = (s in true_secs)
            is_predicted = (s in pred_positives)

            if is_ground_truth and is_predicted:
                class_stats[s]["tp"] += 1
            elif not is_ground_truth and is_predicted:
                class_stats[s]["fp"] += 1
            elif is_ground_truth and not is_predicted:
                class_stats[s]["fn"] += 1

        # Record confusion pair and failure diagnostics
        if not is_top1 and primary and top1_pred:
            pair_key = f"{primary} -> {top1_pred}"
            if pair_key not in confusion_counts:
                confusion_counts[pair_key] = {
                    "true_section": primary,
                    "predicted_section": top1_pred,
                    "count": 0,
                    "confusable_group": confusable_map.get(pair_key, "Other Boundary")
                }
            confusion_counts[pair_key]["count"] += 1

            failures.append({
                "id": rec_id,
                "text": text,
                "language": lang,
                "primary_section": primary,
                "true_sections": sorted(list(true_secs)),
                "predicted_top1": top1_pred,
                "predicted_top1_conf": round(float(top1_conf), 4),
                "topk_predictions": [(k, round(float(v), 4)) for k, v in ranked[:top_k]],
                "in_topk": is_topk,
                "is_confusable_group": bool(pair_key in confusable_map)
            })

    # Compute per-class Precision, Recall, F1
    per_class_results = {}
    f1_list = []
    for sec, stats in class_stats.items():
        tp = stats["tp"]
        fp = stats["fp"]
        fn = stats["fn"]
        supp = stats["support"]

        prec = tp / (tp + fp + 1e-9) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn + 1e-9) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec + 1e-9) if (prec + rec) > 0 else 0.0

        if supp > 0:
            f1_list.append(f1)

        per_class_results[sec] = {
            "support": supp,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4)
        }

    macro_f1 = round(sum(f1_list) / len(f1_list), 4) if f1_list else 0.0

    # Sort confusion pairs descending by frequency
    sorted_confusions = sorted(
        confusion_counts.values(),
        key=lambda x: x["count"],
        reverse=True
    )

    summary = {
        "total_samples": total_samples,
        "top1_accuracy": round(top1_correct / total_samples, 4),
        f"top{top_k}_recall": round(topk_correct / total_samples, 4),
        "macro_f1": macro_f1,
        "total_failures": len(failures),
        "unique_confusion_pairs": len(sorted_confusions)
    }

    return {
        "summary": summary,
        "per_class": per_class_results,
        "confusion_pairs": sorted_confusions,
        "failures": failures
    }


def save_error_analysis(analysis_data: Dict[str, Any], model_name: str, output_dir: str = "results") -> str:
    """Serializes error analysis to JSON."""
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"error_analysis_{model_name}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, indent=2)
    return out_file


def main():
    parser = argparse.ArgumentParser(description="AI Legal Helper Error Analysis Engine")
    parser.add_argument("--model", type=str, default="retrieval", help="Model name inside src.models or src (e.g. retrieval, stub_model)")
    parser.add_argument("--test-data", type=str, default="data/test/stub_test.csv", help="Test dataset CSV path")
    parser.add_argument("--top-k", type=int, default=3, help="Top-K recall threshold")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory to save JSON error report")
    args = parser.parse_args()

    # Dynamic import
    predict_fn = None
    try:
        mod = importlib.import_module(f"src.models.{args.model}")
        if hasattr(mod, "predict_scores"):
            predict_fn = mod.predict_scores
    except ImportError:
        pass

    if predict_fn is None:
        try:
            mod = importlib.import_module(f"src.{args.model}")
            if hasattr(mod, "predict_scores"):
                predict_fn = mod.predict_scores
        except ImportError:
            pass

    if predict_fn is None:
        raise AttributeError(f"Could not load predict_scores for model '{args.model}' from src.models or src")

    print(f"Running Diagnostic Error Analysis for '{args.model}' on '{args.test_data}'...")
    analysis = run_error_analysis(predict_fn, args.test_data, top_k=args.top_k)

    print("\n--- Error Analysis Summary ---")
    for k, v in analysis["summary"].items():
        print(f"  {k:25}: {v}")

    print("\n--- Top Confused Section Pairs ---")
    if analysis["confusion_pairs"]:
        for cp in analysis["confusion_pairs"][:5]:
            print(f"  PPC {cp['true_section']} misclassified as PPC {cp['predicted_section']} ({cp['count']}x) [{cp['confusable_group']}]")
    else:
        print("  Zero misclassifications!")

    saved_path = save_error_analysis(analysis, args.model, args.output_dir)
    print(f"\nDiagnostic error report written to: {saved_path}")


if __name__ == "__main__":
    main()
