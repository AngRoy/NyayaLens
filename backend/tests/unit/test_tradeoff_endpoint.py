"""Unit tests for the metric-conflict tradeoff-selection endpoint.

The endpoint exists to document the human reviewer's choice when two
fairness metrics disagree (design §6.3 F8). These tests pin the contract:

  - 400 if the audit has no surfaced conflicts.
  - 400 if `metric_chosen` is not part of any conflict pair.
  - 200 + persisted tradeoff record + audit-trail event on the happy path.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nyayalens.api import deps
from nyayalens.api.state import StoredAudit
from nyayalens.core.bias.conflicts import Conflict
from nyayalens.main import create_app


@pytest.fixture
def client() -> TestClient:
    deps._state = None
    deps._audit_sink = None
    deps._storage = None
    deps._pii = None
    deps._privacy_filter = None
    deps._llm = None
    deps._domain = None
    return TestClient(create_app())


def _seed_audit(*, conflicts: list[Conflict] | None = None) -> str:
    state = deps.get_app_state(deps.get_settings())
    audit_id = "audit-tradeoff-1"
    state.put_audit(
        StoredAudit(
            audit_id=audit_id,
            organization_id="demo-org",
            title="Tradeoff fixture audit",
            domain="hiring",
            mode="audit",
            provenance_kind="synthetic",
            provenance_label="unit test fixture",
            status="ready_for_review",
            conflicts=conflicts or [],
        )
    )
    return audit_id


def test_tradeoff_endpoint_rejects_audit_with_no_conflicts(client: TestClient) -> None:
    audit_id = _seed_audit(conflicts=[])
    r = client.post(
        f"/api/v1/audits/{audit_id}/tradeoff",
        json={
            "metric_chosen": "dir",
            "justification": "Choosing DIR for compliance with the EEOC 80% rule.",
            "conflicts_acknowledged": ["dir-vs-eod"],
        },
    )
    assert r.status_code == 400
    assert "no metric conflicts" in r.json()["detail"]


def test_tradeoff_endpoint_rejects_metric_outside_conflict_pair(client: TestClient) -> None:
    audit_id = _seed_audit(
        conflicts=[
            Conflict(
                metric_a="dir",
                metric_b="eod",
                description="DP vs EO conflict on Gender.",
                recommendation="Pick one criterion and document why.",
            )
        ]
    )
    r = client.post(
        f"/api/v1/audits/{audit_id}/tradeoff",
        json={
            "metric_chosen": "consistency",
            "justification": "Consistency is not actually one of the conflict pair.",
            "conflicts_acknowledged": ["dir-vs-eod"],
        },
    )
    assert r.status_code == 400
    assert "not part of any detected conflict" in r.json()["detail"]


def test_tradeoff_endpoint_records_choice_and_emits_audit_event(client: TestClient) -> None:
    audit_id = _seed_audit(
        conflicts=[
            Conflict(
                metric_a="dir",
                metric_b="eod",
                description="DP vs EO conflict on Gender.",
                recommendation="Pick one criterion and document why.",
            )
        ]
    )

    r = client.post(
        f"/api/v1/audits/{audit_id}/tradeoff",
        json={
            "metric_chosen": "dir",
            "justification": "Choosing DIR for compliance with the EEOC 80% rule.",
            "conflicts_acknowledged": ["dir-vs-eod"],
        },
    )
    assert r.status_code == 200, r.text
    detail = r.json()
    assert detail["tradeoff"] is not None
    assert detail["tradeoff"]["metric_chosen"] == "dir"
    assert detail["tradeoff"]["selected_by_uid"] == "demo-uid"

    r = client.get("/api/v1/audit-trail")
    assert r.status_code == 200, r.text
    actions = [e["action"] for e in r.json()]
    assert "tradeoff_selected" in actions


def test_tradeoff_endpoint_404_for_unknown_audit(client: TestClient) -> None:
    r = client.post(
        "/api/v1/audits/ghost-audit/tradeoff",
        json={
            "metric_chosen": "dir",
            "justification": "Should never reach the conflict check because the audit is missing.",
            "conflicts_acknowledged": ["dir-vs-eod"],
        },
    )
    assert r.status_code == 404
