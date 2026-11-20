"""Unit tests for Task A2 (src/data/ilsi_parse.py). These need no downloaded data.

Run:  python -m pytest tests/test_ilsi_parse.py -q
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.ilsi_parse import (  # noqa: E402
    load_ipc_to_ppc, map_labels, mask_statutes, normalize_ipc_label, build_text,
)


def test_normalize_label_spellings():
    assert normalize_ipc_label("Section 302") == "302"
    assert normalize_ipc_label("Section_364A") == "364A"
    assert normalize_ipc_label("IPC_354-B") == "354B"
    assert normalize_ipc_label("379") == "379"
    assert normalize_ipc_label(" section 34 ") == "34"
    assert normalize_ipc_label("no number") is None


def test_mapping_uses_a1_table_and_respects_traps():
    m = load_ipc_to_ppc()
    assert m["307"] == "324"           # IPC attempt to murder -> PPC 324
    assert "324" not in m              # IPC 324 (hurt by weapon) must never be mapped
    assert m["364A"] == "365-A"        # kidnapping for ransom
    assert m["341"] == "339" and m["342"] == "340"


def test_map_labels_drops_unmapped_and_dedupes():
    m = load_ipc_to_ppc()
    ppc, kept, dropped = map_labels(["Section 307", "Section 324", "Section 34", "Section 307"], m)
    assert ppc == ["324"]
    assert "324" in dropped and "34" in dropped
    ppc, _, _ = map_labels(["Section 499", "Section 500"], m)
    assert ppc == ["500"]


def test_mask_statutes_removes_citations():
    text = "He was charged u/s 302/34 IPC and under Section 379 of the Indian Penal Code for theft."
    masked, n = mask_statutes(text)
    assert "302" not in masked and "379" not in masked and "IPC" not in masked
    assert "[SEC]" in masked and n >= 2
    assert "theft" in masked


def test_mask_keeps_ordinary_numbers():
    masked, _ = mask_statutes("He took Rs. 500 and 3 phones at 10 pm.")
    assert "500" in masked and "3 phones" in masked


def test_build_text_truncates():
    text, n_full, _ = build_text(["word " * 1000])
    assert n_full == 1000 and len(text.split()) == 400
