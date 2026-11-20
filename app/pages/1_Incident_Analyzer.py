import streamlit as st
import pandas as pd
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

st.set_page_config(page_title="Incident Analyzer", page_icon="🚨", layout="wide")

st.title("🚨 Incident Analyzer")
st.write("Describe an incident in plain English or Roman Urdu to identify applicable Pakistan Penal Code (PPC) sections.")

# Load lookup table
LOOKUP_PATH = os.path.join(PROJECT_ROOT, "data", "lookup", "ppc_lookup.csv")
lookup_df = None
if os.path.exists(LOOKUP_PATH):
    lookup_df = pd.read_csv(LOOKUP_PATH).set_index("section")

# Model selection in sidebar or header
model_choice = st.sidebar.selectbox(
    "Select Classification Model:",
    ["Zero-Shot Retrieval (B4 - all-MiniLM-L6-v2)", "Stub Baseline (K4 Pseudo-Random)"],
    index=0
)

if "Retrieval" in model_choice:
    from src.retrieval import predict_scores
else:
    from src.models.stub_model import predict_scores

user_input = st.text_area(
    "What happened?",
    placeholder="e.g., Two armed men on a motorcycle snatched my mobile phone and wallet near Saddar...",
    height=120
)

col1, col2 = st.columns([1, 4])
with col1:
    analyze_btn = st.button("Analyze Incident", type="primary", use_container_width=True)

if analyze_btn and user_input.strip():
    with st.spinner("Analyzing legal elements..."):
        scores = predict_scores(user_input)
        top_sections = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

    st.subheader("Top Recommended PPC Sections")
    cols = st.columns(3)

    for i, (sec, score) in enumerate(top_sections):
        with cols[i]:
            st.metric(label=f"Rank #{i+1}: Section {sec}", value=f"{score*100:.1f}% Confidence")
            if lookup_df is not None and sec in lookup_df.index:
                row = lookup_df.loc[sec]
                st.write(f"**Offence:** {row['short_name']}")
                st.caption(f"_{row['meaning']}_")
                st.markdown(f"- **FIR / Cognizable:** `{row['cognizable']}`")
                st.markdown(f"- **Bail Status:** `{row['bailable']}`")
                st.markdown(f"- **Punishment:** {row['punishment']}")
            else:
                st.info(f"Section {sec} detailed legal facts pending lookup table sync.")

    st.divider()
    st.subheader("📋 Recommended Next Steps")
    st.markdown("""
    1. **Preserve Evidence:** Retain witness contact details, CCTV recordings, or digital screenshots.
    2. **Filing an FIR:** Visit the nearest police station having territorial jurisdiction where the incident occurred.
    3. **Legal Aid Contact:** In case of emergency or police refusal, contact the legal aid cell or dial **15**.
    """)

st.caption(f"Running on model: **{model_choice}**")
