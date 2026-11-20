import streamlit as st
import json
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.case_finder import search_cases

st.set_page_config(page_title="Similar Case Finder", page_icon="🔍", layout="wide")

st.title("🔍 Supreme Court Similar Case Finder")
st.write("Retrieve Supreme Court of Pakistan criminal precedents matching your factual scenario using high-dimensional dense vector search (FAISS IndexFlatIP).")

# Load section labels for filtering
LABELS_PATH = os.path.join(PROJECT_ROOT, "src", "labels.json")
section_options = ["All Sections"]
if os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels_dict = json.load(f)
        for s, meta in labels_dict.items():
            section_options.append(f"{s} — {meta.get('title', '')[:35]}")

# Quick example scenario buttons
st.markdown("**Quick Example Scenarios:**")
col_e1, col_e2, col_e3, col_e4 = st.columns(4)

default_query = ""
if col_e1.button("🔫 Firearm Murder Ambush"):
    st.session_state["case_query"] = "Accused armed with automatic rifle lay in ambush and opened fatal fire upon the deceased over a land dispute."
if col_e2.button("💰 Bank Cheque Dishonoured"):
    st.session_state["case_query"] = "Accused issued a commercial bank cheque of 10 lac rupees that was dishonoured upon presentation due to insufficient balance."
if col_e3.button("🚗 Highway Armed Robbery"):
    st.session_state["case_query"] = "Three masked men armed with pistols intercepted a vehicle on the highway at night and snatched cash and mobile phones."
if col_e4.button("📞 Kidnapping for Ransom"):
    st.session_state["case_query"] = "Child was abducted while returning from school and callers demanded ten million rupees ransom for safe release."

current_query = st.session_state.get("case_query", "")

query = st.text_area(
    "Enter factual scenario or legal proposition to search precedents:",
    value=current_query,
    placeholder="e.g. Accused while armed with a firearm fired upon the complainant party during a sudden fight...",
    height=110
)

# Check for incoming filter from Section Explorer
preset_sec = st.session_state.get("case_section_filter")
default_filter_idx = 0
if preset_sec:
    for idx_opt, opt in enumerate(section_options):
        if opt.startswith(f"{preset_sec} — "):
            default_filter_idx = idx_opt
            break

col_ctrl1, col_ctrl2 = st.columns([2, 1])
with col_ctrl1:
    selected_filter_str = st.selectbox(
        "Filter by Cited PPC Section (Optional):",
        section_options,
        index=default_filter_idx
    )
    selected_sec = None if selected_filter_str == "All Sections" else selected_filter_str.split(" — ")[0].strip()
    if preset_sec and selected_sec != preset_sec:
        st.session_state["case_section_filter"] = None

with col_ctrl2:
    top_k = st.slider("Number of judgments to retrieve:", min_value=1, max_value=10, value=3)

if preset_sec and selected_sec == preset_sec:
    c_info1, c_info2 = st.columns([4, 1])
    c_info1.info(f"🎯 Filter synchronized to **PPC Section {preset_sec}** from Section Explorer.")
    if c_info2.button("✖️ Clear Section Filter"):
        st.session_state["case_section_filter"] = None
        st.rerun()

find_btn = st.button("🔍 Find Precedents", type="primary", use_container_width=True)

if (find_btn or st.session_state.get("trigger_search", False)) and query.strip():
    st.session_state["trigger_search"] = False
    with st.spinner("Searching 301 Supreme Court of Pakistan criminal judgments..."):
        results = search_cases(query, top_k=top_k, section_filter=selected_sec)

    if not results:
        st.warning(f"No matching Supreme Court judgments found{f' under Section {selected_sec}' if selected_sec else ''}. Try broadening your search query or removing the section filter.")
    else:
        st.subheader(f"🏛️ Top {len(results)} Supreme Court Precedents")
        if selected_sec:
            st.caption(f"Filtered strictly to judgments citing **PPC Section {selected_sec}**")

        for idx, item in enumerate(results, 1):
            sim_pct = item["similarity"] * 100
            citation = item["citation_number"] or "Supreme Court of Pakistan"
            title = item["case_title"] or "Criminal Appeal"
            sections_str = ", ".join(f"PPC {s}" for s in item.get("sections", []))

            with st.container():
                st.markdown(f"### #{idx} · {title}")
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.markdown(f"**Registry Citation:** `{citation}`")
                c2.markdown(f"**Cited Sections:** `{sections_str}`")
                c3.metric("Semantic Match", f"{sim_pct:.1f}%")

                st.markdown("**Prosecution Occurrence Facts:**")
                st.info(f"_{item['text']}_")

                if item.get("full_text"):
                    with st.expander(f"📜 Inspect Judgment Record Excerpt ({item['id']})"):
                        st.text_area(
                            "Full Judgment Excerpt:",
                            value=item["full_text"],
                            height=250,
                            key=f"ft_{item['id']}_{idx}"
                        )
                st.divider()

st.caption("Track B Module (Owner: Abdul Qudoos) — Dense Vector Indexing via FAISS IndexFlatIP over 301 Supreme Court Judgments.")
