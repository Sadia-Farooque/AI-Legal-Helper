import streamlit as st
import os

st.set_page_config(page_title="Similar Case Finder", page_icon="🔍", layout="wide")

st.title("🔍 Supreme Court Similar Case Finder")
st.write("Retrieve Supreme Court of Pakistan judgments with factual precedents matching your scenario.")

query = st.text_area(
    "Enter scenario or section to search case precedents:",
    placeholder="e.g. Armed robbery at a petrol pump with accomplice waiting in car..."
)

top_k = st.slider("Number of judgments to retrieve", min_value=1, max_value=10, value=3)

if st.button("Find Precedents", type="primary"):
    if query.strip():
        st.subheader("Relevant Supreme Court Judgments (Preview Stub)")
        st.info("The semantic FAISS case retrieval engine is scheduled for deployment in Task B5 following SC judgment data extraction in Task B3.")
        
        # Display mock precedent card
        st.markdown("""
        > **PLD 2021 SC 450** — *Muhammad Akram vs. The State*  
        > **Cited Sections:** PPC 392, 34  
        > **Summary Snippet:** The Supreme Court examined the essential ingredients of robbery under Section 392 PPC committed in furtherance of common intention...
        """)
    else:
        st.warning("Please enter a factual scenario or query.")

st.caption("Track B Module (Owner: Abdul Qudoos)")
