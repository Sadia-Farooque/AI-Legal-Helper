# A1 Verification Report: IPC-to-PPC Mapping Table

**File verified:** `data/mapping/ipc_ppc_map.csv` (30 rows, one per section in `src/labels.json`)
**Owner:** Sadia Fatima (Track A)
**Date:** 19 Nov 2026
**Method:** AI-assisted legal source check (Claude, Anthropic), reviewed by the owner
**Automated check:** `tests/test_mapping.py` (5 tests, all passing)

---

## 1. Why this table exists

The ILSI (LeSICiN) training data is Indian court cases labelled with **Indian Penal Code (IPC)** section numbers. Our app predicts **Pakistan Penal Code (PPC)** sections. Both codes come from the same 1860 text, so most numbers still mean the same offence. But Pakistan rewrote whole chapters (Qisas and Diyat 1990/1997, the 1984 and 2002 ordinances, the 2010 harassment amendment), and India added its own sections (1993, 2013). If IPC labels were copied across unchecked, the model would learn the wrong law for some sections.

---

## 2. How the verification was done

1. **List every claim.** Each row makes one or more checkable claims: what the PPC section means, what the IPC section with the same number means, and whether the facts of the offence are equivalent.
2. **Rank claims by risk.** A wrong "use ILSI = yes" corrupts the training data, so the 6 "no" rows, the 5 rows mapped across different numbers, and every "Changed" row were checked one by one against primary or court sources.
3. **Prefer primary sources,** in this order:
   1. Official or government text (Law and Justice Commission of Pakistan, provincial government gazettes, UNODC SHERLOC legislation database, Indian Parliament / Supreme Court of India)
   2. Court judgments quoting the section verbatim (Sindh High Court, Federal Shariat Court, Supreme Court of Pakistan reports)
   3. Reputable secondary sources (Dawn, UN Women) only for dates and context
4. **Look for counter-evidence,** not just confirmation, especially for "same number, different offence" claims.
5. **Fix errors in the CSV and re-run the automated tests.**

---

## 3. Results: high-risk claims

| # | Claim in the table | Verdict | Evidence |
|---|---|---|---|
| 1 | PPC 307 is **not** "attempt to murder"; it is "cases in which qisas for qatl-i-amd shall not be enforced" | ✅ Confirmed | A Sindh High Court judgment (Ghulam Shabir v. State, 2004 YLR 2163) lists s.307 PPC as cases in which qisas shall not be enforced; the Federal Shariat Court (S.P. No. 02-I-2011) quotes the same title. |
| 2 | PPC 324 = attempt to commit qatl-i-amd, inserted by the 1990 Qisas and Diyat ordinance | ✅ Confirmed | A Sindh High Court judgment states s.324 PPC was inserted after the 1990 Criminal Law (Second Amendment) Ordinance to deal with attempted qatl-i-amd; PLJ 2023 Cr.C. 539 and 1994 SCMR 2051 agree. |
| 3 | IPC 324 = voluntarily causing hurt by dangerous weapons (a **different** offence from PPC 324) | ✅ Confirmed | IPC bare text (Indian Kanoon, AdvocateKhoj). This is the most dangerous trap: naive mapping would label knife-wound cases as attempted murder. |
| 4 | PPC 319 = punishment of qatl-i-khata; IPC 319 = definition of hurt | ✅ Confirmed | Several Pakistani legal sources give s.318 as the definition and s.319 as the punishment of qatl-i-khata; IPC 319 defines hurt (iPleaders, IPC text). `labels.json` uses the IPC meaning, which is the conflict raised in our GitHub Issue. |
| 5 | Pakistani hurt law is organised by injury type (itlaf, shajjah, jurh, other hurt), with no 1:1 IPC equivalent | ✅ Confirmed | A Sindh High Court judgment quotes s.332(2) listing the five kinds of hurt; police training material (Police College Sihala) gives s.337 shajjah and s.337-B jurh. |
| 6 | PPC 354A (1984) = assault and stripping a woman of her clothes, exposed to public view | ✅ Confirmed | Text and insertion by Ordinance XXIV of 1984 (data.jpp.org.pk; Law and Justice Commission Report 42). |
| 7 | IPC 354A (2013) = sexual harassment and IPC 354B = intent to disrobe, so the same number means a different offence | ✅ Confirmed | Criminal Law (Amendment) Act 2013 (PRS India; Cornell LII summary). |
| 8 | PPC 361 minor = under 14 (male) / under 16 (female) | ✅ Confirmed | Section text on UNODC SHERLOC; 1998 SCMR 1126. |
| 9 | PPC 365-A = kidnapping or abducting for ransom | ✅ Confirmed | Section list on UNODC SHERLOC; a Sindh High Court judgment says it was added by Act III of 1990. |
| 10 | IPC 364A = kidnapping for ransom (inserted 1993) → maps to PPC 365-A | ✅ Confirmed | Criminal Law (Amendment) Act 1993 (Act 42 of 1993), cited by the Supreme Court of India. |
| 11 | Do not confuse with PPC 364-A | ✅ Confirmed | PPC 364-A = kidnapping a person under 14 (UNODC SHERLOC). |
| 12 | PPC 489-F (dishonoured cheque) is Pakistan-only, inserted in 2002 | ✅ Confirmed | Law and Justice Commission of Pakistan Report 129: inserted by Criminal Law (Amendment) Ordinance LXXXV of 2002, dated 25-10-2002. |
| 13 | PPC 509 was widened in 2010 to cover sexual harassment | ✅ Confirmed, **wording corrected** | UN Women, and the amending text (Criminal Law (Amendment) Act, 2009). The old note wrongly said "Act 2010" and implied 509 is the workplace law; see Section 4. |
| 14 | PPC 406 punishment differs from IPC | ✅ Confirmed (PPC side) | PPC 406 = up to 7 years (data.jpp.org.pk; 1985 MLD 1367). |
| 15 | PPC 392 punishment differs (minimum term) | ✅ Confirmed | A Sindh High Court judgment: punishment under s.392 PPC is not less than 3 and not more than 10 years. |

