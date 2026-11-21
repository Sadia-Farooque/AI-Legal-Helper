# J1 Test Set: construction and label checks

**Files:** `data/test/test_sf.csv` (162 crime descriptions) and `data/test/out_of_scope_sf.csv` (16 non-crime descriptions).
**Owner:** Sadia Fatima (Track A half of J1). **Built:** 21 Nov 2026.

## Why this test set is independent

- **Different generator:** the training stories (A3) were written by Claude; these were written by **ChatGPT** from a different prompt that describes each situation in plain words, never with section numbers or the A3 scenario rules. This reduces the risk that the model has only learned one AI's writing style.
- **Real people:** messages from people outside the team, collected through a Google Form, kept exactly as typed (spelling included). `source=real`.
- **Never used** for training, grid search, model selection or calibration. Results by source are reported separately, so the AI-written and real-person numbers are never mixed up.

## How it was built

1. ChatGPT received a prompt with 28 crime situations (plain descriptions, one per PPC label; 441 and 447 combined) and one non-crime situation, asking for 4 English + 2 Roman Urdu messages each, messy and realistic, with no legal words.
2. **Each message was checked against the PPC** before receiving its label, because the generator only wrote stories and its stories do not always fit the situation it was given.
3. Messages that did not clearly fit were **dropped**, not relabelled, so that every test label is defensible. Stories that also contained a second offence (usually a threat) got the **extra label**.
4. Real-person messages were labelled by reading them against the same criteria.

## Composition

| Part | English | Roman Urdu | Total |
|---|---|---|---|
| ChatGPT crime messages (after checks) | 103 | 56 | 159 |
| Real people, crime | 1 | 2 | 3 |
| Non-crime (should abstain): ChatGPT 15 + real 1 | 11 | 5 | 16 |

## Label decisions (every change from the generator's situation)

| Message | Decision | Reason |
|---|---|---|
| llm_S01_5 | label +506 | earlier threat to kill ('pehle bhi dhamki di thi') |
| llm_S02_4 | dropped | Building owner delaying repairs: omission, not clearly a rash/negligent act under s.319 (may be qatl-bis-sabab, s.322). Ambiguous. |
| llm_S03_4 | dropped | Pouring petrol at the entrance: intent to kill is unclear (could be mischief by fire). Ambiguous. |
| llm_S03_5 | label +506 | earlier threats ('pehle bhi dhamkiyan') |
| llm_S05_1 | label +506 | attackers now threatening the family |
| llm_S05_2 | dropped | Stab wound to the stomach reaches a body cavity: jaifah (s.337-D), not ghayr-jaifah (337-F). Wrong situation. |
| llm_S06_2 | label +506 | threatened to beat him |
| llm_S06_4 | dropped | Surrounding someone so she cannot leave is closer to confinement (340) than restraint (339). Ambiguous. |
| llm_S06_6 | label +506 | threats while blocking ('dhamkiyan') |
| llm_S10_3 | dropped | Child taken by his own father: a father is a lawful guardian, so this is a custody dispute, not clearly kidnapping. |
| llm_S11_2 | dropped | Adult daughter left voluntarily with a man she knew: abduction not clear from the text. |
| llm_S12_6 | label +506 | threat if police informed |
| llm_S19_1 | dropped | Narrative is self-contradictory (money sent to 'my account', yet 'the person who received it' refuses). |
| llm_S19_2 | dropped | Narrative is self-contradictory (father found the wallet, yet 'the person who answered' refuses to return). |
| llm_S23_3 | dropped | Cutting and taking crops is also theft/mischief; combined labels unclear. |
| llm_S24_3 | label +509 | landlord intruded while she was changing: intrusion on a woman's privacy (s.509) |
| real_001 | labelled 509 | Following a woman in person: closest PPC section is 509 (harassment). Debatable: PPC has no specific in-person stalking offence. |
| real_002 | labelled 506 | Threat to kidnap = criminal intimidation. |
| real_003 | labelled 509 | Demands with a threat to fail = sexual harassment by a person in authority (509). |
| real_004 | labelled out of scope | Not a crime: governance complaint (out of scope). |

## Limitations

- Only 3 real-person crime messages (7 people were asked). Real-person results are reported but are far too few for a reliable estimate; the deployed feedback button (extra 3) is how more real data will be collected.
- Situations are balanced (about 6 messages each), unlike real life where theft and harassment are far more common.
- Labels were checked by the project team with AI assistance, not by a practising lawyer.
