"""Unit tests for `core.explain.validator`.

ADR 0005 says every digit in a Gemini-generated explanation must appear in
the metric values we injected. These tests pin that contract: ungrounded
text triggers a regeneration, and a still-ungrounded second response falls
back to a deterministic template.
"""

from __future__ import annotations

from typing import Any

import pytest

from nyayalens.adapters.mock_llm import MockLLMClient
from nyayalens.core._contracts.llm import LLMPayload, StrictPayload
from nyayalens.core.bias.metrics import MetricResult
from nyayalens.core.explain.validator import (
    EXPLAIN_RESPONSE_SCHEMA,
    Explanation,
    explain_metric,
    is_grounded,
    template_fallback,
)


def _result() -> MetricResult:
    return MetricResult(
        metric="dir",
        value=0.56,
        attribute="Gender",
        group_values={"Male": 0.99, "Female": 0.56},
        privileged="Male",
        unprivileged="Female",
        sample_sizes={"Male": 150, "Female": 144},
        threshold=0.80,
        threshold_direction="below",
        reliable=True,
    )


# ---------- is_grounded ----------------------------------------------------


def test_is_grounded_accepts_text_with_only_allowed_numbers() -> None:
    text = "DIR is 0.56 (below the 0.80 threshold)."
    metric_values = {"value": 0.56, "threshold": 0.80}
    assert is_grounded(text, metric_values) is True


def test_is_grounded_rejects_unsourced_number() -> None:
    text = "Their selection rate dropped from 0.99 to 0.34."  # 0.34 nowhere
    metric_values = {"value": 0.56, "group_values": {"Male": 0.99, "Female": 0.56}}
    assert is_grounded(text, metric_values) is False


def test_is_grounded_accepts_text_without_any_numbers() -> None:
    assert is_grounded("Investigate proxy features.", {"value": 0.5}) is True


def test_is_grounded_allows_trivial_framing_numbers() -> None:
    # Years / percentages / counts that come from the prompt scaffold.
    text = "Among the top 5 features, 1 stands out."
    assert is_grounded(text, {"value": 0.56}) is True


# ---------- template_fallback ---------------------------------------------


def test_template_fallback_produces_grounded_explanation() -> None:
    fb = template_fallback(_result(), attribute="Gender", metric_display="DIR")
    assert isinstance(fb, Explanation)
    assert fb.backend == "template-fallback"
    assert "Gender" in fb.summary


def test_template_fallback_handles_unreliable_results() -> None:
    bad = MetricResult(
        metric="dir",
        value=None,
        attribute="Gender",
        reliable=False,
        reason="Privileged-group rate is zero.",
    )
    fb = template_fallback(bad, attribute="Gender", metric_display="DIR")
    assert "unavailable" in fb.summary.lower()


# ---------- explain_metric -------------------------------------------------


def _payload_factory(
    *,
    prompt_template_id: str,
    purpose: str,
    metric_values: dict[str, Any],
    narrative_context: str,
) -> LLMPayload:
    return StrictPayload(
        domain="hiring",
        prompt_template_id=prompt_template_id,
        purpose=purpose,
        metric_values=metric_values,
        narrative_context=narrative_context,
    )


@pytest.mark.asyncio
async def test_explain_metric_returns_grounded_response_when_llm_is_clean() -> None:
    mock = MockLLMClient()
    mock.add_structured(
        "explain.metric.v1",
        "explain_metric",
        {
            "summary": "DIR for Gender is 0.56, below the 0.80 reference.",
            "interpretation": "Group rates differ across Male and Female.",
            "possible_root_causes": ["Historical bias in training data."],
            "investigation_prompts": ["Inspect proxy features."],
        },
    )

    explanation = await explain_metric(
        llm=mock,
        payload_factory=_payload_factory,
        result=_result(),
        attribute="Gender",
        metric_display="Disparate Impact Ratio",
        domain_context="hiring audit",
        backend_name="mock-llm",
    )

    assert explanation.grounded is True
    assert explanation.backend == "mock-llm"
    assert "0.56" in explanation.summary


@pytest.mark.asyncio
async def test_explain_metric_falls_back_to_template_when_grounding_fails_twice() -> None:
    mock = MockLLMClient()
    bad = {
        "summary": "DIR is 0.42 (made up).",  # 0.42 is not in metric_values
        "interpretation": "Decreased by 13 percent.",
        "possible_root_causes": [],
        "investigation_prompts": [],
    }
    mock.add_structured("explain.metric.v1", "explain_metric", bad)

    explanation = await explain_metric(
        llm=mock,
        payload_factory=_payload_factory,
        result=_result(),
        attribute="Gender",
        metric_display="Disparate Impact Ratio",
        domain_context="hiring audit",
        backend_name="mock-llm",
    )

    assert explanation.backend == "template-fallback"
    assert "0.42" not in explanation.summary
    # Sanity: the structured fixture was consumed twice (one initial + one
    # regeneration attempt) before the fallback triggered.
    assert len([c for c in mock.calls if c[0] == "structured"]) == 2
    _ = EXPLAIN_RESPONSE_SCHEMA  # keep import live
