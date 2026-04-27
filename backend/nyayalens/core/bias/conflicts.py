"""Metric-conflict surfacing — design doc §6.3 F6.

Some fairness metrics formally cannot be satisfied simultaneously
(Chouldechova 2017; Kleinberg, Mullainathan, Raghavan 2017). When two
metrics disagree on whether a system is fair, the human reviewer must
choose which criterion to prioritise — and document why.

This module detects three kinds of conflict given a list of `MetricResult`
objects (typically all metrics for one sensitive attribute):

  1. **Demographic parity vs equalised odds** — DIR < 0.80 while |EOD| < 0.10.
  2. **Disparate impact vs calibration**     — DIR < 0.80 while calibration < 0.05.
  3. **Consistency vs group fairness**       — consistency > 0.80 while DIR < 0.80.

Imported by the (forthcoming) `api/audits.py` route. Tests in
`backend/tests/unit/test_conflicts.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from nyayalens.core.bias.metrics import MetricResult


@dataclass(frozen=True, slots=True)
class Conflict:
    metric_a: str
    metric_b: str
    description: str
    recommendation: str


def _by_name(results: list[MetricResult]) -> dict[str, MetricResult]:
    return {r.metric: r for r in results}


def _value(r: MetricResult | None) -> float | None:
    if r is None or r.value is None or not r.reliable:
        return None
    return float(r.value)


def detect_conflicts(metric_results: list[MetricResult]) -> list[Conflict]:
    """Return any active metric tradeoffs in `metric_results`."""
    by = _by_name(metric_results)
    dir_v = _value(by.get("dir"))
    eod_v = _value(by.get("eod"))
    cal_v = _value(by.get("calibration"))
    cons_v = _value(by.get("consistency"))

    out: list[Conflict] = []

    if dir_v is not None and eod_v is not None and dir_v < 0.80 and abs(eod_v) < 0.10:
        out.append(
            Conflict(
                metric_a="dir",
                metric_b="eod",
                description=(
                    f"Disparate Impact Ratio is {dir_v:.2f} (below the 0.80 "
                    f"reference threshold), but Equal Opportunity Difference "
                    f"is {eod_v:+.2f} — within the 0.10 reference range. "
                    f"Outcome rates differ across groups even though "
                    f"qualified candidates from each group are recognised "
                    f"at similar rates."
                ),
                recommendation=(
                    "Improving DIR (e.g. via reweighting) will likely "
                    "increase EOD because the underlying base rates differ. "
                    "A human must decide which fairness criterion is "
                    "appropriate for this hiring context."
                ),
            )
        )

    if dir_v is not None and cal_v is not None and dir_v < 0.80 and cal_v < 0.05:
        out.append(
            Conflict(
                metric_a="dir",
                metric_b="calibration",
                description=(
                    f"DIR is {dir_v:.2f} (below threshold) while "
                    f"calibration difference is {cal_v:.3f} (within "
                    f"reference). Predicted probabilities track actual "
                    f"outcomes within each group, but final selection "
                    f"rates still diverge."
                ),
                recommendation=(
                    "Threshold tuning per group can move DIR above 0.80 "
                    "but typically distorts calibration. Document which "
                    "tradeoff the organisation accepts before deploying."
                ),
            )
        )

    if cons_v is not None and dir_v is not None and cons_v > 0.80 and dir_v < 0.80:
        out.append(
            Conflict(
                metric_a="consistency",
                metric_b="dir",
                description=(
                    f"Consistency score is {cons_v:.2f} (similar candidates "
                    f"treated similarly), yet DIR is {dir_v:.2f} (group "
                    f"selection rates diverge). Individual-level fairness "
                    f"and group-level fairness are pointing in opposite "
                    f"directions."
                ),
                recommendation=(
                    "This typically signals legitimate scoring of features "
                    "that themselves correlate with the sensitive attribute. "
                    "Investigate proxy features before adjusting outcomes."
                ),
            )
        )

    return out


__all__ = ["Conflict", "detect_conflicts"]
