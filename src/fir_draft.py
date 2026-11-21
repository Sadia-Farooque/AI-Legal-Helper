"""Extra 1: Written complaint for the police (darkhwast) generator, English + Urdu.

In Pakistan the police write the FIR itself (s.154 CrPC); what a citizen brings to the police station is a
written application to the SHO asking for an FIR to be registered; police often base the FIR on it.
This module fills that application from a fixed template: the user's own description, the details they enter,
and the sections the Incident Analyzer predicted. It is a template, not machine learning: the model only
supplies the suggested sections.

Deliberate choices
- Sections are presented as "may attract", never as a legal conclusion: the police and courts decide.
- The user's own description is kept word for word (it is their statement).
- Missing details become blank lines to fill by hand, so a half-filled form is still usable.
- Nothing is stored: the draft is built in memory and handed to the user.
"""

import re
from dataclasses import dataclass, field
from datetime import date

CNIC_RE = re.compile(r"^\d{5}-\d{7}-\d$")
BLANK = "________________"


@dataclass
class FIRDetails:
    name: str = ""
    relation: str = ""          # father's / husband's name
    cnic: str = ""
    address: str = ""
    phone: str = ""
    police_station: str = ""
    incident_date: str = ""
    incident_time: str = ""
    place: str = ""
    accused: str = ""           # names / descriptions; empty = unknown
    property_lost: str = ""
    witnesses: str = ""
    delay_reason: str = ""      # why the report is made late (courts scrutinise FIR delay)
    description: str = ""
    sections: list = field(default_factory=list)


def valid_cnic(cnic):
    return not cnic or bool(CNIC_RE.match(cnic.strip()))


def _v(x):
    return x.strip() if x and x.strip() else BLANK


def _sections_en(secs):
    return ", ".join(f"{s}" for s in secs) + " PPC" if secs else ""


def draft_english(d: FIRDetails, today=None):
    today = today or date.today().strftime("%d-%m-%Y")
    accused = d.accused.strip() or "unknown person(s), whom I can identify if seen again"
    lines = [
        "To,",
        f"The Station House Officer (SHO),",
        f"Police Station {_v(d.police_station)}",
        "",
        "Subject: Application for registration of FIR under Section 154 Cr.P.C.",
        "",
        "Respected Sir/Madam,",
        "",
        f"I, {_v(d.name)}, son/daughter/wife of {_v(d.relation)}, CNIC No. {_v(d.cnic)}, resident of "
        f"{_v(d.address)}, mobile No. {_v(d.phone)}, respectfully state as follows:",
        "",
        f"1. On {_v(d.incident_date)} at about {_v(d.incident_time)}, at {_v(d.place)}, the following incident took place:",
        "",
        f"   {d.description.strip() or BLANK}",
        "",
        f"2. The accused: {accused}.",
    ]
    n = 3
    if d.property_lost.strip():
        lines.append(f"{n}. Property taken / loss caused: {d.property_lost.strip()}."); n += 1
    if d.witnesses.strip():
        lines.append(f"{n}. Witnesses: {d.witnesses.strip()}."); n += 1
    if d.delay_reason.strip():
        lines.append(f"{n}. Reason for reporting late: {d.delay_reason.strip()}."); n += 1
    if d.sections:
        lines.append(f"{n}. In my understanding, these facts may attract Section(s) {_sections_en(d.sections)}; "
                     "the final determination rests with the police and the court."); n += 1
    lines += [
        "",
        "It is therefore requested that an FIR be registered against the accused under the relevant provisions "
        "of law, that legal action be taken, and that a copy of the FIR be provided to me free of cost.",
        "",
        "Yours faithfully,",
        "",
        f"Name: {_v(d.name)}",
        "Signature / thumb impression: ________________",
        f"Date: {today}",
    ]
    return "\n".join(lines)


def draft_urdu(d: FIRDetails, today=None):
    today = today or date.today().strftime("%d-%m-%Y")
    accused = d.accused.strip() or "نامعلوم شخص/اشخاص، جنہیں دوبارہ دیکھنے پر شناخت کر سکتا/سکتی ہوں"
    lines = [
        f"بخدمت جناب ایس ایچ او صاحب، تھانہ {_v(d.police_station)}",
        "",
        "عنوان: درخواست برائے اندراج مقدمہ (ایف آئی آر) زیر دفعہ 154 ضابطہ فوجداری",
        "",
        "جناب عالی!",
        "",
        f"گزارش ہے کہ سائل/سائلہ {_v(d.name)} ولد/بنت/زوجہ {_v(d.relation)}، شناختی کارڈ نمبر {_v(d.cnic)}، "
        f"ساکن {_v(d.address)}، موبائل نمبر {_v(d.phone)} ہے۔",
        "",
        f"1۔ مورخہ {_v(d.incident_date)} بوقت تقریباً {_v(d.incident_time)}، بمقام {_v(d.place)} درج ذیل واقعہ پیش آیا:",
        "",
        f"   (بیان سائل کے اپنے الفاظ میں) {d.description.strip() or BLANK}",
        "",
        f"2۔ ملزم/ملزمان: {accused}۔",
    ]
    n = 3
    if d.property_lost.strip():
        lines.append(f"{n}۔ چھینا/چوری شدہ سامان یا نقصان: {d.property_lost.strip()}۔"); n += 1
    if d.witnesses.strip():
        lines.append(f"{n}۔ گواہان: {d.witnesses.strip()}۔"); n += 1
    if d.delay_reason.strip():
        lines.append(f"{n}۔ تاخیر سے رپورٹ کی وجہ: {d.delay_reason.strip()}۔"); n += 1
    if d.sections:
        lines.append(f"{n}۔ میری دانست میں یہ واقعہ تعزیرات پاکستان کی دفعہ/دفعات {', '.join(d.sections)} کے تحت آ سکتا ہے؛ "
                     "حتمی فیصلہ پولیس اور عدالت کا ہے۔"); n += 1
    lines += [
        "",
        "لہٰذا استدعا ہے کہ ملزمان کے خلاف قانون کے مطابق مقدمہ درج کر کے کارروائی کی جائے اور ایف آئی آر کی نقل "
        "سائل/سائلہ کو مفت فراہم کی جائے۔",
        "",
        "العارض",
        "",
        f"نام: {_v(d.name)}",
        "دستخط / انگوٹھا: ________________",
        f"تاریخ: {today}",
    ]
    return "\n".join(lines)


def draft(d: FIRDetails, language="both", today=None):
    if language == "en":
        return draft_english(d, today)
    if language == "ur":
        return draft_urdu(d, today)
    return draft_english(d, today) + "\n\n" + "=" * 60 + "\n\n" + draft_urdu(d, today)
