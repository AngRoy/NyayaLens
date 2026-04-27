"""Mitigation DTOs — currently reweighting only.

Imported by:
- `nyayalens/models/api/audit.py` for `AuditDetailResponse.remediation`
- `nyayalens/models/api/__init__.py` re-exports
- `nyayalens/api/audits.py` (forthcoming) for the remediation endpoints
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from nyayalens.models.api.bias import MetricResultView

Strategy = Literal["reweighting"]
"""MVP: reweighting only. Threshold optimisation and representation balancing
are post-MVP per design doc §6.3 F7."""


class RemediationApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: Strategy = "reweighting"
    target_attribute: str = Field(
        description="Sensitive attribute to remediate against (e.g. 'Gender')."
    )
    target_metric: Literal["dir", "spd"] = "dir"


class RemediationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: Strategy
    target_attribute: str
    target_metric: str
    before: list[MetricResultView]
    after: list[MetricResultView]
    accuracy_delta: float = Field(
        description=(
            "Predicted accuracy change after remediation, on a 0..1 scale. "
            "Negative values mean accuracy went down."
        )
    )
    fairness_delta: float = Field(
        description="Improvement in the target metric (positive = fairer)."
    )
    instance_weights_summary: dict[str, float] = Field(
        default_factory=dict,
        description="Mean weight per group after Kamiran/Calders reweighting.",
    )
    selected_by_uid: str | None = None
    selected_by_name: str | None = None
    selected_at: datetime | None = None
    justification: str = ""


class RemediationApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approver_uid: str
    approver_name: str = Field(min_length=2)
    approver_role: str = Field(min_length=2)
    justification: str = Field(min_length=10)
