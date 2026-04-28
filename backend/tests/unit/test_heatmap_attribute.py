"""Regression guard for H1 — per-attribute identity in `MetricResult`.

The route layer's explanation lookup must be able to pick the DIR result
that belongs to a specific sensitive attribute, not just "any DIR". That
requires `MetricResult.attribute` to be populated by `assemble_heatmap`
for every entry in `detailed`.
"""

from __future__ import annotations

import pandas as pd

from nyayalens.core.bias.heatmap import assemble_heatmap


def _frame_with_two_sensitive_attributes() -> pd.DataFrame:
    rows = []
    # Gender disparity (Male privileged, Female unprivileged).
    rows += [{"Gender": "M", "Region": "N", "Placed": 1}] * 80
    rows += [{"Gender": "M", "Region": "N", "Placed": 0}] * 20
    rows += [{"Gender": "F", "Region": "S", "Placed": 1}] * 30
    rows += [{"Gender": "F", "Region": "S", "Placed": 0}] * 70
    # Add Region cross-mix so it's not perfectly correlated with Gender.
    rows += [{"Gender": "M", "Region": "S", "Placed": 1}] * 40
    rows += [{"Gender": "M", "Region": "S", "Placed": 0}] * 10
    rows += [{"Gender": "F", "Region": "N", "Placed": 1}] * 25
    rows += [{"Gender": "F", "Region": "N", "Placed": 0}] * 25
    return pd.DataFrame(rows)


def test_assemble_heatmap_tags_each_metric_with_its_attribute() -> None:
    df = _frame_with_two_sensitive_attributes()
    out = assemble_heatmap(
        df,
        sensitive_attributes=["Gender", "Region"],
        outcome_column="Placed",
        positive_value=1,
    )
    by_attr = {(r.attribute, r.metric) for r in out.detailed}
    assert ("Gender", "dir") in by_attr
    assert ("Region", "dir") in by_attr


def test_dir_results_for_two_attributes_are_distinct_objects() -> None:
    df = _frame_with_two_sensitive_attributes()
    out = assemble_heatmap(
        df,
        sensitive_attributes=["Gender", "Region"],
        outcome_column="Placed",
        positive_value=1,
    )
    gender_dir = next(r for r in out.detailed if r.metric == "dir" and r.attribute == "Gender")
    region_dir = next(r for r in out.detailed if r.metric == "dir" and r.attribute == "Region")
    # Per-group rates must differ across attributes (different group sets).
    assert set(gender_dir.group_values) == {"M", "F"}
    assert set(region_dir.group_values) == {"N", "S"}
