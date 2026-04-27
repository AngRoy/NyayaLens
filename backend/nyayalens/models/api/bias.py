"""Bias engine output DTOs (heatmap cells, explanations, proxies)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["ok", "warning", "critical", "unavailable"]
"""Cell colour bucket. `unavailable` renders as 'n/a' with a footnote."""


class MetricResultView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str
    display_name: str
    attribute: str
    value: float | None
    threshold: float | None
    threshold_direction: Literal["above", "below", "abs"] | None
    severity: Severity
    privileged: str | None
    unprivileged: str | None
    group_values: dict[str, float] = Field(default_factory=dict)
    sample_sizes: dict[str, int] = Field(default_factory=dict)
    reliable: bool
    reason: str = ""


class BiasGridCell(BaseModel):
    """One cell of the bias heatmap (attribute x metric)."""

    model_config = ConfigDict(extra="forbid")

    attribute: str
    metric: str
    value: float | None
    severity: Severity
    note: str = ""


class BiasGridResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attributes: list[str]
    metrics: list[str]
    cells: list[BiasGridCell]
    detailed: list[MetricResultView]


class ConflictView(BaseModel):
    """Pareto tradeoff — improving one metric may worsen another."""

    model_config = ConfigDict(extra="forbid")

    metric_a: str
    metric_b: str
    description: str
    recommendation: str = Field(
        default="",
        description="Short framing the UI surfaces to help the human reviewer choose.",
    )


class ProxyFlagView(BaseModel):
    """Feature flagged as a potential proxy for a sensitive attribute."""

    model_config = ConfigDict(extra="forbid")

    feature: str
    sensitive_attribute: str
    method: Literal["cramers_v", "point_biserial"]
    strength: float
    severity: Severity
    note: str


class ExplanationView(BaseModel):
    """Gemini-generated, grounded, plain-language explanation."""

    model_config = ConfigDict(extra="forbid")

    metric: str
    attribute: str
    summary: str
    interpretation: str
    possible_root_causes: list[str] = Field(default_factory=list)
    investigation_prompts: list[str] = Field(default_factory=list)
    disclaimer: str
    grounded: bool = Field(
        description=(
            "True iff every digit in the explanation text appears in the "
            "injected metric values. False indicates a fallback template "
            "was substituted (see ADR 0005)."
        )
    )
    backend: str = Field(description="e.g. 'gemini-flash-latest' or 'template-fallback'.")
    generated_at: datetime
