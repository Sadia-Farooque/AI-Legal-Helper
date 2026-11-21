# Supreme Court Judgments Dataset Exploration Report

**Source:** Hugging Face repository `Ibtehaj10/supreme-court-of-pak-judgments`  
**File Location:** `data/raw/sc_judgments.parquet`  
**Total Records:** 1,414 Supreme Court judgments  
**Dataset Columns:** `text, case_details, embeddings, citation_number`  

---

## 1. Summary Statistics

| Metric | Characters per Document | Words per Document |
| :--- | :---: | :---: |
| **Minimum** | 2 | 0 |
| **Median** | 9,398 | 1,514 |
| **Mean** | 21,330 | 3,443 |
| **Maximum** | 632,725 | 103,121 |

*Observations:* Supreme Court judgments are extensive legal texts averaging ~1,500 words per case, with complex appellate rulings extending up to 100,000+ words.

---

## 2. Jurisdiction & Case Type Breakdown

| Jurisdiction Category | Regex Indicator | Document Count | Share (%) |
| :--- | :--- | :---: | :---: |
| **Criminal Appeals** | `CRIMINAL APPEAL` | 249 | 17.6% |
| **Jail Petitions** | `JAIL PETITION` | 99 | 7.0% |
| **Criminal Petitions** | `CRIMINAL PETITION` | 342 | 24.2% |
| **Civil Appeals** | `CIVIL APPEAL` | 382 | 27.0% |
| **Civil Petitions** | `CIVIL PETITION` | 353 | 25.0% |
| **Constitution Petitions** | `CONSTITUTION PETITION` | 261 | 18.5% |

Total cases citing **Pakistan Penal Code (PPC)**: **387** (27.4% of total apex judgments).

---

## 3. Structural Characteristics of Pakistani Judgments

A typical Supreme Court judgment follows a clear 4-part legal format:
1. **Header / Coram:** Bench composition (`PRESENT: Mr. Justice...`), Case Registry Number (`Criminal Appeal No. X of 20XX`), and Party Names (`Appellant VERSUS The State`).
2. **Procedural Recital:** Origin of the appeal (e.g. *Against the judgment dated 12.05.2018 passed by Lahore High Court*).
3. **Factual Narrative (Facts of Occurrence):** Statement of the prosecution case, FIR lodging details, and summary of the crime. This narrative forms the primary training corpus for Task B4 and Task B5.
4. **Appellate Discussion & Order:** Evaluation of eye-witness credibility, medical evidence, recovery of weapon, and operative verdict (*Appeal allowed / dismissed / sentence converted*).

---

## 4. Downstream Implications for Task B3

1. **Filtering:** Pure civil and service tribunal disputes (~60% of the dataset) will be excluded; only cases citing criminal PPC sections will be retained.
2. **Fact Parsing:** The extractor must isolate the factual narrative (opening 200–800 words after procedural recital) to prevent judicial reasoning from confusing semantic similarity in the Similar Case Finder.
3. **Disambiguation:** Procedural citations (e.g., Section 340(2) CrPC, Section 154 CrPC, Section 497 CrPC) must be strictly isolated to avoid mislabeling substantive crimes.
