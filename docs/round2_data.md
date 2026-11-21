# Round 2: fixing the data gap (A2b + A3b)

**Owner:** Sadia Fatima (Track A). Messages written with an AI assistant (Claude); labels checked by
Sadia Fatima (AI-assisted legal check). All numbers below are reproducible with the commands at the end.

## 1. Why: what was wrong (diagnosis)

An honest look at the round-1 model showed three problems:

1. **Almost none of the training data looked like what citizens type.** 1,065 of the 1,507 training rows are formal
   Indian court judgments (ILSI). Our own ablation (`results/ablation.csv`) showed a model trained only on them gets
   **13% top-1** on citizen-style stories. The citizen ability came from 442 AI-written stories, and only **140 of
   them were Roman Urdu (3 to 8 per section; 2 sections had none)**.
2. **No Pakistani text at all**, neither citizen nor court.
3. **Chat spelling** (`kl, mn, tw, k, mara, choot, gyi`) was not normalised.

A real user's message showed it: *"mujhe kl mere roomate ne mara ... choot lage hai ... dhamki de hai ..."* (hurt +
threat: 337-F + 506). The model was unsure (340 at 46%) and abstained.

## 2. What we added

| Change | What | Size | Source |
|---|---|---|---|
| A3b | WhatsApp-style **Roman Urdu** incident messages: messy spelling, both genders, mixed cases (hurt + threat, trespass + threat) | 280 (10 per section, 28 sections) → 224 train / 56 val | Written with Claude, labels checked; `data/processed/synthetic_chat.csv` |
| A2b | **Supreme Court of Pakistan** criminal judgments: only the facts passage ("prosecution case", "facts of the case"...), not the court header | 178 of 301 judgments (142 train / 36 val; 123 had no facts passage) | Track B corpus `sc_clean.csv`; `src/data/sc_facts.py` → `data/processed/sc_facts.csv` |
| Normaliser | 50+ chat spellings mapped to one form (`kl→kal`, `mn→mein`, `tw→to`, `mara→maara`...). Words that are also English (`men, may, use, fir`=FIR) are deliberately **not** mapped | – | `src/preprocess.py` |

**Safeguards**
- **Original split unchanged:** the 1,892 original rows keep exactly the same train/val split (0 changes); new data is
  split separately (`src/data/make_splits.py`). So before/after numbers are comparable.
- **No leakage from the test set:** highest character-level similarity between any new message and any test message
  is **0.47** (no message above 0.6; checked in `tests/test_round2.py`).
- **No answer leakage in court text:** every section number and "PPC" mention is masked to `[SEC]` (0 left; tested).
- **Same hyperparameters:** LR C=16 from the A4 grid; no new search (`src/models/retrain.py`), so the gain is from
  data only.
- **Configuration chosen on validation, not on the test set:** "all data" (E) ≥ "chat only" (C) on every validation
  subset (citizen val 0.801 vs 0.795 top-1; Pakistani court val 0.833 vs 0.694), so E was kept.

## 3. Effect of each change (J1 test set, untouched; `results/round2_ablation.csv`)

| Config | n train | Top-1 | Top-3 | Roman Urdu top-1 | English top-1 |
|---|---|---|---|---|---|
| A baseline (round 1) | 1507 | 0.765 | 0.877 | 0.690 | 0.808 |
| B + chat-spelling normaliser | 1507 | 0.765 | 0.883 | 0.690 | 0.808 |
| C + Roman Urdu chat stories | 1731 | 0.846 | 0.951 | 0.879 | 0.827 |
| D + Supreme Court of Pakistan facts | 1649 | 0.765 | 0.889 | 0.690 | 0.808 |
| **E all (final)** | **1873** | **0.827** | **0.951** | **0.862** | 0.808 |

**Reading:** the Roman Urdu chat stories are what helped citizens. The Pakistani court text does not help citizen
messages (it is formal and 75% murder cases), but it makes the model much better on Pakistani court language
(validation 0.69 → 0.83), so it was kept.

## 4. The app's model before and after (with calibration and the abstain rule)

| TF-IDF + LR | Round 1 | Round 2 |
|---|---|---|
| Top-1 / Top-3 | 0.765 / 0.877 | **0.827 / 0.951** |
| Roman Urdu top-1 | 0.690 | **0.862** |
| Messages it answers (coverage) | 58% | **70%** |
| Top-1 when it answers | 0.926 | 0.920 |
| Non-crime messages refused | 16/16 | 16/16 |
| The hostel message | abstain | **506 (83%), then 337-F** |

## 5. A safety problem we found and fixed

After retraining, the calibration rule (lowest threshold with ≥85% accuracy on validation) fell from 0.70 to
**0.55**, and the app started answering everyday complaints: *a wrong birthday cake → "302 murder" at 66%*, a shoe
exchange → 403, an unpaid small loan → 406. Cause: **the validation set has no non-crime text**, so the rule cannot
see this risk. Fix: a **safety floor**: the threshold never goes below the round-1 value 0.70, which was fixed before
the new data existed (`MIN_THRESHOLD` in `src/calibration.py`, tested). Lowering it would first need non-crime
validation data.

## 6. Limitations (say these openly)

- **Still no real citizen data in training.** The new messages are AI-written in a Pakistani style. "Pakistani data"
  is true only for the Supreme Court judgments.
- **Real messages: still 0 of 3 correct first** (3 is far too few to measure). They are short, code-mixed
  ("i feel insecure", "i am so scared") and about stalking, a kidnapping threat and harassment by a teacher, a style
  we have little of. **Collecting real messages is the next and most important step.**
- The test set is 98% ChatGPT-written, so test scores measure "AI-written citizen text", not real users.
- TF-IDF SVM is now slightly ahead of LR on the test set (0.846 vs 0.827 top-1). We keep LR because models are chosen
  on validation, never on the test set.
- DistilBERT was not retrained (needs a GPU). The J2 hybrid numbers refer to the round-1 model.

## 7. Label notes (tricky cases, for the viva)

- In this project **319 = qatl-i-khata** (accidental killing, e.g. a gun going off while cleaning), not hurt. A beating
  is **337-A** (head/face) or **337-F** (rest of the body).
- **509** has a gender-neutral part (ii): one message is a man harassed by his boss (labelled 509).
- **448** (house-trespass) also covers a shop or a mosque room (building used for property or worship); open land is
  **447 + 441**.
- **382** = the thief carried a weapon but did not use it; **392** = force or threat was used.
- **363** = a child taken from the guardian; **365** = an adult taken and hidden; **365-A** = money demanded.

## 8. Reproduce

```
python -m src.data.sc_facts          # Supreme Court facts passages (masked)
python -m src.data.make_splits       # original split unchanged + new data
python -m src.round2_ablation        # table in section 3
python -m src.models.retrain         # retrain LR / SVM / NB with the A4 settings
python -m src.calibration --model tfidf_lr   (also tfidf_svm, tfidf_nb)
python -m src.evaluate_test          # docs/J1_results.md
python -m pytest tests -q
```
