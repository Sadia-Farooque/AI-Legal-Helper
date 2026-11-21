# AI Legal Helper for Pakistan: Implementation Plan (Sadia Fatima)

**Author:** Sadia Fatima (023-24-0213), owner of Track A and originator of the project idea
**Collaborator:** Abdul Qudoos (023-24-0233), Track B
**Course:** Machine Learning, 5th Semester BS Computer Science
**Working branch:** `sadia` (merged into `main` by Pull Request at the end of each sprint)
**Final deadline:** Saturday 21 Nov 2026, night. **My target:** Saturday 14:00.

This file is my live tracker. I tick items as they finish and add notes to the decision log.

**Status (Sat 21 Nov, 18:30):** all Track A tasks A1–A8, J1 (my half) and J2 done and merged (PR #6). Extra work today: written police application, PDF report, protected feedback, full UI redesign, round 2 data fix (Roman Urdu + Supreme Court of Pakistan data), calibration safety floor, a legal correction (PPC 319). Open: a hands-on model check with messages written by real people (Sprint 5); real-message collection only if that check fails. Deployment after the deadline.

---

## 1. My scope (Track A: citizen side + supervised ML)

| ID  | Task                                                                       | Type           | Deliverable                                                                                  |
| --- | -------------------------------------------------------------------------- | -------------- | -------------------------------------------------------------------------------------------- |
| A1  | IPC-to-PPC mapping table                                                   | Manual (legal) | `data/mapping/ipc_ppc_map.csv` + notes                                                       |
| A2  | LeSICiN (ILSI) parsing and filtering                                       | ML (data)      | `data/processed/ilsi_clean.csv` + class counts                                               |
| A3  | Synthetic incident stories (English + Roman Urdu), verified by hand        | Manual + ML    | `data/processed/synthetic.csv` + generation note                                             |
| A4  | Preprocessing + TF-IDF with LR / SVM / NB + ablation                       | ML             | `src/preprocess.py`, `src/models/classical.py`, `results/*.csv`, ablation table              |
| A5  | DistilBERT multi-label fine-tuning                                         | ML             | `notebooks/A5_distilbert.ipynb`, `src/models/distilbert_model.py`                            |
| A6  | Calibration (Platt scaling of the top-1 confidence) + abstain logic + safety floor | ML     | Calibrated `predict_scores`, reliability diagram, accuracy-vs-coverage chart                 |
| A7  | LIME explanations ("Why this section?")                                    | ML             | `src/explain.py`                                                                             |
| A8  | Next Steps guide + Incident Analyzer page (now "Report an incident")      | Manual + App   | `docs/next_steps.md`, `data/lookup/helplines.csv`, `app/views/report.py`, `src/analyzer.py`, tests |
| A2b | Supreme Court of Pakistan facts passages as training data (round 2)        | ML (data)      | `src/data/sc_facts.py`, `data/processed/sc_facts.csv`                                         |
| A3b | WhatsApp-style Roman Urdu training messages (round 2)                      | Manual + ML    | `data/processed/synthetic_chat.csv`, `docs/round2_data.md`                                    |
| UI  | App redesign (Home, Report an incident, Student Corner, theme)             | App            | `app/Home.py`, `app/legal_ui.py`, `app/views/`, `.streamlit/config.toml`, `tests/test_ui_pages.py` |
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
- [x] S1.6 **J1** (AI-written part done in 3.1; only 3 real messages arrived, so a larger real-message collection runs in Sprint 5, task 5.1) Google Form to 7 real people (3–5 incidents each, about 25–35 real descriptions, `source=real`); generate the rest of my half of the test set with a different AI tool and a different prompt from A3 (to avoid leakage); write it at the level of informal citizen language; save as `source=llm_test`, never `real`
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

### Sprint 3: Sat 00:30–01:00 + 11:30–12:15: the citizen product, the test set, the hybrid ✅ core done

| #       | Task                          | What I get                                                      | Commit message                                                                                      |
| ------- | ----------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| ✅ 3.1  | **J1** held-out test set      | `data/test/test_sf.csv` (real + AI-written, tagged by `source`) | `J1: held-out test set with real and AI-written descriptions, tagged by source`                     |
| ✅ 3.2  | Evaluation                    | all models on the test set → `results/`                         | `Eval: Track A models on held-out test set, split by language and source`                           |
| ✅ 3.3  | **A8** Next Steps + helplines | `docs/next_steps.md`, `data/lookup/helplines.csv`               | `A8: Next Steps guide and source-checked helplines`                                                 |
| ✅ 3.4  | **A8** Incident Analyzer page | `app/pages/1_Incident_Analyzer.py`, `src/analyzer.py`           | `A8: Incident Analyzer page with top-3 sections, legal facts, abstain and explanations`             |
| ✅ 3.5  | **A8** tests                  | `tests/test_analyzer.py`                                        | `A8: tests for analyzer logic (theft, harassment, fraud, Roman Urdu, empty, non-crime)`             |
| ✅ 3.0  | Speed-up for LIME             | batch scoring + cached calibration (0.07 s instead of >60 s)    | `A6/A7: batch scoring and cached calibration for fast LIME explanations`                            |
| ✅ 3.5b | **J2** hybrid LR × retrieval  | `src/hybrid.py`, `src/models/hybrid.py`, `docs/J2_hybrid.md`    | `J2: hybrid of TF-IDF LR and B4 retrieval; beats both on test, not adopted per pre-registered rule` |
| ✅ 3.6  | PR                            | PR #5 `sadia` → `main` merged                                   | (no commit)                                                                                         |
| ✅ 3.7  | Extra 1                       | written police application (darkhwast), see D17                 | `New feature: written police complaint (darkhwast) generator, English and Urdu, with delay field`  |
| ✅ 3.8  | Extra 2 + 3                   | PDF report (Urdu RTL) + feedback (CSV / GitHub Issues)          | `Extras: PDF report with Urdu RTL layout, consent-based feedback to CSV / GitHub Issues`           |
| ✅ 3.9  | Audit                         | fresh-clone check of the whole branch, fix for missing model    | `Fix fresh-clone crash (auto-train missing model), dedupe requirements, remove stale xfail`        |

### Sprint 4: Sat 15:30–18:30: UI redesign, round 2 data fix, legal correction ✅ done

Started from my own review of the app as a real user (UI list with screenshots) and an honest look at the data.

| #       | Task                          | What I get                                                                                     | Commit message                                                                                              |
| ------- | ----------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| ✅ 4.1  | UI: theme + Home              | legal theme (light/dark), welcome page, sidebar menu, developer menu hidden                     | `UI: legal theme, welcome page, sidebar navigation, developer menu hidden`                                  |
| ✅ 4.2  | Helplines nationwide          | helplines by province, next steps without Punjab-only advice                                    | `Helplines and next steps for all provinces, not only Punjab`                                               |
| ✅ 4.3  | Report page                   | abstain gives no legal route, women-only notes, case law inside, protected feedback, loader     | `Report page: no legal route when unsure, women-only notes, case law inside, verified expert feedback, visible loading` |
| ✅ 4.4  | Student Corner                | learn by topic, look-alikes, quiz with setup and results, case law; UI tests                    | `Student Corner: learn by topic, look-alikes, quiz with setup and results, case law; UI tests`              |
| ✅ 4.5  | Normaliser                    | chat spellings (kl, mn, tw, mara...)                                                           | `Roman Urdu normaliser: map common chat spellings (kl, mn, tw, mara, choot...)`                             |
| ✅ 4.6  | **A3b** Roman Urdu chat data  | 280 messages, 10 per section, checked against the test set                                     | `A3b: 280 WhatsApp-style Roman Urdu training messages, 10 per section, checked against test set`            |
| ✅ 4.7  | **A2b** Pakistani court data  | 178 Supreme Court of Pakistan facts passages, section numbers masked                           | `A2b: Supreme Court of Pakistan facts passages as training data, section numbers masked`                    |
| ✅ 4.8  | Split + retrain               | original split unchanged; retrain with A4 settings                                             | `Add round 2 data with original split unchanged; retrain with A4 settings, no new grid search`              |
| ✅ 4.9  | Safety floor + J1 re-run      | threshold never below 0.70                                                                     | `Calibration safety floor 0.70 (stops non-crime answers after retraining); re-run J1 test`                  |
| ✅ 4.10 | Round 2 report                | `docs/round2_data.md`, `src/round2_ablation.py`, `tests/test_round2.py`                        | `Round 2: data ablation, report with limitations, and tests`                                                |
| ✅ 4.11 | Legal fix 319                 | display corrections, 2 quiz questions hidden, `docs/content_fixes.md`                          | `Fix legal error: PPC 319 is qatl-i-khata, not hurt; hide 2 quiz questions with wrong answers; note for Track B` |
| ✅ 4.12 | **J2** re-run                 | hybrid with the round 2 model                                                                  | `J2 re-run with round 2 model: hybrid adds +1.1 val top-3, below adoption margin, LR stays`                 |
| ✅ 4.13 | Merge main + PR #6            | Abdul's grid re-run merged; my A4 ablation table restored; PR #6 merged (merge commit)          | `Restore A4 ablation table removed when the grid search was re-run`                                         |

### Sprint 5: Sat 18:30–20:00: hands-on model check, then submit

| #   | Task                                   | What I get                                                                                   |
| --- | -------------------------------------- | -------------------------------------------------------------------------------------------- |
| 5.0 | ✅ Crime gate experiment (D30)          | measured, not good enough yet, not connected to the app                                      |
| 5.1 | Hands-on check (D29)                    | about 20 messages written by me and friends in our own words, run with `python -m src.quick_check` |
| 5.2 | Decide with the pre-set rule (D29)      | pass → no extra data now; fail → real-message collection (D28) after the deadline            |
| 5.3 | Final push before the deadline         | everything merged into `main`                                                                |

### After the deadline (future work)

1. **Deployment** for real users (Streamlit Community Cloud; feedback token and admin key as secrets).
2. **Real-message collection** (D28) if the check fails, and over time through the verified feedback form.
3. **"Your rights" card** (rule-based, not ML): Constitution Art. 9, 10 (grounds of arrest, lawyer, magistrate within 24 h), 10A, 13, 14 (no torture), 25, and the habeas corpus route (Art. 199) for illegal detention. Note: FIRs cite offence sections (PPC, special laws), not Constitution articles; the Constitution is used for rights, writs and bail. Court routes must be re-checked after the 26th (2024) and 27th (2025) amendments.
4. **Constitution module** in the Student Corner (fundamental rights Art. 8–28, court routes).
5. **Special laws often seen in FIRs:** PECA 2016 (online harassment), workplace harassment law, acid attacks (PPC 336-A/B), Arms Ordinance.
6. DistilBERT retrained on round 2 data; Track B fixes (labels.json 319, quiz, evaluate.py macro-F1); Abdul's J1 half for the blind kappa check.

### Extras (my optional pool), in priority order

Done: 1, 2, 3 (see 3.7, 3.8). Not started: 4, 5.

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
- A PR into `main` at the end of Sprints 2 and 3; Abdul reviews and merges. Done so far: PR #3 (A1), #4 (Sprint 2), #5 (Sprint 3), #6 (Sprint 4, merge commit so every commit stays visible).
- Large raw data (ILSI download, model weights) is never committed. It goes in `.gitignore`; only scripts, processed CSVs and results are committed.

---

## 6. Decision log

| #   | Date   | Decision / finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | 19 Nov | `labels.json` uses IPC meanings for **307** ("attempt to commit qatl-i-amd") and **319** ("hurt"). In the PPC after the Qisas and Diyat law, s.307 = cases where qisas is not enforced, s.319 = punishment of qatl-i-khata, and attempted qatl-i-amd = s.324. The lookup table already treats 319 as qatl-i-khata, so the two files disagree. Raised as a GitHub Issue for Abdul; it must be fixed before any training.                                                                                                                                 |
| D2  | 19 Nov | J1 test set: about 25–35 real descriptions from 7 people via Google Form (`source=real`); the rest AI-generated in a realistic citizen style (time constraint). It is tagged `source=llm_test` and reported as such; it is generated with a different tool and prompt from the A3 training stories so the test set does not mirror the training data. The deployed feedback button (extra 3) is how real-user data gets collected later.                                                                                                                |
| D3  | 19 Nov | ILSI (LeSICiN, Zenodo record 6053791) licence is **CC BY 4.0**; it has train/dev/test JSONL files (id, sentences, cited labels) and the statute texts in `secs.jsonl`. Only the data files are needed; the 2.3 GB sent2vec model is skipped. This fills the "[Check Zenodo]" cells of the proposal.                                                                                                                                                                                                                                                     |
| D4  | 19 Nov | Related work for the report: ILSIC (Paul et al., EACL 2026 Findings, arXiv 2602.00881) finds that models trained only on court judgments do poorly on laypeople's queries. This independently supports our design (synthetic citizen-style stories + a real-person test set). If its lay-query data is publicly released, consider it as extra training data in A2 (check licence first).                                                                                                                                                               |
| D5  | 20 Nov | The 307/319/441 Issue is still open, so Track A handles it without editing Abdul's files: **307** gets no training examples (it is not an offence a citizen can report in the PPC, so the model should never predict it); **319** is trained with the PPC meaning, qatl-i-khata (it matches the lookup table and sections.json); **441 + 447** trespass examples carry both labels (legally both apply), and the app shows them as one result. Revisit if Abdul changes labels.json.                                                                    |
| D6  | 20 Nov | ILSI is used from partial files. Stated in the A2 report: the case count is smaller than the full dataset, but every case kept is complete and valid. ILSI is only a supplement; most citizen-style training data comes from A3.                                                                                                                                                                                                                                                                                                                        |
| D7  | 20 Nov | A3 legal review (`docs/A3_review_fixes.md`): 6 of 84 sampled stories were wrong; the same error patterns were then swept across all 560 stories, so 20 stories were corrected and 557 remain. Main rules: bruises alone are not jurh (337-F needs a real wound); blocking someone's way = 339, keeping them inside = 340.                                                                                                                                                                                                                               |
| D8  | 20 Nov | LR grid: the best C=16 sat at the edge of the grid, so the grid was extended to C=64. C=64 was worse (top-3 0.887 vs 0.904), so C=16 is a true optimum.                                                                                                                                                                                                                                                                                                                                                                                                 |
| D9  | 20 Nov | Ablation (`results/ablation.csv`): trained on ILSI only, citizen-story top-1 is **0.130**, versus 0.757 for synthetic only. This is the domain shift, measured. Synthetic + ILSI is kept: same citizen accuracy (1-story difference), better Roman Urdu micro-F1 (0.807 vs 0.746), and it still handles court-style text (0.626 vs 0.193).                                                                                                                                                                                                              |
| D10 | 20 Nov | DistilBERT (lr 5e-5, best at epoch 5) does worse than TF-IDF + LR on citizen text (top-1 0.652 vs 0.748), and much worse on Roman Urdu (0.407 vs 0.815): English-only pre-training, plus only about 440 citizen stories. **The app uses calibrated TF-IDF + LR.**                                                                                                                                                                                                                                                                                       |
| D11 | 20 Nov | Calibration v1 (temperature over all 30 labels) made ECE worse, because about 29/30 label-cells are negatives. Switched to Platt scaling of the top-1 confidence, which is what the app shows. LR cross-fit ECE 0.254 → 0.191; abstain threshold 0.70 → answers 63% of cases at 87.5% top-1 / 98.6% top-3. DistilBERT was already calibrated (0.125); Platt scaling did not help it (reported as is).                                                                                                                                                   |
| D12 | 20 Nov | Found in the shared `src/evaluate.py`: per-section false positives are never counted, so its "macro-F1" behaves like macro-recall and is too high. Track A uses `src/metrics.py` (true macro-F1); reported to Abdul in PR #4.                                                                                                                                                                                                                                                                                                                           |
| D13 | 21 Nov | Planned "non-crime negatives" retraining was **not needed**: on the held-out test the calibrated LR abstained on 16/16 non-crime messages (threshold 0.70). The `test_non_crime_abstains` test stays as a non-strict xfail guard (later made a normal test in 57dc296; see D24 for the safety floor).                                                                                                                                                                                                                                                                                                                       |
| D14 | 21 Nov | **Held-out test (J1, 162 crime + 16 non-crime, ChatGPT + real people):** LR top-1 0.765 / top-3 0.876 (validation 0.748 / 0.904), so it holds on a different generator. Roman Urdu top-1 0.690 (val 0.815): ChatGPT's spelling differs. Answers 58% of cases at 92.6% top-1. DistilBERT 0.611, confirming D10. Weakest sections: 382 (F1 0.44) and 403 (0.43). Real people: 0/3 top-1, 2/3 top-3; far too few to measure, but real messages are shorter and vaguer.                                                                                     |
| D15 | 21 Nov | **J2 hybrid** (w × LR + (1−w) × retrieval, w = 0.4 chosen on validation): beats both models on validation **and** test (test top-1 0.784, top-3 0.920, Roman Urdu 0.724 vs LR 0.765 / 0.876 / 0.690; retrieval alone 0.414 / 0.710 / 0.224), so the models make different mistakes. **Not adopted in the app**: the rule fixed before testing (validation top-3 gain ≥ 2 pts) gave +1.7 pts. The rule is kept to avoid test-set leakage; adoption is to be re-checked on Abdul's half of J1 (unseen data). Lesson: the rule should have included top-1. |
| D16 | 21 Nov | Merged Abdul's overnight main (B3–B8). He had added a model selector to my Incident Analyzer page; the A8 page replaces it and keeps his B4 model as a "compare with retrieval" panel (agree/disagree signal), so his work stays visible. A copy-paste typo committed in c1de99d (`tfidf_lr.py`) was fixed in 3fc5144.                                                                                                                                                                                                                                  |
| D17 | 21 Nov | "FIR generator" changed after discussion: **police write the FIR themselves (s.154 CrPC)**, so the app generates the citizen's **written application to the SHO (darkhwast)** in English and Urdu from the description and the user's details, with a delay-reason field. It is a template, not ML. For non-cognizable sections the app says the police may refer the matter to a Magistrate (s.155). |
| D18 | 21 Nov | Feedback cannot poison the model: feedback **never retrains anything automatically**. Quick thumbs ratings are stored as ratings only. Expert corrections need a role, a Bar Council licence / enrolment number (or university + roll number), the correct sections and a legal reason; every record is saved as `unverified`, and only team-verified expert rows may ever be used for training (`verified_expert_labels()`). Max 3 submissions per session; incident text stored only with consent; credentials never posted to GitHub Issues. |
| D19 | 21 Nov | Urdu PDF: Urdu needs shaping and right-to-left order. Fixed with arabic-reshaper + python-bidi, wrapping lines **before** reordering, and protecting left-to-right runs (CNIC, phone numbers) with LRE/PDF marks. Regression test with pdfplumber. |
| D20 | 21 Nov | Fresh-clone audit: model weights are git-ignored, so a new machine crashed. The model now trains itself on first start (about a minute) with the A4 setting, thread-safe, and the app starts this in the background when anyone opens the Home page. |
| D21 | 21 Nov | UI redesign from my own review as a user: citizens and students separated; Evaluation shown only to the team (`LEGAL_HELPER_ADMIN=1`); example buttons and names removed from the UI; the disclaimer moved to the bottom plus a warning on Home. **When the model abstains, no legal route is shown** (no FIR steps, no application, no PDF). Women-only notes: 354 and 354-A protect a woman; **509(ii) (sexual harassment) is gender-neutral**; display only, ranking unchanged. #2/#3 results under 40% are listed in one line. Helplines for all provinces, each with a source; a KP police-complaint number could not be verified, so none is shown. Track B's original pages and tests are left untouched; the new pages reuse Track B data and case search. |
| D22 | 21 Nov | **Data gap, measured honestly.** Only 442 training rows looked like citizen text, only **140 were Roman Urdu (3–8 per section)**, there was no Pakistani text, and chat spellings were not normalised. A real hostel message (hurt + threat) made the model abstain. Fix: 280 WhatsApp-style Roman Urdu messages (A3b, max similarity to any test message 0.47), 178 Supreme Court of Pakistan facts passages with section numbers masked (A2b), and 50+ chat spellings. Original split unchanged, hyperparameters unchanged. **J1: top-1 0.765 → 0.827, top-3 0.877 → 0.951, Roman Urdu top-1 0.690 → 0.862, coverage 58% → 70% at 92% top-1.** Real messages still 0/3: more real data is the next step (D28). |
| D23 | 21 Nov | The Supreme Court of Pakistan data does not help citizen messages on the test set (ablation D vs B), but **the final configuration was chosen on validation**: "all data" ≥ "chat only" on every validation subset (Pakistani court validation 0.69 → 0.83), so it is kept. TF-IDF SVM is now slightly ahead of LR on the test set; LR stays because models are chosen on validation, never on the test set. |
| D24 | 21 Nov | **Safety floor.** After retraining, the accuracy rule lowered the abstain threshold to 0.55 and the app answered non-crime messages (a wrong birthday cake → "302 murder" at 66%). Cause: validation has no non-crime text. The threshold now never goes below the round-1 value 0.70 (`MIN_THRESHOLD`, tested); 16/16 non-crime messages are refused again. Lowering it would need non-crime validation data first. |
| D25 | 21 Nov | **Legal error found in shared content:** labels.json and two quiz questions (quiz_007, quiz_008) treat **PPC 319 as hurt**; it is qatl-i-khata (hurt is s.332/337). The Student Corner corrects the name, hides the two questions (58 remain) and renames the 319 distractors; the source files are Track B's, so the fix list is in `docs/content_fixes.md` for Abdul. Continues D1/D5. |
| D26 | 21 Nov | J2 re-run with the round 2 model: w = 0.7, validation top-3 +1.1 pts (below the 2-pt rule), test top-1 unchanged (0.827), top-3 +0.6 pts. **Not adopted, LR stays.** The hybrid helped in round 1 because LR was weak on Roman Urdu; retrieval is English-only (Roman Urdu top-1 0.22) and now adds little. |
| D27 | 21 Nov | Before PR #6, Abdul's main (grid re-run) was merged into `sadia`. Re-running the grid rewrites `docs/A4_results.md` and drops the ablation table (D9), so my version was restored. PR #6 merged with a merge commit, not squash, so the full history stays visible. |
| D28 | 21 Nov | Real-message plan: about 100 **prompted messages written by real people** (32 situations covering all 28 citizen sections, 4 two-offence cases and 12 non-crime cases; writers use their own words, no legal terms, no personal data). **Split by person, decided before reading**: first group = test, the rest = later training. Labels are assigned by us after reading, not taken from the situation picked. Reported as "prompted", not spontaneous. |
| D29 | 21 Nov | **Scope for the deadline.** Slides and viva preparation are not part of this plan; deployment and new features come after the deadline. Before collecting more data, a hands-on check with about 20 messages written by real people (me + friends, own words, never shown to the model before). **Rule fixed before running it:** pass if (a) at least 70% of crime messages have a correct section in the top 3 or are honestly refused, (b) no more than 1 non-crime message gets a confident answer, and (c) no confident answer is dangerously wrong (e.g. murder for a theft). Pass → no extra data now; fail → real-message collection (D28). |
| D30 | 21 Nov | **Found before the hands-on check: the model has no "not a crime" option.** "my landlord wont return my deposit" → 337-F (bodily injury) at 78%: the 30-section model must always pick an offence, and the 70% threshold does not stop every everyday complaint. Tried a separate **crime / not-a-crime gate** (TF-IDF + LR; 666 citizen crime messages vs 140 new non-crime messages, `data/processed/non_crime.csv`, max similarity to any test message 0.37). Best validation setting passes 98% of crimes but stops only 82% of non-crime messages (J1 non-crime: 44%), and it would wrongly block "my landlord beat me when I asked for my deposit" (0.46), which is worse than the problem. **Not connected to the app**; kept as a measured experiment (`src/models/crime_gate.py`, `results/crime_gate.json`). It needs several hundred varied, ideally real, non-crime messages; the real-message form collects them (D28). |
