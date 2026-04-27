"""Grounding validator + template fallback for Gemini explanations.

ADR 0005 mandates: every digit string in an LLM-generated explanation MUST
appear in the metric values we injected into the prompt. If that's not the
case, the explanation is regenerated once. If the second response still
fails, we fall back to a deterministic template — never serve a hallucinated
number.

Imported by:
- `core/explain/__init__.py` re-exports
- `api/audits.py:explain` endpoint (forthcoming)
- `backend/tests/unit/test_grounding.py` (forthcoming)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from nyayalens.core._contracts.llm import LLMClient, LLMPayload
from nyayalens.core.bias.metrics import MetricResult
from nyayalens.core.explain.prompts import (
    EXPLAIN_PROMPT_ID,
    build_explanation_metric_values,
    render_grounded_prompt,
)

GROUNDING_DISCLAIMER: str = (
    "This is interpretive guidance to support human decision-making. It is "
    "not legal, ethical, or compliance advice."
)

EXPLAIN_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "interpretation": {"type": "string"},
        "possible_root_causes": {"type": "array", "items": {"type": "string"}},
        "investigation_prompts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "interpretation"],
}


_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _normalise_number(s: str) -> str:
    if "." not in s:
        return s
    intp, frac = s.split(".", 1)
    frac = frac.rstrip("0")
    return intp if frac == "" else f"{intp}.{frac}"


def _extract_numbers(text: str) -> set[str]:
    return {_normalise_number(m.group(0)) for m in _NUMBER_RE.finditer(text)}


def _allowed_numbers_from(metric_values: dict[str, Any]) -> set[str]:
    """Collect every numeric token the LLM may legitimately cite."""
    out: set[str] = set()

    def visit(v: Any) -> None:
        if isinstance(v, bool):
            return
        if isinstance(v, int | float):
            out.add(_normalise_number(f"{v:.4f}"))
            out.add(_normalise_number(str(v)))
            return
        if isinstance(v, str):
            for n in _extract_numbers(v):
                out.add(n)
            return
        if isinstance(v, dict):
            for vv in v.values():
                visit(vv)
            return
        if isinstance(v, list | tuple | set):
            for vv in v:
                visit(vv)

    visit(metric_values)
    # Always allow trivial framing numbers (years, percentages of typical phrasing).
    out.update({"0", "1", "2", "3", "4", "5", "10", "20", "30", "50", "80", "100"})
    return out


def is_grounded(text: str, metric_values: dict[str, Any]) -> bool:
    """True iff every number in `text` appears in `metric_values`."""
    cited = _extract_numbers(text)
    if not cited:
        return True
    allowed = _allowed_numbers_from(metric_values)
    return cited.issubset(allowed)


@dataclass(frozen=True, slots=True)
class Explanation:
    metric: str
    attribute: str
    summary: str
    interpretation: str
    possible_root_causes: list[str] = field(default_factory=list)
    investigation_prompts: list[str] = field(default_factory=list)
    disclaimer: str = GROUNDING_DISCLAIMER
    grounded: bool = True
    backend: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class GroundingFailureError(RuntimeError):
    """Raised internally when both the first call and the regeneration fail
    grounding. Surface as a fall-back template at the call site."""


def template_fallback(
    result: MetricResult,
    *,
    attribute: str,
    metric_display: str,
) -> Explanation:
    """Return a deterministic, grounded-by-construction explanation."""
    if result.value is None or not result.reliable:
        summary = (
            f"{metric_display} for {attribute} is unavailable. "
            f"Reason: {result.reason or 'insufficient data'}."
        )
        interpretation = (
            "We could not compute a reliable value for this metric on this "
            "dataset. Resolve the data limitation noted above and re-run "
            "the analysis."
        )
        return Explanation(
            metric=result.metric,
            attribute=attribute,
            summary=summary,
            interpretation=interpretation,
            possible_root_causes=[],
            investigation_prompts=[
                "Confirm the dataset includes ground-truth labels.",
                "Verify each demographic group has at least 30 records.",
            ],
            backend="template-fallback",
        )

    threshold = result.threshold
    direction = result.threshold_direction or "abs"
    value = result.value
    privileged = result.privileged or "the higher-rate group"
    unprivileged = result.unprivileged or "the lower-rate group"

    if direction == "below":
        meets = (threshold is None) or (value >= threshold)
    elif direction == "above":
        meets = (threshold is None) or (value <= threshold)
    else:
        meets = (threshold is None) or (abs(value) <= threshold)

    summary = (
        f"{metric_display} for {attribute} is {value:.4f} "
        f"(reference threshold {threshold}). "
        f"Privileged group: {privileged}; unprivileged group: {unprivileged}."
    )
    interpretation = (
        "The result "
        + ("falls within" if meets else "exceeds")
        + " the reference threshold. This is a statistical observation, "
        "not a determination of legal or ethical compliance."
    )
    causes = (
        []
        if meets
        else [
            f"Differences in base rates of qualified candidates between "
            f"{privileged} and {unprivileged}.",
            "Proxy features that correlate with the sensitive attribute.",
            "Historical bias in training data the underlying decision rule was fit to.",
        ]
    )
    prompts = [
        "Inspect feature correlations against the sensitive attribute (proxy detection).",
        "Compare per-group sample sizes and qualification distributions.",
        "Document the rationale for any retained feature flagged as a proxy.",
    ]
    return Explanation(
        metric=result.metric,
        attribute=attribute,
        summary=summary,
        interpretation=interpretation,
        possible_root_causes=causes,
        investigation_prompts=prompts,
        backend="template-fallback",
    )


def _parse_explanation_json(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError:
        return {"summary": str(raw), "interpretation": ""}
    return parsed if isinstance(parsed, dict) else {"summary": str(parsed), "interpretation": ""}


class PayloadFactory(Protocol):
    """Callable that builds a typed `LLMPayload` for one explanation call.

    Signature is documented as a Protocol so callers can pass either a free
    function or a bound method. A concrete implementation lives in
    `api/deps.py` (forthcoming) which wires the PrivacyFilter and the
    current ParsedDataset reference.
    """

    def __call__(
        self,
        *,
        prompt_template_id: str,
        purpose: str,
        metric_values: dict[str, Any],
        narrative_context: str,
    ) -> LLMPayload: ...


async def explain_metric(
    *,
    llm: LLMClient,
    payload_factory: PayloadFactory,
    result: MetricResult,
    attribute: str,
    metric_display: str,
    domain_context: str,
    backend_name: str,
    audit_id: str | None = None,
) -> Explanation:
    """Produce an `Explanation`, regenerating once on grounding failure.

    `payload_factory` is invoked twice if needed: once for the initial
    request and once for the regeneration (so the audit trail records two
    distinct privacy-log entries).
    """
    metric_values = build_explanation_metric_values(result)
    rendered = render_grounded_prompt(
        result=result,
        metric_display=metric_display,
        attribute=attribute,
        domain_context=domain_context,
    )

    for attempt in (1, 2):
        payload = payload_factory(
            prompt_template_id=EXPLAIN_PROMPT_ID,
            purpose="explain_metric",
            metric_values=metric_values,
            narrative_context=rendered,
        )
        response = await llm.generate_structured(
            payload, EXPLAIN_RESPONSE_SCHEMA, audit_id=audit_id
        )
        body = _parse_explanation_json(response)
        flat_text = " ".join(
            [
                str(body.get("summary", "")),
                str(body.get("interpretation", "")),
                " ".join(body.get("possible_root_causes", []) or []),
                " ".join(body.get("investigation_prompts", []) or []),
            ]
        )
        if is_grounded(flat_text, metric_values):
            return Explanation(
                metric=result.metric,
                attribute=attribute,
                summary=str(body.get("summary", "")),
                interpretation=str(body.get("interpretation", "")),
                possible_root_causes=list(body.get("possible_root_causes", []) or []),
                investigation_prompts=list(body.get("investigation_prompts", []) or []),
                grounded=True,
                backend=backend_name,
            )
        if attempt == 2:
            break

    return template_fallback(result, attribute=attribute, metric_display=metric_display)


__all__ = [
    "EXPLAIN_RESPONSE_SCHEMA",
    "GROUNDING_DISCLAIMER",
    "Explanation",
    "GroundingFailureError",
    "PayloadFactory",
    "explain_metric",
    "is_grounded",
    "template_fallback",
]
