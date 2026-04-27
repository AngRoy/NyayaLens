"""Audit document — Firestore shape (mirrors design §8.1).

Imported by:
- `nyayalens/models/firestore/__init__.py` re-exports
- `nyayalens/adapters/firestore.py` (forthcoming) for `/audits/{auditId}` reads/writes
- `nyayalens/api/audits.py` (forthcoming) hydrates `AuditDetailResponse` from this

Distinct from `core/_contracts/audit.py` which defines the AuditSink protocol
(an in-memory Pydantic event passed to a sink). This file is the persisted
Firestore document shape — the storage layout. Glob confirmed no other file
serves this role.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditDoc(BaseModel):
    """Stored at `/audits/{auditId}`.

    The Firestore shape carries nested maps (`schema_payload`, `metrics`,
    `remediation`, etc.) as plain dicts so we can write/read with
    `set(merge=True)` without fighting Pydantic over partial updates. The
    API layer hydrates `AuditDetailResponse` from this shape via the
    serialiser in `adapters.firestore`.
    """

    model_config = ConfigDict(extra="forbid")

    audit_id: str
    organization_id: str
    title: str
    domain: str
    mode: str
    status: str
    provenance: dict[str, Any]

    dataset_ref: str | None = None
    schema_payload: dict[str, Any] = Field(default_factory=dict)
    schema_confirmed_by_uid: str | None = None
    schema_confirmed_at: datetime | None = None

    metrics: dict[str, Any] = Field(default_factory=dict)
    explanations: dict[str, Any] = Field(default_factory=dict)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    proxy_flags: list[dict[str, Any]] = Field(default_factory=list)
    remediation: dict[str, Any] = Field(default_factory=dict)
    sign_off: dict[str, Any] | None = None

    report_path: str | None = None
    recourse_path: str | None = None

    created_by_uid: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(
        default=1,
        description="Optimistic-concurrency version. Increment on every update.",
    )
