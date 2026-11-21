"""Report an incident (citizen page).

A citizen describes what happened in English or Roman Urdu. The page shows the 3 most likely PPC sections
with calibrated confidence and the legal facts from CrPC Schedule II, similar Supreme Court cases, why the model
chose the top section (LIME), a ready-to-sign police application, next steps and a PDF report. If the model is
not confident it asks for more detail and gives NO legal route, so nobody is sent to the police on a guess.
"""

import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st  # noqa: E402

import legal_ui as ui  # noqa: E402
from src import feedback  # noqa: E402
from src.analyzer import analyze, compare_retrieval, legal_condition  # noqa: E402
from src.fir_draft import FIRDetails, draft, valid_cnic  # noqa: E402
from src.next_steps import helplines_for, steps_for  # noqa: E402

MAX_FEEDBACK_PER_SESSION = 3
HIGH, MEDIUM = 0.85, 0.70        # confidence labels; 0.70 is also the abstain threshold (A6 calibration)
CARD_MIN = 0.40                  # #2 / #3 below this are listed in one line as "less likely", not as full cards


@st.cache_data(show_spinner=False)
def _run(text):
    return analyze(text)


@st.cache_data(show_spinner=False)
def _explain(text, section):
    from src.explain import explain, highlight_html
    from src.models.tfidf_lr import predict_scores, predict_scores_batch
    words = explain(text, predict_scores, section=section, num_features=8, num_samples=300,
                    batch_predict=predict_scores_batch)
    return highlight_html(text, words)


@st.cache_data(show_spinner=False)
def _cases(text, k=3):
    from src.case_finder import search_cases
    return search_cases(text, top_k=k)


def _badge(text, kind):
    return f'<span class="badge b-{kind}">{html.escape(text)}</span>'


def _fact_badges(card):
    cog = str(card["cognizable"])
    bail = str(card["bailable"])
    comp = str(card["compoundable"])
    out = _badge("Police can register FIR", "good") if cog.lower().startswith("cognizable") else \
        _badge("No direct FIR: Magistrate route", "mid")
    out += _badge("Bailable", "good") if not bail.lower().startswith("non") else _badge("Non-bailable", "bad")
    out += _badge("Can be settled", "neutral") if not comp.lower().startswith("non") else \
        _badge("Cannot be settled privately", "neutral")
    return out


def _confidence(score):
    if score >= HIGH:
        return f'<span class="conf b-good">High confidence · {score:.0%}</span>'
    if score >= MEDIUM:
        return f'<span class="conf b-mid">Medium confidence · {score:.0%}</span>'
    return f'<span class="conf b-neutral">Low confidence · {score:.0%}</span>'


# ================================================================ page
ui.page_header("Report an incident", "Tell us what happened, in English or Roman Urdu.")

warm = ui.start_warmup()
if warm.is_alive():
    holder = st.empty()
    holder.markdown(ui.loader("Getting the legal model ready... (only the first visit takes a moment)"),
                    unsafe_allow_html=True)
    warm.join()
    holder.empty()

text = st.text_area("What happened?", key="incident", height=130,
                    placeholder="e.g. Last night two men on a motorcycle snatched my phone at gunpoint near Saddar.")
c_go, c_tips = st.columns([1, 4], vertical_alignment="center")
go = c_go.button("Analyze", type="primary", width="stretch")
with c_tips.popover("💡 What should I write?"):
    st.markdown("- **What** was done (snatched, hit, threatened, cheated...)\n- **Who** did it (stranger, "
                "someone you know)\n- **Where** and **when**\n- Was anything **taken** or money **lost**?\n"
                "- Was anyone **hurt** or **threatened**?")

if go:
    if text.strip():
        import time
        from datetime import datetime
        t0 = time.time()
        holder = st.empty()       # shown immediately (st.spinner only appears after a delay)
        holder.markdown(ui.loader("Analysing your description..."), unsafe_allow_html=True)
        result = _run(text)
        time.sleep(max(0.0, 1.2 - (time.time() - t0)))       # long enough to see that something happened
        holder.empty()
        st.session_state["last"] = (text, result)
        st.session_state["analysed_at"] = datetime.now().strftime("%I:%M:%S %p")
        st.toast("Analysis complete", icon="⚖️")
        st.session_state.pop("complaint", None)
    else:
        st.session_state.pop("last", None)
        st.info("Please describe what happened first.")

