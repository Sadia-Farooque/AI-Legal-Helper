import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="Model Evaluation & Benchmarks", page_icon="📊", layout="wide")

st.title("📊 Model Benchmark & Evaluation Dashboard")
st.write("Verifiable performance metrics across baseline and deep learning models adhering to the K6 results contract.")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

result_files = glob.glob(os.path.join(RESULTS_DIR, "*.csv"))

if not result_files:
    st.info("No benchmark results found in `results/`. Run `python src/evaluate.py` to generate evaluation tables.")
else:
    all_data = []
    for f in result_files:
        model_name = os.path.splitext(os.path.basename(f))[0]
        try:
            df = pd.read_csv(f)
            df["model"] = model_name
            all_data.append(df)
        except Exception as e:
            st.error(f"Error reading {f}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        st.subheader("Results Table")
        st.dataframe(combined_df, use_container_width=True)

        st.subheader("Model Comparison Summary")
        pivot_df = combined_df.pivot_table(index=["model", "language"], columns="metric", values="value").reset_index()
        st.dataframe(pivot_df, use_container_width=True)

st.caption("Track B Module (Owner: Abdul Qudoos) — Final evaluation on frozen test set scheduled in Week 11.")
