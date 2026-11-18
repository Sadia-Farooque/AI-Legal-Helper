import streamlit as st

st.set_page_config(page_title="Law Student Practice Quiz", page_icon="📝", layout="wide")

st.title("📝 PPC Criminal Law Practice Quiz")
st.write("Test your proficiency in identifying correct penal provisions and distinguishing confusable offences.")

# Mock sample quiz questions adhering to B6 quiz bank format
SAMPLE_QUESTIONS = [
    {
        "id": "q1",
        "scenario": "A person enters an open shop during the daytime, quietly takes a customer's unattended handbag from the counter without using any weapon or threat, and leaves unnoticed.",
        "options": ["Section 379 (Theft)", "Section 380 (Theft in dwelling house)", "Section 392 (Robbery)", "Section 403 (Dishonest misappropriation)"],
        "correct": 0,
        "explanation": "Section 379 applies because movable property was taken without consent without entering a residential dwelling and without force or intimidation."
    },
    {
        "id": "q2",
        "scenario": "Five armed men storm into a commercial bank at noon, hold security personnel at gunpoint, and force the cashier to hand over cash drawers.",
        "options": ["Section 379 (Theft)", "Section 384 (Extortion)", "Section 392 (Robbery)", "Section 395 (Dacoity)"],
        "correct": 3,
        "explanation": "Section 395 (Dacoity) applies when five or more persons conjointly commit or attempt to commit a robbery."
    }
]

if "quiz_idx" not in st.session_state:
    st.session_state.quiz_idx = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = False

q = SAMPLE_QUESTIONS[st.session_state.quiz_idx]

st.subheader(f"Question #{st.session_state.quiz_idx + 1}")
st.info(q["scenario"])

choice = st.radio("Select the most appropriate Pakistan Penal Code section:", q["options"], index=None)

if st.button("Submit Answer", disabled=st.session_state.answered):
    if choice is not None:
        st.session_state.answered = True
        chosen_idx = q["options"].index(choice)
        if chosen_idx == q["correct"]:
            st.success("✅ **Correct!** " + q["explanation"])
            st.session_state.score += 1
        else:
            st.error("❌ **Incorrect.** " + q["explanation"])
    else:
        st.warning("Please choose an option before submitting.")

if st.session_state.answered:
    if st.button("Next Question"):
        st.session_state.quiz_idx = (st.session_state.quiz_idx + 1) % len(SAMPLE_QUESTIONS)
        st.session_state.answered = False
        st.rerun()

st.sidebar.metric("Current Score", f"{st.session_state.score} / {len(SAMPLE_QUESTIONS)}")
st.caption("Track B Module (Owner: Abdul Qudoos) — Full 60-100 question bank scheduled in Task B6.")
