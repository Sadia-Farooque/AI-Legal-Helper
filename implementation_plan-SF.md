# AI Legal Helper for Pakistan: Implementation Plan (Sadia Fatima)

**Author:** Sadia Fatima , owner of Track A and originator of the project idea
**Collaborator:** Abdul Qudoos, Track B
**Course:** Machine Learning, 5th Semester BS Computer Science
**Working branch:** `sadia` (merged into `main` by Pull Request at the end of each sprint)
**Final deadline:** Saturday 21 Nov 2026, night. **My target:** Saturday 14:00.

This file is my live tracker. I tick items as they finish and add notes to the decision log.

---

## 1. My scope (Track A: citizen side + supervised ML)

| ID | Task | Type | Deliverable |
|----|------|------|-------------|
| A1 | IPC-to-PPC mapping table | Manual (legal) | `data/mapping/ipc_ppc_map.csv` + notes |
| A2 | LeSICiN (ILSI) parsing and filtering | ML (data) | `data/processed/ilsi_clean.csv` + class counts |
| A3 | Synthetic incident stories (English + Roman Urdu), verified by hand | Manual + ML | `data/processed/synthetic.csv` + generation note |
| A4 | Preprocessing + TF-IDF with LR / SVM / NB + ablation | ML | `src/preprocess.py`, `src/models/classical.py`, `results/*.csv`, ablation table |
| A5 | DistilBERT multi-label fine-tuning | ML | `notebooks/A5_distilbert.ipynb`, `src/models/distilbert_model.py` |
| A6 | Calibration (temperature scaling) + abstain logic | ML | Calibrated `predict_scores`, reliability diagram, accuracy-vs-coverage chart |
| A7 | LIME explanations ("Why this section?") | ML | `src/explain.py` |
| A8 | Next Steps guide + Incident Analyzer page | Manual + App | `docs/next_steps.md`, `data/lookup/helplines.csv`, `app/pages/1_Incident_Analyzer.py`, tests |
| J1 | My half of the held-out test set (AI-generated, labelled honestly as such) | Manual + ML | 100+ English, 30+ Roman Urdu, `source=llm_test`; 30 of Abdul's labelled blind |
| J2 | Hybrid, final evaluation, demo + slides on my models | Shared | Demo script, slides |

**Contracts I must follow (agreed at kickoff):**
- **K3 data format:** `id, text, sections, primary_section, language, source, split`. `sections` is a JSON list such as `["392","506"]`. `language` is `en` or `roman_ur`. `source` is `ilsi`, `synthetic`, `sc`, `llm_test` or `real`.
- **K4 model contract:** `predict_scores(text) -> {section: score in [0,1]}` for all 30 sections in `src/labels.json`.
- **K6 results:** `results/<model_name>.csv` with columns `metric, language, value`, produced by `src/evaluate.py`.
- I edit only my own files. Abdul's files (`labels.json`, lookup, content, his pages) are changed only through an Issue or PR he approves.

---

## 2. Status at start (Thu 19 Nov, 21:00)

**Already in the repo (Abdul):** K1–K9 kickoff (folders, `labels.json` with 30 sections, `evaluate.py`, stub model, stub test set, app skeleton), B1 lookup table (30 rows), B2 section summaries and confusable groups.

**Mine:** nothing yet. The Incident Analyzer page exists only as a skeleton that calls the stub model.

---

## 3. Sprint plan

### Sprint 1: Thursday night (about 2.5 h, short because of the quiz)
Goal: set up, the legal foundation (A1), and start everything that needs waiting time.

- [ ] S1.1 Clone the repo, set my Git identity, create and push branch `sadia`
- [ ] S1.2 Commit this plan file
- [ ] S1.3 Python environment (venv + light requirements)
- [ ] S1.4 **A1** IPC-to-PPC mapping table for all 30 sections: Same / Changed / Not in IPC, with notes and sources
- [ ] S1.5 Open a GitHub Issue: labels 307 and 319 use IPC meanings (see Decision log, D1)
- [ ] S1.6 **J1** Generate my half of the test set with a different AI tool and a different prompt from A3 (to avoid leakage); write it at the level of informal citizen language; save as `source=llm_test`, never `real`
- [ ] S1.7 Start the LeSICiN (ILSI) download so it is ready for Friday

### Sprint 2: Friday (main block, about 9–10 h)
Goal: all data and all models.

