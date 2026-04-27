"""Audit lifecycle DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from nyayalens.models.api.bias import (
    BiasGridResponse,
    ConflictView,
    ExplanationView,
    ProxyFlagView,
)
from nyayalens.models.api.dataset import SchemaView
from nyayalens.models.api.evidence import DataProvenance
from nyayalens.models.api.remediate import RemediationResult

Mode = Literal["audit", "probe"]
"""Top-level evidence mode (design doc §6.3). Never intermixed."""

AuditStatus = Literal[
    "draft",
    "schema_pending",
    "analyzing",
    "ready_for_review",
    "remediated",
    "signed_off",
    "archived",
]


class AuditCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str
    domain: Literal["hiring", "lending", "admissions", "general"] = "hiring"
    mode: Mode = "audit"
    title: str = Field(min_length=3, max_length=200)
    provenance: DataProvenance


class AuditSummary(BaseModel):
    """Card-sized view for the home dashboard (S02)."""

    model_config = ConfigDict(extra="forbid")

    audit_id: str
    title: str
    status: AuditStatus
    mode: Mode
    domain: str
    provenance: DataProvenance
    created_at: datetime
    updated_at: datetime
    headline_finding: str = ""


class SignOffView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_uid: str
    reviewer_name: str
    reviewer_role: str
    signed_at: datetime
    notes: str


class SignOffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_uid: str
    reviewer_name: str = Field(min_length=2)
    reviewer_role: str = Field(min_length=2)
    notes: str = Field(min_length=10, description="Justification, minimum 10 chars.")
    confirmed: bool = Field(description="Must be True to sign off.")


class AuditDetailResponse(BaseModel):
    """Full audit record returned to the dashboard / report viewer."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    audit_id: str
    organization_id: str
    title: str
    status: AuditStatus
    mode: Mode
    domain: str
    provenance: DataProvenance

    schema_: SchemaView | None = Field(alias="schema")
    bias_grid: BiasGridResponse | None
    explanations: list[ExplanationView] = Field(default_factory=list)
    conflicts: list[ConflictView] = Field(default_factory=list)
    proxy_flags: list[ProxyFlagView] = Field(default_factory=list)
    remediation: RemediationResult | None = None
    sign_off: SignOffView | None = None

    report_url: str | None = None
    recourse_url: str | None = None

    created_at: datetime
    updated_at: datetime
