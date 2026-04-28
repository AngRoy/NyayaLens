"""Unit tests for `RegexPIIRecognizer`.

The MVP recogniser is intentionally regex-only (ADR 0003). It must catch
common Indian formats AND international E.164 / US / UK phone numbers, or
the privacy filter will under-redact uploads from non-Indian datasets.
"""

from __future__ import annotations

import pytest

from nyayalens.adapters.inmemory import RegexPIIRecognizer


@pytest.fixture
def recognizer() -> RegexPIIRecognizer:
    return RegexPIIRecognizer()


def _entity_types(rec: RegexPIIRecognizer, text: str) -> set[str]:
    return {m.entity_type for m in rec.recognize(text)}


@pytest.mark.parametrize(
    "phone",
    [
        "9876543210",  # IN bare 10-digit
        "+91 9876543210",  # IN E.164 with space
        "+91-9876543210",  # IN E.164 with hyphen
    ],
)
def test_recognises_indian_phone_formats(recognizer: RegexPIIRecognizer, phone: str) -> None:
    assert "PHONE_NUMBER" in _entity_types(recognizer, phone), phone


@pytest.mark.parametrize(
    "phone",
    [
        "+1 415 555 0123",  # US E.164
        "+1-415-555-0123",  # US with hyphens
        "+44 20 7946 0958",  # UK landline
        "+33 1 42 86 82 00",  # France
        "+49 30 901820",  # Germany
    ],
)
def test_recognises_international_phone_formats(recognizer: RegexPIIRecognizer, phone: str) -> None:
    assert "PHONE_NUMBER" in _entity_types(recognizer, phone), phone


def test_does_not_flag_short_digit_runs_as_phone(recognizer: RegexPIIRecognizer) -> None:
    # 6-digit pin code or year — must not be misclassified as a phone number.
    assert "PHONE_NUMBER" not in _entity_types(recognizer, "560001 2024")


def test_email_still_recognised(recognizer: RegexPIIRecognizer) -> None:
    assert "EMAIL_ADDRESS" in _entity_types(recognizer, "alice@example.test")
