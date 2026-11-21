"""Home: welcome, what the site can do, who it is for, and an honest warning."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st  # noqa: E402

import legal_ui as ui  # noqa: E402

st.markdown(
    f'<div class="hero">{ui.scales(size=92, width=2.2)}'
    '<h1>AI Legal Helper for Pakistan</h1>'
    '<p class="tag">Understand the law. Know your next step.</p>'
    '<p class="urdu">قانون کو سمجھیں، اگلا قدم جانیں</p>'
    '<p class="intro">Free, private help with Pakistan\'s criminal law, for citizens and law students. '
    'Write in English or Roman Urdu.</p></div>',
    unsafe_allow_html=True)

st.write("")
left, right = st.columns(2, gap="large")
with left, st.container(key="choice_report"):
    st.markdown("### 🚨 I need legal help")
    st.markdown("Describe it in your own words. See which laws may apply, whether the police must register "
                "an FIR, and what to do next.")
    if st.button("Report an incident →", type="primary", width="stretch", key="go_report"):
        st.switch_page(os.path.join(ui.APP_DIR, "views", "report.py"))
with right, st.container(key="choice_learn"):
    st.markdown("### 🎓 I'm a law student")
    st.markdown("Learn the key offences topic by topic, compare look-alike sections, read real Supreme Court "
                "cases and quiz yourself.")
    if st.button("Open the Student Corner →", type="primary", width="stretch", key="go_learn"):
        st.switch_page(os.path.join(ui.APP_DIR, "views", "learn.py"))

ui.rule()
st.markdown("#### What you get")
tiles = [
    ("📜", "Likely PPC sections", "The top 3 sections, with how sure the model is."),
    ("🚓", "FIR, bail, settlement", "Whether police can register an FIR, and the punishment."),
    ("🏛️", "Similar court cases", "Real Supreme Court of Pakistan judgments with similar facts."),
    ("📝", "Police application", "A ready-to-sign complaint in English and Urdu, plus a PDF report."),
]
for col, (icon, title, text) in zip(st.columns(4), tiles):
    col.markdown(f'<div class="tile"><div class="t-icon">{icon}</div><div class="t-title">{title}</div>'
                 f'<div class="t-text">{text}</div></div>', unsafe_allow_html=True)

st.write("")
st.markdown(
    '<div class="warn"><b>⚠️ Please read before you use it.</b><br>'
    '• This is an AI tool, <b>not a lawyer</b>. It can be wrong.<br>'
    '• It covers 30 common offences (theft, robbery, hurt, fraud, harassment, threats and more), not all of '
    'Pakistani law.<br>'
    '• Before you act, confirm with a lawyer or call the free legal-advice helpline <b>1099</b>.</div>',
    unsafe_allow_html=True)
st.markdown('<div class="sos">In danger right now? Call <a href="tel:15">15</a> (police) or '
            '<a href="tel:1122">1122</a> (ambulance).</div>', unsafe_allow_html=True)
st.caption("🔒 Nothing you type is saved unless you choose to send feedback.")
