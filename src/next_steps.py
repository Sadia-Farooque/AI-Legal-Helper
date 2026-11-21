"""Task A8: "What should I do now?" guide shown with every analysis.

Content is deliberately conservative: it explains procedure (CrPC) and evidence, never predicts an
outcome. Each item is tied to a statutory provision or an official source (see data/lookup/helplines.csv).
`python -m src.next_steps` regenerates docs/next_steps.md from this file so the doc and app never drift.
"""

import csv
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HELPLINES_CSV = os.path.join(PROJECT_ROOT, "data", "lookup", "helplines.csv")

CATEGORY_OF = {
    **{s: "violence" for s in ["302", "319", "324", "337-A", "337-F"]},
    **{s: "liberty" for s in ["339", "340", "363", "365", "365-A"]},
    **{s: "women" for s in ["354", "354A", "509"]},
    **{s: "property" for s in ["379", "380", "382", "392", "395", "403", "411"]},
    **{s: "money" for s in ["384", "406", "420", "489-F"]},
    **{s: "land" for s in ["441", "447", "448"]},
    **{s: "words" for s in ["500", "506"]},
}

CATEGORY_TITLE = {
    "violence": "Injury or death", "liberty": "Restraint, confinement or kidnapping",
    "women": "Harassment or assault on a woman", "property": "Theft, robbery or stolen property",
    "money": "Fraud, extortion or cheque", "land": "Trespass on land or house",
    "words": "Threats or defamation",
}

CATEGORY_TIPS = {
    "violence": [
        "If someone is injured, call **1122** (ambulance) or **15**.",
        "Get a **medico-legal examination (MLC)** at a government hospital as soon as possible; the injury report is key evidence. Keep every medical paper.",
        "Photograph the injuries the same day and again after a few days.",
        "Do not wash or throw away blood-stained clothes or the weapon/object used; hand them to the police.",
    ],
    "liberty": [
        "Kidnapping or a missing child: call **15** immediately. For children also call **1121**.",
        "Write down vehicle numbers, phone numbers that called you, and the time of every call.",
        "If money is demanded, inform the police before paying; keep every message or recording.",
    ],
    "women": [
        "Women's helpline (Punjab): **1043**; free legal advice anywhere in Pakistan: **1099**.",
        "Write down date, time, place and words/gestures used; names of witnesses.",
        "Harassment at the workplace can also go to the workplace inquiry committee or the Ombudsperson under the Protection against Harassment of Women at the Workplace Act 2010.",
        "Online messages or pictures: take screenshots with the account name and date, then report to **NCCIA 1799**.",
    ],
    "property": [
        "List what was taken with serial numbers, IMEI (phones), receipts and photos.",
        "Ask nearby shops/houses for **CCTV footage quickly**; many systems overwrite within days.",
        "If you later see your property with someone else, do not confront them; tell the police.",
    ],
    "money": [
        "Keep every receipt, bank transfer, JazzCash/Easypaisa record, agreement and chat.",
        "Bank/online fraud: call your bank immediately to block the account or card, then report to **NCCIA 1799**.",
        "Bounced cheque: keep the **original cheque and the bank's return memo**; a lawyer can also advise on civil recovery of the money.",
        "Threats to force payment (bhatta): do not keep paying silently; report to **15** and keep the messages.",
    ],
    "land": [
        "Keep ownership papers (registry, fard, allotment letter, rent agreement) and photos of the intrusion.",
        "Illegal occupation of land can also be raised before the court under the Illegal Dispossession Act 2005; ask a lawyer.",
        "Do not use force to remove trespassers yourself; it can create a case against you.",
    ],
    "words": [
        "Save threatening messages, call recordings and voice notes; write down who heard spoken threats.",
        "Threats to kill or cause serious harm are serious: report to **15**.",
        "Defamation online may also fall under PECA 2016; report online material to **NCCIA 1799**.",
    ],
}

