"""LLM Bias Probe DTOs — design doc §6.3 F11."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DemographicVariation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(
        description="Short tag shown in the UI (e.g. 'Indian male', 'Indian female')."
    )
    markers: dict[str, str] = Field(
        description=(
            "Marker substitutions applied to the base prompt — e.g. "
            "{'name': 'Rahul Sharma', 'pronouns': 'he/him'}."
        )
    )


class PerturbationProbeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(min_length=2, description="Role being evaluated (e.g. 'Software Engineer').")
    criteria: str = Field(
        min_length=10,
        description="Evaluation criteria the LLM is asked to score against.",
    )
    candidate_profile_template: str = Field(
        min_length=20,
        description=(
            "Profile template with {name} and {pronouns} placeholders. The probe "
            "fills these from each demographic variation and asks Gemini to "
            "evaluate the (otherwise identical) candidate."
        ),
    )
    variations: list[DemographicVariation] = Field(min_length=2, max_length=10)


class ProbeVariantResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    markers: dict[str, str]
    response_text: str
    score: float | None = Field(
        default=None,
        description="Numeric score parsed from the LLM response, on a 0..10 scale.",
    )
    flagged_phrases: list[str] = Field(default_factory=list)


class PerturbationProbeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    probe_id: str
    role: str
    variants: list[ProbeVariantResult]
    max_score_difference: float
    score_variance: float
    flagged_pattern_summary: list[str] = Field(default_factory=list)
    interpretation: str
    backend: str
    created_at: datetime


class JdScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(min_length=2)
    job_description: str = Field(min_length=20)


class JdScanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str
    inclusivity_score: float = Field(
        ge=0.0, le=1.0, description="Heuristic score from the JD scanner."
    )
    flagged_phrases: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Each entry: {phrase, category, suggestion}.",
    )
    rewrite_suggestions: list[str] = Field(default_factory=list)
    backend: str
    created_at: datetime
