"""Tests for Extra 1 (src/fir_draft.py). Run: python -m pytest tests/test_fir_draft.py -q"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.fir_draft import BLANK, FIRDetails, draft, valid_cnic  # noqa: E402

FULL = FIRDetails(name="Ayesha Khan", relation="Imran Khan", cnic="35202-1234567-8", address="House 5, Gulberg, Lahore",
                  phone="0300-1234567", police_station="Gulberg", incident_date="20-11-2026", incident_time="9:30 pm",
                  place="Main Boulevard", accused="", property_lost="Samsung phone, Rs. 5,000 cash",
                  witnesses="Ali Raza", description="Two men on a bike snatched my phone at gunpoint.",
                  sections=["392", "506"])


def test_english_contains_key_parts():
    t = draft(FULL, "en", today="21-11-2026")
    assert "Section 154 Cr.P.C." in t and "Police Station Gulberg" in t
    assert "392, 506 PPC" in t and "final determination rests with the police" in t
    assert "Two men on a bike snatched my phone at gunpoint." in t      # statement kept verbatim
    assert "unknown person(s)" in t                                        # empty accused -> unknown


def test_urdu_contains_key_parts():
    t = draft(FULL, "ur", today="21-11-2026")
    assert "درخواست برائے اندراج مقدمہ" in t and "154" in t and "392, 506" in t
    assert "تھانہ Gulberg" in t


def test_both_languages_and_blanks_for_missing_fields():
    t = draft(FIRDetails(description="My bike was stolen."), "both", today="21-11-2026")
    assert "To," in t and "بخدمت" in t
    assert BLANK in t                                                      # missing details stay fillable
    assert "may attract" not in t                                          # no sections -> no legal claim


def test_optional_lines_only_when_given():
    t = draft(FIRDetails(description="x"), "en")
    assert "Witnesses" not in t and "Property taken" not in t


def test_cnic_validation():
    assert valid_cnic("35202-1234567-8") and valid_cnic("")
    assert not valid_cnic("3520212345678") and not valid_cnic("35202-123-8")


def test_delay_reason_only_when_given():
    assert "Reason for reporting late" not in draft(FIRDetails(description="x"), "en")
    t = draft(FIRDetails(description="x", delay_reason="I was in hospital"), "both")
    assert "Reason for reporting late: I was in hospital" in t and "تاخیر سے رپورٹ کی وجہ" in t
