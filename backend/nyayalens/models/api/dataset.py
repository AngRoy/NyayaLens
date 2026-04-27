"""Dataset upload + schema detection DTOs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from nyayalens.models.api.evidence import DataProvenance

ColumnType = Literal["numeric", "categorical", "datetime", "text", "boolean"]


class ColumnSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    dtype: ColumnType
    null_count: int
    unique_count: int
    sample_values: list[str] = Field(
        default_factory=list,
        description="Up to 5 redacted sample values (post-PII scrub).",
    )
    top_values: list[dict[str, Any]] = Field(
        default_factory=list,
        description="For categoricals: list of {value, count}; for numerics: empty.",
    )
    numeric_summary: dict[str, float] | None = Field(
        default=None,
        description="For numerics: {min, max, mean, median, std}.",
    )


class DatasetPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[ColumnSummary]
    row_count: int
    sample_rows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Up to 10 redacted sample rows for the upload preview screen.",
    )


class DatasetUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    preview: DatasetPreview
    provenance: DataProvenance


class SensitiveAttrView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: str
    dtype: ColumnType
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_privileged_value: str | None = None
    suggested_unprivileged_value: str | None = None
    rationale: str = Field(
        default="",
        description="Plain-language explanation of why this was flagged sensitive.",
    )


class OutcomeColumnView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: str
    positive_value: Any = Field(
        description="The cell value treated as the favourable outcome (e.g. 1, 'Yes')."
    )
    confidence: float = Field(ge=0.0, le=1.0)


class SchemaView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sensitive_attributes: list[SensitiveAttrView]
    outcome_column: OutcomeColumnView | None
    feature_columns: list[str]
    identifier_columns: list[str] = Field(
        default_factory=list,
        description="Columns flagged as PII-bearing identifiers and excluded from analysis.",
    )
    score_column: str | None = Field(
        default=None,
        description="Column carrying continuous scores/probabilities, if present.",
    )


class SchemaDetectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    dataset_id: str
    schema_: SchemaView = Field(alias="schema")
    needs_review: bool = Field(
        description=(
            "True when any classification has confidence < 0.6 — the UI must "
            "force the user to review/confirm before proceeding."
        ),
    )
    domain: Literal["hiring", "lending", "admissions", "general"] = "hiring"


class SchemaConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: SchemaView = Field(alias="schema")
    confirmed_by_uid: str
    confirmed_by_name: str
    confirmed_by_role: str
