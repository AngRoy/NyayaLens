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

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias

import numpy as np
import numpy.typing as npt
import pandas as pd

SeriesInput: TypeAlias = pd.Series | npt.NDArray[Any] | Sequence[object]
FeatureInput: TypeAlias = pd.DataFrame | npt.NDArray[Any]

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
    attribute: str = ""
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


def _coerce_series(x: SeriesInput) -> pd.Series:
    """Normalise input to a pandas Series with a default integer index."""
    if isinstance(x, pd.Series):
        return x.reset_index(drop=True)
    return pd.Series(x)


def _align(*series: pd.Series) -> tuple[pd.Series, ...]:
    """Drop rows where any input is NaN.

    Inputs may share names (e.g. y_true and y_pred both called "Placed").
    To prevent ``pd.concat`` from collapsing same-named columns, we rename
    each input to ``__col_<i>`` before concat then return them in order.
    """
    renamed = [s.rename(f"__col_{i}").reset_index(drop=True) for i, s in enumerate(series)]
    frame = pd.concat(renamed, axis=1).dropna(how="any")
    return tuple(frame[f"__col_{i}"].rename(series[i].name) for i in range(len(series)))


def _group_rates(
    y_pred: pd.Series, sensitive: pd.Series, positive_label: object = 1
) -> tuple[dict[str, float], dict[str, int]]:
    """Return positive-outcome rate and sample size per group."""
    rates: dict[str, float] = {}
    sizes: dict[str, int] = {}
    for group, mask in sensitive.groupby(sensitive, observed=False).groups.items():
        idx = sensitive.index.isin(mask)
        group_pred = y_pred[idx]
        sizes[str(group)] = len(group_pred)
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
    y_pred: SeriesInput,
    sensitive: SeriesInput,
    *,
    positive_label: object = 1,
) -> MetricResult:
    """Difference in positive-outcome rate between unprivileged and privileged groups.

    ``SPD = P(y_hat=1 | D=unprivileged) - P(y_hat=1 | D=privileged)``

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
    y_pred: SeriesInput,
    sensitive: SeriesInput,
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


def equal_opportunity_difference(
    y_true: SeriesInput,
    y_pred: SeriesInput,
    sensitive: SeriesInput,
    *,
    positive_label: object = 1,
) -> MetricResult:
    """Difference in true-positive rates between unprivileged and privileged groups.

    ``EOD = TPR_unprivileged - TPR_privileged`` where ``TPR = TP / (TP + FN)``.

    EOD of 0.0 means qualified candidates from both groups are recognised at
    equal rates. Negative values mean the unprivileged group's qualified
    candidates are more likely to be missed.

    A group with no positive ``y_true`` rows has an undefined TPR; it is
    excluded from the privileged/unprivileged pick. If fewer than two groups
    survive that filter the metric is unavailable.
    """
    yt, yp, s = _align(_coerce_series(y_true), _coerce_series(y_pred), _coerce_series(sensitive))
    tprs: dict[str, float] = {}
    sizes: dict[str, int] = {}
    for group, idx in s.groupby(s, observed=False).groups.items():
        in_group = s.index.isin(idx)
        positives = yt[in_group] == positive_label
        sizes[str(group)] = int(in_group.sum())
        if positives.sum() == 0:
            tprs[str(group)] = float("nan")
            continue
        tp = ((yp[in_group] == positive_label) & positives).sum()
        tprs[str(group)] = float(tp) / float(positives.sum())

    privileged, unprivileged = _pick_privileged_unprivileged(tprs)
    small_reason = _small_group_reason(sizes)

    if privileged is None or unprivileged is None:
        return MetricResult(
            metric="eod",
            value=None,
            group_values=tprs,
            sample_sizes=sizes,
            threshold=0.10,
            threshold_direction="abs",
            reliable=False,
            reason="Fewer than two groups had any positive ground-truth rows.",
        )

    value = tprs[unprivileged] - tprs[privileged]
    return MetricResult(
        metric="eod",
        value=value,
        group_values=tprs,
        privileged=privileged,
        unprivileged=unprivileged,
        sample_sizes=sizes,
        threshold=0.10,
        threshold_direction="abs",
        reliable=not small_reason,
        reason=small_reason,
    )


def consistency_score(
    features: FeatureInput,
    y_pred: SeriesInput,
    *,
    n_neighbors: int = 5,
) -> MetricResult:
    """How similarly similar individuals are treated.

    Implements Zemel et al. 2013:
        ``C = 1 - (1/n) sum |y_hat_i - mean(y_hat_kNN(i))|``

    Range: 0 (worst) to 1 (best). A single attribute-agnostic number — there
    is no privileged/unprivileged group here.

    Reference: AIF360 ``binary_label_dataset_metric.py:124``.
    """
    from sklearn.neighbors import NearestNeighbors

    if isinstance(features, pd.DataFrame):
        x = features.select_dtypes(include=[np.number]).to_numpy(dtype=float)
    else:
        x = np.asarray(features, dtype=float)

    yp = _coerce_series(y_pred).to_numpy()
    if x.shape[0] != yp.shape[0]:
        raise ValueError(f"features ({x.shape[0]}) and y_pred ({yp.shape[0]}) length mismatch")

    n = x.shape[0]
    if n < 2 or x.shape[1] == 0:
        return MetricResult(
            metric="consistency",
            value=None,
            sample_sizes={"_total": int(n)},
            threshold=0.80,
            threshold_direction="below",
            reliable=False,
            reason="Consistency requires ≥2 rows and ≥1 numeric feature column.",
        )

    k = min(n_neighbors + 1, n)  # +1 because the row itself is its own NN
    nn = NearestNeighbors(n_neighbors=k)
    nn.fit(x)
    _, indices = nn.kneighbors(x)

    yp_numeric = pd.to_numeric(pd.Series(yp), errors="coerce").to_numpy()
    if np.isnan(yp_numeric).any():
        return MetricResult(
            metric="consistency",
            value=None,
            sample_sizes={"_total": int(n)},
            threshold=0.80,
            threshold_direction="below",
            reliable=False,
            reason="Consistency requires numeric y_pred (cannot coerce categorical).",
        )

    neighbour_means = np.array(
        [yp_numeric[idx[1:]].mean() for idx in indices]  # exclude self
    )
    diffs = np.abs(yp_numeric - neighbour_means)
    score = float(1.0 - diffs.mean())
    reliable = n >= MIN_GROUP_SIZE
    reason = "" if reliable else f"Total sample size {n} below {MIN_GROUP_SIZE}."

    return MetricResult(
        metric="consistency",
        value=score,
        sample_sizes={"_total": int(n)},
        threshold=0.80,
        threshold_direction="below",
        reliable=reliable,
        reason=reason,
    )


def calibration_difference(
    y_true: SeriesInput,
    y_prob: SeriesInput,
    sensitive: SeriesInput,
    *,
    n_bins: int = 10,
    positive_label: object = 1,
) -> MetricResult:
    """Difference in expected-calibration-error (ECE) between groups.

    For each group we compute ECE — the weighted mean absolute gap between
    the predicted probability of the positive class and the empirical
    positive rate, across ``n_bins`` equal-width bins. We return the
    difference between the worst and best group ECE.

    Smaller is better. Threshold reference: 0.05 per design doc §6.3 F3.

    Requires probability scores in ``y_prob`` (continuous in [0, 1]); falls
    back to unavailable if any group has fewer than ``n_bins`` rows.
    """
    yt, yp, s = _align(_coerce_series(y_true), _coerce_series(y_prob), _coerce_series(sensitive))
    yp_num = pd.to_numeric(yp, errors="coerce")
    if yp_num.isna().any():
        return MetricResult(
            metric="calibration",
            value=None,
            sample_sizes={},
            threshold=0.05,
            threshold_direction="below",
            reliable=False,
            reason="Calibration requires numeric probability scores in y_prob.",
        )
    if yp_num.min() < 0 or yp_num.max() > 1:
        return MetricResult(
            metric="calibration",
            value=None,
            sample_sizes={},
            threshold=0.05,
            threshold_direction="below",
            reliable=False,
            reason="y_prob values must lie in [0, 1].",
        )

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    eces: dict[str, float] = {}
    sizes: dict[str, int] = {}
    for group, idx in s.groupby(s, observed=False).groups.items():
        in_group = s.index.isin(idx)
        sizes[str(group)] = int(in_group.sum())
        if in_group.sum() < n_bins:
            eces[str(group)] = float("nan")
            continue
        gp = yp_num[in_group].to_numpy()
        gt = (yt[in_group] == positive_label).to_numpy().astype(float)
        ece_total = 0.0
        n_group = float(gp.shape[0])
        for i in range(n_bins):
            lo, hi = bins[i], bins[i + 1]
            mask = (gp >= lo) & (gp < hi if i < n_bins - 1 else gp <= hi)
            if mask.sum() == 0:
                continue
            avg_conf = float(gp[mask].mean())
            avg_pos = float(gt[mask].mean())
            ece_total += (mask.sum() / n_group) * abs(avg_pos - avg_conf)
        eces[str(group)] = ece_total

    finite = {g: e for g, e in eces.items() if not np.isnan(e)}
    if len(finite) < 2:
        return MetricResult(
            metric="calibration",
            value=None,
            group_values=eces,
            sample_sizes=sizes,
            threshold=0.05,
            threshold_direction="below",
            reliable=False,
            reason=(f"Need ≥2 groups with at least {n_bins} samples each to compute calibration."),
        )

    privileged = min(finite, key=lambda g: finite[g])  # best calibrated
    unprivileged = max(finite, key=lambda g: finite[g])  # worst calibrated
    value = finite[unprivileged] - finite[privileged]
    small_reason = _small_group_reason(sizes)

    return MetricResult(
        metric="calibration",
        value=value,
        group_values=eces,
        privileged=privileged,
        unprivileged=unprivileged,
        sample_sizes=sizes,
        threshold=0.05,
        threshold_direction="below",
        reliable=not small_reason,
        reason=small_reason,
    )


__all__ = [
    "MIN_GROUP_SIZE",
    "MetricResult",
    "calibration_difference",
    "consistency_score",
    "disparate_impact_ratio",
    "equal_opportunity_difference",
    "statistical_parity_difference",
]