if "last" in st.session_state:
    text, res = st.session_state["last"]
    status = res["status"]
    st.caption(f"Result for the description analysed at {st.session_state.get('analysed_at', '')}.")

    if status == "urdu_script":
        st.info("Urdu script is not supported yet. Please type in **Roman Urdu** (e.g. *mera mobile cheen liya*) "
                "or English.")
    elif status == "empty":
        st.info("Please describe what happened.")

    # ------------------------------------------------------------ not confident: ask for detail, no legal route
    elif status == "abstain":
        with st.container(border=True):
            detailed = len(text.split()) >= 15
            if detailed:
                st.markdown("### 🤔 I can't answer this one reliably")
                st.markdown("Your description has detail, but my model has not seen enough examples like it, so "
                            "it is not confident enough to name a law. **This is a limit of the model, not of your "
                            "writing.** Please call **1099** for free legal advice. In danger now? Call **15**.")
                st.markdown("If you want to try again, adding these can help:")
            else:
                st.markdown("### 🤔 I need a bit more detail")
                st.markdown("I'm not confident enough to name a law for this, so I won't guess. "
                            "Please add these details and try again:")
            st.markdown("- **What exactly was done?** (snatched, hit, threatened, cheated, entered, harassed...)\n"
                        "- **Who did it?** A stranger, someone you know, an official?\n"
                        "- **Was anything taken or money lost?** How much?\n"
                        "- **Was anyone hurt, threatened or held against their will?**\n"
                        "- **Where and when** did it happen?")
            st.markdown("It may also **not be a criminal matter** (for example a dispute about marks, salary, "
                        "rent or a contract). For free advice call **1099**. In danger now? Call **15**.")

    # ------------------------------------------------------------ confident: results
    else:
        cards = res["results"]
        top = cards[0]
        lang = "Roman Urdu" if res["language"] == "roman_ur" else "English"

        st.markdown("### Sections that may apply")
        st.caption(f"Language detected: {lang}. Confidence is calibrated: at High, about 9 in 10 answers were "
                   "correct in our tests.")
        main = [c for i, c in enumerate(cards) if i == 0 or c["score"] >= CARD_MIN]
        minor = [c for c in cards if c not in main]
        for i, (col, card) in enumerate(zip(st.columns(len(main)) if len(main) > 1 else [st.container()], main)):
            with col, st.container(border=True):
                st.markdown(f'<div class="sec-no">#{i + 1} · PPC {card["section"]}'
                            f'{" (with 441)" if card["also_441"] else ""}</div>', unsafe_allow_html=True)
                st.markdown(f"#### {card['name']}")
                st.markdown(_confidence(card["score"]), unsafe_allow_html=True)
                st.progress(min(max(card["score"], 0.0), 1.0))
                st.markdown(_fact_badges(card), unsafe_allow_html=True)
                cond = legal_condition(card["section"], text)
                if cond:
                    st.markdown(f'<div class="cond">⚠️ {html.escape(cond)}</div>', unsafe_allow_html=True)
                if card["punishment"]:
                    st.caption(f"**Punishment:** {card['punishment']}")
                with st.expander("What this means"):
                    st.write(card["summary"] or card["meaning"])
                    if card["elements"]:
                        st.markdown("**Must be true:**\n" + "\n".join(f"- {e}" for e in card["elements"]))
                    if card["court"]:
                        st.caption(f"Tried by: {card['court']}")

        if minor:
            st.caption("Less likely: " + " · ".join(f"PPC {c['section']} {c['name']} ({c['score']:.0%})"
                                                    for c in minor))

        conf = res.get("confusable")
        if conf and conf["a_text"] and conf["b_text"]:
            st.markdown(f'<div class="warn"><b>{conf["a"]} or {conf["b"]}?</b> These two are easy to confuse.<br>'
                        f'• <b>{conf["a"]}:</b> {html.escape(conf["a_text"])}<br>'
                        f'• <b>{conf["b"]}:</b> {html.escape(conf["b_text"])}</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1.expander("🔍 Why this result?"):
            st.caption(f"Words that pushed the model towards Section {top['section']} (green) or away (red).")
            if st.button("Show the important words", key="lime"):
                with st.spinner("Testing which words matter..."):
                    st.session_state["lime_html"] = (text, _explain(text, top["section"]))
            if st.session_state.get("lime_html", (None,))[0] == text:
                st.markdown(f'<div style="line-height:2;font-size:1.05rem">{st.session_state["lime_html"][1]}'
                            '</div>', unsafe_allow_html=True)
        with c2.expander("🧠 Second opinion from another AI model"):
            ranked, _err = compare_retrieval(text)
            if ranked is None:
                st.caption("The second model is not installed on this server.")
            else:
                from src.analyzer import section_card
                names = [f"Section {s} ({section_card(s, v)['name']})" for s, v in ranked]
                if ranked[0][0] == top["section"]:
                    st.success(f"Agrees: it also picks **Section {top['section']}** first.")
                else:
                    st.warning(f"Disagrees: it picks **{names[0]}** first, so treat the result with extra care.")
                st.caption("Its top 3: " + " · ".join(names))

        # -------------------------------------------------------- similar Supreme Court cases
        ui.rule()
        st.markdown("### 🏛️ Similar Supreme Court cases")
        st.caption("Real judgments of the Supreme Court of Pakistan with facts closest to yours. "
                   "They show how courts treated similar situations; every case is different.")
        try:
            with st.spinner("Searching 301 Supreme Court judgments..."):
                found = _cases(text)
            if found:
                ui.case_cards(found, "rep")
            else:
                st.caption("No close match found.")
        except Exception:  # noqa: BLE001 (needs sentence-transformers + the case index)
            st.caption("Case search is not available on this server (needs `sentence-transformers` and the "
                       "case index: `python src/case_finder.py --build-index`).")

        # -------------------------------------------------------- police application
        ui.rule()
        with st.expander("📝 Write my application to the police (darkhwast)"):
            if str(top["cognizable"]).lower().startswith("non"):
                st.info(f"Section {top['section']} is non-cognizable: police may record it and refer you to a "
                        "Magistrate (s.155 CrPC). The application is still useful as your written statement.")
            st.caption("Police write the FIR themselves (s.154 CrPC) from what you tell them. This fills a standard "
                       "application with your details so nothing is forgotten. Empty fields become blank lines. "
                       "Nothing you enter is saved.")
            with st.form("fir_form"):
                f1, f2 = st.columns(2)
                name = f1.text_input("Your name")
                relation = f2.text_input("Father's / husband's name")
                cnic = f1.text_input("CNIC (optional)", placeholder="35202-1234567-8")
                phone = f2.text_input("Mobile number")
                address = st.text_input("Your address")
                f3, f4, f5 = st.columns(3)
                ps = f3.text_input("Police station (thana)")
                when = f4.date_input("Date of incident", value=None, format="DD/MM/YYYY")
                at = f5.text_input("Approximate time", placeholder="9:30 pm")
                place = st.text_input("Place of incident")
                accused = st.text_input("Accused: names or descriptions (leave empty if unknown)")
                prop = st.text_input("Property taken / loss (optional)")
                wit = st.text_input("Witnesses (optional)")
                delay = st.text_input("If reporting late: reason for the delay (optional)")
                secs = st.multiselect("Sections to mention", [c["section"] for c in cards], default=[top["section"]])
                lang_choice = st.radio("Language", ["English + Urdu", "English", "Urdu"], horizontal=True)
                make = st.form_submit_button("Create application", type="primary")
            if make:
                if not valid_cnic(cnic):
                    st.error("CNIC should look like 35202-1234567-8 (or leave it empty).")
                else:
                    details = FIRDetails(name=name, relation=relation, cnic=cnic, address=address, phone=phone,
                                         police_station=ps, incident_date=when.strftime("%d-%m-%Y") if when else "",
                                         incident_time=at, place=place, accused=accused, property_lost=prop,
                                         witnesses=wit, delay_reason=delay, description=text, sections=secs)
                    code = {"English + Urdu": "both", "English": "en", "Urdu": "ur"}[lang_choice]
                    doc = draft(details, code)
                    st.session_state["complaint"] = (draft(details, "en") if code in ("both", "en") else None,
                                                     draft(details, "ur") if code in ("both", "ur") else None)
                    st.text_area("Your application", doc, height=340)
                    st.download_button("⬇️ Download application (.txt)", doc.encode("utf-8"),
                                       file_name="Police_application.txt", mime="text/plain")
                    st.caption("Print, sign and take it with a copy of your CNIC to the police station. "
                               "Keep a photo of the signed copy. It is also added to the PDF report below.")

        # -------------------------------------------------------- what to do now
        st.markdown("### What to do now")
        guide = res["guide"]
        cog = guide.get("first_section_cognizable")
        tab_steps, tab_type = st.tabs(["Steps", "For this type of incident"])
        with tab_steps:
            for i, (title, body) in enumerate(steps_for(cog), 1):
                st.markdown(f"**{i}. {title}.** {body}")
        with tab_type:
            if guide["categories"]:
                for _, title, tips in guide["categories"]:
                    st.markdown(f"**{title}**\n" + "\n".join(f"- {t}" for t in tips))
            else:
                st.write("No specific tips for this description.")
        st.caption("📞 Helplines for your province are in the sidebar.")

        # -------------------------------------------------------- PDF
        st.write("")
        try:
            from src.pdf_export import build_pdf
            comp_en, comp_ur = st.session_state.get("complaint", (None, None))
            pdf = build_pdf(text, res, comp_en, comp_ur, helplines_for(ui.current_province()))
            with st.container(key="pdf_dl"):
                st.download_button("⬇️ Download my PDF report" + (" (with my application)" if comp_en or comp_ur
                                                                    else ""),
                                   pdf, file_name="incident_report.pdf", mime="application/pdf", width="stretch")
        except ImportError:
            st.caption("PDF export needs `pip install fpdf2 uharfbuzz arabic-reshaper python-bidi`.")

        # -------------------------------------------------------- feedback (protected against bad input)
        ui.rule()
        st.markdown("#### Was this helpful?")
        sent = st.session_state.setdefault("feedback_count", 0)
        rating = st.feedback("thumbs", key=f"thumbs_{hash(text)}")
        if rating is not None and not st.session_state.get(f"rated_{hash(text)}") and sent < MAX_FEEDBACK_PER_SESSION:
            rec = feedback.make_record("helpful" if rating == 1 else "not helpful", [c["section"] for c in cards],
                                       [], "anonymous", "", text, False, "tfidf_lr", status, kind="rating")
            feedback.save_csv(rec)
            st.session_state[f"rated_{hash(text)}"] = True
            st.session_state["feedback_count"] = sent + 1
            st.caption("Thanks, noted.")

        with st.expander("⚖️ Are you a lawyer or law student? Report a legal error"):
            st.caption("Feedback **never changes the model automatically**. Each correction is checked by the team: "
                       "we verify your credential and the PPC / CrPC text first. Only verified corrections can ever "
                       "be used to improve the model.")
            if st.session_state["feedback_count"] >= MAX_FEEDBACK_PER_SESSION:
                st.info("Thank you, we have received your feedback for this session.")
            else:
                labels = json.load(open(os.path.join(ui.PROJECT_ROOT, "src", "labels.json"), encoding="utf-8"))
                with st.form("expert_form", clear_on_submit=False):
                    e1, e2 = st.columns(2)
                    role = e1.selectbox("I am a", ["Advocate", "Law student", "Law graduate"], index=None,
                                        placeholder="Choose...")
                    who = e2.text_input("Full name")
                    cred = e1.text_input("Bar Council licence / enrolment no., or university + roll no.")
                    contact = e2.text_input("Email or phone (so we can verify)")
                    verdict = st.radio("The result was", ["Correct", "Partly correct", "Wrong"], horizontal=True)
                    correct = st.multiselect("Which section(s) are correct?",
                                             [s for s in labels if s != "307"],
                                             format_func=lambda s: f"{s} · {labels[s]['title'][:45]}")
                    reason = st.text_area("Legal reason (which element is missing or wrong?)", height=90)
                    consent = st.checkbox("The incident text may be stored anonymously with my correction")
                    send = st.form_submit_button("Send for review", type="primary")
                if send:
                    problems = feedback.valid_expert(role.lower() if role else "", who, cred, reason, correct)
                    if problems:
                        st.error("\n".join(f"- {p}" for p in problems))
                    else:
                        rec = feedback.make_record(verdict.lower(), [c["section"] for c in cards], correct,
                                                   role.lower(), reason, text, consent, "tfidf_lr", status,
                                                   kind="expert", name=who, credential=cred, contact=contact)
                        try:
                            secrets = dict(st.secrets)
                        except Exception:  # noqa: BLE001 (no secrets file configured)
                            secrets = {}
                        feedback.submit(rec, secrets)
                        st.session_state["feedback_count"] += 1
                        st.success("Thank you. Your correction is saved as **unverified** until a team member checks "
                                   "your credential and the law.")

ui.footer_disclaimer()
