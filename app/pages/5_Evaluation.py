import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="Model Evaluation & Benchmarks", page_icon="📊", layout="wide")

st.title("📊 Model Benchmark & Evaluation Dashboard")
st.write("Verifiable performance metrics across baseline, retrieval, and deep learning models adhering to the K6 results contract.")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

result_files = glob.glob(os.path.join(RESULTS_DIR, "*.csv"))

if not result_files:
    st.info("No benchmark results found in `results/`. Run `python src/evaluate.py` to generate evaluation tables.")
else:
    k6_data = []
    other_files = {}

    for f in result_files:
        model_name = os.path.splitext(os.path.basename(f))[0]
        try:
            df = pd.read_csv(f)
            # Check if this file conforms to K6 results schema
            if {"metric", "language", "value"}.issubset(set(df.columns)):
                df["model"] = model_name
                k6_data.append(df)
            else:
                other_files[model_name] = df
        except Exception as e:
            st.error(f"Error reading {f}: {e}")

    if k6_data:
        combined_df = pd.concat(k6_data, ignore_index=True)

        st.subheader("🏆 Model Comparison Summary (K6 Benchmark Contract)")
        pivot_df = combined_df.pivot_table(
            index=["model", "language"],
            columns="metric",
            values="value"
        ).reset_index()
        st.dataframe(pivot_df, use_container_width=True)

        st.subheader("📋 Raw K6 Metrics Table")
        st.dataframe(combined_df[["model", "language", "metric", "value"]], use_container_width=True)

    if other_files:
        st.divider()
        st.subheader("🔬 Additional Experiment Data (Grids & Ablations)")
        tabs = st.tabs(list(other_files.keys()))
        for tab, (name, df) in zip(tabs, other_files.items()):
            with tab:
                st.write(f"**File:** `results/{name}.csv` ({len(df)} rows, {len(df.columns)} columns)")
                st.dataframe(df, use_container_width=True)

st.caption("Track B Module (Owner: Abdul Qudoos) — Final evaluation on frozen test set scheduled in Week 11.")
