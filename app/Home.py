import streamlit as st
import json
import os

st.set_page_config(
    page_title="AI Legal Helper for Pakistan",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚖️ AI Legal Helper for Pakistan")
st.caption("Machine Learning System for Pakistani Criminal Law (PPC & CrPC)")

st.markdown("""
Welcome to the **AI Legal Helper for Pakistan**, an AI-powered legal intelligence system designed for ordinary citizens and law students.

### 👥 System Capabilities

1. **🚨 Incident Analyzer (For Citizens):**  
   Describe an incident in plain English or Roman Urdu (e.g., *"two men on a bike snatched my phone"*). The system identifies the most relevant Pakistan Penal Code (PPC) sections, FIR eligibility (cognizability), bailability, and statutory punishments.
   
2. **📖 PPC Section Explorer (For Law Students):**  
   Search and explore 30 core criminal sections with plain-English definitions, legal elements, and side-by-side comparisons of confusable sections.

3. **🔍 Similar Case Finder (For Law Students):**  
   Retrieve relevant Supreme Court of Pakistan judgments by semantic scenario search.

4. **📝 Practice Quiz (For Law Students):**  
   Test your ability to distinguish nuanced criminal offences through realistic scenario questions.

5. **📊 Evaluation & Benchmark Dashboard (For Evaluators):**  
   Review verifiable model benchmarks, top-3 recall, F1-scores, and Roman Urdu vs English accuracy curves.
""")

st.info("⚠️ **Legal Disclaimer:** This tool is an academic Machine Learning project developed for educational and informational purposes. It does not constitute formal legal counsel. For actionable legal representation, please consult a licensed advocate or legal aid authority.")

st.sidebar.success("Select a page from above to get started.")
