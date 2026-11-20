"""Tests for Task A4 preprocessing. Run: python -m pytest tests/test_preprocess.py -q"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.preprocess import normalize  # noqa: E402


def test_lowercase_and_whitespace():
    assert normalize("  Two MEN   snatched\n my Phone ") == "two men snatched my phone"


def test_removes_sec_placeholder():
    assert "sec" not in normalize("He was charged [SEC] for theft")


def test_roman_urdu_variants_are_unified():
    assert normalize("Usne paisay nhi diye") == normalize("usne paise nahi diye")
    assert normalize("mobile cheen kr bhaag gaye") == "mobile cheen kar bhaag gaye"
    assert normalize("bachay ko aghwa kar liya") == "bachay ko agwa kar liya"


def test_english_lookalikes_are_not_mapped():
    assert normalize("he told me") == "he told me"


def test_placeholders():
    out = normalize("Call 0300-1234567 or see https://x.com, sent 5000000")
    assert "phonetoken" in out and "urltoken" in out and "numtoken" in out


def test_empty_and_none():
    assert normalize("") == "" and normalize(None) == ""
