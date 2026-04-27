"""Explain service — grounded plain-language metric explanations."""

from nyayalens.core.explain.prompts import (
    EXPLAIN_PROMPT_ID,
    GROUNDED_EXPLANATION_TEMPLATE,
    SYSTEM_PROMPT,
    build_explanation_metric_values,
    render_grounded_prompt,
)
from nyayalens.core.explain.validator import (
    GROUNDING_DISCLAIMER,
    Explanation,
    GroundingFailureError,
    explain_metric,
    is_grounded,
    template_fallback,
)

__all__ = [
    "EXPLAIN_PROMPT_ID",
    "GROUNDED_EXPLANATION_TEMPLATE",
    "GROUNDING_DISCLAIMER",
    "SYSTEM_PROMPT",
    "Explanation",
    "GroundingFailureError",
    "build_explanation_metric_values",
    "explain_metric",
    "is_grounded",
    "render_grounded_prompt",
    "template_fallback",
]
