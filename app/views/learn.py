"""Student Corner: learn the 30 offences topic by topic, compare look-alike sections, quiz yourself and search
Supreme Court case law. Uses the Track B content (labels, CrPC Schedule II lookup, section summaries, confusable
groups, quiz bank, case index) through a single guided page instead of four separate ones.
"""

import html
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

import legal_ui as ui  # noqa: E402
from src.next_steps import CATEGORY_OF  # noqa: E402

ROOT = ui.PROJECT_ROOT

TOPICS = {   # key -> (label, one-line intro)
    "violence": ("🩸 Body & life", "Killing, attempts to kill and causing hurt."),
    "liberty": ("⛓️ Liberty & kidnapping", "Stopping, confining, kidnapping or abducting a person."),
    "women": ("👩 Protection of women", "Assault, stripping and insulting modesty; sexual harassment."),
    "property": ("🏠 Theft & robbery", "Taking property: theft, robbery, dacoity and stolen goods."),
    "money": ("💰 Fraud, cheques & extortion", "Cheating, breach of trust, bounced cheques and bhatta."),
    "land": ("🧱 Land & trespass", "Entering or staying on someone's land or house unlawfully."),
    "words": ("🗣️ Threats & defamation", "Threatening someone or harming their reputation."),
}
TOPIC_OF = dict(CATEGORY_OF)
TOPIC_OF.setdefault("307", "violence")


@st.cache_data
def load():
    def j(*p, default=None):
        path = os.path.join(ROOT, *p)
        return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default
    labels = j("src", "labels.json", default={})
    lookup = pd.read_csv(os.path.join(ROOT, "data", "lookup", "ppc_lookup.csv"), dtype=str).set_index("section")
    content = j("data", "content", "sections.json", default={})
    groups = j("data", "content", "confusable_groups.json", default=[])
    quiz = j("data", "content", "quiz_bank.json", default=[])
    cases = j("models", "case_metadata.json", default=[])
    by_sec = {}
    for c in cases:
        for s in c.get("sections", []):
            by_sec.setdefault(str(s).strip(), []).append(c)
    return labels, lookup.to_dict("index"), content, groups, quiz, by_sec


labels, lookup, content, groups, quiz_bank, cases_by_sec = load()
SECTIONS = [s for s in labels if s != "307"]   # 307 is not an offence a citizen can report in the PPC (D1)


def goto(mode, **state):
    st.session_state["learn_mode"] = mode
    st.session_state.update(state)


def facts(sec):
    r = lookup.get(sec, {})
    cog = str(r.get("cognizable", ""))
    bail = str(r.get("bailable", ""))
    comp = str(r.get("compoundable", ""))
    b = lambda t, k: f'<span class="badge b-{k}">{html.escape(t)}</span>'  # noqa: E731
    return ((b("Cognizable", "good") if cog.lower().startswith("cognizable") else b("Non-cognizable", "mid")) +
            (b("Non-bailable", "bad") if bail.lower().startswith("non") else b("Bailable", "good")) +
            (b("Non-compoundable", "neutral") if comp.lower().startswith("non") else b("Compoundable", "neutral")))


def section_detail(sec):
    lab, c, r = labels.get(sec, {}), content.get(sec, {}), lookup.get(sec, {})
    st.markdown(f'<div class="sec-no">PPC {sec}</div>', unsafe_allow_html=True)
    st.markdown(f"#### {lab.get('title', '')}")
    if lab.get("citizen_term"):
        st.caption(f"In everyday words: {lab['citizen_term']}")
    st.markdown(facts(sec), unsafe_allow_html=True)
    with st.expander("Read more"):
        st.markdown(c.get("summary", r.get("meaning", "")))
        if c.get("elements"):
            st.markdown("**What the prosecution must prove**\n" + "\n".join(f"- {e}" for e in c["elements"]))
        if c.get("example_scenarios"):
            st.markdown("**Example**\n\n_" + c["example_scenarios"][0] + "_")
        st.markdown(f"**Punishment:** {r.get('punishment', '-')}  \n**Tried by:** {r.get('court', '-')}")
        if lab.get("confusable_with"):
            st.caption("Often confused with: " + ", ".join(f"PPC {x}" for x in lab["confusable_with"]))
        n = len(cases_by_sec.get(sec, []))
        if n:
            st.caption(f"🏛️ {n} Supreme Court judgment(s) in our collection cite this section (see Case law).")
        src = r.get("source")
        if src:
            st.caption(f"Source: {src}")


# ================================================================ page
ui.page_header("Student Corner", "Learn the offences people report most, then test yourself.",
               icon='<span style="font-size:2.4rem">🎓</span>')

