import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="PPC Section Explorer", page_icon="📖", layout="wide")

st.title("📖 PPC Section Explorer & Confusable Groups")
st.write("Browse and understand 30 core Pakistan Penal Code (PPC) sections, examine statutory prosecution elements, and master subtle confusable distinctions.")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LABELS_PATH = os.path.join(PROJECT_ROOT, "src", "labels.json")
LOOKUP_PATH = os.path.join(PROJECT_ROOT, "data", "lookup", "ppc_lookup.csv")
SECTIONS_CONTENT_PATH = os.path.join(PROJECT_ROOT, "data", "content", "sections.json")
CONFUSABLE_PATH = os.path.join(PROJECT_ROOT, "data", "content", "confusable_groups.json")

# Load datasets
labels = {}
if os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)

lookup_df = None
if os.path.exists(LOOKUP_PATH):
    lookup_df = pd.read_csv(LOOKUP_PATH).set_index("section")

sections_content = {}
if os.path.exists(SECTIONS_CONTENT_PATH):
    with open(SECTIONS_CONTENT_PATH, "r", encoding="utf-8") as f:
        sections_content = json.load(f)

confusable_groups = []
if os.path.exists(CONFUSABLE_PATH):
    with open(CONFUSABLE_PATH, "r", encoding="utf-8") as f:
        confusable_groups = json.load(f)

tab1, tab2 = st.tabs(["📚 Section Directory & Elements", "⚖️ Confusable Groups Comparison"])

with tab1:
    search_term = st.text_input("Search sections by number, name, or keyword (e.g. 392, robbery, cheque, murder, fraud):")

    filtered = []
    for sec, data in labels.items():
        query = search_term.lower().strip()
        if not query or query in sec.lower() or query in data.get("title", "").lower() or query in data.get("citizen_term", "").lower():
            filtered.append(data)

    st.write(f"Showing **{len(filtered)}** of **{len(labels)}** sections:")

    for item in filtered:
        sec = item["section"]
        title = item["title"]
        citizen_term = item.get("citizen_term", "")
        content = sections_content.get(sec, {})

        with st.expander(f"Section {sec}: {title} — [{citizen_term}]"):
            col_left, col_right = st.columns([3, 2])

            with col_left:
                st.markdown("#### 📝 Conceptual Summary")
                st.write(content.get("summary", "Summary pending."))

                st.markdown("#### ⚖️ Statutory Elements of the Offence (What Prosecution Must Prove)")
                elements = content.get("elements", [])
                if elements:
                    for elem in elements:
                        st.markdown(f"- {elem}")
                else:
                    st.info("Statutory elements being compiled.")

                st.markdown("#### 🏙️ Realistic Pakistani Scenarios")
                scenarios = content.get("example_scenarios", [])
                for idx, sc in enumerate(scenarios, 1):
                    st.markdown(f"**Scenario {idx}:** _{sc}_")

            with col_right:
                st.markdown("#### 🏛️ Statutory Facts (CrPC Sched II)")
                if lookup_df is not None and sec in lookup_df.index:
                    row = lookup_df.loc[sec]
                    st.markdown(f"- **FIR / Cognizability:** `{row['cognizable']}`")
                    st.markdown(f"- **Bail Status:** `{row['bailable']}`")
                    st.markdown(f"- **Compounding:** `{row['compoundable']}`")
                    st.markdown(f"- **Statutory Penalty:** {row['punishment']}")
                    st.markdown(f"- **Trial Court:** {row['court']}")
                    st.caption(f"Source: {row['source']} (Checked: {row['date_checked']})")

                if item.get("confusable_with"):
                    st.warning(f"⚠️ **Confusable With:** Sections {', '.join(item['confusable_with'])}")

                if "statutory_reference" in content:
                    st.caption(f"Reference: `{content['statutory_reference']}`")

with tab2:
    st.subheader("⚖️ Key Statutory Distinctions (Confusable Groups)")
    st.write("Master the subtle dividing lines between commonly confused Pakistan Penal Code sections.")

    for grp in confusable_groups:
        with st.expander(f"📌 {grp['group_name']} (Sections {', '.join(grp['sections'])})"):
            st.info(f"**Distinction Summary:** {grp['distinction_summary']}")

            st.markdown("#### Key Differentiators:")
            for sec_num, diff_text in grp["key_differentiators"].items():
                sec_title = labels.get(sec_num, {}).get("title", "")
                st.markdown(f"- **Section {sec_num} ({sec_title}):** {diff_text}")

            st.error(f"💡 **Critical Student Pitfall:** {grp['critical_student_pitfall']}")

st.caption("Track B Module (Owner: Abdul Qudoos)")
