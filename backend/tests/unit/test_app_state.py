"""Unit tests for `nyayalens.api.state.AppState`.

The MVP store is small enough that its tests live next to the metric
oracles. Focus is on behaviour the route layer relies on: thread-safe CRUD,
unknown-field rejection on updates (so a typo'd state.update_audit kwarg
fails loudly instead of silently accreting attributes on the dataclass).
"""

from __future__ import annotations

import pytest

from nyayalens.api.state import AppState, StoredAudit


def _make_audit(audit_id: str = "audit-001") -> StoredAudit:
    return StoredAudit(
        audit_id=audit_id,
        organization_id="org-001",
        title="t",
        domain="hiring",
        mode="audit",
        provenance_kind="synthetic",
        provenance_label="x",
    )


def test_update_audit_rejects_unknown_field_name() -> None:
    state = AppState()
    state.put_audit(_make_audit())

    with pytest.raises(ValueError) as exc:
        state.update_audit("audit-001", no_such_field="anything")

    assert "no_such_field" in str(exc.value)


def test_update_audit_accepts_known_fields() -> None:
    state = AppState()
    state.put_audit(_make_audit())

    refreshed = state.update_audit("audit-001", status="signed_off", sign_off={"k": "v"})

    assert refreshed is not None
    assert refreshed.status == "signed_off"
    assert refreshed.sign_off == {"k": "v"}


def test_update_audit_returns_none_for_unknown_audit_id() -> None:
    state = AppState()

    result = state.update_audit("does-not-exist", status="signed_off")

    assert result is None
