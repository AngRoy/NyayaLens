"""Audit-trail writer helpers.

Wraps the `AuditSink` protocol with a small ergonomic surface so the API
layer doesn't sprinkle event-construction boilerplate across endpoints.
The Firestore-backed implementation lives in `adapters/firestore.py`.

Imported by:
- `core/govern/__init__.py` re-exports
- `api/audits.py`, `api/recourse.py`, etc. — every state-changing endpoint
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from nyayalens.core._contracts.audit import AuditAction, AuditEvent, AuditSink


class AuditWriteError(RuntimeError):
    """Raised when the AuditSink failed to persist an event."""


async def write_audit_event(
    sink: AuditSink,
    *,
    audit_id: str | None,
    organization_id: str,
    action: AuditAction,
    user_id: str,
    user_name: str,
    user_role: str,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditEvent:
    """Construct and write a single audit event. Returns the event written."""
    event = AuditEvent(
        event_id=uuid4(),
        audit_id=audit_id,
        organization_id=organization_id,
        action=action,
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        timestamp=datetime.now(UTC),
        ip_address=ip_address,
        details=details or {},
    )
    try:
        await sink.write(event)
    except Exception as exc:
        raise AuditWriteError(f"failed to write audit event {action}: {exc}") from exc
    return event


def summarise_event(event: AuditEvent) -> str:
    """One-line summary suitable for the audit-trail list UI (S13)."""
    when = event.timestamp.strftime("%Y-%m-%d %H:%M UTC")
    if event.action == "schema_confirmed":
        return f"{when} — {event.user_name} confirmed schema"
    if event.action == "tradeoff_selected":
        choice = event.details.get("metric", "(unspecified)")
        return f"{when} — {event.user_name} chose to prioritise {choice}"
    if event.action == "mitigation_applied":
        strat = event.details.get("strategy", "remediation")
        return f"{when} — {event.user_name} applied {strat}"
    if event.action == "signoff_completed":
        return f"{when} — {event.user_name} signed off ({event.user_role})"
    if event.action == "recourse_filed":
        return f"{when} — recourse request filed"
    if event.action == "recourse_resolved":
        state = event.details.get("status", "resolved")
        return f"{when} — {event.user_name} marked recourse {state}"
    if event.action == "privacy_log":
        purpose = event.details.get("purpose", "llm_call")
        return f"{when} — privacy log: {purpose}"
    return f"{when} — {event.action} by {event.user_name}"


class AuditWriter:
    """Bundles a sink with a default actor + organisation for call-site sugar."""

    def __init__(
        self,
        sink: AuditSink,
        *,
        organization_id: str,
        user_id: str,
        user_name: str,
        user_role: str,
        ip_address: str | None = None,
    ) -> None:
        self._sink = sink
        self._org = organization_id
        self._uid = user_id
        self._uname = user_name
        self._urole = user_role
        self._ip = ip_address

    async def write(
        self,
        action: AuditAction,
        *,
        audit_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        return await write_audit_event(
            self._sink,
            audit_id=audit_id,
            organization_id=self._org,
            action=action,
            user_id=self._uid,
            user_name=self._uname,
            user_role=self._urole,
            details=details,
            ip_address=self._ip,
        )


__all__ = [
    "AuditWriteError",
    "AuditWriter",
    "summarise_event",
    "write_audit_event",
]
