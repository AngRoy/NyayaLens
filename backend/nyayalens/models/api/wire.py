"""Route-layer wire DTOs — the request/response shapes the frontend parses.

These are deliberately separate from the design-doc-aligned DTOs in this
package's other modules (``audit.py``, ``bias.py``, ``probe.py``, etc.).
The wire shapes here are what the Flutter client consumes today; the
design-doc DTOs are the future ideal that the API will graduate to as
endpoints are reshaped.

Imported by:
- ``nyayalens.api.routes`` — every endpoint reads/writes one of these
- ``nyayalens.models.api.__init__`` re-exports
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------


class DatasetUploadWireResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    row_count: int
    column_count: int
    columns: list[dict[str, Any]]
    sample_rows: list[dict[str, Any]]


class DetectSchemaWireResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    needs_review: bool
    sensitive_attributes: list[dict[str, Any]]
    outcome_column: dict[str, Any] | None
    feature_columns: list[str]
    identifier_columns: list[str]
    score_column: str | None


# ---------------------------------------------------------------------------
# Audits
# ---------------------------------------------------------------------------


class CreateAuditWireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    dataset_id: str
    domain: str = "hiring"
    mode: str = "audit"
    provenance_kind: str = "synthetic"
    provenance_label: str = "Synthetic seeded demo"
    sensitive_attributes: list[str]
    outcome_column: str
    positive_value: Any = 1
    score_column: str | None = None
    feature_columns: list[str] = Field(default_factory=list)
    identifier_columns: list[str] = Field(default_factory=list)


class AuditSummaryWireResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    title: str
    status: str
    mode: str
    domain: str
    provenance_kind: str
    provenance_label: str


class AuditDetailWireResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: AuditSummaryWireResponse
    sensitive_attributes: list[str] = Field(default_factory=list)
    outcome_column: str | None = None
    metrics: list[dict[str, Any]] = Field(default_factory=list)
    heatmap_cells: list[dict[str, Any]] = Field(default_factory=list)
    explanations: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    proxies: list[dict[str, Any]] = Field(default_factory=list)
    remediation: dict[str, Any] | None = None
    sign_off: dict[str, Any] | None = None
    has_report: bool = False


class RemediateWireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_attribute: str
    justification: str = Field(min_length=10)


class SignOffWireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str = Field(min_length=10)
    confirmed: bool


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


class JdScanWireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(min_length=2)
    job_description: str = Field(min_length=20)


class JdScanWireResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str
    inclusivity_score: float
    flagged_phrases: list[dict[str, Any]]
    rewrite_suggestions: list[str]
    backend: str
    created_at: datetime


class PerturbationWireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    criteria: str
    candidate_profile_template: str
    variations: list[dict[str, Any]] = Field(min_length=2, max_length=10)
    audit_id: str | None = None


class PerturbationWireResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    probe_id: str
    role: str
    variants: list[dict[str, Any]]
    max_score_difference: float
    score_variance: float
    flagged_pattern_summary: list[str]
    interpretation: str
    backend: str


# ---------------------------------------------------------------------------
# Recourse
# ---------------------------------------------------------------------------


class RecourseSummaryWireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_cycle_label: str = Field(min_length=2)
    organization_name: str = Field(min_length=2)
    contact_email: str
    sla_business_days: int = 15
    extra_regulatory_references: list[str] = Field(default_factory=list)


class RecourseSummaryWireResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    organization_name: str
    decision_cycle_label: str
    factor_categories: list[str]
    aggregate_statistics: dict[str, str]
    automated_tools_used: list[str]
    how_to_request_review: str
    contact_email: str
    regulatory_references: list[str]


class RecourseRequestWireBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    applicant_identifier: str
    contact_email: str
    request_type: str = "human_review"
    body: str = Field(min_length=10, max_length=2000)


class RecourseRequestWireResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: str = "pending"


__all__ = [
    "AuditDetailWireResponse",
    "AuditSummaryWireResponse",
    "CreateAuditWireRequest",
    "DatasetUploadWireResponse",
    "DetectSchemaWireResponse",
    "JdScanWireRequest",
    "JdScanWireResponse",
    "PerturbationWireRequest",
    "PerturbationWireResponse",
    "RecourseRequestWireBody",
    "RecourseRequestWireResponse",
    "RecourseSummaryWireRequest",
    "RecourseSummaryWireResponse",
    "RemediateWireRequest",
    "SignOffWireRequest",
]
