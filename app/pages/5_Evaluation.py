import streamlit as st
import pandas as pd
import glob
import json
import os

st.set_page_config(page_title="Model Evaluation & Benchmarks", page_icon="📊", layout="wide")

st.title("📊 Model Benchmark & Error Analysis Dashboard")
st.write(
    "Rigorous evaluation metrics and fine-grained error diagnosis across baseline, retrieval, "
    "and deep learning models adhering to the K6 results contract."
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
LABELS_PATH = os.path.join(PROJECT_ROOT, "src", "labels.json")

# Load section labels for title lookups
section_titles = {}
if os.path.exists(LABELS_PATH):
    try:
        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            lbl_data = json.load(f)
            section_titles = {k: v.get("title", "") for k, v in lbl_data.items()}
    except Exception:
        pass

tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Model Benchmark Leaderboard",
    "🔍 Error Analysis & Confusions",
    "🕵️ Misclassification Inspector",
    "🔬 Raw Grids & Ablations"
])

# -------------------------------------------------------------
# TAB 1: MODEL BENCHMARK LEADERBOARD (K6 Contract)
# -------------------------------------------------------------
with tab1:
    result_files = glob.glob(os.path.join(RESULTS_DIR, "*.csv"))
    k6_data = []
    other_files = {}

    for f in result_files:
        model_name = os.path.splitext(os.path.basename(f))[0]
        try:
            df = pd.read_csv(f)
            if {"metric", "language", "value"}.issubset(set(df.columns)):
                df["model"] = model_name
                k6_data.append(df)
            else:
                other_files[model_name] = df
        except Exception:
            pass

    if k6_data:
        combined_df = pd.concat(k6_data, ignore_index=True)

        # Pivot to tabular structure
        pivot_df = combined_df.pivot_table(
            index=["model", "language"],
            columns="metric",
            values="value"
        ).reset_index()

        col_filter1, col_filter2 = st.columns([2, 1])
        all_langs = sorted(list(pivot_df["language"].unique()))
        with col_filter1:
            sel_lang = st.selectbox("Filter Benchmark by Language / Split:", ["All Languages"] + all_langs)

        filtered_pivot = pivot_df if sel_lang == "All Languages" else pivot_df[pivot_df["language"] == sel_lang]

        st.subheader("🏆 Model Comparison Summary (K6 Schema)")
        st.dataframe(filtered_pivot, use_container_width=True)

        # Interactive Comparative Bar Chart
        if not filtered_pivot.empty:
            st.subheader("📈 Performance Comparison")
            chart_metrics = [m for m in ["top1_accuracy", "top3_recall", "macro_f1"] if m in filtered_pivot.columns]
            if chart_metrics:
                chart_df = filtered_pivot.copy()
                chart_df["Model_Split"] = chart_df["model"].astype(str) + " [" + chart_df["language"].astype(str) + "]"
                chart_df = chart_df.set_index("Model_Split")[chart_metrics]
                st.bar_chart(chart_df)

        st.subheader("📋 Raw K6 Metrics Records")
        with st.expander("Inspect Unpivoted K6 Records"):
            st.dataframe(combined_df[["model", "language", "metric", "value"]], use_container_width=True)
    else:
        st.info("No K6 benchmark results found in `results/`. Run `python src/evaluate.py` to generate evaluation tables.")

