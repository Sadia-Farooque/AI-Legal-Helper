import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="PPC Section Explorer", page_icon="📖", layout="wide")

st.title("📖 PPC Section Explorer")
st.write("Browse and understand 30 core Pakistan Penal Code (PPC) sections and compare confusable legal categories.")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LABELS_PATH = os.path.join(PROJECT_ROOT, "src", "labels.json")
LOOKUP_PATH = os.path.join(PROJECT_ROOT, "data", "lookup", "ppc_lookup.csv")

labels = {}
if os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)

lookup_df = None
if os.path.exists(LOOKUP_PATH):
    lookup_df = pd.read_csv(LOOKUP_PATH).set_index("section")

search_term = st.text_input("Search by section number or keyword (e.g. 392, robbery, theft, cheque, fraud):")

filtered = []
for sec, data in labels.items():
    query = search_term.lower().strip()
    if not query or query in sec.lower() or query in data.get("title", "").lower() or query in data.get("citizen_term", "").lower():
        filtered.append(data)

st.write(f"Showing **{len(filtered)}** of **{len(labels)}** sections:")

for item in filtered:
    sec = item["section"]
    with st.expander(f"Section {sec}: {item['title']} ({item.get('citizen_term', '')})"):
        st.write(f"**Category:** {item.get('category', 'N/A')}")
        if item.get("confusable_with"):
            st.warning(f"⚠️ **Frequently confusable with:** Sections {', '.join(item['confusable_with'])}")
        
        if lookup_df is not None and sec in lookup_df.index:
            row = lookup_df.loc[sec]
            st.markdown(f"- **Plain Meaning:** {row['meaning']}")
            st.markdown(f"- **Cognizability:** {row['cognizable']}")
            st.markdown(f"- **Bailability:** {row['bailable']}")
            st.markdown(f"- **Punishment:** {row['punishment']}")
        else:
            st.info("Comprehensive statutory breakdown being compiled in Task B1.")

st.caption("Track B Module (Owner: Abdul Qudoos)")
