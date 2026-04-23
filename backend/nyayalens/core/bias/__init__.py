"""Bias engine.

Pure functions over NumPy/Pandas. No Firebase, no Gemini. See ADR 0002 for
why we implement from scratch rather than wrap AIF360/Fairlearn.
"""

from nyayalens.core.bias.metrics import (
    MIN_GROUP_SIZE,
    MetricResult,
    disparate_impact_ratio,
    statistical_parity_difference,
)
from nyayalens.core.bias.registry import METRICS, MetricFn

__all__ = [
    "METRICS",
    "MIN_GROUP_SIZE",
    "MetricFn",
    "MetricResult",
    "disparate_impact_ratio",
    "statistical_parity_difference",
]
