"""Governance DTOs — audit trail entries surfaced to the UI."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditTrailEntryView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    audit_id: str | None
    organization_id: str
    action: str
    user_id: str
    user_name: str
    user_role: str
    timestamp: datetime
    summary: str
    details: dict[str, Any] = {}
