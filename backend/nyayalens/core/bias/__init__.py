"""Bias engine.

Pure functions over NumPy/Pandas. No Firebase, no Gemini. See ADR 0002 for
why we implement from scratch rather than wrap AIF360/Fairlearn.

Imported by tests and by the (forthcoming) `core.bias.heatmap` orchestrator
and `api.audits` route.
"""

from nyayalens.core.bias.metrics import (
    MIN_GROUP_SIZE,
    MetricResult,
    calibration_difference,
    consistency_score,
    disparate_impact_ratio,
    equal_opportunity_difference,
    statistical_parity_difference,
)
from nyayalens.core.bias.registry import METRICS, MetricFn

__all__ = [
    "METRICS",
    "MIN_GROUP_SIZE",
    "MetricFn",
    "MetricResult",
    "calibration_difference",
    "consistency_score",
    "disparate_impact_ratio",
    "equal_opportunity_difference",
    "statistical_parity_difference",
]
