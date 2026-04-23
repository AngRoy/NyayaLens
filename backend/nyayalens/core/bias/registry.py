"""Metric registry — iterate whatever metric functions are wired up.

Call sites (heatmap assembly, explanation dispatch) should use this registry
rather than hard-coding metric names. Adding a new metric means adding one
entry here; the UI and explanation pipeline pick it up automatically.
"""

from __future__ import annotations

from typing import Any, Callable

from nyayalens.core.bias.metrics import (
    MetricResult,
    disparate_impact_ratio,
    statistical_parity_difference,
)

# All metric functions have the same contract, but their positional args
# differ (SPD/DIR need y_pred + sensitive; EOD needs y_true + y_pred +
# sensitive; Consistency needs features + y_pred; Calibration needs y_true +
# y_prob + sensitive). The registry carries a `required_inputs` list so
# callers know what to pass.
MetricFn = Callable[..., MetricResult]


METRICS: dict[str, dict[str, Any]] = {
    "spd": {
        "fn": statistical_parity_difference,
        "display_name": "Statistical Parity Difference",
        "required_inputs": ["y_pred", "sensitive"],
        "threshold_rule": "|value| < 0.10 is within reference threshold",
        "legal_heritage": "Engineering reference; not a legal standard.",
    },
    "dir": {
        "fn": disparate_impact_ratio,
        "display_name": "Disparate Impact Ratio",
        "required_inputs": ["y_pred", "sensitive"],
        "threshold_rule": "value >= 0.80 meets the EEOC 80% rule",
        "legal_heritage": "US EEOC Uniform Guidelines — adverse-impact threshold.",
    },
    # EOD, Consistency, Calibration will be added in Week 2/Week 3 commits.
}


__all__ = ["METRICS", "MetricFn"]
