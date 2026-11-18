# AI Legal Helper for Pakistan — Implementation Plan (Abdul Qudoos)

**Author:** Abdul Qudoos  
**Collaborator:** Sadia Fatima  
**Course:** Machine Learning (5th Semester BS Computer Science)  
**Document Purpose:** Master execution roadmap for Abdul Qudoos's responsibilities under the **Two Independent Tracks** task division, including kickoff status, track roadmap, and the concrete implementation plan for the next task (**Task B1: Legal Lookup Table**).

---

## 1. Track Architecture & Core Responsibilities

Under the updated task division, the project is structured into two completely independent, parallel tracks designed to eliminate cross-dependencies:

```mermaid
flowchart LR
    subgraph Kickoff["Week 1: Shared Kickoff (K1-K9)"]
        K["Contracts, Stubs, Labels, Repo & Eval"]
    end

    subgraph TrackA["Track A: Sadia (Citizen + Supervised ML)"]
        A1["A1: IPC-to-PPC Map"] --> A2["A2: ILSI Parsing"]
        A2 --> A3["A3: Synthetic Stories"]
        A3 --> A4["A4: Classical Baselines"]
        A4 --> A5["A5: DistilBERT"]
        A5 --> A6["A6-A7: Calibration & LIME"]
        A6 --> A8["A8: Analyzer Page"]
    end

    subgraph TrackB["Track B: Abdul (Student + Retrieval ML + Legal Knowledge)"]
        B1["B1: Legal Lookup Table"] --> B2["B2: Section Summaries"]
        B2 --> B3["B3: SC Judgment Extraction"]
        B3 --> B4["B4: Retrieval Classifier"]
        B4 --> B5["B5: Case Finder"]
        B5 --> B6["B6: Quiz Bank"]
        B6 --> B7["B7: Explorer/Finder/Quiz Pages"]
        B7 --> B8["B8: Evaluation Page & Tooling"]
    end

    subgraph Integration["Weeks 11-12: Integration (J2)"]
        J2["Hybrid Model, Final Evaluation & Report"]
    end

    Kickoff --> TrackA
    Kickoff --> TrackB
    TrackA --> Integration
    TrackB --> Integration
```

### Abdul Qudoos's Scope (Track B):
1. **Legal Knowledge Foundation:** Authoring the authoritative CrPC Schedule II lookup table (B1), plain-English section summaries, elements of offence, and confusable pair taxonomies (B2).
2. **Supreme Court Judgment Mining:** Exploration and regex-based section citation extraction on Pakistan SC judgments (B3).
3. **Retrieval-Based ML & Case Search:** Building zero-shot sentence-embedding retrieval classifier for section recommendation (B4) and FAISS-based Similar Case Finder (B5).
4. **Student Educational Suite:** Authoring a 60–100 scenario quiz bank (B6) and developing the Streamlit Section Explorer, Case Finder, and Quiz pages (B7).
5. **Evaluation Suite & Error Analysis:** Developing the model evaluation dashboard and comparative error analysis tooling (B8).
6. **Shared Deliverables:** Co-collecting and labelling the real-person test set (J1), and co-building the hybrid model and final defense materials (J2).

---

## 2. Master Task Matrix for Abdul Qudoos

