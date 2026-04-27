"""Metric registry — iterate whatever metric functions are wired up.

Call sites (heatmap assembly, explanation dispatch) should use this registry
rather than hard-coding metric names. Adding a new metric means adding one
entry here; the UI and explanation pipeline pick it up automatically.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nyayalens.core.bias.metrics import (
    MetricResult,
    calibration_difference,
    consistency_score,
    disparate_impact_ratio,
    equal_opportunity_difference,
    statistical_parity_difference,
)

# All metric functions have the same return type but their positional args
# differ. The `required_inputs` field is the contract callers use to assemble
# the right payload (e.g. heatmap orchestrator).
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
    "eod": {
        "fn": equal_opportunity_difference,
        "display_name": "Equal Opportunity Difference",
        "required_inputs": ["y_true", "y_pred", "sensitive"],
        "threshold_rule": "|value| < 0.10 is within reference threshold",
        "legal_heritage": "Hardt et al. 2016 — equality-of-opportunity criterion.",
    },
    "consistency": {
        "fn": consistency_score,
        "display_name": "Consistency",
        "required_inputs": ["features", "y_pred"],
        "threshold_rule": "value > 0.80 indicates similar individuals are treated similarly",
        "legal_heritage": "Zemel et al. 2013 — individual-fairness reference.",
    },
    "calibration": {
        "fn": calibration_difference,
        "display_name": "Calibration Difference",
        "required_inputs": ["y_true", "y_prob", "sensitive"],
        "threshold_rule": "value < 0.05 indicates similar calibration across groups",
        "legal_heritage": "Engineering reference; not a legal standard.",
    },
}


__all__ = ["METRICS", "MetricFn"]
