"""Unit tests for `core.recourse.summary.build_recourse_summary`."""

from __future__ import annotations

import pandas as pd

from nyayalens.core.bias.metrics import MetricResult
from nyayalens.core.mitigate.reweighting import apply_reweighting
from nyayalens.core.recourse.summary import (
    DEFAULT_REGULATORY_REFERENCES,
    build_recourse_summary,
)


def _placed_frame(group_a_pos: int, group_b_pos: int) -> pd.DataFrame:
    rows = (
        [{"sens": "A", "y": 1}] * group_a_pos
        + [{"sens": "A", "y": 0}] * (100 - group_a_pos)
        + [{"sens": "B", "y": 1}] * group_b_pos
        + [{"sens": "B", "y": 0}] * (100 - group_b_pos)
    )
    return pd.DataFrame(rows)


def test_summary_drops_unreliable_metrics() -> None:
    metrics = [
        MetricResult(
            metric="dir",
            value=0.56,
            attribute="Gender",
            reliable=True,
            threshold=0.80,
            threshold_direction="below",
        ),
        MetricResult(
            metric="eod",
            value=None,
            attribute="Gender",
            reliable=False,
            reason="too few positive labels",
        ),
    ]
    summary = build_recourse_summary(
        audit_id="audit-001",
        organization_name="Org",
        decision_cycle_label="2026 placements",
        metrics=metrics,
        factor_categories=["CGPA"],
        automated_tools_used=["NyayaLens"],
        contact_email="hr@example.test",
    )
    assert "dir" in summary.aggregate_statistics
    assert "eod" not in summary.aggregate_statistics


def test_summary_renders_dir_after_as_n_a_when_undefined() -> None:
    df = _placed_frame(group_a_pos=0, group_b_pos=0)
    rem = apply_reweighting(df, sensitive_column="sens", outcome_column="y")
    assert rem.dir_after is None  # H2 contract

    summary = build_recourse_summary(
        audit_id="audit-001",
        organization_name="Org",
        decision_cycle_label="2026 placements",
        metrics=[],
        factor_categories=[],
        automated_tools_used=[],
        contact_email="hr@example.test",
        remediation=rem,
    )
    assert summary.aggregate_statistics["dir_after_mitigation"] == "n/a"


def test_summary_carries_regulatory_references() -> None:
    summary = build_recourse_summary(
        audit_id="audit-001",
        organization_name="Org",
        decision_cycle_label="2026 placements",
        metrics=[],
        factor_categories=[],
        automated_tools_used=[],
        contact_email="hr@example.test",
        extra_regulatory_references=["NYC Local Law 144"],
    )
    assert all(ref in summary.regulatory_references for ref in DEFAULT_REGULATORY_REFERENCES)
    assert "NYC Local Law 144" in summary.regulatory_references


def test_summary_includes_contact_in_how_to_request_review() -> None:
    summary = build_recourse_summary(
        audit_id="audit-001",
        organization_name="Org",
        decision_cycle_label="2026 placements",
        metrics=[],
        factor_categories=[],
        automated_tools_used=[],
        contact_email="hr@example.test",
        sla_business_days=10,
    )
    assert "hr@example.test" in summary.how_to_request_review
    assert "10" in summary.how_to_request_review
