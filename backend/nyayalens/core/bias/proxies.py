"""Proxy-feature detection — design doc §6.3 F7.

Identifies non-sensitive feature columns that correlate strongly with a
sensitive attribute and may therefore act as a discrimination proxy.

Methods:
  - **Cramér's V** for categorical x categorical pairs.
  - **Point-biserial r** for numeric feature x binary categorical sensitive.

Default flagging threshold is 0.30 (configurable per organisation in
`firestore.OrganizationPolicy.proxy_threshold`). Output is *flag-only* —
removal/retention is a human decision per the design.

Imported by the (forthcoming) `core/bias/heatmap.py` orchestrator and
`api/audits.py` route. Tests in `backend/tests/unit/test_proxies.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

DEFAULT_PROXY_THRESHOLD: float = 0.30


@dataclass(frozen=True, slots=True)
class ProxyFlag:
    feature: str
    sensitive_attribute: str
    method: Literal["cramers_v", "point_biserial"]
    strength: float
    severity: Literal["ok", "warning", "critical"]
    note: str


def _cramers_v(a: pd.Series, b: pd.Series) -> float:
    """Cramér's V — symmetric in [0, 1]; 0 = independence, 1 = perfect."""
    contingency = pd.crosstab(a, b)
    n = float(contingency.to_numpy().sum())
    if n == 0 or contingency.shape[0] < 2 or contingency.shape[1] < 2:
        return 0.0

    row_totals = contingency.sum(axis=1).to_numpy(dtype=float)
    col_totals = contingency.sum(axis=0).to_numpy(dtype=float)
    expected = np.outer(row_totals, col_totals) / n
    observed = contingency.to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2_terms = np.where(expected > 0, (observed - expected) ** 2 / expected, 0.0)
    chi2 = float(chi2_terms.sum())
    k = min(contingency.shape) - 1
    if k <= 0:
        return 0.0
    return float(np.sqrt((chi2 / n) / k))


def _point_biserial(numeric: pd.Series, binary: pd.Series) -> float:
    """Point-biserial — Pearson r between numeric and 0/1 series. Absolute value."""
    aligned = pd.concat([numeric, binary], axis=1).dropna()
    if aligned.empty:
        return 0.0
    x = pd.to_numeric(aligned.iloc[:, 0], errors="coerce")
    y_cat = aligned.iloc[:, 1]
    if y_cat.nunique() != 2:
        return 0.0
    levels = sorted(y_cat.unique().tolist(), key=str)
    y = (y_cat == levels[1]).astype(float)
    x = x.dropna()
    y = y.loc[x.index]
    if x.std(ddof=0) == 0 or y.std(ddof=0) == 0:
        return 0.0
    r = float(np.corrcoef(x, y)[0, 1])
    return float(abs(r))


def _severity(strength: float, threshold: float) -> Literal["ok", "warning", "critical"]:
    if strength < threshold:
        return "ok"
    if strength < min(0.6, threshold + 0.2):
        return "warning"
    return "critical"


def _to_categorical(series: pd.Series) -> pd.Series:
    """Bin a numeric series into quartiles; pass categoricals through."""
    if pd.api.types.is_numeric_dtype(series):
        try:
            return pd.qcut(series, q=4, duplicates="drop").astype(str)
        except ValueError:
            return series.astype(str)
    return series.astype(str)


def _correlate(
    sens: pd.Series, feat: pd.Series
) -> tuple[Literal["cramers_v", "point_biserial"], float]:
    sens_is_numeric = pd.api.types.is_numeric_dtype(sens)
    feat_is_numeric = pd.api.types.is_numeric_dtype(feat)

    if feat_is_numeric and not sens_is_numeric and sens.nunique() == 2:
        return "point_biserial", _point_biserial(feat, sens)
    if sens_is_numeric and not feat_is_numeric and feat.nunique() == 2:
        return "point_biserial", _point_biserial(sens, feat)

    a = _to_categorical(sens)
    b = _to_categorical(feat)
    return "cramers_v", _cramers_v(a, b)


def detect_proxies(
    df: pd.DataFrame,
    sensitive_columns: list[str],
    feature_columns: list[str],
    *,
    threshold: float = DEFAULT_PROXY_THRESHOLD,
) -> list[ProxyFlag]:
    """Return correlation flags reaching `threshold`, sorted by strength desc."""
    flags: list[ProxyFlag] = []
    for sens in sensitive_columns:
        if sens not in df.columns:
            continue
        sens_series = df[sens]
        for feat in feature_columns:
            if feat == sens or feat not in df.columns:
                continue
            feat_series = df[feat]
            method, strength = _correlate(sens_series, feat_series)
            if strength < threshold:
                continue
            sev = _severity(strength, threshold)
            note = (
                f"{feat} correlates with {sens} via {method} at "
                f"strength {strength:.2f}. Consider whether retaining {feat} "
                f"is justified for the role."
            )
            flags.append(
                ProxyFlag(
                    feature=feat,
                    sensitive_attribute=sens,
                    method=method,
                    strength=strength,
                    severity=sev,
                    note=note,
                )
            )
    flags.sort(key=lambda f: f.strength, reverse=True)
    return flags


__all__ = ["DEFAULT_PROXY_THRESHOLD", "ProxyFlag", "detect_proxies"]
