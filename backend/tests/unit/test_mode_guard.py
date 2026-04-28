"""Tests for the audit/probe mode guard on lifecycle endpoints.

Per design §6.3 F4 audit-mode and probe-mode never intermix. The
real-data lifecycle (analyze, remediate, tradeoff, sign-off, recourse,
report) must refuse a probe-mode record with HTTP 409 so the UI surfaces
the boundary violation distinctly from a missing record (404).
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


def _seed_probe_audit(*, conflicts: list[Conflict] | None = None) -> str:
    state = deps.get_app_state(deps.get_settings())
    audit_id = "probe-record-1"
    state.put_audit(
        StoredAudit(
            audit_id=audit_id,
            organization_id="demo-org",
            title="Probe-mode record",
            domain="hiring",
            mode="probe",
            provenance_kind="llm_generated",
            provenance_label="Mock probe scenarios",
            status="ready_for_review",
            conflicts=conflicts or [],
        )
    )
    return audit_id


def test_analyze_endpoint_refuses_probe_mode(client: TestClient) -> None:
    audit_id = _seed_probe_audit()
    r = client.post(f"/api/v1/audits/{audit_id}/analyze")
    assert r.status_code == 409
    assert "mode='audit'" in r.json()["detail"]


def test_remediate_endpoint_refuses_probe_mode(client: TestClient) -> None:
    audit_id = _seed_probe_audit()
    r = client.post(
        f"/api/v1/audits/{audit_id}/remediate",
        json={
            "target_attribute": "Gender",
            "justification": "Trying to apply reweighting to a probe record.",
        },
    )
    assert r.status_code == 409


def test_tradeoff_endpoint_refuses_probe_mode(client: TestClient) -> None:
    audit_id = _seed_probe_audit(
        conflicts=[
            Conflict(
                metric_a="dir",
                metric_b="eod",
                description="Probe record should never reach this check.",
                recommendation="Pick one and document.",
            )
        ]
    )
    r = client.post(
        f"/api/v1/audits/{audit_id}/tradeoff",
        json={
            "metric_chosen": "dir",
            "justification": "Probe records cannot legitimately resolve metric conflicts.",
            "conflicts_acknowledged": ["dir-vs-eod"],
        },
    )
    assert r.status_code == 409


def test_signoff_endpoint_refuses_probe_mode(client: TestClient) -> None:
    audit_id = _seed_probe_audit()
    r = client.post(
        f"/api/v1/audits/{audit_id}/sign-off",
        json={
            "notes": "Trying to sign off a probe-mode record should be rejected.",
            "confirmed": True,
        },
    )
    assert r.status_code == 409


def test_recourse_summary_endpoint_refuses_probe_mode(client: TestClient) -> None:
    audit_id = _seed_probe_audit()
    r = client.post(
        f"/api/v1/audits/{audit_id}/recourse-summary",
        json={
            "decision_cycle_label": "Probe cycle",
            "organization_name": "NyayaLens demo",
            "contact_email": "ops@example.com",
            "sla_business_days": 15,
            "extra_regulatory_references": [],
        },
    )
    assert r.status_code == 409


def test_file_recourse_endpoint_refuses_probe_mode(client: TestClient) -> None:
    audit_id = _seed_probe_audit()
    r = client.post(
        "/api/v1/recourse-requests",
        json={
            "audit_id": audit_id,
            "applicant_identifier": "Applicant #X",
            "contact_email": "x@example.com",
            "request_type": "human_review",
            "body": "Cannot file recourse on a probe-mode record.",
        },
    )
    assert r.status_code == 409


def test_generate_report_endpoint_refuses_probe_mode(client: TestClient) -> None:
    audit_id = _seed_probe_audit()
    r = client.post(f"/api/v1/audits/{audit_id}/report/generate")
    assert r.status_code == 409


def test_get_audit_allows_probe_mode_for_read(client: TestClient) -> None:
    """Read-only `GET /audits/{id}` must remain usable so the UI can display
    probe records in lists/dashboards. Only the *mutation* endpoints are gated."""
    audit_id = _seed_probe_audit()
    r = client.get(f"/api/v1/audits/{audit_id}")
    assert r.status_code == 200
    assert r.json()["summary"]["mode"] == "probe"
