"""Audit-trail contract.

Every semantic decision point (schema confirmation, mitigation approval,
sign-off, recourse resolution, privacy-relevant LLM call) writes an
`AuditEvent` through an `AuditSink`.

ADR 0004 documents why the MVP sink writes to Firestore and how the contract
supports a post-MVP migration to Cloud Logging.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

AuditAction = Literal[
    "dataset_uploaded",
    "schema_detected",
    "schema_confirmed",
    "analysis_started",
    "analysis_completed",
    "explanation_generated",
    "conflict_surfaced",
    "tradeoff_selected",
    "mitigation_applied",
    "signoff_requested",
    "signoff_completed",
    "report_generated",
    "recourse_filed",
    "recourse_assigned",
    "recourse_resolved",
    "privacy_log",
]
"""Closed vocabulary of audit actions.

Adding a new action requires a code change, which in turn shows up in a PR
review — the opposite of silent extensibility.
"""


class AuditEvent(BaseModel):
    """One entry in the immutable audit trail.

    See design doc §7.2.4 for the canonical shape. Fields are optional here
    because different actions emit different detail shapes.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    audit_id: str | None = Field(
        default=None,
        description="The parent audit, if the event is part of one.",
    )
    organization_id: str

    action: AuditAction
    user_id: str
    user_name: str
    user_role: str

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ip_address: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Action-specific details. Shape depends on the action; see "
            "docs/audit-events.md (post-MVP) for the registry."
        ),
    )


@runtime_checkable
class AuditSink(Protocol):
    """Protocol implemented by concrete audit-trail backends.

    MVP: `adapters.firestore.FirestoreAuditSink`.
    Post-MVP: `adapters.cloud_logging.CloudLoggingAuditSink` (see ADR 0004).
    """

    async def write(self, event: AuditEvent) -> None:
        """Append a single audit event. Must be atomic with the caller's
        business write when both live in the same Firestore transaction.
        """
        ...

    async def write_batch(self, events: list[AuditEvent]) -> None:
        """Append many events in order. Used when a single operation emits
        multiple logical events (e.g. mitigation_applied + signoff_requested).
        """
        ...


__all__ = ["AuditAction", "AuditEvent", "AuditSink"]
