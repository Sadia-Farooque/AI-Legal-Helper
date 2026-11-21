"""Incident Analyzer (Track A, Task A8; owner: Sadia Fatima).

A citizen describes what happened in English or Roman Urdu. The page shows the 3 most likely PPC sections
with calibrated confidence, the legal facts from CrPC Schedule II (FIR / bail / compounding / punishment),
"Why this section?" word highlights (LIME), how confusable sections differ, and what to do next.
If the model is not confident enough it says so instead of guessing.
"""

import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.analyzer import analyze, compare_retrieval  # noqa: E402
import json  # noqa: E402

from src import feedback  # noqa: E402
from src.fir_draft import FIRDetails, draft, valid_cnic  # noqa: E402
from src.next_steps import helplines  # noqa: E402

st.set_page_config(page_title="Incident Analyzer", page_icon="🚨", layout="wide")

EXAMPLES = {
    "Phone snatching (Roman Urdu)": "Kal raat do larkay bike par aaye aur pistol dikha kar mera mobile aur wallet cheen kar bhaag gaye",
    "Bounced cheque": "My friend borrowed 3 lakh and gave me a cheque to repay it. The bank returned it saying insufficient funds.",
    "Harassment at work": "A man in my office keeps sending me vulgar messages at night and makes dirty comments about me.",
    "Land occupied": "Our neighbour broke our boundary wall and entered our plot with his workers to build a room on it.",
    "Ghar mein chori (Roman Urdu)": "Hum shaadi par gaye thay, peeche se choron ne ghar ka taala tor kar almari se zewar aur cash chura liya",
}


@st.cache_resource(show_spinner=False)
def _warm_model():
    analyze("warm up the model")      # loads the trained model once per server
    return True


@st.cache_data(show_spinner=False)
def _run(text):
    return analyze(text)


@st.cache_data(show_spinner=False)
def _explain(text, section):
    from src.explain import explain, highlight_html
    from src.models.tfidf_lr import predict_scores, predict_scores_batch
    words = explain(text, predict_scores, section=section, num_features=8, num_samples=300,
                    batch_predict=predict_scores_batch)
    return highlight_html(text, words), words


def _set_example(t):
    st.session_state["incident"] = t


def _badge(label, value):
    v = str(value)
    good = v.lower().startswith(("cognizable", "bailable", "compoundable"))
    colour = "#1f6f5c" if good else "#a33a2b"
    return (f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;border-radius:999px;'
            f'border:1px solid {colour};color:{colour};font-size:0.8rem">{label}: {v}</span>')


st.title("🚨 Incident Analyzer")
st.caption("Describe what happened in **English or Roman Urdu**. You'll see which Pakistan Penal Code sections may "
           "apply, whether police can register an FIR, and what to do next.")
st.warning("**This is legal information, not legal advice.** An AI model can be wrong. For an actual case, "
           "speak to a lawyer or call the free legal-advice helpline **1099**.", icon="⚖️")

_warm_model()

st.write("Try an example:")
cols = st.columns(len(EXAMPLES))
for c, (label, text) in zip(cols, EXAMPLES.items()):
    c.button(label, on_click=_set_example, args=(text,), key=f"ex_{label}")

text = st.text_area("What happened?", key="incident", height=120,
                    placeholder="e.g. Two men on a motorcycle snatched my phone near Saddar at gunpoint...")
go = st.button("Analyze", type="primary")

if go and text.strip():
    with st.spinner("Reading your description..."):
        res = _run(text)
    st.session_state["last"] = (text, res)