- [ ] S2.1 **A2** Parse ILSI: facts + cited sections, keep only "Same" sections from A1, truncation comparison (first 512 tokens vs key sentences), class-count table
- [ ] S2.2 **A3** Generate synthetic stories: about 30 English + 10 Roman Urdu per section, about 10% multi-offence; one documented prompt template
- [ ] S2.3 **A3** Verify every story with a review script that flags duplicates, too-short stories and section-keyword leaks, then a manual read; log what was deleted or fixed
- [ ] S2.4 **A4** `src/preprocess.py`: lowercasing, cleaning, Roman Urdu spelling normalisation (nahi/nahin, kr/kar, ...)
- [ ] S2.5 **A4** Group-aware train/val split (near-duplicates stay together)
- [ ] S2.6 **A4** TF-IDF (word + char n-grams) with one-vs-rest LR / Linear SVM / NB, class_weight=balanced, grid search
- [ ] S2.7 **A4** Ablation: synthetic only / ILSI only / both
- [ ] S2.8 **A5** DistilBERT multi-label on Colab GPU: 2–3 learning rates, early stopping; run evaluate.py
- [ ] S2.9 **A6** Temperature scaling, reliability diagram, accuracy-vs-coverage curve, abstain threshold
- [ ] S2.10 **A7** `src/explain.py` with LIME; check 10 examples by eye
- [ ] S2.11 Open a PR `sadia` → `main` (data + models)

### Sprint 3: Saturday until 14:00 (about 6 h)
Goal: the citizen product, the test set, then extras.

- [ ] S3.1 **A8** `docs/next_steps.md`: FIR procedure (s.154 CrPC), police refusal (senior officers, Justice of Peace under s.22-A CrPC), evidence to keep, when to see a lawyer
- [ ] S3.2 **A8** `data/lookup/helplines.csv`: official sources only, each with a source link and date checked
- [ ] S3.3 **A8** Rebuild the Incident Analyzer: real model, top-3 cards with the legal facts card, confidence bars, abstain message, "Why this section?" highlights, Next Steps panel, disclaimer
- [ ] S3.4 **A8** Unit tests: theft, harassment, fraud, Roman Urdu, empty input, non-crime text
- [ ] S3.5 **J1** Check and label my AI-generated test set → `data/test/llm_test_sf.csv`; label 30 of Abdul's blind; compute agreement (Cohen's kappa)
- [ ] S3.6 Run all my models on the held-out test set → `results/` (feeds Abdul's Evaluation page)
- [ ] S3.7 PR `sadia` → `main`
- [ ] S3.8 Extras, in priority order (below)

### Extras (my optional pool), in priority order
1. **FIR draft generator:** fills a complaint draft (English + Urdu) from the incident text + predicted sections; downloadable
2. **PDF export** of the full analysis (sections, legal facts, next steps)
3. **"Was this correct?" feedback button:** logs to CSV and becomes new labelled data for real users after deployment
4. **Voice input (Whisper)**
5. **Urdu script input** via transliteration to Roman Urdu

---

## 4. If I fall behind
Cut in this order: (1) multilingual model in A5, (2) ablation reduced to with / without synthetic, (3) LIME replaced by top TF-IDF words.
**Never cut:** verified data, DistilBERT, calibration + abstain, the held-out test set, the disclaimer.

---

## 5. Git workflow
- One working branch, `sadia`. One commit per finished step, with a message such as `A1: add IPC-to-PPC mapping for 30 sections`.
- A PR into `main` at the end of Sprints 2 and 3; Abdul reviews and merges.
- Large raw data (ILSI download, model weights) is never committed. It goes in `.gitignore`; only scripts, processed CSVs and results are committed.

---

## 6. Decision log
| # | Date | Decision / finding |
|---|------|--------------------|
| D1 | 19 Nov | `labels.json` uses IPC meanings for **307** ("attempt to commit qatl-i-amd") and **319** ("hurt"). In the PPC after the Qisas and Diyat law, s.307 = cases where qisas is not enforced, s.319 = punishment of qatl-i-khata, and attempted qatl-i-amd = s.324. The lookup table already treats 319 as qatl-i-khata, so the two files disagree. Raised as a GitHub Issue for Abdul; it must be fixed before any training. |
| D2 | 19 Nov | J1 test set will be AI-generated instead of collected from real people (time constraint). It is tagged `source=llm_test` and reported as such; it is generated with a different tool and prompt from the A3 training stories so the test set does not mirror the training data. The deployed feedback button (extra 3) is how real-user data gets collected later. |
