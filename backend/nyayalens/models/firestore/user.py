"""User document shape per design §8.1.

Imported by:
- `nyayalens/models/firestore/__init__.py` re-exports
- `nyayalens/adapters/firestore.py` (forthcoming) read/write of `/users/{uid}`
- `nyayalens/api/deps.py` (forthcoming) currentUser injection

Maps to Firestore path: `/users/{uid}`. ISO-8601 timestamps used by Firestore.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["admin", "analyst", "reviewer", "viewer"]


class UserDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")

    uid: str
    display_name: str
    email: str
    role: Role
    organization_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