MODES = ["📚 Learn", "⚖️ Look-alikes", "📝 Quiz", "🏛️ Case law"]
st.session_state.setdefault("learn_mode", MODES[0])
mode = st.segmented_control("Section", MODES, key="learn_mode", label_visibility="collapsed")
mode = mode or MODES[0]
st.write("")

# ---------------------------------------------------------------- Learn
if mode == MODES[0]:
    jump = st.selectbox("Jump to a section", SECTIONS, index=None, placeholder="Search by number or name, e.g. 392",
                        format_func=lambda s: f"PPC {s} · {labels[s]['title']}")
    if jump:
        with st.container(border=True):
            section_detail(jump)
        ui.rule()

    st.session_state.setdefault("topic", "property")
    topic = st.pills("Choose a topic", list(TOPICS), key="topic", format_func=lambda k: TOPICS[k][0])
    topic = topic or "property"
    st.markdown(f"**{TOPICS[topic][0]}**: {TOPICS[topic][1]}")
    secs = [s for s in SECTIONS if TOPIC_OF.get(s) == topic]
    cols = st.columns(2)
    for i, s in enumerate(secs):
        with cols[i % 2], st.container(border=True):
            section_detail(s)

    b1, b2, _ = st.columns([1, 1, 1.4])
    b1.button("📝 Quiz me on this topic", type="primary", width="stretch",
              on_click=goto, args=(MODES[2],), kwargs={"quiz_topic": topic, "quiz": None})
    b2.button("⚖️ Compare look-alikes", width="stretch", on_click=goto, args=(MODES[1],),
              kwargs={"alike_topic": topic})

