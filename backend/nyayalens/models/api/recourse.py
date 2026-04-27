"""Applicant recourse DTOs — design doc §6.3 F9."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ResolutionState = Literal[
    "pending",
    "in_review",
    "resolved_upheld",
    "resolved_overturned",
    "resolved_referred",
]


class RecourseSummaryView(BaseModel):
    """Aggregate, applicant-facing transparency summary (no individual scores).

    Generated once per audit cycle; the organisation shares it with affected
    applicants. Distinct from a recourse *request* (filed by an applicant).
    """

    model_config = ConfigDict(extra="forbid")

    audit_id: str
    organization_name: str
    decision_cycle_label: str

    automated_tools_used: list[str]
    factor_categories: list[str]
    aggregate_statistics: dict[str, str] = Field(
        default_factory=dict,
        description="e.g. {'gender_dir': '0.84', 'category_dir': '0.91'} — strings for clarity.",
    )

    how_to_request_review: str
    contact_email: str
    regulatory_references: list[str] = Field(default_factory=list)
    generated_at: datetime


class RecourseRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    applicant_identifier: str = Field(
        description=(
            "Anonymized identifier such as 'Applicant #A7F3'. The org maps "
            "this to a real person via their own HR systems; NyayaLens never "
            "stores the mapping."
        )
    )
    request_type: Literal["human_review", "explanation", "appeal"]
    contact_email: str
    body: str = Field(min_length=10, max_length=2000)


class RecourseRequestView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    audit_id: str
    applicant_identifier: str
    request_type: Literal["human_review", "explanation", "appeal"]
    status: ResolutionState
    assigned_to_name: str | None = None
    reviewer_notes: str = ""
    created_at: datetime
    resolved_at: datetime | None = None
