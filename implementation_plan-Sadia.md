# AI Legal Helper for Pakistan: Implementation Plan (Sadia Fatima)

**Author:** Sadia Fatima (023-24-0213), owner of Track A and originator of the project idea
**Collaborator:** Abdul Qudoos (023-24-0233), Track B
**Course:** Machine Learning, 5th Semester BS Computer Science
**Working branch:** `sadia` (merged into `main` by Pull Request at the end of each sprint)
**Final deadline:** Saturday 21 Nov 2026, night. **My target:** Saturday 14:00.

This file is my live tracker. I tick items as they finish and add notes to the decision log.

---

## 1. My scope (Track A: citizen side + supervised ML)

| ID  | Task                                                                       | Type           | Deliverable                                                                                  |
| --- | -------------------------------------------------------------------------- | -------------- | -------------------------------------------------------------------------------------------- |
| A1  | IPC-to-PPC mapping table                                                   | Manual (legal) | `data/mapping/ipc_ppc_map.csv` + notes                                                       |
| A2  | LeSICiN (ILSI) parsing and filtering                                       | ML (data)      | `data/processed/ilsi_clean.csv` + class counts                                               |
| A3  | Synthetic incident stories (English + Roman Urdu), verified by hand        | Manual + ML    | `data/processed/synthetic.csv` + generation note                                             |
| A4  | Preprocessing + TF-IDF with LR / SVM / NB + ablation                       | ML             | `src/preprocess.py`, `src/models/classical.py`, `results/*.csv`, ablation table              |
| A5  | DistilBERT multi-label fine-tuning                                         | ML             | `notebooks/A5_distilbert.ipynb`, `src/models/distilbert_model.py`                            |
| A6  | Calibration (temperature scaling) + abstain logic                          | ML             | Calibrated `predict_scores`, reliability diagram, accuracy-vs-coverage chart                 |
| A7  | LIME explanations ("Why this section?")                                    | ML             | `src/explain.py`                                                                             |
| A8  | Next Steps guide + Incident Analyzer page                                  | Manual + App   | `docs/next_steps.md`, `data/lookup/helplines.csv`, `app/pages/1_Incident_Analyzer.py`, tests |
| J1  | My half of the held-out test set (AI-generated, labelled honestly as such) | Manual + ML    | 100+ English, 30+ Roman Urdu, `source=llm_test`; 30 of Abdul's labelled blind                |
| J2  | Hybrid, final evaluation, demo + slides on my models                       | Shared         | Demo script, slides                                                                          |

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

- [x] S1.1 Clone the repo, set my Git identity, create and push branch `sadia`
- [x] S1.2 Commit this plan file
- [x] S1.3 Python environment (venv + light requirements)
- [x] S1.4 **A1** IPC-to-PPC mapping table for all 30 sections, with notes and sources; `tests/test_mapping.py`; source-verified in `docs/A1_verification_report.md` (3 notes corrected)
- [x] S1.5 Open a GitHub Issue: labels 307 and 319 use IPC meanings (see Decision log, D1)
- [ ] S1.6 **J1** Google Form to 7 real people (3–5 incidents each, about 25–35 real descriptions, `source=real`); generate the rest of my half of the test set with a different AI tool and a different prompt from A3 (to avoid leakage); write it at the level of informal citizen language; save as `source=llm_test`, never `real`
- [x] S1.7 ILSI download: partial (Zenodo kept cutting the connection; about 15 MB of case files). JSONL is one case per line, so all complete lines are usable (see D6)
- [x] S1.8 PR #3 `sadia` → `main` (A1) merged. Note: commit c6f24f1 accidentally deleted the plan file; restored in 2.0

### Sprint 2: Friday night (21:45 → 00:20): all data and all models ✅ done

Each row = one commit. The commit message is exactly what I type.

