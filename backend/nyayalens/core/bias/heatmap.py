"""Heatmap orchestrator — assembles the bias grid for the dashboard (S05).

Iterates `METRICS` x sensitive attributes, dispatches each metric with the
right keyword args, and produces:

  - `metrics: list[MetricResult]` — the raw, per-cell results
  - `cells: list[HeatmapCell]`    — UI-ready (attribute, metric, value, severity)

Severity grading uses thresholds passed in by the caller (typically pulled
from `OrganizationDoc.policy`). Defaults match design doc §6.3 F3.

Imported by the (forthcoming) `api/audits.py` route. Tests in
`backend/tests/unit/test_heatmap.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal

import pandas as pd

from nyayalens.core.bias.metrics import MetricResult
from nyayalens.core.bias.registry import METRICS

Severity = Literal["ok", "warning", "critical", "unavailable"]


@dataclass(frozen=True, slots=True)
class HeatmapCell:
    attribute: str
    metric: str
    value: float | None
    severity: Severity
    note: str


@dataclass(frozen=True, slots=True)
class Thresholds:
    dir_warning: float = 0.85
    dir_critical: float = 0.80
    spd: float = 0.10
    eod: float = 0.10
    consistency: float = 0.80
    calibration: float = 0.05


@dataclass(frozen=True, slots=True)
class HeatmapResult:
    attributes: list[str]
    metrics: list[str]
    cells: list[HeatmapCell]
    detailed: list[MetricResult]


def grade(metric_name: str, result: MetricResult, t: Thresholds) -> Severity:
    """Bucket a `MetricResult` into a UI severity colour."""
    if not result.reliable or result.value is None:
        return "unavailable"

    v = result.value
    if metric_name == "spd":
        return "ok" if abs(v) < t.spd else "warning" if abs(v) < t.spd * 2 else "critical"
    if metric_name == "dir":
        return "ok" if v >= t.dir_warning else "warning" if v >= t.dir_critical else "critical"
    if metric_name == "eod":
        return "ok" if abs(v) < t.eod else "warning" if abs(v) < t.eod * 2 else "critical"
    if metric_name == "consistency":
        return "ok" if v >= t.consistency else "warning" if v >= t.consistency - 0.1 else "critical"
    if metric_name == "calibration":
        return "ok" if v < t.calibration else "warning" if v < t.calibration * 2 else "critical"
    return "unavailable"


def assemble_heatmap(
    df: pd.DataFrame,
    *,
    sensitive_attributes: list[str],
    outcome_column: str,
    positive_value: Any = 1,
    score_column: str | None = None,
    feature_columns: list[str] | None = None,
    thresholds: Thresholds | None = None,
) -> HeatmapResult:
    """Compute the full bias grid for one audit.

    - ``sensitive_attributes`` from confirmed schema. For each, all metrics
      from `METRICS` are computed.
    - ``outcome_column`` is the *predicted* outcome. ``positive_value`` is the
      favourable label.
    - ``score_column`` carries probabilities, required for Calibration.
    - ``feature_columns`` are numeric columns required for Consistency.
    """
    t = thresholds or Thresholds()
    feature_columns = feature_columns or []

    detailed: list[MetricResult] = []
    cells: list[HeatmapCell] = []

    y_pred = df[outcome_column]

    for attr in sensitive_attributes:
        if attr not in df.columns:
            continue
        sens = df[attr]

        for metric_name, spec in METRICS.items():
            fn = spec["fn"]
            required = set(spec["required_inputs"])
            kwargs: dict[str, Any] = {}

            if "y_pred" in required:
                kwargs["y_pred"] = (y_pred == positive_value).astype(int)
            if "sensitive" in required:
                kwargs["sensitive"] = sens
            if "y_true" in required:
                # Without explicit ground truth we treat the recorded
                # outcome as truth — the dashboard surfaces this caveat.
                kwargs["y_true"] = (y_pred == positive_value).astype(int)
            if "y_prob" in required:
                if score_column is None or score_column not in df.columns:
                    detailed.append(
                        MetricResult(
                            metric=metric_name,
                            value=None,
                            attribute=attr,
                            reliable=False,
                            reason=(
                                "Calibration requires probability scores; "
                                "this dataset has no score column."
                            ),
                        )
                    )
                    cells.append(
                        HeatmapCell(
                            attribute=attr,
                            metric=metric_name,
                            value=None,
                            severity="unavailable",
                            note="Score column missing.",
                        )
                    )
                    continue
                kwargs["y_prob"] = df[score_column]
            if "features" in required:
                numeric_features = [
                    c for c in feature_columns if pd.api.types.is_numeric_dtype(df[c])
                ]
                if not numeric_features:
                    detailed.append(
                        MetricResult(
                            metric=metric_name,
                            value=None,
                            attribute=attr,
                            reliable=False,
                            reason="Consistency requires numeric feature columns.",
                        )
                    )
                    cells.append(
                        HeatmapCell(
                            attribute=attr,
                            metric=metric_name,
                            value=None,
                            severity="unavailable",
                            note="No numeric features for k-NN.",
                        )
                    )
                    continue
                kwargs["features"] = df[numeric_features]

            result = replace(fn(**kwargs), attribute=attr)
            detailed.append(result)
            severity = grade(metric_name, result, t)
            cells.append(
                HeatmapCell(
                    attribute=attr,
                    metric=metric_name,
                    value=result.value,
                    severity=severity,
                    note=result.reason or "",
                )
            )

    return HeatmapResult(
        attributes=sensitive_attributes,
        metrics=list(METRICS.keys()),
        cells=cells,
        detailed=detailed,
    )


__all__ = ["HeatmapCell", "HeatmapResult", "Thresholds", "assemble_heatmap", "grade"]
