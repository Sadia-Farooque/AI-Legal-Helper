# Data Specification & Standards

This document specifies the unified data standard for the **AI Legal Helper for Pakistan** project. All datasets across all stages (`data/raw/`, `data/processed/`, and `data/test/`) must conform to this schema.

## Canonical CSV Schema

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique record identifier (e.g. `syn_0001`, `ilsi_0123`, `sc_0045`, `real_0012`) | `"syn_0042"` |
| `text` | string | Raw or normalized incident narrative | `"Two armed men stopped my motorcycle and snatched my phone and wallet."` |
| `sections` | string (JSON array) | List of applicable PPC section numbers | `["392", "34"]` |
| `primary_section` | string | Single primary section under which the offence is primarily categorized | `"392"` |
| `language` | string | Language code: `"en"` (English) or `"roman_ur"` (Roman Urdu) | `"en"` |
| `source` | string | Origin tag: `"sc"` (Supreme Court), `"ilsi"` (Indian LeSICiN), `"synthetic"` (LLM generated), `"real"` (Real-person test set) | `"synthetic"` |
| `split` | string | Dataset partition: `"train"`, `"val"`, or `"test"` | `"train"` |

## Section ID Format
- All sections must match the keys in `src/labels.json`.
- Standard sections: `"302"`, `"379"`, `"392"`, `"420"`, etc.
- Hyphenated or letter-suffixed sections: `"354A"`, `"489-F"`, `"337-A"`, `"337-F"`.

## Split Rules
1. `real` data is strictly reserved for `test` split (frozen evaluation).
2. Synthetic variations of the same scenario must not cross between `train` and `val`.
