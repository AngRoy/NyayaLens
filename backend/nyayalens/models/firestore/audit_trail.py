"""Audit-trail document — append-only per ADR 0004.

Imported by:
- `nyayalens/models/firestore/__init__.py` re-exports
- `nyayalens/adapters/firestore.py` (forthcoming) `FirestoreAuditSink.write`

Maps to Firestore path: `/audit_trail/{trailId}`. Distinct from
`core/_contracts/audit.py:AuditEvent` (the Protocol-side dataclass): this file
is the persisted shape with `event_id` as the document ID. Glob confirmed
no other file serves this role.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditTrailDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    audit_id: str | None = None
    organization_id: str
    action: str
    user_id: str
    user_name: str
    user_role: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ip_address: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
