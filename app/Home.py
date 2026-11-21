"""Entry point of the AI Legal Helper for Pakistan (python run_app.py  ->  streamlit run app/Home.py).

Sets the page style, starts loading the model in the background, builds the sidebar (navigation + helplines)
and runs the selected page. Pages live in app/views/. The Evaluation dashboard is shown only to the team
(see legal_ui.is_admin).
"""

import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.dirname(APP_DIR), APP_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st  # noqa: E402

st.set_page_config(page_title="AI Legal Helper for Pakistan", page_icon=os.path.join(APP_DIR, "assets", "scales.svg"),
                   layout="wide", initial_sidebar_state="expanded")

import legal_ui as ui  # noqa: E402

ui.inject_css()
ui.start_warmup()
st.logo(ui.LOGO_PATH, size="large", icon_image=ui.ICON_PATH)

pages = [
    st.Page(os.path.join(APP_DIR, "views", "home.py"), title="Home", icon="🏠", default=True),
    st.Page(os.path.join(APP_DIR, "views", "report.py"), title="Report an incident", icon="🚨", url_path="report"),
    st.Page(os.path.join(APP_DIR, "views", "learn.py"), title="Student Corner", icon="🎓", url_path="learn"),
]
if ui.is_admin():
    pages.append(st.Page(os.path.join(APP_DIR, "pages", "5_Evaluation.py"), title="Evaluation (team only)",
                         icon="📊", url_path="evaluation"))

nav = st.navigation(pages)
ui.sidebar_helplines()
nav.run()
