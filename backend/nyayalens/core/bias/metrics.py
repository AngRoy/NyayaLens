"""Fairness metrics — pure functions, NumPy/Pandas only.

Implements the five metrics from design doc §6.3 Feature F3:
  - Statistical Parity Difference (SPD)
  - Disparate Impact Ratio (DIR, 80% rule)
  - Equal Opportunity Difference (EOD)
  - Consistency score (k-NN, Zemel et al. 2013)
  - Calibration Difference (grouped ECE)

This module implements **SPD and DIR** on Week 1 Day 3-4. EOD follows on
Day 8; Consistency and Calibration on Week 3. The registry in
`core.bias.registry` iterates whatever is implemented at import time.

Edge-case behaviour is explicit, surfaced to the UI, and documented per
metric. See ADR 0002. Reference implementations we studied:

  - holisticai/src/holisticai/bias/metrics/_classification.py:42
  - AIF360/aif360/metrics/classification_metric.py:676
  - fairlearn/fairlearn/metrics/_fairness_metrics.py:12

No code is copied; numerical behaviour is validated against AIF360/Fairlearn
test fixtures in backend/tests/unit/test_metrics.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

# Minimum samples per demographic group for a metric to be considered reliable.
# Below this threshold we return the metric with `reliable=False` and the UI
# shows "n/a" with a footnote. Design doc §7.2.2 edge-case handling.
MIN_GROUP_SIZE: int = 30


@dataclass(frozen=True, slots=True)
class MetricResult:
    """Result of computing one fairness metric on one sensitive attribute.

    Attributes:
        metric: Canonical metric name (matches registry key).
        value: The scalar metric value, or None if it could not be computed.
        group_values: Per-group statistic (e.g. selection rate per group).
        privileged: Name of the group receiving the most favourable outcomes
            (highest selection rate, TPR, etc.).
        unprivileged: Name of the group receiving the least favourable
            outcomes.
        reliable: False when any group sat below MIN_GROUP_SIZE or when the
            metric could not be computed (e.g. zero-denominator DIR). The
            UI renders unreliable metrics as "n/a" with a footnote.
        reason: Human-readable explanation when `reliable=False` or when
            `value=None`. Surfaced in the explanation panel.
        sample_sizes: n per group — always populated.
        threshold: Reference threshold used by the UI to colour the cell
            (red / amber / green).
        threshold_direction: Whether crossing the threshold means the metric
            went ABOVE or BELOW a safe value (determines colour direction).
    """

    metric: str
    value: float | None
    group_values: dict[str, float] = field(default_factory=dict)
    privileged: str | None = None
    unprivileged: str | None = None
    reliable: bool = True
    reason: str = ""
    sample_sizes: dict[str, int] = field(default_factory=dict)
    threshold: float | None = None
    threshold_direction: Literal["above", "below", "abs"] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _coerce_series(x: pd.Series | np.ndarray | list[object]) -> pd.Series:
    """Normalise input to a pandas Series with a default integer index."""
    if isinstance(x, pd.Series):
        return x.reset_index(drop=True)
    return pd.Series(x)


def _align(*series: pd.Series) -> tuple[pd.Series, ...]:
    """Drop rows where any input is NaN.

    All fairness metrics require aligned, complete records. We drop incomplete
    rows rather than imputing so the numbers stay exactly reproducible.
    """
    frame = pd.concat(series, axis=1)
    frame = frame.dropna(how="any")
    return tuple(frame[col] for col in frame.columns)


def _group_rates(
    y_pred: pd.Series, sensitive: pd.Series, positive_label: object = 1
) -> tuple[dict[str, float], dict[str, int]]:
    """Return positive-outcome rate and sample size per group."""
    rates: dict[str, float] = {}
    sizes: dict[str, int] = {}
    for group, mask in sensitive.groupby(sensitive, observed=False).groups.items():
        idx = sensitive.index.isin(mask)
        group_pred = y_pred[idx]
        sizes[str(group)] = int(len(group_pred))
        if len(group_pred) == 0:
            rates[str(group)] = float("nan")
            continue
        rates[str(group)] = float((group_pred == positive_label).mean())
    return rates, sizes


def _pick_privileged_unprivileged(
    rates: dict[str, float],
) -> tuple[str | None, str | None]:
    """Privileged = highest positive rate; unprivileged = lowest.

    When rates tie, we pick the lexicographically-first name as privileged
    so the result is deterministic. SPD / DIR under a tie are 0 / 1
    respectively regardless of which name gets which label.

    Returns ``(None, None)`` only when fewer than two groups have finite rates.
    """
    finite = {g: r for g, r in rates.items() if not np.isnan(r)}
    if len(finite) < 2:
        return None, None
    # Sort by (rate desc, name asc) — stable tie-break.
    ordered = sorted(finite.items(), key=lambda kv: (-kv[1], kv[0]))
    privileged = ordered[0][0]
    unprivileged = ordered[-1][0]
    return privileged, unprivileged


def _small_group_reason(sizes: dict[str, int]) -> str:
    """Return a non-empty explanation string if any group is below MIN_GROUP_SIZE."""
    small = {g: n for g, n in sizes.items() if n < MIN_GROUP_SIZE}
    if not small:
        return ""
    parts = ", ".join(f"{g} (n={n})" for g, n in small.items())
    return (
        f"Groups below minimum sample size (n={MIN_GROUP_SIZE}): {parts}. "
        f"Results are reported but flagged as unreliable."
    )


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def statistical_parity_difference(
    y_pred: pd.Series | np.ndarray | list[object],
    sensitive: pd.Series | np.ndarray | list[object],
    *,
    positive_label: object = 1,
) -> MetricResult:
    """Difference in positive-outcome rate between unprivileged and privileged groups.

    ``SPD = P(Ŷ=1 | D=unprivileged) − P(Ŷ=1 | D=privileged)``

    SPD of 0.0 means both groups receive the positive outcome at the same
    rate. Negative values mean the unprivileged group is worse off. Design
    doc reference threshold: |SPD| < 0.10.

    Args:
        y_pred: Predicted labels or decisions.
        sensitive: Demographic group membership, one label per record.
        positive_label: Value of `y_pred` that counts as the favourable
            outcome. Defaults to 1.

    Returns:
        A MetricResult whose `value` is the SPD scalar (or None when fewer
        than two groups have data).
    """
    y, s = _align(_coerce_series(y_pred), _coerce_series(sensitive))
    rates, sizes = _group_rates(y, s, positive_label=positive_label)
    privileged, unprivileged = _pick_privileged_unprivileged(rates)

    small_reason = _small_group_reason(sizes)
    base = MetricResult(
        metric="spd",
        value=None,
        group_values=rates,
        sample_sizes=sizes,
        threshold=0.10,
        threshold_direction="abs",
        reliable=not small_reason,
        reason=small_reason,
    )

    if privileged is None or unprivileged is None:
        return MetricResult(
            metric=base.metric,
            value=None,
            group_values=base.group_values,
            sample_sizes=base.sample_sizes,
            threshold=base.threshold,
            threshold_direction=base.threshold_direction,
            reliable=False,
            reason="Fewer than two groups with finite positive-outcome rates.",
        )

    value = rates[unprivileged] - rates[privileged]
    return MetricResult(
        metric="spd",
        value=value,
        group_values=rates,
        privileged=privileged,
        unprivileged=unprivileged,
        sample_sizes=sizes,
        threshold=0.10,
        threshold_direction="abs",
        reliable=base.reliable,
        reason=base.reason,
    )


def disparate_impact_ratio(
    y_pred: pd.Series | np.ndarray | list[object],
    sensitive: pd.Series | np.ndarray | list[object],
    *,
    positive_label: object = 1,
) -> MetricResult:
    """Ratio of unprivileged-group positive-outcome rate to privileged-group rate.

    ``DIR = P(Ŷ=1 | D=unprivileged) / P(Ŷ=1 | D=privileged)``

    DIR of 1.0 is parity. The EEOC "80% rule" (design doc §6.3) says DIR
    below 0.80 is prima facie evidence of adverse impact in US employment
    law. We use that as our default threshold.

    Edge cases:

      - Privileged rate is 0 → DIR undefined; we return `value=None` with
        ``reliable=False`` and a reason explaining the zero denominator.
      - Fewer than two groups have finite rates → same treatment.
    """
    y, s = _align(_coerce_series(y_pred), _coerce_series(sensitive))
    rates, sizes = _group_rates(y, s, positive_label=positive_label)
    privileged, unprivileged = _pick_privileged_unprivileged(rates)

    small_reason = _small_group_reason(sizes)

    if privileged is None or unprivileged is None:
        return MetricResult(
            metric="dir",
            value=None,
            group_values=rates,
            sample_sizes=sizes,
            threshold=0.80,
            threshold_direction="below",
            reliable=False,
            reason="Fewer than two groups with finite positive-outcome rates.",
        )

    if rates[privileged] == 0.0:
        return MetricResult(
            metric="dir",
            value=None,
            group_values=rates,
            privileged=privileged,
            unprivileged=unprivileged,
            sample_sizes=sizes,
            threshold=0.80,
            threshold_direction="below",
            reliable=False,
            reason="Privileged-group positive-outcome rate is 0; DIR is undefined.",
        )

    value = rates[unprivileged] / rates[privileged]
    return MetricResult(
        metric="dir",
        value=value,
        group_values=rates,
        privileged=privileged,
        unprivileged=unprivileged,
        sample_sizes=sizes,
        threshold=0.80,
        threshold_direction="below",
        reliable=not small_reason,
        reason=small_reason,
    )


# EOD, Consistency, Calibration land in later commits — see ADR 0002.
# The registry in core.bias.registry picks them up once implemented.


__all__ = [
    "MIN_GROUP_SIZE",
    "MetricResult",
    "disparate_impact_ratio",
    "statistical_parity_difference",
]