| #      | Task                          | What I get                                                                                                      | Commit message                                                                        |
| ------ | ----------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| ✅ 2.0 | Restore plan                  | this file back on GitHub                                                                                        | `Plan: restore plan file deleted in c6f24f1, add sprint task list with commits`       |
| ✅ 2.1 | **A2** ILSI parser            | `src/data/ilsi_parse.py`, `tests/test_ilsi_parse.py`, `data/processed/ilsi_clean.csv`, `docs/A2_ilsi_report.md` | `A2: parse ILSI, map IPC to PPC via A1 table, mask statute mentions, coverage report` |
| ✅ 2.2 | **A3** synthetic stories      | `data/processed/synthetic.csv`, `docs/A3_generation_note.md`                                                    | `A3: synthetic citizen incident stories in English and Roman Urdu`                    |
| ✅ 2.3 | **A3** quality checks         | `src/data/review_synthetic.py`, review log in the A3 note                                                       | `A3: automated quality checks and review log for synthetic stories`                   |
| ✅ 2.4 | **A4** preprocessing          | `src/preprocess.py`, `tests/test_preprocess.py`                                                                 | `A4: text preprocessing with Roman Urdu spelling normalisation and tests`             |
| ✅ 2.5 | **A4** split + baselines      | `src/data/make_splits.py`, `src/models/classical.py`, `results/tfidf_*.csv`                                     | `A4: grouped train/val split and TF-IDF LR/SVM/NB baselines with grid search`         |
| ✅ 2.6 | **A4** ablation               | `results/ablation.csv`, `docs/A4_results.md`                                                                    | `A4: data-source ablation (synthetic only, ILSI only, both)`                          |
| ✅ 2.7 | **A5** DistilBERT (Colab GPU) | `notebooks/A5_distilbert.ipynb`, `src/models/distilbert_model.py`, `results/distilbert.csv`                     | `A5: DistilBERT multi-label fine-tuning notebook and model wrapper`                   |
| ✅ 2.8 | **A6** calibration + abstain  | `src/calibration.py`, reliability diagram, coverage curve                                                       | `A6: temperature-scaling calibration, reliability diagram and abstain threshold`      |
| ✅ 2.9 | **A7** explanations           | `src/explain.py`, `tests/test_explain.py`                                                                       | `A7: LIME word-level explanations for predictions`                                    |
| 2.10   | PR                            | PR `sadia` → `main`                                                                                             | (no commit; reviewed by Abdul)                                                        |

### Sprint 3: Saturday 09:00–14:00: the citizen product, the test set, then extras

| #   | Task                          | What I get                                                      | Commit message                                                                          |
| --- | ----------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 3.1 | **J1** held-out test set      | `data/test/test_sf.csv` (real + AI-written, tagged by `source`) | `J1: held-out test set with real and AI-written descriptions, tagged by source`         |
| 3.2 | Evaluation                    | all models on the test set → `results/`                         | `Eval: Track A models on held-out test set, split by language and source`               |
| 3.3 | **A8** Next Steps + helplines | `docs/next_steps.md`, `data/lookup/helplines.csv`               | `A8: Next Steps guide and source-checked helplines`                                     |
| 3.4 | **A8** Incident Analyzer page | `app/pages/1_Incident_Analyzer.py`, `src/analyzer.py`           | `A8: Incident Analyzer page with top-3 sections, legal facts, abstain and explanations` |
| 3.5 | **A8** tests                  | `tests/test_analyzer.py`                                        | `A8: tests for analyzer logic (theft, harassment, fraud, Roman Urdu, empty, non-crime)` |
| 3.6 | PR                            | PR `sadia` → `main`                                             | (no commit)                                                                             |
| 3.7 | Extra 1                       | FIR draft generator                                             | `Extra: FIR complaint draft generator (English and Urdu)`                               |
| 3.8 | Extra 2                       | PDF export                                                      | `Extra: PDF export of incident analysis`                                                |
| 3.9 | Extra 3                       | feedback button                                                 | `Extra: "Was this correct?" feedback logging`                                           |

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

