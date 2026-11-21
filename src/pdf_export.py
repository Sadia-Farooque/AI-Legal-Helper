"""Extra 2: PDF export of the analysis (and the police complaint, if generated).

English text uses DejaVu Sans (bundled with matplotlib, full Unicode Latin). The Urdu complaint needs a font
with Urdu letters (ہ ے ۔) and right-to-left text shaping (fpdf2 + uharfbuzz). The first suitable font found
is used: assets/fonts/*.ttf, then common Windows fonts (Tahoma, Arial, Segoe UI, Times New Roman). If none
is found, the PDF says so and the Urdu complaint remains available in the .txt download.

Urdu layout: letters are joined with arabic-reshaper and the mixed Urdu/English line is put in visual order with
python-bidi (Unicode bidirectional algorithm). Runs of Latin letters and digits (names, CNIC, dates, phone
numbers) are wrapped in left-to-right embedding marks so they are never reversed. (First version used the
shaping engine with a forced RTL direction; testing showed split words and reversed CNIC numbers.)

Requires: pip install fpdf2 arabic-reshaper python-bidi
"""

import glob
import os
import re
from datetime import date

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
URDU_TEST = "ہےۓ۔ٹڈڑں"
CANDIDATES = (sorted(glob.glob(os.path.join(PROJECT_ROOT, "assets", "fonts", "*.ttf"))) +
              [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", f)
               for f in ("tahoma.ttf", "arial.ttf", "segoeui.ttf", "times.ttf")] +
              ["/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"])


def latin_font():
    import matplotlib
    return os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf", "DejaVuSans.ttf")


def urdu_font():
    from fontTools.ttLib import TTFont
    for p in CANDIDATES:
        if os.path.exists(p):
            try:
                cmap = TTFont(p, fontNumber=0).getBestCmap()
                if all(ord(c) in cmap for c in URDU_TEST):
                    return p
            except Exception:  # noqa: BLE001
                continue
    return None


_LTR_RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .,:/\-]*[A-Za-z0-9]|[A-Za-z0-9]")


def urdu_visual(line):
    """Return an Urdu line in visual (display) order with joined letters; LTR runs kept intact."""
    import arabic_reshaper
    from bidi.algorithm import get_display
    protected = _LTR_RUN.sub(lambda m: "\u202a" + m.group(0) + "\u202c", line)
    return get_display(arabic_reshaper.reshape(protected))


def wrap_rtl(pdf, line, width):
    """Wrap a logical Urdu line into display lines BEFORE bidi reordering (wrapping after reordering would put
    the start of a sentence on the second line)."""
    words, out, cur = line.split(), [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if cur and pdf.get_string_width(urdu_visual(cand)) > width:
            out.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out or [" "]


def _plain(s):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", str(s or ""))


def build_pdf(text, res, complaint_en=None, complaint_ur=None, helplines=None):
    from fpdf import FPDF
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_font("dv", fname=latin_font())
    pdf.add_page()
    W = pdf.epw

    def h(t, size=14):
        pdf.set_font("dv", size=size); pdf.multi_cell(W, 8, t, new_x="LMARGIN", new_y="NEXT"); pdf.ln(1)

    def p(t, size=10):
        pdf.set_font("dv", size=size); pdf.multi_cell(W, 5.5, _plain(t), new_x="LMARGIN", new_y="NEXT"); pdf.ln(1)

    h("Incident analysis: AI Legal Helper for Pakistan", 15)
    p(f"Date: {date.today().strftime('%d-%m-%Y')}", 9)
    p("Legal information, not legal advice. An AI model can be wrong. For an actual case, consult a lawyer "
      "or call the free legal-advice helpline 1099 (Ministry of Human Rights).", 9)
    h("What happened (as described)", 12); p(text)
    if res.get("status") == "abstain":
        h("Result", 12)
        p(f"The model was not confident enough (below {res['threshold']:.0%}) to name a section. "
          "Please consult a lawyer or call 1099.")
    elif res.get("results"):
        h("Sections that may apply", 12)
        for i, c in enumerate(res["results"], 1):
            p(f"#{i}  Section {c['section']} PPC: {c['name']}  (confidence {c['score']:.0%})", 11)
            p(f"FIR: {c['cognizable']}   |   Bail: {c['bailable']}   |   Settlement: {c['compoundable']}", 9)
            if c.get("punishment"):
                p(f"Punishment: {c['punishment']}", 9)
            if c.get("summary") or c.get("meaning"):
                p(c.get("summary") or c.get("meaning"), 9)
    g = res.get("guide") or {}
    if g.get("general"):
        h("What to do now", 12)
        for i, (t, body) in enumerate(g["general"], 1):
            p(f"{i}. {t}. {body}", 9)
    if helplines:
        h("Helplines", 12)
        for r in helplines:
            p(f"{r['number']}: {r['name']} ({r['area']})", 9)
    if complaint_en:
        pdf.add_page(); h("Written complaint for the police (English)", 13); p(complaint_en)
    if complaint_ur:
        pdf.add_page()
        uf = urdu_font()
        if uf:
            pdf.add_font("ur", fname=uf)
            pdf.set_font("ur", size=13)
            pdf.multi_cell(W, 9, urdu_visual("پولیس کے لیے تحریری درخواست"), align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.set_font("ur", size=11)
            for line in complaint_ur.split("\n"):
                if not line.strip():
                    pdf.ln(4)
                    continue
                # new_x="LMARGIN": return to the left margin after every line (bug found in testing: without it each
                # line started where the previous one ended and drifted off the page).
                for part in wrap_rtl(pdf, line, W - 2):
                    pdf.cell(W, 7.5, urdu_visual(part), align="R", new_x="LMARGIN", new_y="NEXT")
        else:
            h("Written complaint for the police (Urdu)", 13)
            p("No Urdu font was found on this computer, so the Urdu complaint is not included in the PDF. "
              "Please use the .txt download for the Urdu version.")
    return bytes(pdf.output())
