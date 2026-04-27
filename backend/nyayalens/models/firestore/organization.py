"""Organization document shape per design §8.1.

Imported by:
- `nyayalens/models/firestore/__init__.py` re-exports
- `nyayalens/adapters/firestore.py` (forthcoming) read/write of `/organizations/{orgId}`
- `nyayalens/api/audits.py` (forthcoming) for policy lookup before metric severity grading

Maps to Firestore path: `/organizations/{orgId}`. Default thresholds match
design §6.3 F3 reference values.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dir_warning_threshold: float = 0.85
    dir_critical_threshold: float = 0.80
    spd_threshold: float = 0.10
    eod_threshold: float = 0.10
    proxy_threshold: float = 0.30
    required_approvers: list[str] = Field(default_factory=list)
    recourse_enabled: bool = True
    contact_email: str = ""


class OrganizationDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str
    name: str
    policy: OrganizationPolicy = Field(default_factory=OrganizationPolicy)
    created_at: datetime = Field(default_factory=datetime.utcnow)