GENERAL_STEPS = [
    ("If you are in danger right now", "Call **15** (police) or **1122** (ambulance). Your safety comes first."),
    ("Cognizable offence: register an FIR",
     "Go to the police station of the area where it happened and tell them what happened (spoken or written). "
     "For a cognizable offence the police must write it down as an FIR (s.154 CrPC). Check that names, time, place "
     "and witnesses are correct before signing, and ask for your free copy of the FIR."),
    ("Non-cognizable offence: different route",
     "For a non-cognizable offence the police record the information in a register and refer you to a Magistrate "
     "(s.155 CrPC); they cannot investigate without the Magistrate's order. You can also file a complaint directly "
     "before a Magistrate (s.200 CrPC), usually through a lawyer."),
    ("If the police refuse to register your FIR",
     "1) Approach senior police officers (SP / DPO); in Punjab call the IGP Complaint Centre **1787**. "
     "2) File an application under **s.22-A(6) CrPC** before the Sessions Judge / Additional Sessions Judge acting "
     "as ex-officio Justice of Peace, who can direct the police to act."),
    ("Keep evidence", "Photos, videos, screenshots, medical papers, receipts, names and numbers of witnesses. "
     "Keep originals safe and give the police copies."),
    ("Get free legal advice", "Call **1099** (Ministry of Human Rights, toll-free). For bail, court cases or serious "
     "offences, speak to a lawyer."),
]


def helplines():
    with open(HELPLINES_CSV, "r", encoding="utf-8") as f:
        return {r["key"]: r for r in csv.DictReader(f)}


def guidance(sections, lookup=None):
    """Return the guide for the predicted sections: categories (in rank order), tips, and FIR route."""
    cats = []
    for s in sections:
        c = CATEGORY_OF.get(s)
        if c and c not in cats:
            cats.append(c)
    cognizable = None
    if lookup:
        flags = [str(lookup.get(s, {}).get("cognizable", "")) for s in sections[:1]]
        cognizable = not any(f.lower().startswith("non") for f in flags) if flags and flags[0] else None
    return {
        "categories": [(c, CATEGORY_TITLE[c], CATEGORY_TIPS[c]) for c in cats],
        "first_section_cognizable": cognizable,
        "general": GENERAL_STEPS,
    }


def to_markdown():
    hl = helplines()
    L = ["# Next Steps Guide (Task A8)", "",
         "Shown in the Incident Analyzer after every analysis. Generated from `src/next_steps.py` "
         "(`python -m src.next_steps`). This is general legal information, not legal advice.", "",
         "## General steps", ""]
    for i, (t, body) in enumerate(GENERAL_STEPS, 1):
        L.append(f"{i}. **{t}.** {body}")
    L += ["", "## Extra steps by type of incident", ""]
    for c, title in CATEGORY_TITLE.items():
        secs = ", ".join(s for s, cc in CATEGORY_OF.items() if cc == c)
        L += [f"### {title} ({secs})", ""] + [f"- {t}" for t in CATEGORY_TIPS[c]] + [""]
    L += ["## Helplines (each checked against its source)", "",
          "| Number | Service | Area | Use for | Source | Checked |", "|---|---|---|---|---|---|"]
    for r in hl.values():
        L.append(f"| **{r['number']}** | {r['name']} | {r['area']} | {r['use_for']} | "
                 f"[{r['source']}]({r['source_url']}) | {r['date_checked']} |")
    L += ["", "Legal basis: Code of Criminal Procedure 1898, ss.154, 155, 200 and 22-A(6) "
          "(ex-officio Justice of Peace may direct the police on non-registration of an FIR). "
          "Numbers change: two commonly shared numbers were found outdated during this check "
          "(Punjab Police complaints 8787 → **1787**; FIA cybercrime 1991/9911 → **NCCIA 1799**).", ""]
    return "\n".join(L)


if __name__ == "__main__":
    out = os.path.join(PROJECT_ROOT, "docs", "next_steps.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(to_markdown())
    print("->", os.path.relpath(out, PROJECT_ROOT))
