"""Unit tests for `_extract_score` in the perturbation probe.

The probe lives in `core/llm_probe/resume_screening`. Locks in the contract
that the score must be on a `Score: X` (or `Score = X`) line — falling
back to "any 1-10 number" produces dangerous false positives when the
LLM's prose contains years of experience or other noise digits.
"""

from __future__ import annotations

from nyayalens.core.llm_probe.resume_screening import _extract_score


def test_extracts_score_with_colon() -> None:
    assert _extract_score("Score: 7.5\nReasoning follows.") == 7.5


def test_extracts_score_with_equals() -> None:
    assert _extract_score("Score = 8") == 8.0


def test_extracts_score_ten_exactly() -> None:
    assert _extract_score("Score: 10") == 10.0


def test_returns_none_when_label_missing() -> None:
    # Prior regex would have grabbed "5" from "5 years"; the new contract
    # rejects un-labelled candidate scores to prevent false positives.
    assert _extract_score("I'd give 7/10 — 5 years of experience.") is None


def test_returns_none_for_empty_text() -> None:
    assert _extract_score("") is None


def test_returns_none_when_score_out_of_range() -> None:
    assert _extract_score("Score: 99") is None