| Task ID | Phase / Weeks | Task Name | Type | Hours | Deliverables | Dependencies / Hand-offs |
| :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| **K1–K9** | **Week 1** | **Shared Kickoff, Contracts & Stubs** | **Setup + ML** | **8h** | Repo, `labels.json`, stubs, `evaluate.py`, app skeleton | Shared with Sadia |
| **B1** | **Weeks 2–3** | **Legal Lookup Table (CrPC Schedule II)** | **Manual / Legal** | **12h** | `data/lookup/ppc_lookup.csv` (all 30 sections) | None (Sadia consumes in Wk 9) |
| **B2** | Weeks 3–4 | Section Summaries, Elements & Confusable Groups | Manual / Legal | 10h | `data/content/sections.json`, `confusable_groups.json` | B1 |
| **B3** | Weeks 4–5 | Supreme Court Judgments Exploration & Regex Extraction | ML (Data) | 10h | `data/processed/sc_clean.csv`, regex precision report | K2 |
| **B4** | Weeks 5–6 | Retrieval Classifier (Sentence Embeddings) | ML | 12h | `src/retrieval.py`, zero-shot results CSV | B2, K7 |
| **J1** | Weeks 6–9 | Real-Person Test Set (Abdul's Half: 100 En + 30 Roman) | Manual | 6h | Part of `data/test/real_test.csv` (frozen) | K2 |
| **B5** | Week 7 | Similar Case Finder (FAISS / Vector Index) | ML | 8h | `src/case_finder.py`, semantic case search API | B3 |
| **B6** | Week 8 | Quiz Bank (60 to 100 Scenarios) | Manual | 10h | `data/content/quiz_bank.json` | B2 |
| **B7** | Weeks 9–10 | Student App Pages (Explorer, Case Finder, Quiz) | App Dev | 14h | `app/pages/2_Section_Explorer.py`, `3_Case_Finder.py`, `4_Quiz.py` | B1, B2, B5, B6 |
| **B8** | Week 10 | Evaluation Page & Error Analysis Tooling | ML + App | 8h | `app/pages/5_Evaluation.py`, `src/error_analysis.py` | K6, K7 |
| **J2** | Weeks 11–12 | Hybrid Model, System Integration, Report & Slides | All | 14h | Hybrid predictor, final report, presentation deck | A6, B4, J1 |

*Total Track Commitment:* **112 Hours** (8h Kickoff + 84h Track B + 6h J1 + 14h J2).

---

## 3. Current Status: What is Done vs. What is Remaining

### 3.1 Completed Items
- [x] **K1 (Repo & Environment):** Standard directory tree initialized (`data/*`, `app/*`, `src/*`, `models/*`, `results/*`, `docs/*`, `tests/*`). [requirements.txt](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/requirements.txt) and [.gitignore](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/.gitignore) configured.
- [x] **K2 (PPC Label Space):** [src/labels.json](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/src/labels.json) frozen with 30 target sections, citizen colloquial terms, legal categories, and confusable cross-references. Verified via unit test.
- [x] **K3 (Data Format Standard):** [data/README.md](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/data/README.md) defines canonical CSV schema (`id`, `text`, `sections`, `language`, `source`, `split`).

### 3.2 Kickoff Enablers & Stubs (Completed)
- [x] **K4 & K8 (Model Contract & Predictor Stub):** [src/models/stub_model.py](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/src/models/stub_model.py) exposing `predict_scores(text) -> dict`.
- [x] **K5 & K8 (Lookup Stub):** Initial 5-row placeholder [data/lookup/ppc_lookup.csv](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/data/lookup/ppc_lookup.csv) so Track A app code never blocks.
- [x] **K7 (Evaluation Engine):** [src/evaluate.py](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/src/evaluate.py) implementing top-1 accuracy, top-3 recall, and multi-label micro/macro F1 metrics.
- [x] **K8 (Evaluation Stub Sentences):** [data/test/stub_test.csv](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/data/test/stub_test.csv) (20 test cases).
- [x] **K6 (Results Contract):** [results/stub_model.csv](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/results/stub_model.csv) generated and validated.
- [x] **K9 (App Skeleton):** [app/Home.py](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/app/Home.py) and all 5 multi-page templates in [app/pages/](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/app/pages/).

---

## 4. Deep-Dive Implementation Plan: Next Task (Task B1: Legal Lookup Table)

### 4.1 Task Summary
- **Task ID:** `B1`
- **Owner:** Abdul Qudoos
- **Timeline:** Weeks 2 to 3
- **Estimated Hours:** 12 Hours
- **Goal:** Author the authoritative, verified legal facts table (`data/lookup/ppc_lookup.csv`) covering all 30 PPC sections in `labels.json` sourced directly from Schedule II of the Code of Criminal Procedure (CrPC).
- **Handoff Importance:** Sadia's Incident Analyzer page (Task A8) displays FIR eligibility, bailability, and punishments from this exact file. Providing it early (Week 3) gives Sadia a 6-week buffer.

---

### 4.2 Data Contract Specification for `ppc_lookup.csv` (K5 Contract)

Every row corresponds to one section in `src/labels.json` and must contain exactly these 10 columns:

| Column Name | Type | Permitted Values / Description | Example |
| :--- | :--- | :--- | :--- |
| `section` | string | Exact PPC section number matching `labels.json` | `"392"` |
| `short_name` | string | Brief title of the offence | `"Robbery"` |
| `meaning` | string | Clear 1-line plain-English explanation for lay citizens | `"Taking property by force, fear of injury, or wrongful restraint"` |
| `cognizable` | string | `"Cognizable"` (Police can arrest without warrant / FIR) or `"Non-cognizable"` | `"Cognizable"` |
| `bailable` | string | `"Bailable"` or `"Non-bailable"` | `"Non-bailable"` |
| `compoundable` | string | `"Compoundable"` (Victim can compromise under s.345 CrPC) or `"Non-compoundable"` | `"Non-compoundable"` |
| `punishment` | string | Statutory penalty range under PPC | `"Rigorous imprisonment for 3 to 10 years, and fine; if on highway between sunset and sunrise, up to 14 years"` |
| `court` | string | Competent trial court under Schedule II CrPC | `"Court of Session or Magistrate of the first class"` |
| `source` | string | Official legal reference | `"PPC 1860 & CrPC Schedule II (amended 2023)"` |
| `date_checked` | string | Verification date in ISO format | `"2026-11-18"` |

---

### 4.3 Step-by-Step Execution Plan for B1

```mermaid
flowchart TD
    S1["Step 1: Extract 30 Frozen Sections from src/labels.json"] --> S2["Step 2: Research Statutory Facts from CrPC Schedule II & s.345 CrPC"]
    S2 --> S3["Step 3: Draft Plain-English Citizen Meanings for Lay Users"]
    S3 --> S4["Step 4: Compile data/lookup/ppc_lookup.csv"]
    S4 --> S5["Step 5: Automated Verification Test (tests/test_lookup.py)"]
    S5 --> S6["Step 6: Push to Repo & Notify Sadia (Asynchronous Review)"]
```

#### Step 1: Extract and Initialize Target Sections
Read `src/labels.json` to ensure 100% section parity:
- 30 target sections: `302`, `307`, `319`, `324`, `337-A`, `337-F`, `339`, `340`, `354`, `354A`, `363`, `365`, `365-A`, `379`, `380`, `382`, `384`, `392`, `395`, `403`, `406`, `411`, `420`, `441`, `447`, `448`, `489-F`, `500`, `506`, `509`.

#### Step 2: Extract Procedural Facts from Schedule II of CrPC
For each section, extract the statutory procedural categorisation:
1. **Cognizability (Column 3 of Sched II):** Whether police may arrest without warrant. (Critical for citizen: can an FIR be filed directly at the thana?).
2. **Bailability (Column 5 of Sched II):** Whether bail is a matter of statutory right or court discretion.
3. **Compoundability (s. 345 CrPC):** Can the victim pardon or settle the offence with or without court permission?
4. **Punishment (Column 7 of Sched II & PPC text):** Exact minimum/maximum imprisonment and fine provisions.
5. **Trial Court (Column 8 of Sched II):** Magistrate of 1st class, Magistrate Section 30, Court of Session.

#### Step 3: Write Lay-Friendly Section Meanings
Craft an accessible, jargon-free 1-line definition for ordinary citizens (e.g. for Section 489-F: *"Dishonestly issuing a cheque that bounces due to insufficient funds"*).

#### Step 4: Author `data/lookup/ppc_lookup.csv`
Compile all rows into the CSV format, ensuring UTF-8 encoding and clean comma separation with quoted strings where commas appear.

#### Step 5: Implement Automated Schema & Completeness Test (`tests/test_lookup.py`)
Write an automated unit test verifying:
- Exactly 30 rows matching `src/labels.json`.
- No empty strings across any of the 10 required columns.
- Valid enum values: `cognizable` in `{"Cognizable", "Non-cognizable"}`; `bailable` in `{"Bailable", "Non-bailable"}`; `compoundable` in `{"Compoundable", "Non-compoundable"}`.

---

### 4.4 Deliverables & Definition of Done for Task B1
- [x] `data/lookup/ppc_lookup.csv` authored with all 30 PPC sections populated across all 10 columns.
- [x] Every entry backed by an official statutory source citation and check date.
- [x] Unit test `tests/test_lookup.py` passing with 100% coverage of lookup rows.
- [x] Initial kickoff stubs (K4, K5, K7, K8, K9) generated so the team repository is completely operational.
- [x] Ready to commit under feature branch `aq`.


---

## 5. Deep-Dive Implementation Plan: Task B2 (Section Summaries, Elements of Offence & Confusable Groups)

### 5.1 Task Overview & Downstream Impact
- **Task ID:** `B2`
- **Owner:** Abdul Qudoos
- **Timeline:** Weeks 3 to 4
- **Estimated Effort:** 10 Hours
- **Goal:** Author the comprehensive student-facing legal learning content and the semantic knowledge base for the retrieval model:
  1. Plain-English conceptual summaries (3–5 lines each).
  2. The statutory **"Elements of the Offence"** (essential legal ingredients prosecution must establish in court).
  3. Realistic, contextual Pakistani scenario examples for each section.
  4. Curate 8 to 12 **Confusable Groups** detailing specific distinctions between subtle statutory offences.
- **Why Authentic Legal Data Matters (Anti-Slop Protocol):**
  - **B4 Retrieval Classifier:** Sentence-transformer models (`all-MiniLM-L6-v2`) will embed this text to match user incident descriptions. If elements and summaries are vague generic text, cosine similarity will collapse across adjacent crimes (e.g. failing to distinguish theft from robbery).
  - **B6 Quiz Bank & B7 Section Explorer:** Real students and evaluators will judge the system's depth based on whether the "ingredients of the crime" match the Pakistan Penal Code 1860 and established Supreme Court precedent (*SCMR* / *PLD* doctrine).

---

### 5.2 Schema Contracts & Standards

#### A. Schema Contract for `data/content/sections.json`
Dictionary keyed by section ID (`"302"`, `"379"`, `"489-F"`, etc.):
```json
{
  "392": {
    "section": "392",
    "title": "Punishment for robbery",
    "category": "Offences Against Property",
    "summary": "Robbery is an aggravated form of either theft or extortion. It occurs when an offender voluntarily causes or attempts to cause death, hurt, or wrongful restraint (or the immediate fear thereof) in order to commit the theft, carry away stolen property, or commit extortion.",
    "elements": [
      "Commission of theft (s.378) or extortion (s.383)",
      "Offender voluntarily caused or attempted to cause death, hurt, or wrongful restraint",
      "The violence or threat was exerted during the transaction (in order to commit the offence or carry away property)",
      "Causing an immediate apprehension of personal injury"
    ],
    "example_scenarios": [
      "Two armed assailants intercepted a commuter's motorbike at a traffic signal in Saddar, held a loaded handgun to his chest, and forcibly took his mobile phone and cash.",
      "A pedestrian walking through an alley was grabbed by the neck from behind by an offender wielding a knife, who threatened to slash him if he did not relinquish his watch."
    ],
    "statutory_reference": "Pakistan Penal Code 1860, Sections 390 & 392"
  }
}
```

#### B. Schema Contract for `data/content/confusable_groups.json`
Array of group objects targeting difficult distinction boundaries:
```json
[
  {
    "group_id": "grp_theft_robbery_dacoity",
    "group_name": "Aggravated Property Offenses (Theft vs. Robbery vs. Dacoity)",
    "sections": ["379", "380", "382", "392", "395"],
    "distinction_summary": "The boundary hinges on location, force/threat exerted, preparation, and the number of offenders participating conjointly.",
    "key_differentiators": {
      "379": "Simple theft: taking movable property without consent, zero violence or threat exerted.",
      "380": "Theft inside a residential dwelling, tent, or vessel used for living or storage.",
      "382": "Theft where the thief makes overt preparations for causing death or hurt (e.g., carrying weapons under clothes).",
      "392": "Robbery: violence, restraint, or immediate fear of hurt is actually exerted during the theft or escape.",
      "395": "Dacoity: robbery committed by 5 or more persons acting conjointly."
    },
    "critical_student_pitfall": "Students frequently confuse 392 and 395. The moment a robbery involves five or more conjoint perpetrators, Section 392 transitions into Section 395 (Dacoity), which carries higher statutory penalties."
  }
]
```

---

### 5.3 Target Confusable Groups (10 Core Boundaries)

1. **Group 1: Theft vs. Dwelling Theft vs. Prepared Theft vs. Robbery vs. Dacoity** (`379`, `380`, `382`, `392`, `395`)
2. **Group 2: Extortion vs. Criminal Intimidation** (`384`, `506`)
3. **Group 3: Criminal Misappropriation vs. Criminal Breach of Trust vs. Cheating** (`403`, `406`, `420`)
4. **Group 4: Cheating / Fraud vs. Dishonestly Issuing a Cheque** (`420`, `489-F`)
5. **Group 5: Premeditated Murder vs. Attempted Murder vs. Attempted Qatl** (`302`, `307`, `324`)
6. **Group 6: Bodily Harm Categories (Shajjah vs. Jurh vs. Hurt)** (`337-A`, `337-F`, `319`)
7. **Group 7: Wrongful Restraint vs. Wrongful Confinement** (`339`, `340`)
8. **Group 8: Kidnapping vs. Abduction vs. Ransom Kidnapping** (`363`, `365`, `365-A`)
9. **Group 9: Offences against Women & Modesty** (`354`, `354A`, `509`)
10. **Group 10: Criminal Trespass vs. House-Trespass** (`441`, `447`, `448`)

---

### 5.4 Step-by-Step Implementation Workflow

```mermaid
flowchart TD
    Step1["Step 1: Statutory Ingredient Extraction (PPC Text & Supreme Court Precedents)"] --> Step2["Step 2: Realistic Scenario Drafting (Pakistani Fact Patterns)"]
    Step2 --> Step3["Step 3: Compile data/content/sections.json"]
    Step3 --> Step4["Step 4: Formulate Confusable Matrices (data/content/confusable_groups.json)"]
    Step4 --> Step5["Step 5: Automated Integrity & Anti-Slop Test Suite (tests/test_content.py)"]
    Step5 --> Step6["Step 6: Execute Validation Test & Git Commit"]
```

#### Step 1: Extract Genuine Legal Elements
For each of the 30 sections in [src/labels.json](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/src/labels.json), extract the statutory ingredients required under Pakistani law:
- Must cite exact mens rea (e.g. *dishonest intention*, *knowledge*, *voluntarily*).
- Must cite exact actus reus (e.g. *moving property*, *causing bodily pain*, *restraining within limits*).
- Must explicitly state statutory exceptions or aggravations where applicable.

#### Step 2: Formulate Authentic Pakistani Incident Scenarios
Draft 2 concrete scenarios per section based on realistic real-world cases:
- *Robbery / 392:* Gunpoint motorbike snatching in an urban market.
- *Dishonoured Cheque / 489-F:* Wholesale commercial vendor receiving a post-dated cheque that gets stamped "Account Insufficient Funds".
- *Cyber / Modesty / 509:* Unsolicited obscene messaging, stalking, or workplace verbal harassment.
- *Trespass / 447:* Forcible boundary intrusion or unlawful land encroachment.

#### Step 3: Compile Confusable Matrices
Detail the statutory dividing line for all 10 groups, clarifying the exact pivot point where an act crosses from one section to another.

#### Step 4: Author the Content Files
- Create [data/content/sections.json](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/data/content/sections.json).
- Create [data/content/confusable_groups.json](file:///c:/Users/Microsoft/Desktop/AI-Legal-Helper-for-Pakistan/data/content/confusable_groups.json).

#### Step 5: Implement Automated Anti-Slop Integrity Test (`tests/test_content.py`)
To ensure high data quality and avoid incomplete entries:
1. **Parity Check:** All 30 sections in `src/labels.json` must be present in `sections.json`.
2. **Completeness Check:** Each section must have `summary` >= 80 characters, at least 2 distinct `elements`, at least 2 `example_scenarios`, and a valid `statutory_reference`.
3. **Confusable Groups Check:** At least 8 to 10 confusable groups, each with at least 2 sections, a non-empty `distinction_summary`, and non-empty `key_differentiators` for each member section.
4. **Referential Integrity Check:** Every section referenced inside `confusable_groups.json` must exist in `src/labels.json`.

---

### 5.5 Verification Command & Test Protocol

Run the data integrity test suite via Python:
```bash
& "C:\Users\Microsoft\AppData\Local\Python\bin\python.exe" tests/test_content.py
```
**Expected Outcome:** 100% assertions pass across all 30 section entries and 10 confusable groups.

---

### 5.6 Deliverables & Definition of Done for Task B2
- [x] `data/content/sections.json` authored with all 30 PPC sections, summaries, statutory elements, and real scenarios.
- [x] `data/content/confusable_groups.json` authored with 10 detailed comparison matrices and pitfall notes.
- [x] Automated validation suite `tests/test_content.py` created and executing cleanly with 100% pass rate.
- [x] Section Explorer app page (`app/pages/2_Section_Explorer.py`) verified to render the new content seamlessly.
- [x] Staged and ready for commit under branch `aq`.