| #   | Date   | Decision / finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| --- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| D1  | 19 Nov | `labels.json` uses IPC meanings for **307** ("attempt to commit qatl-i-amd") and **319** ("hurt"). In the PPC after the Qisas and Diyat law, s.307 = cases where qisas is not enforced, s.319 = punishment of qatl-i-khata, and attempted qatl-i-amd = s.324. The lookup table already treats 319 as qatl-i-khata, so the two files disagree. Raised as a GitHub Issue for Abdul; it must be fixed before any training.                                                              |
| D2  | 19 Nov | J1 test set: about 25–35 real descriptions from 7 people via Google Form (`source=real`); the rest AI-generated in a realistic citizen style (time constraint). It is tagged `source=llm_test` and reported as such; it is generated with a different tool and prompt from the A3 training stories so the test set does not mirror the training data. The deployed feedback button (extra 3) is how real-user data gets collected later.                                             |
| D3  | 19 Nov | ILSI (LeSICiN, Zenodo record 6053791) licence is **CC BY 4.0**; it has train/dev/test JSONL files (id, sentences, cited labels) and the statute texts in `secs.jsonl`. Only the data files are needed; the 2.3 GB sent2vec model is skipped. This fills the "[Check Zenodo]" cells of the proposal.                                                                                                                                                                                  |
| D4  | 19 Nov | Related work for the report: ILSIC (Paul et al., EACL 2026 Findings, arXiv 2602.00881) finds that models trained only on court judgments do poorly on laypeople's queries. This independently supports our design (synthetic citizen-style stories + a real-person test set). If its lay-query data is publicly released, consider it as extra training data in A2 (check licence first).                                                                                            |
| D5  | 20 Nov | The 307/319/441 Issue is still open, so Track A handles it without editing Abdul's files: **307** gets no training examples (it is not an offence a citizen can report in the PPC, so the model should never predict it); **319** is trained with the PPC meaning, qatl-i-khata (it matches the lookup table and sections.json); **441 + 447** trespass examples carry both labels (legally both apply), and the app shows them as one result. Revisit if Abdul changes labels.json. |
| D6  | 20 Nov | ILSI is used from partial files. Stated in the A2 report: the case count is smaller than the full dataset, but every case kept is complete and valid. ILSI is only a supplement; most citizen-style training data comes from A3.                                                                                                                                                                                                                                                     |
| D7  | 20 Nov | A3 legal review (`docs/A3_review_fixes.md`): 6 of 84 sampled stories were wrong; the same error patterns were then swept across all 560 stories, so 20 stories were corrected and 557 remain. Main rules: bruises alone are not jurh (337-F needs a real wound); blocking someone's way = 339, keeping them inside = 340.                                                                                                                                                            |
| D8  | 20 Nov | LR grid: the best C=16 sat at the edge of the grid, so the grid was extended to C=64. C=64 was worse (top-3 0.887 vs 0.904), so C=16 is a true optimum.                                                                                                                                                                                                                                                                                                                              |
| D9  | 20 Nov | Ablation (`results/ablation.csv`): trained on ILSI only, citizen-story top-1 is **0.130**, versus 0.757 for synthetic only. This is the domain shift, measured. Synthetic + ILSI is kept: same citizen accuracy (1-story difference), better Roman Urdu micro-F1 (0.807 vs 0.746), and it still handles court-style text (0.626 vs 0.193).                                                                                                                                           |
| D10 | 20 Nov | DistilBERT (lr 5e-5, best at epoch 5) does worse than TF-IDF + LR on citizen text (top-1 0.652 vs 0.748), and much worse on Roman Urdu (0.407 vs 0.815): English-only pre-training, plus only about 440 citizen stories. **The app uses calibrated TF-IDF + LR.**                                                                                                                                                                                                                    |
| D11 | 20 Nov | Calibration v1 (temperature over all 30 labels) made ECE worse, because about 29/30 label-cells are negatives. Switched to Platt scaling of the top-1 confidence, which is what the app shows. LR cross-fit ECE 0.254 → 0.191; abstain threshold 0.70 → answers 63% of cases at 87.5% top-1 / 98.6% top-3. DistilBERT was already calibrated (0.125); Platt scaling did not help it (reported as is).                                                                                |
| D12 | 20 Nov | Found in the shared `src/evaluate.py`: per-section false positives are never counted, so its "macro-F1" behaves like macro-recall and is too high. Track A uses `src/metrics.py` (true macro-F1); reported to Abdul in PR #4.                                                                                                                                                                                                                                                        |
