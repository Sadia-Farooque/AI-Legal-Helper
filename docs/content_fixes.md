# Content corrections for Track B files (found during the UI review, 21 Nov)

The Student Corner (Track A UI) corrects these **on display only**. The source files are Track B's, so the real fix
should be made there. After that, the display patches in `app/views/learn.py` can be removed.

## 1. PPC 319 is qatl-i-khata, not hurt

In the Pakistan Penal Code (after the Qisas and Diyat amendments), **s.318 defines and s.319 punishes qatl-i-khata**,
i.e. causing death by mistake of act or fact. Hurt is defined in **s.332** and punished under **s.337 and its
sub-sections** (337-A shajjah, 337-F jurh, 337-J hurt by poison, 337-L other hurt, ...).

| File | Problem | Suggested fix |
|---|---|---|
| `src/labels.json` → `"319"` | title "Hurt (Causing bodily pain, harm, disease, infirmity)"; citizen_term "Physical assault / Causing physical hurt" | title "Punishment of qatl-i-khata"; citizen term "Accidental killing / gun going off by mistake" |
| `data/content/quiz_bank.json` → `quiz_007` | correct answer "Section 319 PPC (Definition & Punishment for Hurt)" for a non-lethal poisoning | correct law is 337-J (outside our 30): replace or remove the question |
| `data/content/quiz_bank.json` → `quiz_008` | correct answer "Section 319 PPC (Hurt)" for torture of a domestic worker | 337 series (outside our 30): replace or remove the question |
| `quiz_bank.json` → `quiz_001`, `quiz_005`, `quiz_009`, `quiz_012` | distractor option names 319 as "Hurt" / "General Hurt" / "Simple Hurt" | rename to "Section 319 PPC (Qatl-i-Khata)" |

`data/content/sections.json` (319 summary and elements) and `data/lookup/ppc_lookup.csv` (319 = Qatl-i-Khata) are
already correct.

## What the UI does until then

- Shows 319 as "Qatl-i-khata (killing by mistake)" everywhere in the Student Corner.
- Hides quiz_007 and quiz_008 (58 questions remain).
- Renames the 319 distractors to "Section 319 PPC (Qatl-i-Khata)".
