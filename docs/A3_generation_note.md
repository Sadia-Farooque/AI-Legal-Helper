# A3 Generation Note: synthetic citizen incident stories

**File:** `data/processed/synthetic.csv` (560 generated; **557 after review**: 3 removed and 17 corrected, see `docs/A3_review_fixes.md`)
**Owner:** Sadia Fatima (Track A)
**Date:** 20 Nov 2026
**Generator:** an AI assistant (Claude, Anthropic), from the per-section legal guidelines below.
**Checks:** `src/data/review_synthetic.py` (automated) + manual review of a stratified sample (results in `docs/A3_review_log.md`)

---

## 1. Why synthetic data

Our users write short, informal descriptions ("2 larkay bike par aaye aur mobile cheen liya"), while ILSI is long, formal Indian court text. Recent work on Indian statute identification (ILSIC, Paul et al., EACL 2026 Findings) reports that models trained only on court judgments perform poorly on queries written by laypeople. Synthetic stories close this domain gap. They also give the only training data for the 9 labels that ILSI does not cover (A2 report): 319, 337-A, 337-F, 354A, 365-A, 382, 403, 441, 489-F.

## 2. Generation instructions (the "prompt template")

Every story was written to these rules:

1. **Voice:** a citizen reporting what happened to them, a relative or a neighbour, in the first or third person, the way they would tell a friend or a police moharrir.
2. **Facts, not law:** describe what happened. Never use section numbers or legal terms (qatl-i-amd, dacoity, trespass, extortion, breach of trust, defamation, misappropriation, intimidation, shajjah, jurh). Everyday words people actually use are allowed: chori, snatching, fraud, bhatta, kidnap.
3. **Realism:** Pakistani places (Karachi, Lahore, Multan, Gujranwala, villages, katcha area), Pakistani context (JazzCash, OLX, committee, bhatta, jirga, brick kiln), money in rupees or lakh.
4. **Variety:** victim, relative or witness as narrator; 10–60 words; some lower-case, missing punctuation and typos, like real typing.
5. **Roman Urdu:** natural spellings, as people type them (kar/kr, nahi/nahin, mein/me); mixed English words allowed.
6. **Volume:** 12 English + 5 Roman Urdu per section covered by ILSI; 16 English + 7 Roman Urdu for the 9 sections ILSI does not cover.
7. **Multi-offence stories (about 10%):** only combinations that are legally sound together (e.g. robbery + attempted murder, house-trespass + threats, theft from a house + receiving stolen property).
8. **Sensitive offences (354, 354A, 509):** factual and non-graphic. They describe the act, not sexual detail.

## 3. Per-section scenario guidelines (legal accuracy)

| Section   | What a story must contain                                                                                                          | What it must NOT be                                                           |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 302       | Intentional killing (shot, stabbed, strangled, poisoned)                                                                           | Accident or negligence (→ 319)                                                |
| 319       | Death by mistake or negligence: gun accident, mistaken identity while hunting or guarding, careless work                           | Road accident (that is s.320, not in the label set); intentional killing      |
| 324       | Clear intent to kill, victim survives                                                                                              | Ordinary injury without intent to kill (→ 337-A/F)                            |
| 337-A     | Injury to the **head or face** (cuts, fractures of the nose or skull, face wounds)                                                 | Body injuries (→ 337-F); broken teeth (a different PPC category)              |
| 337-F     | Wounds (skin broken, cut, bleeding), fractures or dislocations on the **body** other than head or face, not reaching a body cavity | Head/face injuries; bruises or swelling alone (that is 'other hurt', s.337-L) |
| 339       | Blocking someone's way in a direction they have a right to go                                                                      | Keeping them inside a place they cannot leave (→ 340)                         |
| 340       | Confining someone within limits (locked room, godown, kiln)                                                                        | Only blocking a path                                                          |
| 354       | Force or touch on a woman with intent to outrage modesty                                                                           | Words or gestures only (→ 509)                                                |
| 354A      | Stripping a woman of her clothes **and exposing her to public view**                                                               | Touching only (→ 354)                                                         |
| 363       | Taking a minor (boy under 14, girl under 16) from a guardian                                                                       | An adult (→ 365)                                                              |
| 365       | Adult abducted and kept secretly, no ransom                                                                                        | A ransom demand (→ 365-A)                                                     |
| 365-A     | Kidnapping with a ransom demand                                                                                                    |                                                                               |
| 379       | Taking property without force or entering a house                                                                                  | Inside a dwelling (→ 380); force or threat (→ 392)                            |
| 380       | Theft inside a house, flat, room or hostel                                                                                         |                                                                               |
| 382       | Theft where the thief came **prepared** to cause hurt or restraint (hidden weapon, ropes) but did not use it on the victim         | Weapon shown to the victim (→ 392)                                            |
| 384       | Property or a document delivered **because of** threats                                                                            | Threat only, nothing delivered (→ 506)                                        |
| 392       | Snatching or taking with force or threat (gunpoint, knife, pulling a bag so the victim falls)                                      | 5 or more offenders (→ 395)                                                   |
| 395       | Robbery by **5 or more** people                                                                                                    | Fewer than 5                                                                  |
| 403       | Keeping found or mistakenly received property                                                                                      | Taking from someone's possession (→ 379); entrusted property (→ 406)          |
| 406       | Property **entrusted** and then misused or kept                                                                                    | Deception at the start (→ 420)                                                |
| 411       | Buying or keeping property **knowing** it was stolen                                                                               |                                                                               |
| 420       | Deception that makes the victim hand over money or property                                                                        |                                                                               |
| 441 + 447 | Entering someone's land or premises to occupy it or annoy them; both labels, because 441 defines and 447 punishes (decision D5)    | Entering a house (→ 448)                                                      |
| 448       | Entering a house or dwelling without permission                                                                                    |                                                                               |
| 489-F     | A cheque given for a loan or obligation, dishonoured                                                                               |                                                                               |
| 500       | False statements harming someone's reputation                                                                                      |                                                                               |
| 506       | Threats of death, injury, acid or burning                                                                                          |                                                                               |
| 509       | Remarks, gestures or messages of a sexual nature; demands for sexual favours                                                       | Physical touch (→ 354)                                                        |

## 4. Known simplifications (stated for the report)

- **307** has no stories: in the PPC it is not an offence a citizen can report (A1, D5).
- **Aggravated house-trespass (ss.449–452)** is outside the label set. Stories where trespass leads to murder or attempted murder were labelled with the main offence only, and 448 is used only for simple house-trespass.
- **Online offences** (blackmail with photos, social-media harassment) may also fall under PECA 2016. Only the PPC label is given here.
- **Generator bias:** all stories come from one AI model, so the vocabulary and style are less varied than real users. This is why the held-out test set (J1) uses a **different** generator and real people, and why results are reported separately by source.

## 5. Columns

K3 schema (`id, text, sections, primary_section, language, source=synthetic, split`) plus `group_id` (used by the A4 grouped split so near-identical stories never sit in both train and validation) and `generator`.
