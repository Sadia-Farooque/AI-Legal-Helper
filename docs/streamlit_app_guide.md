# Streamlit Web Application — Architecture & Troubleshooting Guide

**AI Legal Helper for Pakistan**  
**Module:** `app/`  
**Last Updated:** November 2026  

---

## 1. Application Architecture

The application is structured as a native Streamlit multi-page application under `app/`:

```text
AI-Legal-Helper-for-Pakistan/
├── run_app.py                       # Root convenience launcher
├── app/
│   ├── Home.py                      # Main landing page & navigation overview
│   └── pages/                       # Subpages discovered automatically by Streamlit
│       ├── 1_Incident_Analyzer.py   # Citizen Incident Analyzer (B4 Retrieval / K4 Stub)
│       ├── 2_Section_Explorer.py    # Law Student PPC Section Explorer (B1/B2 Data)
│       ├── 3_Case_Finder.py         # Supreme Court Similar Case Finder (B5)
│       ├── 4_Quiz.py                # Law Student Practice Quiz (B6)
│       └── 5_Evaluation.py          # Benchmark Dashboard (K6 Results & Grids)
├── data/                            # Lookup, content, and processed data
├── models/                          # Pre-encoded section embeddings & indexes
└── results/                         # Evaluation tables and experiment metrics
```

---

## 2. How to Launch the Application

Streamlit requires invoking a web server process rather than executing scripts directly with `python`.

### Recommended (Root Launcher)
Run from the repository root:
```powershell
python run_app.py
```
This automatically invokes the current Python environment's Streamlit module on `app/Home.py` with telemetry disabled.

### Direct Command
```powershell
python -m streamlit run app/Home.py
```

### Accessing the Web UI
Open your browser to:
```
http://localhost:8501
```

---

## 3. Common Loading Errors & Troubleshooting

| Symptom / Error | Root Cause | Solution |
|---|---|---|
| `streamlit : The term 'streamlit' is not recognized...` | `streamlit.exe` is installed in `...\pythoncore-3.14-64\Scripts`, which is not on the Windows system `PATH`. | Run via python module: `python -m streamlit run app/Home.py` or use `python run_app.py`. |
| `Error: Invalid value: File does not exist: Home.py` | Command run from repository root as `streamlit run Home.py`. `Home.py` is inside `app/`. | Run `python -m streamlit run app/Home.py`. |
| `missing ScriptRunContext! This warning can be ignored when running in bare mode.` (printed 15+ times) | User ran `python app/Home.py` directly instead of `streamlit run`. Python executes it without a Streamlit server context. | Launch using `python -m streamlit run app/Home.py`. |
| Multi-page sidebar missing pages | Multi-page scripts placed in wrong directory. Streamlit requires a `pages/` directory sibling to the main entry file (`app/Home.py`). | Keep subpages strictly in `app/pages/`. |
| `5_Evaluation.py` shows messy 64-column table filled with `NaN`s | Raw experiment logs (`ablation.csv`, `distilbert_grid.csv`) in `results/` lack `metric`, `language`, `value` columns required by K6 schema. | `5_Evaluation.py` filters K6 benchmark files into the main table and separates raw grid tables into dedicated tabs. |

---

## 4. Page Inventory & Features

### `app/Home.py`
* Serves as the central landing page.
* Sets global page configuration (`st.set_page_config`) with layout and page title.
* Provides high-level documentation of citizen and law student capabilities.
* Displays formal academic legal disclaimer.

### `app/pages/1_Incident_Analyzer.py`
* **Target Audience:** Citizens seeking legal guidance on incidents.
* **Features:**
  * Free-text incident description (English or Roman Urdu).
  * **Model Selector:** Toggle between **Zero-Shot Retrieval (Task B4 — `all-MiniLM-L6-v2`)** and **Stub Baseline (Task K4)**.
  * Real-time semantic prediction of top-3 PPC sections.
  * Instant retrieval of statutory facts (Cognizability, Bailability, Punishment, Court) from authoritative CrPC Schedule II lookup table (`data/lookup/ppc_lookup.csv`).
  * Procedural advice on filing an FIR and emergency legal aid contact.

### `app/pages/2_Section_Explorer.py`
* **Target Audience:** Law students and practitioners.
* **Features:**
  * Full search by section number, legal title, or citizen terminology across 30 PPC sections.
  * Conceptual summaries and statutory elements of offences (prosecution burden of proof) from `data/content/sections.json`.
  * Realistic Pakistani factual scenarios.
  * Side-by-side **Confusable Groups Comparison** tab mastering fine distinctions (e.g., Hurt degrees 337-A vs 337-F, Theft 379 vs Robbery 392 vs Dacoity 395).

### `app/pages/3_Case_Finder.py`
* **Target Audience:** Law students researching judicial precedents.
* **Status:** UI skeleton ready; integrates with FAISS index on 301 Supreme Court judgments in Task B5.

### `app/pages/4_Quiz.py`
* **Target Audience:** Law students testing penal law proficiency.
* **Features:** Scenario-based multiple-choice questions with instant scoring, feedback, and statutory explanations. Full 60–100 question bank planned in Task B6.

### `app/pages/5_Evaluation.py`
* **Target Audience:** Academic evaluators, reviewers, and teammates.
* **Features:**
  * Dynamic discovery and aggregation of K6 benchmark results (`retrieval.csv`, `distilbert_val.csv`, `tfidf_*_val.csv`).
  * Pivot comparison table comparing Top-1 Accuracy, Top-3 Recall, Micro-F1, and Macro-F1 across English, Roman Urdu, and combined sets.
  * Dedicated tabs for inspection of ablation and grid-search experimental datasets.

---

## 5. Automated Headless UI Testing

All Streamlit pages can be validated programmatically without opening a browser using Streamlit's testing framework (`streamlit.testing.v1.AppTest`):

```powershell
python -c "
from streamlit.testing.v1 import AppTest
for p in ['app/Home.py', 'app/pages/1_Incident_Analyzer.py', 'app/pages/2_Section_Explorer.py', 'app/pages/3_Case_Finder.py', 'app/pages/4_Quiz.py', 'app/pages/5_Evaluation.py']:
    at = AppTest.from_file(p).run(timeout=10)
    assert not at.exception, f'Error in {p}: {at.exception}'
    print(f'✅ {p} OK')
"
```
