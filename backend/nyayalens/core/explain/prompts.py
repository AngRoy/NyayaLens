"""Grounded-explanation prompt templates.

Domain-agnostic scaffolding lives here; hiring-specific verbiage and
examples live in `domains/hiring/prompts.py`. The composition happens at
call time in `validator.explain_metric()`.

Imported by:
- `core/explain/__init__.py` re-exports
- `core/explain/validator.py:explain_metric`
"""

from __future__ import annotations

from typing import Any

from nyayalens.core.bias.metrics import MetricResult

EXPLAIN_PROMPT_ID: str = "explain.metric.v1"
"""Stable ID logged in PrivacyLogEntry — bump when the template changes."""

SYSTEM_PROMPT: str = (
    "You are a fairness analyst writing for a non-technical HR compliance "
    "officer. You explain statistical findings in clear, actionable "
    "language. You NEVER declare a system 'fair' or 'unfair'. You present "
    "evidence and ask the reader to investigate.\n\n"
    "IMPORTANT: Every number in your explanation must come from the "
    "provided data. Do not generate, estimate, or round any numbers. Use "
    "the exact values provided. Do not invent percentages or counts."
)

GROUNDED_EXPLANATION_TEMPLATE: str = (
    "Metric: {metric_display}\n"
    "Sensitive attribute: {attribute}\n"
    "Computed value: {value}\n"
    "Reference threshold: {threshold} ({threshold_direction})\n"
    "Privileged group: {privileged}\n"
    "Unprivileged group: {unprivileged}\n"
    "Per-group statistic: {group_values}\n"
    "Sample sizes: {sample_sizes}\n\n"
    "Domain context:\n{domain_context}\n\n"
    "Your task: explain this finding in plain English for a hiring "
    "compliance officer. Provide:\n"
    "  1. A one-sentence summary that uses the exact numbers above.\n"
    "  2. What the metric measures and why it matters here.\n"
    "  3. How the result compares to the reference threshold.\n"
    "  4. 2-4 possible root causes worth investigating (NOT conclusions).\n"
    "  5. A short list of next-step questions for the reviewer.\n\n"
    "Respond ONLY in JSON with keys: "
    "summary, interpretation, possible_root_causes (array), "
    "investigation_prompts (array)."
)


def build_explanation_metric_values(result: MetricResult) -> dict[str, Any]:
    """Pack metric numbers into the dict the PrivacyFilter slots into the payload.

    Used by `validator.explain_metric()` to inject grounded values into the
    LLM payload's ``metric_values`` field. Every numeric value the LLM may
    cite must appear here.
    """
    out: dict[str, Any] = {
        "metric": result.metric,
        "value": result.value,
        "threshold": result.threshold,
        "threshold_direction": result.threshold_direction,
        "privileged": result.privileged,
        "unprivileged": result.unprivileged,
        "group_values": {
            k: round(float(v), 4)
            for k, v in result.group_values.items()
            if v is not None and v == v  # filter NaN
        },
        "sample_sizes": dict(result.sample_sizes),
        "reliable": result.reliable,
        "reason": result.reason,
    }
    return out


def _format_group_values(group_values: dict[str, float]) -> str:
    if not group_values:
        return "(no per-group rates)"
    return ", ".join(f"{k}: {v:.4f}" for k, v in group_values.items())


def _format_sample_sizes(sizes: dict[str, int]) -> str:
    if not sizes:
        return "(unspecified)"
    return ", ".join(f"{k}: n={v}" for k, v in sizes.items())


def _format_value(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.4f}"


def render_grounded_prompt(
    *,
    result: MetricResult,
    metric_display: str,
    attribute: str,
    domain_context: str,
) -> str:
    """Compose the grounded prompt body that goes into `narrative_context`."""
    return GROUNDED_EXPLANATION_TEMPLATE.format(
        metric_display=metric_display,
        attribute=attribute,
        value=_format_value(result.value),
        threshold=_format_value(result.threshold),
        threshold_direction=result.threshold_direction or "n/a",
        privileged=result.privileged or "n/a",
        unprivileged=result.unprivileged or "n/a",
        group_values=_format_group_values(result.group_values),
        sample_sizes=_format_sample_sizes(result.sample_sizes),
        domain_context=domain_context.strip() or "(none)",
    )


__all__ = [
    "EXPLAIN_PROMPT_ID",
    "GROUNDED_EXPLANATION_TEMPLATE",
    "SYSTEM_PROMPT",
    "build_explanation_metric_values",
    "render_grounded_prompt",
]
