"""Recourse-request document shape per design §8.1.

Imported by:
- `nyayalens/models/firestore/__init__.py` re-exports
- `nyayalens/adapters/firestore.py` (forthcoming)
- `nyayalens/api/recourse.py` (forthcoming) endpoints

Maps to Firestore path: `/recourse_requests/{requestId}`. Glob confirmed
no other file serves this role.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RecourseRequestDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    audit_id: str
    organization_id: str
    applicant_identifier: str
    contact_email: str
    request_type: Literal["human_review", "explanation", "appeal"]
    status: Literal[
        "pending",
        "in_review",
        "resolved_upheld",
        "resolved_overturned",
        "resolved_referred",
    ] = "pending"
    body: str = ""
    assigned_to_uid: str | None = None
    assigned_to_name: str | None = None
    reviewer_notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