if "last" in st.session_state:
    text, res = st.session_state["last"]
    status = res["status"]

    if status == "urdu_script":
        st.info("Urdu script is not supported yet. Please type in **Roman Urdu** (e.g. *mera mobile cheen liya*) "
                "or English.")
    elif status == "empty":
        st.info("Please describe what happened.")
    else:
        lang = "Roman Urdu" if res["language"] == "roman_ur" else "English"
        if status == "abstain":
            st.error(f"**I'm not sure about this one.** My best guess is below **{res['threshold']:.0%}** "
                     "confidence, so I won't pretend to know. It may not be a criminal matter, or it needs more "
                     "detail (what was done, by whom, was anything taken, was anyone hurt or threatened?). "
                     "For advice call **1099** (free).")
            with st.expander("Show my low-confidence guesses anyway"):
                for card in res["results"]:
                    st.write(f"Section **{card['section']}** · {card['name']} · {card['score']:.0%}")
        else:
            st.subheader("Sections that may apply")
            st.caption(f"Detected language: {lang} · confidence is calibrated: about 87% of answers at this "
                       f"level are correct on our validation data")
            cards = st.columns(len(res["results"]))
            for i, (col, card) in enumerate(zip(cards, res["results"])):
                with col, st.container(border=True):
                    st.markdown(f"**#{i + 1} · Section {card['section']} PPC**"
                                + (" (with 441)" if card["also_441"] else ""))
                    st.markdown(f"### {card['name']}")
                    st.progress(min(max(card["score"], 0.0), 1.0), text=f"Confidence {card['score']:.0%}")
                    st.markdown(_badge("FIR", card["cognizable"]) + _badge("Bail", card["bailable"]) +
                                _badge("Settlement", card["compoundable"]), unsafe_allow_html=True)
                    if card["punishment"]:
                        st.caption(f"**Punishment:** {card['punishment']}")
                    with st.expander("What this section means"):
                        st.write(card["summary"] or card["meaning"])
                        if card["elements"]:
                            st.markdown("**What must be true:**\n" + "\n".join(f"- {e}" for e in card["elements"]))
                        if card["court"]:
                            st.caption(f"Tried by: {card['court']}")

            conf = res.get("confusable")
            if conf and conf["a_text"] and conf["b_text"]:
                with st.container(border=True):
                    st.markdown(f"**{conf['a']} or {conf['b']}? How they differ**")
                    st.markdown(f"- **{conf['a']}:** {conf['a_text']}\n- **{conf['b']}:** {conf['b_text']}")

            with st.expander("Compare with the retrieval model (Track B, B4: sentence embeddings)"):
                ranked, err = compare_retrieval(text)
                if ranked is None:
                    st.caption("The retrieval model is not available on this machine "
                               "(needs `sentence-transformers` and its index: `python src/retrieval.py --build-index`).")
                else:
                    agree = ranked[0][0] == res["results"][0]["section"]
                    st.markdown("  \n".join(f"#{i + 1} · Section **{s}** · similarity score {v:.0%}"
                                             for i, (s, v) in enumerate(ranked)))
                    st.caption("✅ Both models agree on the top section." if agree else
                               "⚠️ The two models disagree on the top section, so treat the result with extra care.")

            if st.checkbox(f"🔍 Why Section {res['results'][0]['section']}? Show the words that led to it"):
                with st.spinner("Testing which words matter..."):
                    html, words = _explain(text, res["results"][0]["section"])
                st.markdown(f'<div style="line-height:2;font-size:1.05rem">{html}</div>', unsafe_allow_html=True)
                st.caption("Green words pushed the model towards this section, red words away from it "
                           "(LIME explanation).")


            with st.expander("📝 Written complaint for the police (darkhwast)"):
                top = res["results"][0]
                if str(top["cognizable"]).lower().startswith("non"):
                    st.info(f"Section {top['section']} is non-cognizable: the police may record it and refer you to "
                            "a Magistrate (s.155 CrPC). The application is still useful as your written statement.")
                st.caption("The police write the FIR themselves (s.154 CrPC), usually based on what you tell them or "
                           "a written application like this one. This fills a standard application with your own "
                           "words, so nothing important is forgotten. Empty fields become blank lines to complete "
                           "by hand. Nothing you enter is saved.")
                with st.form("fir_form"):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Your name")
                    relation = c2.text_input("Father's / husband's name")
                    cnic = c1.text_input("CNIC (optional)", placeholder="35202-1234567-8")
                    phone = c2.text_input("Mobile number")
                    address = st.text_input("Your address")
                    c3, c4, c5 = st.columns(3)
                    ps = c3.text_input("Police station (thana)")
                    when = c4.date_input("Date of incident", value=None, format="DD/MM/YYYY")
                    at = c5.text_input("Approximate time", placeholder="9:30 pm")
                    place = st.text_input("Place of incident")
                    accused = st.text_input("Accused: names or descriptions (leave empty if unknown)")
                    prop = st.text_input("Property taken / loss (optional)")
                    wit = st.text_input("Witnesses (optional)")
                    delay = st.text_input("If reporting late: reason for the delay (optional)")
                    secs = st.multiselect("Sections to mention", [c["section"] for c in res["results"]],
                                          default=[res["results"][0]["section"]])
                    lang = st.radio("Language", ["English + Urdu", "English", "Urdu"], horizontal=True)
                    make = st.form_submit_button("Generate complaint")
                if make:
                    if not valid_cnic(cnic):
                        st.error("CNIC should look like 35202-1234567-8 (or leave it empty).")
                    else:
                        details = FIRDetails(name=name, relation=relation, cnic=cnic, address=address, phone=phone,
                                             police_station=ps, incident_date=when.strftime("%d-%m-%Y") if when else "",
                                             incident_time=at, place=place, accused=accused, property_lost=prop,
                                             witnesses=wit, delay_reason=delay, description=text,
                                             sections=secs)
                        code = {"English + Urdu": "both", "English": "en", "Urdu": "ur"}[lang]
                        doc = draft(details, code)
                        st.session_state["complaint"] = (draft(details, "en") if code in ("both", "en") else None,
                                                         draft(details, "ur") if code in ("both", "ur") else None)
                        st.text_area("Your complaint (you can edit it after downloading)", doc, height=360)
                        st.download_button("⬇️ Download complaint (.txt)", doc.encode("utf-8"),
                                           file_name="Police_complaint.txt", mime="text/plain")
                        st.caption("Print it, sign it, and take it with a copy of your CNIC to the police station. "
                                   "Keep a photo of the signed copy.")

        st.divider()
        st.subheader("What to do now")
        guide = res["guide"]
        tab_steps, tab_type, tab_help = st.tabs(["Steps", "For this type of incident", "Helplines"])
        with tab_steps:
            cog = guide.get("first_section_cognizable")
            if status == "ok" and cog is False:
                st.info("The top section is **non-cognizable**: police cannot register an FIR for it directly; "
                        "see step 3.")
            for i, (title, body) in enumerate(guide["general"], 1):
                st.markdown(f"**{i}. {title}.** {body}")
        with tab_type:
            if guide["categories"]:
                for _, title, tips in guide["categories"]:
                    st.markdown(f"**{title}**\n" + "\n".join(f"- {t}" for t in tips))
            else:
                st.write("No specific tips for this description.")
        with tab_help:
            for h in helplines().values():
                st.markdown(f"**{h['number']}**: {h['name']} ({h['area']}). {h['use_for']}. "
                            f"[source]({h['source_url']}), checked {h['date_checked']}")

        # ---- PDF export (Extra 2) -------------------------------------------------------------
        st.divider()
        try:
            from src.pdf_export import build_pdf
            comp_en, comp_ur = st.session_state.get("complaint", (None, None))
            pdf = build_pdf(text, res, comp_en, comp_ur, list(helplines().values()))
            st.download_button("⬇️ Download PDF report" + (" (with your complaint)" if comp_en or comp_ur else ""),
                               pdf, file_name="incident_report.pdf", mime="application/pdf")
        except ImportError:
            st.caption("PDF export needs `pip install fpdf2 uharfbuzz`.")

        # ---- Feedback (Extra 3) ----------------------------------------------------------------
        with st.expander("💬 Was this correct? Lawyers and law students: please tell us if anything is wrong"):
            with st.form("feedback_form", clear_on_submit=True):
                verdict = st.radio("Was the result correct?", ["Yes", "Partly", "No"], horizontal=True)
                all_secs = [s_ for s_ in json.load(open(os.path.join(PROJECT_ROOT, "src", "labels.json"),
                                                        encoding="utf-8")) if s_ != "307"]
                correct = st.multiselect("Which sections are actually correct? (optional)", all_secs)
                role = st.selectbox("I am a", ["Citizen", "Law student", "Lawyer", "Other"])
                comment = st.text_area("What is wrong or missing? Bugs, wrong legal facts, suggestions...", height=90)
                consent = st.checkbox("I agree that my incident description may be stored anonymously to improve "
                                      "the model")
                sent = st.form_submit_button("Send feedback")
            if sent:
                rec = feedback.make_record(verdict.lower(), [c["section"] for c in res.get("results", [])], correct,
                                           role.lower(), comment, text, consent, "tfidf_lr", status)
                try:
                    secrets = dict(st.secrets)
                except Exception:  # noqa: BLE001 (no secrets file configured)
                    secrets = {}
                out = feedback.submit(rec, secrets)
                st.success("Thank you! Your feedback was saved" +
                           (f" and shared with the team ([issue]({out['issue_url']}))." if out["issue_url"] else "."))

st.divider()
st.caption("Model: TF-IDF + Logistic Regression trained on 1,335 court cases and 557 reviewed citizen-style "
           "stories, with calibrated confidence and an abstain rule (Track A, Sadia Fatima). Comparison model and "
           "legal facts (CrPC Schedule II lookup, section summaries): Track B, Abdul Qudoos. Nothing you type is stored.")
