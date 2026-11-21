"""Supreme Court Judgments Regex Citation & Fact Extractor.
Processes data/raw/sc_judgments.parquet into canonical data/processed/sc_clean.csv.
Adheres to Task B3 specification.
"""

import json
import os
import re
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_PARQUET = os.path.join(PROJECT_ROOT, "data", "raw", "sc_judgments.parquet")
LABELS_JSON = os.path.join(PROJECT_ROOT, "src", "labels.json")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "sc_clean.csv")

def load_target_labels():
    with open(LABELS_JSON, "r", encoding="utf-8") as f:
        labels_dict = json.load(f)
    return set(labels_dict.keys())

def extract_case_metadata(text, raw_details):
    # Citation / Appeal number
    citation_no = ""
    if isinstance(raw_details, dict) and "id" in raw_details:
        citation_no = raw_details["id"].replace(".pdf", "").replace("_", " ")

    m_case = re.search(r'(?:CRIMINAL\s+APPEAL|JAIL\s+PETITION|CRIMINAL\s+PETITION|CIVIL\s+APPEAL)\s+(?:NO\.?|NUMBER)?\s*([0-9]+(?:\s*-\s*[A-Z])?\s*(?:OF|/)\s*[0-9]{4})', text[:1500], re.I)
    if m_case:
        citation_no = m_case.group(0).strip()

    # Case Title (e.g. Appellant VERSUS State)
    title = ""
    m_title = re.search(
        r'([A-Z][A-Za-z\s\.,\(\)]+?)\s+(?:\.{2,}|\s+)\s*(?:Appellant|Petitioner|Applicant)s?\(?s?\)?\s+(?:VERSUS|V/S|Vs\.?)\s+([A-Z][A-Za-z\s\.,\(\)]+?)\s+(?:\.{2,}|\s+)\s*(?:Respondent|The\s+State|State)',
        text[:2000],
        re.I
    )
    if m_title:
        appellant = re.sub(r'\s+', ' ', m_title.group(1)).strip()
        respondent = re.sub(r'\s+', ' ', m_title.group(2)).strip()
        if len(appellant) < 60 and len(respondent) < 60:
            title = f"{appellant} vs. {respondent}"

    if not title:
        # Fallback to first line or generic identifier
        lines = [line.strip() for line in text[:600].split("\n") if line.strip()]
        for l in lines:
            if "vs" in l.lower() or "versus" in l.lower():
                title = l[:80]
                break
        if not title:
            title = citation_no or "Supreme Court of Pakistan"

    return citation_no, title

def extract_cited_ppc_sections(text, target_labels):
    """Extracts PPC sections using high-precision regex with disambiguation against CrPC/Constitution."""
    found = set()

    # Strict CrPC disambiguation: identify procedural patterns to ignore
    # e.g. 340(2) CrPC, 497 CrPC, 154 CrPC, 417 CrPC, 345 CrPC, 439 CrPC
    crpc_mentions = set(re.findall(r'(\d{3})\s*(?:\(\d+\))?\s*(?:of\s+the\s+)?(?:Cr\.?P\.?C|Code\s+of\s+Criminal\s+Procedure)', text, re.I))

    # Pattern 1: Explicit PPC citation: "Section 302 PPC", "Sec. 392 of the Pakistan Penal Code", "s. 489-F"
    p1 = re.finditer(r'(?:sections?|secs?\.?|s\.)\s*([0-9]{3}(?:-[A-Z]+|[A-Z])?)(?:\([a-z0-9ivx]+\))?\s*(?:of\s+(?:the\s+)?)?(?:P\.?P\.?C\.?|Pakistan\s+Penal\s+Code)', text, re.I)
    for m in p1:
        sec = m.group(1).upper()
        if sec in target_labels:
            found.add(sec)

    # Pattern 2: Charge notation: "u/s 302/34", "under section 392/395", "u/s 489-F"
    p2 = re.finditer(r'(?:u/s|under\s+sections?)\s*([0-9]{3}(?:-[A-Z]+|[A-Z])?)(?:\([a-z0-9ivx]+\))?(?:[/\s,]+(?:and\s+)?([0-9]{3}(?:-[A-Z]+|[A-Z])?))*[\s,]*(?:P\.?P\.?C\.?|Pakistan\s+Penal\s+Code)?', text, re.I)
    for m in p2:
        for g in m.groups():
            if g:
                sec = g.upper().replace(' ', '')
                if sec == '354-A': sec = '354A'
                if sec == '365A': sec = '365-A'
                if sec in target_labels and sec not in crpc_mentions:
                    found.add(sec)

    # Pattern 3: Distinctive specialized sections: 489-F, 354A, 365-A, 337-A, 337-F
    p3 = re.finditer(r'\b(489-F|354-?A|365-?A|337-[AF])(?:\([a-z0-9ivx]+\))?\b', text, re.I)
    for m in p3:
        sec = m.group(1).upper().replace('-', '')
        if sec == '354A': found.add('354A')
        elif sec == '365A': found.add('365-A')
        elif '489' in sec: found.add('489-F')
        elif '337A' in sec: found.add('337-A')
        elif '337F' in sec: found.add('337-F')

    # Remove false-positive 340 if only mentioned in context of Section 340(2) CrPC
    if "340" in found and ("340" in crpc_mentions or re.search(r'340\s*\(\s*2\s*\)', text)):
        found.remove("340")

    return sorted(list(found))

