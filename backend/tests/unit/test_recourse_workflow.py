"""Unit tests for the recourse review workflow.

Covers the AppState CRUD layer and the HTTP surface (file → list → assign →
resolve). The full audit lifecycle integration test in
`tests/integration/test_audit_lifecycle.py` exercises the happy path; this
file targets the state machine and RBAC edge cases.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nyayalens.api import deps
from nyayalens.api.state import AppState, StoredAudit, StoredRecourseRequest
from nyayalens.main import create_app

# --- AppState CRUD ------------------------------------------------------


def _make_request(
    request_id: str = "r-1", organization_id: str = "demo-org"
) -> StoredRecourseRequest:
    return StoredRecourseRequest(
        request_id=request_id,
        audit_id="a-1",
        organization_id=organization_id,
        applicant_identifier="Applicant #A7F3",
        contact_email="applicant@example.com",
        request_type="human_review",
        body="The decision feels wrong because of disparity X.",
    )


def test_put_and_get_recourse_request_round_trip() -> None:
    state = AppState()
    state.put_recourse_request(_make_request("r-1"))

    fetched = state.get_recourse_request("r-1")
    assert fetched is not None
    assert fetched.status == "pending"
    assert fetched.assigned_to_uid is None


def test_list_recourse_requests_is_org_scoped() -> None:
    state = AppState()
    state.put_recourse_request(_make_request("r-1", organization_id="org-a"))
    state.put_recourse_request(_make_request("r-2", organization_id="org-b"))

    org_a = state.list_recourse_requests("org-a")
    org_b = state.list_recourse_requests("org-b")
    assert {r.request_id for r in org_a} == {"r-1"}
    assert {r.request_id for r in org_b} == {"r-2"}


def test_update_recourse_request_rejects_unknown_field() -> None:
    state = AppState()
    state.put_recourse_request(_make_request("r-1"))

    with pytest.raises(ValueError, match="unknown StoredRecourseRequest field"):
        state.update_recourse_request("r-1", not_a_real_field="x")


def test_update_recourse_request_returns_none_for_missing() -> None:
    state = AppState()
    assert state.update_recourse_request("ghost", status="in_review") is None


def test_update_recourse_request_mutates_status_and_reviewer() -> None:
    state = AppState()
    state.put_recourse_request(_make_request("r-1"))

    updated = state.update_recourse_request(
        "r-1",
        status="in_review",
        assigned_to_uid="rev-uid",
        assigned_to_name="Priya Sharma",
    )
    assert updated is not None
    assert updated.status == "in_review"
    assert updated.assigned_to_name == "Priya Sharma"


# --- HTTP surface -------------------------------------------------------


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


@pytest.fixture
def seeded_audit(client: TestClient) -> str:
    """Create the smallest valid audit so file_recourse has an audit to bind to."""
    state = deps.get_app_state(deps.get_settings())
    audit_id = "audit-test-1"
    state.put_audit(
        StoredAudit(
            audit_id=audit_id,
            organization_id="demo-org",
            title="Recourse workflow test audit",
            domain="hiring",
            mode="audit",
            provenance_kind="synthetic",
            provenance_label="unit test fixture",
            status="signed_off",
        )
    )
    return audit_id


def test_file_recourse_persists_and_returns_pending(client: TestClient, seeded_audit: str) -> None:
    r = client.post(
        "/api/v1/recourse-requests",
        json={
            "audit_id": seeded_audit,
            "applicant_identifier": "Applicant #X",
            "contact_email": "x@example.com",
            "request_type": "human_review",
            "body": "Please review my placement decision.",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    request_id = body["request_id"]
    assert body["status"] == "pending"

    r = client.get("/api/v1/recourse-requests")
    assert r.status_code == 200, r.text
    items = r.json()["requests"]
    assert any(it["request_id"] == request_id for it in items)


def test_file_recourse_rejects_missing_audit(client: TestClient) -> None:
    r = client.post(
        "/api/v1/recourse-requests",
        json={
            "audit_id": "does-not-exist",
            "applicant_identifier": "Applicant #X",
            "contact_email": "x@example.com",
            "request_type": "human_review",
            "body": "Please review my placement decision.",
        },
    )
    assert r.status_code == 404


def test_assign_then_resolve_full_workflow(client: TestClient, seeded_audit: str) -> None:
    filed = client.post(
        "/api/v1/recourse-requests",
        json={
            "audit_id": seeded_audit,
            "applicant_identifier": "Applicant #Y",
            "contact_email": "y@example.com",
            "request_type": "human_review",
            "body": "I'd like a manual review of the recommendation.",
        },
    ).json()
    request_id = filed["request_id"]

    r = client.post(
        f"/api/v1/recourse-requests/{request_id}/assign",
        json={"assignee_uid": "rev-uid", "assignee_name": "Reviewer Bot"},
    )
    assert r.status_code == 200, r.text
    record = r.json()
    assert record["status"] == "in_review"
    assert record["assigned_to_name"] == "Reviewer Bot"

    r = client.post(
        f"/api/v1/recourse-requests/{request_id}/resolve",
        json={
            "resolution": "resolved_overturned",
            "reviewer_notes": "Manual review showed the original score was incorrect.",
        },
    )
    assert r.status_code == 200, r.text
    record = r.json()
    assert record["status"] == "resolved_overturned"
    assert record["resolved_at"] is not None

    r = client.post(
        f"/api/v1/recourse-requests/{request_id}/resolve",
        json={
            "resolution": "resolved_upheld",
            "reviewer_notes": "Reviewing again should be blocked once resolved.",
        },
    )
    assert r.status_code == 409


def test_resolve_unknown_request_is_404(client: TestClient) -> None:
    r = client.post(
        "/api/v1/recourse-requests/ghost-id/resolve",
        json={
            "resolution": "resolved_upheld",
            "reviewer_notes": "Should never reach the audit because ghost-id is not stored.",
        },
    )
    assert r.status_code == 404


def test_audit_trail_records_recourse_lifecycle(client: TestClient, seeded_audit: str) -> None:
    filed = client.post(
        "/api/v1/recourse-requests",
        json={
            "audit_id": seeded_audit,
            "applicant_identifier": "Applicant #Z",
            "contact_email": "z@example.com",
            "request_type": "appeal",
            "body": "Formal appeal — disparity exceeds the threshold.",
        },
    ).json()
    request_id = filed["request_id"]
    client.post(
        f"/api/v1/recourse-requests/{request_id}/assign",
        json={"assignee_uid": "rev-uid", "assignee_name": "R1"},
    )
    client.post(
        f"/api/v1/recourse-requests/{request_id}/resolve",
        json={
            "resolution": "resolved_referred",
            "reviewer_notes": "Escalated to the external compliance authority.",
        },
    )

    r = client.get("/api/v1/audit-trail")
    assert r.status_code == 200, r.text
    actions = [e["action"] for e in r.json()]
    assert "recourse_filed" in actions
    assert "recourse_assigned" in actions
    assert "recourse_resolved" in actions
