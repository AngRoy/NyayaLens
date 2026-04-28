"""Unit tests for `core.llm_probe.resume_screening.run_perturbation_probe`."""

from __future__ import annotations

import pytest

from nyayalens.adapters.mock_llm import MockLLMClient
from nyayalens.core._contracts.llm import LLMPayload, StrictPayload
from nyayalens.core.llm_probe.resume_screening import (
    Variation,
    run_perturbation_probe,
)


def _factory(
    *,
    prompt_template_id: str,
    purpose: str,
    narrative_context: str,
) -> LLMPayload:
    return StrictPayload(
        domain="hiring",
        prompt_template_id=prompt_template_id,
        purpose=purpose,
        narrative_context=narrative_context,
    )


@pytest.mark.asyncio
async def test_probe_reports_no_disparity_when_scores_match() -> None:
    mock = MockLLMClient()
    mock.add_text(
        "probe.resume.v1",
        "probe_perturbation",
        "Score: 8.5\nStrong fit for the role.",
    )
    result = await run_perturbation_probe(
        llm=mock,
        payload_factory=_factory,
        role="Engineer",
        criteria="5+ years experience",
        candidate_profile_template="Name: {name}",
        variations=[
            Variation(label="A", markers={"name": "Alice"}),
            Variation(label="B", markers={"name": "Bob"}),
        ],
        backend_name="mock-llm",
    )
    assert result.max_score_difference == 0.0
    assert result.role == "Engineer"
    assert "no demographic-perturbation effect" in result.interpretation


@pytest.mark.asyncio
async def test_probe_requires_at_least_two_variations() -> None:
    mock = MockLLMClient()
    with pytest.raises(ValueError, match="At least two demographic variations"):
        await run_perturbation_probe(
            llm=mock,
            payload_factory=_factory,
            role="Engineer",
            criteria="ten plus years",
            candidate_profile_template="Name: {name}",
            variations=[Variation(label="solo", markers={"name": "Alice"})],
            backend_name="mock-llm",
        )


@pytest.mark.asyncio
async def test_probe_collects_flagged_phrases_across_variants() -> None:
    mock = MockLLMClient()
    mock.add_text(
        "probe.resume.v1",
        "probe_perturbation",
        "Score: 6.0\nWeak english and questionable cultural fit.",
    )
    result = await run_perturbation_probe(
        llm=mock,
        payload_factory=_factory,
        role="Engineer",
        criteria="ten plus years",
        candidate_profile_template="Name: {name}",
        variations=[
            Variation(label="A", markers={"name": "A"}),
            Variation(label="B", markers={"name": "B"}),
        ],
        backend_name="mock-llm",
    )
    flagged_set = set(result.flagged_pattern_summary)
    assert "weak english" in flagged_set
    assert "cultural fit" in flagged_set
