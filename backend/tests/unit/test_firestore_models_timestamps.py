"""Regression guard: firestore document defaults must be tz-aware UTC.

`datetime.utcnow()` is deprecated in 3.12 and removed in 3.14. Every
Firestore-shape model in `nyayalens.models.firestore` must default its
timestamp fields to `datetime.now(UTC)` so the wire shape carries the
``+00:00`` suffix and the build does not warn.
"""

from __future__ import annotations

from datetime import UTC

from nyayalens.models.firestore import (
    AuditDoc,
    AuditTrailDoc,
    OrganizationDoc,
    RecourseRequestDoc,
    UserDoc,
)


def test_audit_doc_created_and_updated_at_are_tz_aware_utc() -> None:
    doc = AuditDoc(
        audit_id="audit-001",
        organization_id="org-001",
        title="t",
        domain="hiring",
        mode="audit",
        status="draft",
        provenance={"kind": "synthetic", "label": "x"},
        created_by_uid="uid-001",
    )
    assert doc.created_at.tzinfo is UTC
    assert doc.updated_at.tzinfo is UTC


def test_audit_trail_doc_timestamp_is_tz_aware_utc() -> None:
    doc = AuditTrailDoc(
        event_id="evt-001",
        organization_id="org-001",
        action="schema_confirmed",
        user_id="uid-001",
        user_name="n",
        user_role="admin",
    )
    assert doc.timestamp.tzinfo is UTC


def test_organization_doc_created_at_is_tz_aware_utc() -> None:
    doc = OrganizationDoc(organization_id="org-001", name="Org")
    assert doc.created_at.tzinfo is UTC


def test_recourse_request_doc_created_at_is_tz_aware_utc() -> None:
    doc = RecourseRequestDoc(
        request_id="req-001",
        audit_id="audit-001",
        organization_id="org-001",
        applicant_identifier="Applicant #A001",
        contact_email="a@b.test",
        request_type="human_review",
    )
    assert doc.created_at.tzinfo is UTC


def test_user_doc_created_at_is_tz_aware_utc() -> None:
    doc = UserDoc(
        uid="uid-001",
        display_name="Demo",
        email="a@b.test",
        role="admin",
        organization_id="org-001",
    )
    assert doc.created_at.tzinfo is UTC
