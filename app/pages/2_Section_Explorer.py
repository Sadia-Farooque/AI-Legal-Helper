import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="PPC Section Explorer", page_icon="📖", layout="wide")

st.title("📖 PPC Section Explorer & Confusable Groups")
st.write(
    "Explore 30 core Pakistan Penal Code (PPC) sections, examine prosecution legal elements, "
    "review procedural rules under CrPC Schedule II, and study relevant Supreme Court precedents."
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LABELS_PATH = os.path.join(PROJECT_ROOT, "src", "labels.json")
LOOKUP_PATH = os.path.join(PROJECT_ROOT, "data", "lookup", "ppc_lookup.csv")
SECTIONS_CONTENT_PATH = os.path.join(PROJECT_ROOT, "data", "content", "sections.json")
CONFUSABLE_PATH = os.path.join(PROJECT_ROOT, "data", "content", "confusable_groups.json")
CASES_META_PATH = os.path.join(PROJECT_ROOT, "models", "case_metadata.json")

# Load datasets safely
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

cases_metadata = []
if os.path.exists(CASES_META_PATH):
    with open(CASES_META_PATH, "r", encoding="utf-8") as f:
        cases_metadata = json.load(f)

# Helper function to switch pages safely
def safe_switch_page(page_name: str):
    try:
        st.switch_page(page_name)
    except Exception:
        st.info(f"Please navigate to `{page_name}` using the sidebar.")

# Index cases by section for instant cross-referencing
cases_by_section = {}
for c in cases_metadata:
    for sec_ref in c.get("sections", []):
        sec_clean = str(sec_ref).strip()
        if sec_clean not in cases_by_section:
            cases_by_section[sec_clean] = []
        cases_by_section[sec_clean].append(c)

tab1, tab2 = st.tabs(["📚 Section Directory & Legal Analysis", "⚖️ Confusable Groups Comparison"])

with tab1:
    # Top search & multi-filter controls
    col_search, col_cat = st.columns([2, 1])

    default_search = st.session_state.get("explorer_search", "")
    with col_search:
        search_term = st.text_input(
            "Search sections by number, name, or citizen term (e.g. 302, cheque, dacoity, fraud, kidnap):",
            value=default_search,
            placeholder="Type section number or term..."
        )

    categories = ["All Categories"] + sorted(list(set(data.get("category", "General") for data in labels.values())))
    with col_cat:
        selected_category = st.selectbox("Filter by Legal Category:", categories)

    with st.expander("⚙️ CrPC Schedule II Procedural Filters (Bail / FIR / Compromise)", expanded=False):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            cognizable_filter = st.selectbox("Arrest / FIR Status:", ["All", "Cognizable (Police Arrests w/o Warrant)", "Non-cognizable (Warrant Required)"])
        with col_f2:
            bailable_filter = st.selectbox("Bail Posture:", ["All", "Bailable (Bail as of Right)", "Non-bailable (Judicial Discretion)"])
        with col_f3:
            compoundable_filter = st.selectbox("Compromise / Sulh:", ["All", "Compoundable (Sulh Permitted)", "Non-compoundable (No Private Compromise)"])

    # Filtering logic
    filtered = []
    for sec, data in labels.items():
        q_term = search_term.lower().strip()
        title = data.get("title", "").lower()
        citizen = data.get("citizen_term", "").lower()

        # Text search matching
        match_text = (not q_term or q_term in sec.lower() or q_term in title or q_term in citizen)
        if not match_text:
            continue

        # Category matching
        if selected_category != "All Categories" and data.get("category") != selected_category:
            continue

        # CrPC Procedural matching
        if lookup_df is not None and sec in lookup_df.index:
            row = lookup_df.loc[sec]
            cog_val = str(row["cognizable"])
            bail_val = str(row["bailable"]).lower()
            comp_val = str(row["compoundable"]).lower()

            if "Cognizable (" in cognizable_filter and cog_val != "Cognizable":
                continue
            if "Non-cognizable (" in cognizable_filter and cog_val != "Non-cognizable":
                continue

            if "Non-bailable" in bailable_filter:
                if "non-bailable" not in bail_val:
                    continue
            elif "Bailable (" in bailable_filter:
                if "bailable" not in bail_val or "non-bailable" in bail_val:
                    continue

            if "Non-compoundable" in compoundable_filter:
                if "non-compoundable" not in comp_val:
                    continue
            elif "Compoundable (" in compoundable_filter:
                if "compoundable" not in comp_val or "non-compoundable" in comp_val:
                    continue

        filtered.append(data)

    st.write(f"Showing **{len(filtered)}** of **{len(labels)}** target PPC sections:")

    if not filtered:
        st.warning("No sections match the current filters. Broaden your search or reset procedural filters above.")

    for item in filtered:
        sec = item["section"]
        title = item["title"]
        citizen_term = item.get("citizen_term", "")
        cat = item.get("category", "General")
        content = sections_content.get(sec, {})

        # Procedural badges row
        badge_cog = "⚪ Sched II Info"
        badge_bail = "⚪ Bail"
        badge_comp = "⚪ Sulh"
        court_info = "Competent Court"
        penalty_info = "Penalty"

        if lookup_df is not None and sec in lookup_df.index:
            row = lookup_df.loc[sec]
            is_cog = row["cognizable"] == "Cognizable"
            badge_cog = "🔵 Cognizable (Arrest w/o Warrant)" if is_cog else "⚪ Non-cognizable (Warrant Req.)"

            is_non_bail = "non-bailable" in str(row["bailable"]).lower()
            badge_bail = "🔴 Non-bailable" if is_non_bail else "🟢 Bailable"

            is_non_comp = "non-compoundable" in str(row["compoundable"]).lower()
            badge_comp = "🚫 Non-compoundable" if is_non_comp else "🤝 Compoundable"

            court_info = row["court"]
            penalty_info = row["punishment"]

        expander_title = f"Section {sec}: {title} — [{citizen_term}] ({cat})"
        with st.expander(expander_title):
            # Badge summary header
            b1, b2, b3, b4 = st.columns([1.5, 1, 1.2, 2])
            b1.caption(f"**FIR / Police:** `{badge_cog}`")
            b2.caption(f"**Bail:** `{badge_bail}`")
            b3.caption(f"**Compromise:** `{badge_comp}`")
            b4.caption(f"**Trial Court:** `{court_info}`")

            st.divider()

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
                st.markdown("#### 🏛️ Statutory Penalty & Procedure (CrPC)")
                st.markdown(f"- **Prescribed Penalty:** {penalty_info}")
                st.markdown(f"- **Competent Trial Court:** {court_info}")
                if lookup_df is not None and sec in lookup_df.index:
                    st.caption(f"Schedule II Reference: `{lookup_df.loc[sec]['source']}` (Verified: {lookup_df.loc[sec]['date_checked']})")

                if item.get("confusable_with"):
                    st.warning(f"⚠️ **Confusable With:** Sections {', '.join(item['confusable_with'])}")

                if "statutory_reference" in content:
                    st.caption(f"PPC Reference: `{content['statutory_reference']}`")

                st.divider()

                # Live Supreme Court precedents cross-reference
                sec_cases = cases_by_section.get(sec, [])
                st.markdown(f"#### 🏛️ Supreme Court Precedents ({len(sec_cases)} found)")
                if sec_cases:
                    for c_idx, c_item in enumerate(sec_cases[:2], 1):
                        c_title = c_item.get("case_title", "Criminal Appeal")
                        c_num = c_item.get("citation_number", "SC Pakistan")
                        c_snippet = (c_item.get("text", "")[:130] + "...") if c_item.get("text") else ""
                        st.markdown(f"**{c_idx}. {c_title}** (`{c_num}`)")
                        if c_snippet:
                            st.caption(f"_{c_snippet}_")

                    if st.button(f"🔍 Search Precedents for Section {sec}", key=f"btn_case_{sec}"):
                        st.session_state["case_section_filter"] = sec
                        safe_switch_page("pages/3_Case_Finder.py")
                else:
                    st.caption("No direct Supreme Court judgments indexed in the 301 criminal appeal benchmark.")

                st.divider()

                # Practice Quiz deep link
                st.markdown("#### 🎯 Test Your Knowledge")
                if st.button(f"📝 Practice Scenarios for Section {sec}", key=f"btn_quiz_{sec}"):
                    st.session_state["quiz_target_section"] = sec
                    safe_switch_page("pages/4_Quiz.py")

with tab2:
    st.subheader("⚖️ Key Statutory Distinctions (Confusable Groups)")
    st.write(
        "Master the subtle dividing lines between commonly confused Pakistan Penal Code sections. "
        "Understanding these distinctions is essential for legal drafting and judicial exam preparation."
    )

    for grp in confusable_groups:
        grp_secs = grp.get("sections", [])
        with st.expander(f"📌 {grp['group_name']} (Sections {', '.join(grp_secs)})"):
            st.info(f"**Statutory Distinction Summary:** {grp['distinction_summary']}")

            st.markdown("#### Side-by-Side Key Differentiators:")
            diff_table = []
            for s_num in grp_secs:
                diff_text = grp.get("key_differentiators", {}).get(s_num, "N/A")
                title_text = labels.get(s_num, {}).get("title", f"Section {s_num}")
                cog_stat = lookup_df.loc[s_num]["cognizable"] if (lookup_df is not None and s_num in lookup_df.index) else "N/A"
                bail_stat = lookup_df.loc[s_num]["bailable"] if (lookup_df is not None and s_num in lookup_df.index) else "N/A"
                diff_table.append({
                    "Section": f"PPC {s_num}",
                    "Title": title_text,
                    "Cognizability": cog_stat,
                    "Bail Posture": bail_stat,
                    "Statutory Boundary & Differentiator": diff_text
                })

            st.table(pd.DataFrame(diff_table).set_index("Section"))

            st.error(f"💡 **Critical Student Pitfall:** {grp['critical_student_pitfall']}")

st.caption("Track B Module (Owner: Abdul Qudoos) — Student Legal Explorer & Statutory Elements Engine.")