# -------------------------------------------------------------
# TAB 2: ERROR ANALYSIS & CONFUSION PAIRS
# -------------------------------------------------------------
with tab2:
    st.subheader("🔍 Fine-Grained Error Diagnosis & Confusion Discovery")
    error_files = glob.glob(os.path.join(RESULTS_DIR, "error_analysis_*.json"))

    if not error_files:
        st.info("No error analysis reports found. Run `python src/error_analysis.py --model retrieval` to generate diagnostic reports.")
    else:
        model_options = [os.path.basename(f).replace("error_analysis_", "").replace(".json", "") for f in error_files]
        sel_err_model = st.selectbox("Select Model for Diagnostic Breakdown:", model_options)

        target_json = os.path.join(RESULTS_DIR, f"error_analysis_{sel_err_model}.json")
        with open(target_json, "r", encoding="utf-8") as f:
            err_data = json.load(f)

        summary = err_data.get("summary", {})
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Evaluated Test Samples", summary.get("total_samples", 0))
        m1_top1 = summary.get("top1_accuracy", 0.0)
        m2.metric("Top-1 Accuracy", f"{m1_top1 * 100:.1f}%")
        m1_topk = summary.get("top3_recall", 0.0)
        m3.metric("Top-3 Recall", f"{m1_topk * 100:.1f}%")
        m4.metric("Macro F1", f"{summary.get('macro_f1', 0.0):.4f}")

        st.divider()

        # Top Confused Pairs Table
        st.markdown("### ⚖️ Top Off-Diagonal Confusion Pairs")
        st.write("Identifies the most frequent statutory boundaries where the model selected an incorrect primary section:")
        conf_pairs = err_data.get("confusion_pairs", [])
        if conf_pairs:
            conf_rows = []
            for cp in conf_pairs:
                true_s = cp["true_section"]
                pred_s = cp["predicted_section"]
                true_title = section_titles.get(true_s, "")
                pred_title = section_titles.get(pred_s, "")
                conf_rows.append({
                    "True Section": f"PPC {true_s} ({true_title[:30]})",
                    "Predicted Section": f"PPC {pred_s} ({pred_title[:30]})",
                    "Misclassification Count": cp["count"],
                    "Confusable Boundary Category": cp.get("confusable_group", "Other")
                })
            st.dataframe(pd.DataFrame(conf_rows), use_container_width=True)
        else:
            st.success("🎉 Zero off-diagonal misclassifications! Model achieved 100% Top-1 accuracy.")

        st.divider()

        # Per-Section Breakdown Table
        st.markdown("### 📊 Per-Class Precision, Recall & F1 Breakdown")
        per_class = err_data.get("per_class", {})
        if per_class:
            class_rows = []
            for s_num, stats in per_class.items():
                if stats.get("support", 0) > 0:
                    class_rows.append({
                        "Section": f"PPC {s_num}",
                        "Title": section_titles.get(s_num, "N/A"),
                        "Support": stats["support"],
                        "True Positives": stats["tp"],
                        "False Positives": stats["fp"],
                        "False Negatives": stats["fn"],
                        "Precision": stats["precision"],
                        "Recall": stats["recall"],
                        "F1-Score": stats["f1"]
                    })
            if class_rows:
                df_pc = pd.DataFrame(class_rows).sort_values("F1-Score", ascending=True)
                st.dataframe(df_pc, use_container_width=True)

# -------------------------------------------------------------
# TAB 3: MISCLASSIFICATION INSPECTOR
# -------------------------------------------------------------
with tab3:
    st.subheader("🕵️ Qualitative Failure Mode Inspector")
    st.write("Drill down into individual misclassified test samples to understand failure patterns.")

    if not error_files:
        st.info("No error analysis files available.")
    else:
        target_json = os.path.join(RESULTS_DIR, f"error_analysis_{sel_err_model}.json")
        with open(target_json, "r", encoding="utf-8") as f:
            err_data = json.load(f)

        failures = err_data.get("failures", [])
        if not failures:
            st.success(f"No misclassifications recorded for {sel_err_model}!")
        else:
            st.caption(f"Showing **{len(failures)}** misclassified cases for `{sel_err_model}`:")

            for idx, fail in enumerate(failures, 1):
                in_top3_badge = "🟢 In Top-3" if fail.get("in_topk") else "🔴 Missed Top-3"
                is_conf_badge = "⚠️ Recognized Confusable Pair" if fail.get("is_confusable_group") else "⚪ Boundary Error"

                with st.expander(f"Case #{idx} [{fail.get('id', 'N/A')}] — True: PPC {fail.get('primary_section')} vs Pred: PPC {fail.get('predicted_top1')} ({in_top3_badge})"):
                    st.markdown(f"**Citizen Incident Narrative ({fail.get('language', 'en').upper()}):**")
                    st.info(f"_{fail.get('text')}_")

                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Ground Truth Target:** `PPC {fail.get('primary_section')}`")
                    c2.markdown(f"**Model Top-1 Predicted:** `PPC {fail.get('predicted_top1')}`")
                    c3.markdown(f"**Model Top-1 Confidence:** `{fail.get('predicted_top1_conf', 0.0):.4f}`")

                    st.markdown("**Top-3 Model Ranking:**")
                    topk_display = [f"**#{rank}** PPC {s} (Score: `{score:.4f}`)" for rank, (s, score) in enumerate(fail.get("topk_predictions", []), 1)]
                    st.markdown(" · ".join(topk_display))

                    if fail.get("is_confusable_group"):
                        st.warning("⚠️ This error aligns with a recognized statutory boundary from `data/content/confusable_groups.json`.")

# -------------------------------------------------------------
# TAB 4: RAW GRIDS & ABLATIONS
# -------------------------------------------------------------
with tab4:
    st.subheader("🔬 Experiment Grids, Ablations & Calibration Files")
    if other_files:
        exp_tabs = st.tabs(list(other_files.keys()))
        for t, (name, df) in zip(exp_tabs, other_files.items()):
            with t:
                st.write(f"**File:** `results/{name}.csv` ({len(df)} rows, {len(df.columns)} columns)")
                st.dataframe(df, use_container_width=True)
    else:
        st.info("No additional experiment files found.")

st.caption("Track B Module (Owner: Abdul Qudoos) — Comprehensive Evaluation Suite adhering to K6/K7 Contracts.")
