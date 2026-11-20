import streamlit as st
import json
import os
import random

st.set_page_config(page_title="Law Student Practice Quiz", page_icon="📝", layout="wide")

st.title("📝 PPC Criminal Law Practice Quiz")
st.write("Master fine-grained statutory boundaries across 30 Pakistan Penal Code offences through verified Pakistani legal scenarios.")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUIZ_BANK_PATH = os.path.join(PROJECT_ROOT, "data", "content", "quiz_bank.json")

# Load questions from verified bank
questions_bank = []
if os.path.exists(QUIZ_BANK_PATH):
    with open(QUIZ_BANK_PATH, "r", encoding="utf-8") as f:
        questions_bank = json.load(f)

if not questions_bank:
    st.error("Quiz bank not found. Please run `python src/data/build_quiz_bank.py` first.")
    st.stop()

# Sidebar: Controls & Filters
st.sidebar.header("🎯 Quiz Setup & Filters")

# Category filter
all_categories = sorted(list(set(q.get("category", "General") for q in questions_bank)))
selected_category = st.sidebar.selectbox("Filter by Category:", ["All Categories"] + all_categories)

# Difficulty filter
selected_difficulty = st.sidebar.selectbox(
    "Filter by Difficulty Tier:",
    ["All Difficulties", "Easy (Statutory Recall)", "Medium (Boundary Resolution)", "Hard (Complex Mens Rea / Injury)"]
)

# Apply filters
filtered_questions = questions_bank
if selected_category != "All Categories":
    filtered_questions = [q for q in filtered_questions if q.get("category") == selected_category]

if "Easy" in selected_difficulty:
    filtered_questions = [q for q in filtered_questions if q.get("difficulty") == "easy"]
elif "Medium" in selected_difficulty:
    filtered_questions = [q for q in filtered_questions if q.get("difficulty") == "medium"]
elif "Hard" in selected_difficulty:
    filtered_questions = [q for q in filtered_questions if q.get("difficulty") == "hard"]

if not filtered_questions:
    st.warning("No questions match the selected filter criteria. Please broaden your selection in the sidebar.")
    st.stop()

# State initialization
if "quiz_idx" not in st.session_state:
    st.session_state.quiz_idx = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "total_attempted" not in st.session_state:
    st.session_state.total_attempted = 0
if "answered" not in st.session_state:
    st.session_state.answered = False
if "selected_choice" not in st.session_state:
    st.session_state.selected_choice = None
if "filter_hash" not in st.session_state:
    st.session_state.filter_hash = f"{selected_category}_{selected_difficulty}"

# Reset index if filter changes
current_filter_hash = f"{selected_category}_{selected_difficulty}"
if st.session_state.filter_hash != current_filter_hash:
    st.session_state.quiz_idx = 0
    st.session_state.answered = False
    st.session_state.selected_choice = None
    st.session_state.filter_hash = current_filter_hash

# Bound index safely
if st.session_state.quiz_idx >= len(filtered_questions):
    st.session_state.quiz_idx = 0

q = filtered_questions[st.session_state.quiz_idx]

# Sidebar scorecard
st.sidebar.divider()
st.sidebar.markdown("### 📊 Performance Dashboard")
acc_pct = (st.session_state.score / st.session_state.total_attempted * 100) if st.session_state.total_attempted > 0 else 0.0
st.sidebar.metric("Accuracy", f"{acc_pct:.1f}%")
st.sidebar.metric("Score", f"{st.session_state.score} / {st.session_state.total_attempted}")
st.sidebar.caption(f"Active Pool: **{len(filtered_questions)}** questions available")

if st.sidebar.button("🔄 Reset Quiz Session"):
    st.session_state.quiz_idx = 0
    st.session_state.score = 0
    st.session_state.total_attempted = 0
    st.session_state.answered = False
    st.session_state.selected_choice = None
    st.rerun()

# Main Quiz Interface
col_meta1, col_meta2, col_meta3 = st.columns([2, 1, 1])
col_meta1.caption(f"📂 Category: **{q.get('category', 'Criminal Law')}**")
diff_badge = {"easy": "🟢 Easy", "medium": "🟡 Medium", "hard": "🔴 Hard"}.get(q.get("difficulty", "medium"), "🟡")
col_meta2.caption(f"Tier: **{diff_badge}**")
col_meta3.caption(f"Question **{st.session_state.quiz_idx + 1}** of **{len(filtered_questions)}**")

st.progress((st.session_state.quiz_idx + 1) / len(filtered_questions))

# Scenario Box
st.info(f"**Factual Scenario:**\n\n_{q['scenario']}_")

# Radio choice
choice = st.radio(
    "Select the applicable Pakistan Penal Code (PPC) provision:",
    q["options"],
    index=None if not st.session_state.answered else (
        q["options"].index(st.session_state.selected_choice) if st.session_state.selected_choice in q["options"] else None
    ),
    disabled=st.session_state.answered,
    key=f"radio_{q['id']}_{st.session_state.quiz_idx}"
)

col_act1, col_act2 = st.columns([1, 4])

with col_act1:
    if not st.session_state.answered:
        submit_btn = st.button("Submit Answer", type="primary", use_container_width=True)
        if submit_btn:
            if choice is not None:
                st.session_state.answered = True
                st.session_state.selected_choice = choice
                st.session_state.total_attempted += 1
                chosen_idx = q["options"].index(choice)
                if chosen_idx == q["correct_index"]:
                    st.session_state.score += 1
                st.rerun()
            else:
                st.warning("Please select an option before submitting.")
    else:
        next_btn = st.button("Next Question ➡️", type="primary", use_container_width=True)
        if next_btn:
            st.session_state.quiz_idx = (st.session_state.quiz_idx + 1) % len(filtered_questions)
            st.session_state.answered = False
            st.session_state.selected_choice = None
            st.rerun()

# Feedback & Educational Deep Dive
if st.session_state.answered:
    chosen_idx = q["options"].index(st.session_state.selected_choice)
    is_correct = (chosen_idx == q["correct_index"])

    if is_correct:
        st.success(f"🎉 **Correct Answer!** You identified Section {q['target_section']} PPC.")
    else:
        st.error(f"❌ **Incorrect.** You selected `{st.session_state.selected_choice}`. The correct provision is `{q['options'][q['correct_index']]}`.")

    with st.container():
        st.markdown("#### ⚖️ Authoritative Statutory Reasoning")
        st.write(q["explanation"])

        if q.get("legal_elements_tested"):
            st.markdown("**Key Prosecution Elements Tested:**")
            for elem in q["legal_elements_tested"]:
                st.markdown(f"- `{elem}`")

        if q.get("statutory_reference"):
            st.caption(f"Statutory Reference: `{q['statutory_reference']}`")

st.divider()
st.caption("Track B Module (Owner: Abdul Qudoos) — 60-Scenario Educational Benchmark grounded in Pakistan Penal Code & CrPC jurisprudence.")
