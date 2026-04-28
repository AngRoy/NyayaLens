"""Kamiran & Calders 2012 reweighting — design doc §6.3 F7.

Computes per-instance weights such that the weighted distribution of
(group, outcome) cells is independent. The "after" effect on the dataset
is simulated by recomputing group selection rates *as if* the weighted
empirical distribution were the new ground truth — this is the standard
demo of reweighting impact, even though in production the weights are
fed back to a downstream scoring model.

Reference impl studied (no code copied):
  AIF360/aif360/algorithms/preprocessing/reweighing.py:1-70

Imported by:
- `core/mitigate/__init__.py` re-exports
- `api/audits.py:remediate` POST endpoint (forthcoming)
- `backend/tests/unit/test_reweighting.py` (forthcoming)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class ReweightingResult:
    weights: pd.Series
    group_weight_summary: dict[str, float]
    cell_weight_summary: dict[str, float]
    rates_before: dict[str, float]
    rates_after: dict[str, float]
    spd_before: float
    spd_after: float
    # DIR is None when the privileged-group positive rate is zero (the ratio
    # is undefined). NaN was previously used here but serialises to invalid
    # JSON; None becomes a clean `null` on the wire and forces the UI to
    # render "n/a".
    dir_before: float | None
    dir_after: float | None
    accuracy_estimate_delta: float


def reweighting_weights(
    sensitive: pd.Series,
    outcome: pd.Series,
    *,
    positive_value: Any = 1,
) -> pd.Series:
    """Return one weight per row (Kamiran/Calders).

    For every (group, outcome) cell::

        weight(g, o) = (P(o) x P(g)) / P(g, o)
                     = (n_o x n_g) / (n x n_{g,o})

    Aligned to the reset index of `sensitive` / `outcome`.
    """
    if len(sensitive) != len(outcome):
        raise ValueError(
            f"sensitive ({len(sensitive)}) and outcome ({len(outcome)}) length mismatch"
        )

    s = sensitive.reset_index(drop=True)
    y = (outcome.reset_index(drop=True) == positive_value).astype(int)
    n = float(len(s))

    weights = np.ones(int(n), dtype=float)
    p_outcome = {int(o): float((y == o).sum()) / n for o in (0, 1)}

    for _group, idx in s.groupby(s, observed=False).groups.items():
        rows = list(idx)
        n_g = float(len(rows))
        if n_g == 0:
            continue
        p_group = n_g / n
        for o in (0, 1):
            cell_rows = [i for i in rows if y.iloc[i] == o]
            n_go = float(len(cell_rows))
            if n_go == 0:
                continue
            w = (p_outcome[o] * p_group) / (n_go / n)
            for i in cell_rows:
                weights[i] = w

    return pd.Series(weights, index=s.index, name="reweight")


def _selection_rates(
    sensitive: pd.Series, outcome: pd.Series, *, positive_value: Any
) -> dict[str, float]:
    """Per-group positive-outcome rate, computed in numpy."""
    sens_arr = sensitive.to_numpy()
    y_pos = (outcome == positive_value).to_numpy(dtype=float)
    rates: dict[str, float] = {}
    for group in pd.unique(sens_arr):
        mask = sens_arr == group
        if not mask.any():
            continue
        rates[str(group)] = float(y_pos[mask].mean())
    return rates


def _weighted_selection_rates(
    sensitive: pd.Series,
    outcome: pd.Series,
    weights: pd.Series,
    *,
    positive_value: Any,
) -> dict[str, float]:
    """Per-group weighted positive-outcome rate, computed in numpy."""
    sens_arr = sensitive.to_numpy()
    w_arr = weights.to_numpy(dtype=float)
    y_pos = (outcome == positive_value).to_numpy(dtype=float)
    rates: dict[str, float] = {}
    for group in pd.unique(sens_arr):
        mask = sens_arr == group
        if not mask.any():
            continue
        denom = float(w_arr[mask].sum())
        rates[str(group)] = float((w_arr[mask] * y_pos[mask]).sum() / denom) if denom > 0 else 0.0
    return rates


def _spd_dir_from_rates(rates: dict[str, float]) -> tuple[float, float | None]:
    """Return (SPD, DIR) where DIR is `None` if the privileged rate is zero
    (ratio undefined) — JSON-safe alternative to `float('nan')`.
    """
    if len(rates) < 2:
        return 0.0, 1.0
    ordered = sorted(rates.items(), key=lambda kv: (-kv[1], kv[0]))
    privileged = ordered[0][1]
    unprivileged = ordered[-1][1]
    spd = unprivileged - privileged
    if privileged == 0.0:
        return spd, None
    return spd, unprivileged / privileged


def apply_reweighting(
    df: pd.DataFrame,
    *,
    sensitive_column: str,
    outcome_column: str,
    positive_value: Any = 1,
) -> ReweightingResult:
    """Compute the full before/after summary used by the dashboard."""
    if sensitive_column not in df.columns:
        raise ValueError(f"sensitive_column {sensitive_column!r} not in df")
    if outcome_column not in df.columns:
        raise ValueError(f"outcome_column {outcome_column!r} not in df")

    sens = df[sensitive_column].reset_index(drop=True)
    outc = df[outcome_column].reset_index(drop=True)

    weights = reweighting_weights(sens, outc, positive_value=positive_value)

    rates_before = _selection_rates(sens, outc, positive_value=positive_value)
    rates_after = _weighted_selection_rates(sens, outc, weights, positive_value=positive_value)

    spd_before, dir_before = _spd_dir_from_rates(rates_before)
    spd_after, dir_after = _spd_dir_from_rates(rates_after)

    group_weight_summary: dict[str, float] = {}
    cell_weight_summary: dict[str, float] = {}
    sens_arr = sens.to_numpy()
    weights_arr = weights.to_numpy(dtype=float)
    y_pos_arr = (outc == positive_value).to_numpy(dtype=int)
    for group in pd.unique(sens_arr):
        in_group = sens_arr == group
        if not in_group.any():
            continue
        group_weight_summary[str(group)] = float(weights_arr[in_group].mean())
        for o in (0, 1):
            cell_mask = in_group & (y_pos_arr == o)
            if not cell_mask.any():
                continue
            cell_weight_summary[f"{group}|{o}"] = float(weights_arr[cell_mask].mean())

    # Accuracy delta: heuristic estimate. Bounded to [-0.05, 0]. Real numbers
    # come from a downstream model run; the UI labels this as "estimated".
    weight_var = float(weights.var(ddof=0))
    accuracy_estimate_delta = -min(0.05, weight_var * 0.05)

    return ReweightingResult(
        weights=weights,
        group_weight_summary=group_weight_summary,
        cell_weight_summary=cell_weight_summary,
        rates_before=rates_before,
        rates_after=rates_after,
        spd_before=spd_before,
        spd_after=spd_after,
        dir_before=dir_before,
        dir_after=dir_after,
        accuracy_estimate_delta=accuracy_estimate_delta,
    )


__all__ = ["ReweightingResult", "apply_reweighting", "reweighting_weights"]