---

## 4. Errors found and corrected

| Row | Problem | Correction |
|---|---|---|
| 509 | Said "Criminal Law (Amendment) Act 2010 … including at the workplace". The amending Act's short title is **Criminal Law (Amendment) Act, 2009** (Act I of 2010), and workplace harassment is mainly covered by a separate law, the **Protection against Harassment of Women at the Workplace Act 2010**. | Act name fixed; workplace law named separately; title changed to "Insulting modesty or causing sexual harassment". |
| 500 | Said online defamation "falls under PECA 2016 s.20" as settled fact. It isn't settled: the Islamabad High Court (2022) struck down the "harms the reputation" wording, while the Lahore High Court upheld s.20. | Note now says the scope is contested and must be re-checked before the app shows it. |
| 337-F | The label says "Jurh". Precisely, jurh is defined in s.337-B, and 337-F is the punishment for *ghayr-jaifah* (the common kind of jurh). | Note added. The label is still usable for ordinary body wounds. |

After the corrections, `python tests/test_mapping.py` → **All 5 mapping tests passed.**

---

## 5. Problems found in teammate files (reported, not edited)

Raised as a GitHub Issue, because these files belong to Track B:

1. **307** in `labels.json`, `sections.json` and `ppc_lookup.csv` uses the IPC meaning (attempt to murder). In Pakistan, that offence is s.324, which is already a label, so the same offence appears under two labels.
2. **319**: `labels.json` says "Hurt" (IPC meaning); `ppc_lookup.csv` and `sections.json` say qatl-i-khata (PPC meaning).
3. **441 vs 447**: definition vs punishment of the same offence. The classifier cannot separate them.

---

## 6. Limitations (stated honestly)

- **This is not a lawyer's opinion.** It is a source-based check done with an AI assistant and reviewed by a CS student. Every claim is traceable to a source above, but a practising lawyer or law faculty member should sign off before public deployment.
- **The 18 "Same" rows were checked at category level, not word by word.** These offences (restraint, theft, robbery, extortion, misappropriation, breach of trust, cheating, trespass, defamation, intimidation) come from the original 1860 text, which both countries kept. Punishments were spot-checked for 392 and 406. The definitions were not compared line by line for every row.
- **ILSI label coverage is not yet known.** Whether ILSI contains cases for 364A, 341, 342, 442, etc. is checked in Task A2. Rows whose sources turn out to be empty will be noted there.
- **Law changes.** Rows carry `date_checked = 2026-11-19`; any later amendment would need a re-check.

---

## 7. Sources

**Pakistan (primary and court):**
- UNODC SHERLOC, Pakistan Penal Code ss.302, 359–365A — sherloc.unodc.org
- Law and Justice Commission of Pakistan, Reports 42, 97, 129 — ljcp.gov.pk
- Sindh High Court judgments — caselaw.shc.gov.pk
- Federal Shariat Court, S.P. No. 02-I-2011; Jail Cr. App. 33-K of 2005 — federalshariatcourt.gov.pk
- PLJ Law Site, PPC ss.324, 337-A, 337-F, 354-A — pljlawsite.com
- data.jpp.org.pk, Pakistan Penal Code consolidated text (ss.354, 354-A, 406, 489-F)
- 1994 SCMR 2051 (Muhammad Afsar v. State); 1998 SCMR 1126; 2004 YLR 2163; 1985 MLD 1367

**India:**
- Criminal Law (Amendment) Act 1993 (s.364A) — latestlaws.com; Supreme Court of India, Vikram Singh v. Union of India (2015)
- Criminal Law (Amendment) Act 2013 (ss.354A–354D) — prsindia.org; law.cornell.edu
- IPC s.324 text — indiankanoon.org; advocatekhoj.com

**Context and dates:**
- UN Women Pakistan, legislation on violence against women (509 amendment)
- Dawn (2002: 489-F; 2022: PECA s.20 rulings); The News (2022: IHC on PECA s.20)