def extract_factual_narrative(text):
    """Extracts the opening facts of occurrence / prosecution case summary from the first 5000 characters."""
    opening = text[:5000]

    # Look for fact markers within opening
    fact_markers = [
        r'(?:briefly\s+stated|facts\s+of\s+the\s+case\s+are|prosecution\s+case\s+is\s+that|prosecution\s+story\s+in\s+brief|incident\s+took\s+place\s+on|as\s+per\s+the\s+FIR)[,\s:]+(.+?)(?:learned\s+counsel|we\s+have\s+heard|having\s+considered|on\s+conclusion|after\s+investigation)',
        r'(?:prosecution\s+case|prosecution\s+story)[,\s:]+(.+?)(?:learned\s+counsel|we\s+have\s+heard|the\s+trial\s+court)',
    ]

    for pat in fact_markers:
        m = re.search(pat, opening, re.I | re.DOTALL)
        if m:
            fact_candidate = m.group(1).strip()
            fact_candidate = re.sub(r'\s+', ' ', fact_candidate)
            if len(fact_candidate) >= 150:
                return fact_candidate[:1000]

    # Fallback: extract paragraphs from opening
    paragraphs = [p.strip() for p in opening.split("\n\n") if p.strip()]
    narrative_parts = []
    for p in paragraphs[1:]:
        clean_p = re.sub(r'\s+', ' ', p)
        # Skip purely procedural lines
        if re.search(r'JUDGMENT|ORDER|PRESENT:|CIVIL APPEAL|CRIMINAL APPEAL', clean_p, re.I):
            continue
        narrative_parts.append(clean_p)
        if sum(len(x) for x in narrative_parts) >= 400:
            break

    fallback_text = " ".join(narrative_parts)
    if len(fallback_text) >= 150:
        return fallback_text[:1000]

    # Absolute fallback: first 600 chars cleaned
    return re.sub(r'\s+', ' ', opening[:800]).strip()

def run_extraction():
    print(f"Loading raw dataset: {RAW_PARQUET}")
    df = pd.read_parquet(RAW_PARQUET)
    target_labels = load_target_labels()
    print(f"Loaded {len(target_labels)} target PPC section labels.")

    records = []
    skipped_no_criminal = 0
    skipped_no_sections = 0

    for idx, row in df.iterrows():
        text = str(row["text"])
        details = row["case_details"]

        # Fast filter: skip obvious pure civil/service cases without criminal context
        is_criminal = bool(re.search(r'CRIMINAL|JAIL\s+PETITION|P\.?P\.?C|Pakistan\s+Penal\s+Code|FIR\s+No|police\s+station|sessions\s+judge|conviction|sentence', text, re.I))
        if not is_criminal:
            skipped_no_criminal += 1
            continue

        cited_sections = extract_cited_ppc_sections(text, target_labels)
        if not cited_sections:
            skipped_no_sections += 1
            continue

        citation_no, title = extract_case_metadata(text, details)
        facts = extract_factual_narrative(text)

        if len(facts) < 100:
            continue

        primary = cited_sections[0]

        # 80/20 train/val split based on case index hash
        split = "train" if (idx % 5 != 0) else "val"

        record = {
            "id": f"sc_{len(records)+1:04d}",
            "text": facts,
            "full_text": text[:5000], # truncated full text for reader modal
            "sections": json.dumps(cited_sections),
            "primary_section": primary,
            "language": "en",
            "source": "sc",
            "split": split,
            "case_title": title,
            "citation_number": citation_no,
        }
        records.append(record)

    out_df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    out_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"\nExtraction Complete!")
    print(f"Total raw judgments processed: {len(df)}")
    print(f"Skipped non-criminal / civil disputes: {skipped_no_criminal}")
    print(f"Skipped without target PPC sections: {skipped_no_sections}")
    print(f"Successfully extracted criminal judgments: {len(out_df)}")
    print(f"Saved to: {OUTPUT_CSV}")

    # Display section distribution
    print("\n--- Extracted Section Counts ---")
    sec_counts = {}
    for secs_str in out_df["sections"]:
        secs = json.loads(secs_str)
        for s in secs:
            sec_counts[s] = sec_counts.get(s, 0) + 1

    for s, c in sorted(sec_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  PPC {s:7}: {c:3d} cases")

    return out_df

if __name__ == "__main__":
    run_extraction()
