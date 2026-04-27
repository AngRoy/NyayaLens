"""Schema-detection orchestrator.

Combines parser + PrivacyFilter + LLMClient to identify (a) sensitive
attributes, (b) the outcome column, (c) feature columns, (d) identifier
columns, with confidence scores. Sub-0.6 confidence anywhere triggers a
``needs_review`` flag so the UI must force the human to confirm.

Imported by:
- `api/datasets.py:detect_schema` POST endpoint (forthcoming)
- `api/audits.py:analyze` flow (forthcoming)

The Gemini prompt template is owned by the domain layer
(`domains/hiring/prompts.py:SCHEMA_PROMPT_ID`). This module composes the
domain prompt with the privacy-filtered payload from `core/schema/pii.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nyayalens.core._contracts.llm import LLMClient
from nyayalens.core.schema.parser import ParsedDataset
from nyayalens.core.schema.pii import PrivacyFilter, PrivacyOutcome

GEMINI_SCHEMA_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sensitive_attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "column": {"type": "string"},
                    "category": {"type": "string"},
                    "confidence": {"type": "number"},
                    "rationale": {"type": "string"},
                },
                "required": ["column", "confidence"],
            },
        },
        "outcome_column": {
            "type": "object",
            "properties": {
                "column": {"type": "string"},
                "positive_value": {},
                "confidence": {"type": "number"},
            },
            "required": ["column", "confidence"],
        },
        "feature_columns": {"type": "array", "items": {"type": "string"}},
        "identifier_columns": {"type": "array", "items": {"type": "string"}},
        "score_column": {"type": ["string", "null"]},
    },
    "required": [
        "sensitive_attributes",
        "outcome_column",
        "feature_columns",
        "identifier_columns",
    ],
}

CONFIDENCE_REVIEW_THRESHOLD: float = 0.60


@dataclass(frozen=True, slots=True)
class SensitiveAttrDetection:
    column: str
    category: str  # "gender", "age", "race", "caste", "religion", "disability", ...
    confidence: float
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class OutcomeDetection:
    column: str
    positive_value: Any
    confidence: float


@dataclass(frozen=True, slots=True)
class SchemaDetectionResult:
    sensitive_attributes: list[SensitiveAttrDetection]
    outcome: OutcomeDetection | None
    feature_columns: list[str]
    identifier_columns: list[str]
    score_column: str | None
    needs_review: bool
    privacy: PrivacyOutcome
    raw_response: dict[str, Any] = field(default_factory=dict)


class SchemaDetector:
    """Orchestrates Gemini-driven schema detection over a privacy-filtered payload."""

    def __init__(
        self,
        llm: LLMClient,
        privacy_filter: PrivacyFilter,
        *,
        prompt_template_id: str = "schema.detect.v1",
        purpose: str = "schema_detection",
    ) -> None:
        self._llm = llm
        self._privacy = privacy_filter
        self._prompt_id = prompt_template_id
        self._purpose = purpose

    async def detect(
        self,
        dataset: ParsedDataset,
        *,
        domain: str = "hiring",
        narrative_context: str = "",
        audit_id: str | None = None,
    ) -> SchemaDetectionResult:
        outcome = self._privacy.build_payload(
            dataset.df,
            dataset.columns,
            prompt_template_id=self._prompt_id,
            purpose=self._purpose,
            domain=domain,
            mode="balanced",
            narrative_context=narrative_context,
        )

        response = await self._llm.generate_structured(
            outcome.payload,
            GEMINI_SCHEMA_JSON_SCHEMA,
            audit_id=audit_id,
        )

        sens_raw = response.get("sensitive_attributes", []) or []
        sensitive: list[SensitiveAttrDetection] = []
        for s in sens_raw:
            try:
                sensitive.append(
                    SensitiveAttrDetection(
                        column=str(s["column"]),
                        category=str(s.get("category", "unknown")),
                        confidence=float(s.get("confidence", 0.0)),
                        rationale=str(s.get("rationale", "")),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue

        outcome_raw = response.get("outcome_column")
        outcome_det: OutcomeDetection | None = None
        if isinstance(outcome_raw, dict) and "column" in outcome_raw:
            try:
                outcome_det = OutcomeDetection(
                    column=str(outcome_raw["column"]),
                    positive_value=outcome_raw.get("positive_value", 1),
                    confidence=float(outcome_raw.get("confidence", 0.0)),
                )
            except (TypeError, ValueError):
                outcome_det = None

        feature_columns = [str(c) for c in response.get("feature_columns", []) if c]
        identifier_columns = [str(c) for c in response.get("identifier_columns", []) if c]
        score_column_raw = response.get("score_column")
        score_column = str(score_column_raw) if score_column_raw else None

        # Augment identifier_columns with PII verdicts so the bias engine
        # never sees a column the privacy layer flagged as PII.
        pii_columns = {v.column for v in outcome.verdicts if v.is_pii}
        for c in pii_columns:
            if c not in identifier_columns:
                identifier_columns.append(c)
        feature_columns = [c for c in feature_columns if c not in pii_columns]

        confidences = [s.confidence for s in sensitive]
        if outcome_det is not None:
            confidences.append(outcome_det.confidence)
        needs_review = bool(
            not confidences or any(c < CONFIDENCE_REVIEW_THRESHOLD for c in confidences)
        )

        return SchemaDetectionResult(
            sensitive_attributes=sensitive,
            outcome=outcome_det,
            feature_columns=feature_columns,
            identifier_columns=identifier_columns,
            score_column=score_column,
            needs_review=needs_review,
            privacy=outcome,
            raw_response=response,
        )


__all__ = [
    "CONFIDENCE_REVIEW_THRESHOLD",
    "GEMINI_SCHEMA_JSON_SCHEMA",
    "OutcomeDetection",
    "SchemaDetectionResult",
    "SchemaDetector",
    "SensitiveAttrDetection",
]
