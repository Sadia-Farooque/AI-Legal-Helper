"""Shared look and building blocks for every page of the AI Legal Helper (styling, sidebar, loader, footer).

Colours come from .streamlit/config.toml (light + dark theme). Everything here uses semi-transparent brass and
oxblood tones so it reads well in both themes.
"""

import html
import os
import sys
import threading

import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
for _p in (PROJECT_ROOT, APP_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from src.next_steps import PROVINCES, helplines_for  # noqa: E402

LOGO_PATH = os.path.join(APP_DIR, "assets", "logo.svg")
ICON_PATH = os.path.join(APP_DIR, "assets", "scales.svg")

# Scales of justice (tarazu), drawn for this project. Used as the watermark, the hero emblem and the loader.
SCALES_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' fill='none' stroke='{c}'
stroke-width='{w}' stroke-linecap='round' stroke-linejoin='round'>
<circle cx='60' cy='13' r='4'/><line x1='60' y1='17' x2='60' y2='97'/>
<g class='beam'><line x1='18' y1='30' x2='102' y2='30'/>
<line x1='24' y1='30' x2='12' y2='64'/><line x1='24' y1='30' x2='36' y2='64'/>
<path d='M8 64 Q24 80 40 64 Z'/>
<line x1='96' y1='30' x2='84' y2='64'/><line x1='96' y1='30' x2='108' y2='64'/>
<path d='M80 64 Q96 80 112 64 Z'/></g>
<path d='M42 106 L78 106 L70 97 L50 97 Z'/></svg>"""


def scales(color="#C9A44C", width=2.2, size=48, cls=""):
    svg = SCALES_SVG.format(c=color, w=width).replace("<svg ", f"<svg width='{size}' height='{size}' class='{cls}' ", 1)
    return svg.replace("\n", " ")


def _watermark_url():
    svg = SCALES_SVG.format(c="#C9A44C", w=1.4).replace("\n", " ").replace("<svg ", "<svg stroke-opacity='.09' ", 1)
    return "data:image/svg+xml;utf8," + svg.replace("#", "%23").replace("'", "%27").replace("<", "%3C").replace(">", "%3E")


CSS = """
<style>
/* ---------- chrome: no running-man / Stop widget, no anchor-link icons, transparent header ---------- */
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stStatusWidget"] { visibility: hidden; }
[data-testid="stHeaderActionElements"] { display: none !important; }
#MainMenu + div, footer { visibility: hidden; }

/* ---------- background: brass rule on top + large faint scales watermark ---------- */
.stApp::before {
  content: ""; position: fixed; top: 0; left: 0; right: 0; height: 4px; z-index: 1000;
  background: linear-gradient(90deg, #8E2431 0%, #C9A44C 50%, #1E5631 100%);
}
/* watermark sits centred in the content area and stays still while the page scrolls */
[data-testid="stMain"] { background: url("__WATERMARK__") no-repeat center 55% / min(70vh, 620px); }
.block-container { padding-top: 2.6rem; max-width: 1150px; }

/* ---------- headings ---------- */
h1, h2, h3 { letter-spacing: .2px; }
.page-head { display: flex; align-items: center; gap: .9rem; margin-bottom: .3rem; }
.page-head h1 { margin: 0; padding: 0; font-size: 2.1rem; }
.page-sub { opacity: .8; font-size: 1.05rem; margin: 0 0 1.2rem 0; }
.rule { height: 1px; border: 0; margin: 1.6rem 0 1.2rem;
        background: linear-gradient(90deg, rgba(201,164,76,.6), rgba(201,164,76,0)); }

/* ---------- hero (home) ---------- */
.hero { text-align: center; padding: 1.2rem 1rem .4rem; }
.hero svg { display: block; margin: 0 auto; }
.hero h1 { font-size: 2.6rem; margin: .6rem 0 .2rem; }
.hero .tag { font-size: 1.2rem; opacity: .85; margin: 0; }
.hero .urdu { font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', serif; font-size: 1.25rem;
              color: #C9A44C; direction: rtl; margin: .2rem 0 .8rem; }
.hero .intro { max-width: 640px; margin: 0 auto; opacity: .85; }

/* ---------- cards ---------- */
.tile { border: 1px solid rgba(201,164,76,.35); background: rgba(201,164,76,.06); border-radius: .7rem;
        padding: .9rem 1rem; height: 100%; }
.tile .t-icon { font-size: 1.5rem; }
.tile .t-title { font-weight: 700; margin: .25rem 0 .15rem; }
.tile .t-text { font-size: .92rem; opacity: .85; }
.warn { border-left: 4px solid #C98A1B; background: rgba(201,138,27,.10); border-radius: .5rem;
        padding: .9rem 1.1rem; margin: .4rem 0; }
.warn b { color: #C98A1B; }
.sos { border: 1px solid rgba(178,58,72,.55); background: rgba(178,58,72,.10); border-radius: .6rem;
       padding: .7rem 1rem; text-align: center; font-weight: 600; }
.sos a { text-decoration: none; }

/* choice cards on home */
[class*="st-key-choice_"] { border: 1px solid rgba(201,164,76,.45) !important; background: rgba(201,164,76,.05);
                           border-radius: .9rem !important; padding: 1.2rem 1.3rem !important; }
[class*="st-key-choice_"] h3 { margin-top: 0; }
/* both choice cards the same height, buttons aligned at the bottom */
[data-testid="stHorizontalBlock"]:has([class*="st-key-choice_"]) { align-items: stretch; }
[data-testid="stColumn"]:has([class*="st-key-choice_"]) > div,
[data-testid="stColumn"]:has([class*="st-key-choice_"]) [data-testid="stVerticalBlock"]:has(> [class*="st-key-choice_"]) { height: 100%; }
[class*="st-key-choice_"] { height: 100%; }
[class*="st-key-choice_"] > div:last-child { margin-top: auto; }

/* ---------- badges / confidence ---------- */
.badge { display: inline-block; margin: 2px 6px 4px 0; padding: 2px 10px; border-radius: 999px;
         font-size: .8rem; border: 1px solid currentColor; white-space: nowrap; }
.b-good { color: #3FA37A; } .b-bad { color: #D0525F; } .b-mid { color: #C98A1B; } .b-neutral { opacity: .8; }
.conf { font-weight: 700; font-size: .85rem; }
.cond { font-size: .85rem; border-left: 3px solid #C98A1B; padding: .3rem .6rem; margin: .4rem 0;
        background: rgba(201,138,27,.08); border-radius: .3rem; }
.sec-no { font-size: .8rem; letter-spacing: 1px; text-transform: uppercase; color: #C9A44C; font-weight: 700; }

/* ---------- Supreme Court case cards ---------- */
.case { border: 1px solid rgba(201,164,76,.35); border-left: 4px solid #C9A44C; border-radius: .6rem;
        padding: .9rem 1.1rem .6rem; margin: .6rem 0 .2rem; background: rgba(201,164,76,.04); }
.case .c-top { display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; flex-wrap: wrap; }
.case .c-cite { font-weight: 700; letter-spacing: .3px; }
.case .c-match { font-weight: 700; color: #C9A44C; white-space: nowrap; }
.case .c-meta { font-size: .85rem; opacity: .8; margin: .15rem 0 .5rem; }
.case .c-facts { font-style: italic; opacity: .92; border-left: 2px solid rgba(201,164,76,.4);
                 padding-left: .8rem; margin: .3rem 0 .4rem; }

/* ---------- buttons ---------- */
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { font-weight: 600; }
.st-key-pdf_dl button { background: #1F5A99 !important; color: #fff !important; border: 0 !important;
                        font-weight: 700 !important; font-size: 1.05rem !important; padding: .75rem 1rem !important; }
.st-key-pdf_dl button:hover { background: #2A6DB5 !important; }

/* ---------- sidebar helplines ---------- */
.hl { display: flex; gap: .7rem; align-items: baseline; padding: .32rem 0; text-decoration: none !important;
      border-bottom: 1px dashed rgba(201,164,76,.25); color: inherit !important; }
.hl b { min-width: 5.6rem; color: #C9A44C; font-size: 1.02rem; }
.hl span { font-size: .85rem; opacity: .9; line-height: 1.25; }

/* ---------- loader ---------- */
.loader { text-align: center; padding: 3rem 1rem; }
.loader .beam { transform-origin: 60px 30px; animation: tilt 1.6s ease-in-out infinite; }
@keyframes tilt { 0%,100% { transform: rotate(-7deg); } 50% { transform: rotate(7deg); } }
.loader p { opacity: .8; margin-top: .6rem; }

/* ---------- footer ---------- */
.foot { font-size: .85rem; opacity: .8; border-top: 1px solid rgba(201,164,76,.3); padding-top: .9rem;
        margin-top: 2.5rem; }
</style>
"""


def inject_css():
    st.markdown(CSS.replace("__WATERMARK__", _watermark_url()), unsafe_allow_html=True)


def page_header(title, subtitle=None, icon=None):
    emblem = icon or scales(size=44)
    st.markdown(f'<div class="page-head">{emblem}<h1>{html.escape(title)}</h1></div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="page-sub">{subtitle}</p>', unsafe_allow_html=True)


def rule():
    st.markdown('<hr class="rule">', unsafe_allow_html=True)


def loader(message="Getting things ready..."):
    return (f'<div class="loader">{scales(size=86, width=2.4)}<p>{html.escape(message)}</p></div>')


def footer_disclaimer():
    st.markdown(
        '<div class="foot">⚖️ <b>Legal information, not legal advice.</b> This is an AI tool and it can be wrong. '
        'Use it to understand your situation, then confirm with a lawyer or the free legal-advice helpline '
        '<b>1099</b> before you act. Nothing you type is saved unless you choose to send feedback.</div>',
        unsafe_allow_html=True)


def case_cards(results, key_prefix):
    for i, c in enumerate(results, 1):
        secs = ", ".join(f"PPC {s}" for s in c.get("sections", [])) or "Not listed"
        cite = html.escape(c.get("citation_number") or c.get("case_title") or "Supreme Court of Pakistan")
        facts = html.escape((c.get("text") or "").strip())
        st.markdown(
            f'<div class="case"><div class="c-top"><span class="c-cite">{i}. {cite}</span>'
            f'<span class="c-match">{c.get("similarity", 0):.0%} similar</span></div>'
            f'<div class="c-meta">Supreme Court of Pakistan · Sections cited: {html.escape(secs)}</div>'
            f'<div class="c-facts">{facts}</div></div>', unsafe_allow_html=True)
        if c.get("full_text"):
            with st.expander("Read the judgment excerpt"):
                st.text_area("Judgment excerpt", c["full_text"], height=260, label_visibility="collapsed",
                             key=f"{key_prefix}_{c.get('id', i)}_{i}")


# ---------------------------------------------------------------- sidebar
def sidebar_helplines():
    with st.sidebar:
        st.markdown("#### 📞 Helplines")
        prov = st.selectbox("Your province", PROVINCES, key="province",
                            help="Shows national numbers plus the numbers for your province.")
        rows = [r for r in helplines_for(prov) if prov != "All Pakistan" or r["province"] == "All"]
        items = "".join(
            f'<a class="hl" href="tel:{r["number"].replace("-", "")}" title="{html.escape(r["use_for"])}">'
            f'<b>{html.escape(r["number"])}</b><span>{html.escape(r["name"])}</span></a>' for r in rows)
        st.markdown(items, unsafe_allow_html=True)
        if prov == "All Pakistan":
            st.caption("Choose your province to see local women's, child and police-complaint lines.")


def current_province():
    return st.session_state.get("province", "All Pakistan")


# ---------------------------------------------------------------- admin switch
def is_admin():
    """The Evaluation dashboard is for the team and examiners only.
    Show it with:  $env:LEGAL_HELPER_ADMIN="1"; python run_app.py   (or ?admin=<key> if LEGAL_HELPER_ADMIN_KEY is set)
    """
    if os.environ.get("LEGAL_HELPER_ADMIN") == "1":
        return True
    key = os.environ.get("LEGAL_HELPER_ADMIN_KEY")
    if not key:
        try:
            key = st.secrets.get("LEGAL_HELPER_ADMIN_KEY")
        except Exception:  # noqa: BLE001 (no secrets file)
            key = None
    return bool(key) and st.query_params.get("admin") == key


# ---------------------------------------------------------------- model warm-up
def _warm():
    try:
        from src.models.tfidf_lr import _model
        _model()                       # loads (or, on a fresh clone, trains) the classifier once per server
    except Exception:  # noqa: BLE001 (the Report page will show the real error if loading fails)
        pass


@st.cache_resource(show_spinner=False)
def start_warmup():
    """Start loading the model in the background as soon as anyone opens the site, so the Report page is ready."""
    t = threading.Thread(target=_warm, daemon=True, name="model-warmup")
    t.start()
    return t