# ---------------------------------------------------------------- Look-alikes
elif mode == MODES[1]:
    st.markdown("Sections that students and even police often mix up, and the one fact that separates them.")
    want = st.session_state.get("alike_topic")
    shown = [g for g in groups if not want or any(TOPIC_OF.get(s) == want for s in g["sections"])] or groups
    if want:
        f1, f2 = st.columns([3, 1])
        f1.caption(f"Showing groups for **{TOPICS[want][0]}**.")
        f2.button("Show all", on_click=lambda: st.session_state.update(alike_topic=None))
    for g in shown:
        with st.container(border=True):
            st.markdown(f"#### {g['group_name'].split(':', 1)[-1].strip()}")
            st.markdown(f"**Key difference:** {g['distinction_summary']}")
            rows = [{"Section": f"PPC {s}", "Name": labels.get(s, {}).get("title", ""),
                     "What makes it this offence": g.get("key_differentiators", {}).get(s, "")}
                    for s in g["sections"]]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            st.markdown(f'<div class="cond">💡 <b>Common mistake:</b> {html.escape(g["critical_student_pitfall"])}'
                        '</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- Quiz
elif mode == MODES[2]:
    q = st.session_state.get("quiz")

    if not q:                                            # ---- setup
        with st.container(border=True):
            st.markdown("#### Set up your quiz")
            topic_opts = ["all"] + list(TOPICS)
            default_topic = st.session_state.get("quiz_topic") or "all"
            c1, c2 = st.columns(2)
            t = c1.selectbox("Topic", topic_opts, index=topic_opts.index(default_topic),
                             format_func=lambda k: "All topics" if k == "all" else TOPICS[k][0])
            d = c2.selectbox("Difficulty", ["any", "easy", "medium", "hard"],
                             format_func=lambda k: {"any": "Any", "easy": "🟢 Easy", "medium": "🟡 Medium",
                                                    "hard": "🔴 Hard"}[k])
            pool = [x for x in quiz_bank if (t == "all" or TOPIC_OF.get(x["target_section"]) == t)
                    and (d == "any" or x["difficulty"] == d)]
            sizes = [n for n in (5, 10, 15, 20) if n <= len(pool)] or ([len(pool)] if pool else [])
            if not pool:
                st.warning("No questions for this choice. Try another topic or difficulty.")
            else:
                n = st.pills("Number of questions", sizes, default=sizes[min(1, len(sizes) - 1)])
                st.caption(f"{len(pool)} questions available for this choice.")
                if st.button("Start quiz", type="primary", disabled=not n):
                    st.session_state["quiz"] = {"ids": [x["id"] for x in random.sample(pool, n)], "i": 0,
                                                "answers": {}, "topic": t}
                    st.rerun()

    else:
        bank = {x["id"]: x for x in quiz_bank}
        ids, i = q["ids"], q["i"]

        if i < len(ids):                                 # ---- running
            item = bank[ids[i]]
            top_l, top_r = st.columns([3, 1], vertical_alignment="center")
            top_l.markdown(f"**Question {i + 1} of {len(ids)}**")
            show = top_r.toggle("Show score", key="show_score")
            if show:
                done = q["answers"]
                right = sum(1 for k, v in done.items() if v == bank[k]["correct_index"])
                top_r.caption(f"{right} / {len(done)} correct so far")
            st.progress(i / len(ids))
            with st.container(border=True):
                st.markdown(f"_{item['scenario']}_")
                answered = item["id"] in q["answers"]
                pick = st.radio("Which PPC section applies?", range(len(item["options"])),
                                format_func=lambda k: item["options"][k], index=q["answers"].get(item["id"]),
                                disabled=answered, key=f"quiz_{item['id']}")
            if not answered:
                if st.button("Check answer", type="primary", disabled=pick is None):
                    q["answers"][item["id"]] = pick
                    st.rerun()
            else:
                ok = q["answers"][item["id"]] == item["correct_index"]
                (st.success if ok else st.error)(
                    ("✅ Correct!" if ok else f"❌ Not quite. Correct answer: **{item['options'][item['correct_index']]}**"))
                st.markdown(f"**Why:** {item['explanation']}")
                last = i + 1 == len(ids)
                if st.button("See my results" if last else "Next question →", type="primary"):
                    q["i"] += 1
                    st.rerun()
            if st.button("⏹ End quiz", key="quit", help="Stop now and go back to quiz setup"):
                st.session_state["quiz"] = None
                st.rerun()

        else:                                            # ---- results (always shown at the end)
            right = [k for k in ids if q["answers"].get(k) == bank[k]["correct_index"]]
            pct = len(right) / len(ids)
            verdict = ("Excellent! 🏆" if pct >= .9 else "Good work 👍" if pct >= .7 else
                       "Getting there 📖" if pct >= .5 else "Keep practising 💪")
            with st.container(border=True):
                st.markdown(f"### Your result: {len(right)} / {len(ids)} ({pct:.0%})")
                st.markdown(f"**{verdict}**")
                st.progress(pct)
                per = {}
                for k in ids:
                    tk = TOPIC_OF.get(bank[k]["target_section"], "violence")
                    a, b = per.get(tk, (0, 0))
                    per[tk] = (a + (k in right), b + 1)
                st.dataframe(pd.DataFrame([{"Topic": TOPICS[tk][0], "Correct": f"{a} / {b}",
                                            "Score": f"{a / b:.0%}"} for tk, (a, b) in per.items()]),
                             hide_index=True, width="stretch")
            wrong = [k for k in ids if k not in right]
            if wrong:
                st.markdown("#### Review your mistakes")
                for k in wrong:
                    item = bank[k]
                    with st.expander(f"PPC {item['target_section']}: {item['scenario'][:90]}..."):
                        st.markdown(f"_{item['scenario']}_")
                        st.markdown(f"Your answer: {item['options'][q['answers'][k]]}  \n"
                                    f"**Correct: {item['options'][item['correct_index']]}**")
                        st.markdown(item["explanation"])
            r1, r2, _ = st.columns([1, 1, 2])
            if r1.button("Retry these questions", width="stretch"):
                st.session_state["quiz"] = {"ids": ids, "i": 0, "answers": {}, "topic": q["topic"]}
                st.rerun()
            if r2.button("New quiz", type="primary", width="stretch"):
                st.session_state["quiz"] = None
                st.rerun()

# ---------------------------------------------------------------- Case law
else:
    st.markdown("Search **301 Supreme Court of Pakistan** criminal judgments by meaning, not just keywords.")
    qtext = st.text_area("Describe the facts or the legal point", height=110, key="case_q",
                         placeholder="e.g. accused fired at the complainant during a sudden quarrel over land")
    c1, c2 = st.columns([2, 1])
    sec = c1.selectbox("Only cases citing this section (optional)", SECTIONS, index=None, placeholder="Any section",
                       format_func=lambda s: f"PPC {s} · {labels[s]['title'][:40]}")
    k = c2.slider("How many cases", 1, 10, 3)
    if st.button("Search cases", type="primary") and qtext.strip():
        try:
            from src.case_finder import search_cases
            with st.spinner("Searching judgments..."):
                st.session_state["case_hits"] = search_cases(qtext, top_k=k, section_filter=sec)
        except Exception:  # noqa: BLE001
            st.session_state["case_hits"] = None
            st.warning("Case search is not available on this server (needs `sentence-transformers` and the case "
                       "index: `python src/case_finder.py --build-index`).")
    hits = st.session_state.get("case_hits")
    if hits is not None:
        if hits:
            ui.case_cards(hits, "learn")
        else:
            st.info("No matching judgments. Try different words or remove the section filter.")

ui.footer_disclaimer()
