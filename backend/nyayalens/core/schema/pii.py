"""Privacy filter — the typed-payload constructor that enforces ADR 0005.

The PrivacyFilter is the **only** way to construct an `LLMPayload`. The
Gemini adapter accepts only those typed envelopes, so a developer who
forgets to invoke this class cannot accidentally send raw PII to the LLM —
they will see a mypy error first.

Imported by:
- `core/schema/__init__.py` re-exports
- `core/schema/detector.py` orchestrator (forthcoming)
- `api/audits.py` for explanation/probe payloads (forthcoming)

Pipeline (Balanced mode, default):
  1. Run the injected `PIIRecognizer` over each column's sample values.
  2. If >=70% of non-null sample cells in a column carry a PII entity, mark
     the entire column as PII and replace every sample with a redaction
     token (e.g. ``[REDACTED:PERSON]``).
  3. Aggregate per-column metadata + redacted samples into a `BalancedPayload`.

Strict mode never includes redacted samples — only column metadata.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

from nyayalens.core._contracts.llm import (
    BalancedPayload,
    LLMPayload,
    StrictPayload,
)
from nyayalens.core._contracts.pii import PIIMatch, PIIRecognizer
from nyayalens.core.schema.parser import ColumnInfo

PrivacyMode = Literal["strict", "balanced"]
"""MVP supports Strict and Balanced. Local mode (Gemma) is post-MVP."""

# Column-level PII verdict threshold. If at least this fraction of a
# column's non-null sample cells contain any PII entity, the entire
# column is treated as PII.
COLUMN_PII_THRESHOLD: float = 0.70

# Names that strongly signal a column is PII even if values don't trigger
# Presidio (e.g. a "Roll_No" column with values that don't match any
# built-in pattern).
PII_COLUMN_NAME_HINTS: tuple[str, ...] = (
    "name",
    "first_name",
    "last_name",
    "full_name",
    "email",
    "e-mail",
    "phone",
    "mobile",
    "contact",
    "address",
    "aadhaar",
    "aadhar",
    "pan",
    "passport",
    "voter",
    "ssn",
    "dl_no",
    "license",
    "roll_no",
    "rollno",
    "roll number",
    "student_id",
    "employee_id",
    "id_no",
)


@dataclass(frozen=True, slots=True)
class ColumnPrivacyVerdict:
    column: str
    is_pii: bool
    detected_entities: list[str]
    masked_count: int
    sample_size: int
    name_hint_match: bool


def _column_name_is_pii_hint(name: str) -> bool:
    lowered = name.strip().lower()
    return any(hint in lowered for hint in PII_COLUMN_NAME_HINTS)


def _redact(text: str, matches: list[PIIMatch]) -> str:
    """Return `text` with each match span replaced by ``[REDACTED:<TYPE>]``."""
    if not matches:
        return text
    sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
    out = text
    for m in sorted_matches:
        token = f"[REDACTED:{m.entity_type}]"
        out = out[: m.start] + token + out[m.end :]
    return out


@dataclass(frozen=True, slots=True)
class PrivacyAuditLog:
    """One PrivacyFilter invocation. Caller forwards this to the audit sink."""

    columns_inspected: list[str]
    pii_columns: list[str]
    entity_counts: dict[str, int]
    privacy_mode: PrivacyMode


@dataclass(frozen=True, slots=True)
class PrivacyOutcome:
    payload: LLMPayload
    audit: PrivacyAuditLog
    verdicts: list[ColumnPrivacyVerdict]


class PrivacyFilter:
    """The typed-payload constructor.

    Construct once per backend boot; reuse across requests. The injected
    `PIIRecognizer` is the only stateful dependency.
    """

    def __init__(self, recognizer: PIIRecognizer) -> None:
        self._recognizer = recognizer

    def scan_columns(
        self,
        df: pd.DataFrame,
        columns: list[ColumnInfo],
    ) -> list[ColumnPrivacyVerdict]:
        """Decide PII status per column. Side-effect free."""
        verdicts: list[ColumnPrivacyVerdict] = []
        for col in columns:
            series = df[col.name].dropna().astype(str)
            sample_size = int(min(len(series), 100))
            sample = series.head(sample_size).tolist()

            entities_seen: list[str] = []
            cells_with_pii = 0
            for cell in sample:
                matches = self._recognizer.recognize(cell)
                if matches:
                    cells_with_pii += 1
                    entities_seen.extend(m.entity_type for m in matches)

            ratio = (cells_with_pii / sample_size) if sample_size else 0.0
            name_hint = _column_name_is_pii_hint(col.name)
            is_pii = name_hint or ratio >= COLUMN_PII_THRESHOLD

            verdicts.append(
                ColumnPrivacyVerdict(
                    column=col.name,
                    is_pii=is_pii,
                    detected_entities=sorted(set(entities_seen)),
                    masked_count=cells_with_pii,
                    sample_size=sample_size,
                    name_hint_match=name_hint,
                )
            )
        return verdicts

    def build_payload(
        self,
        df: pd.DataFrame,
        columns: list[ColumnInfo],
        *,
        prompt_template_id: str,
        purpose: str,
        domain: str = "hiring",
        mode: PrivacyMode = "balanced",
        narrative_context: str = "",
        metric_values: dict[str, Any] | None = None,
    ) -> PrivacyOutcome:
        """Assemble a typed `LLMPayload` for one Gemini call."""
        verdicts = self.scan_columns(df, columns)
        verdict_by_col = {v.column: v for v in verdicts}

        column_metadata: list[dict[str, Any]] = []
        for col in columns:
            v = verdict_by_col[col.name]
            column_metadata.append(
                {
                    "name": col.name,
                    "dtype": col.dtype,
                    "null_count": col.null_count,
                    "unique_count": col.unique_count,
                    "is_pii": v.is_pii,
                    "detected_entities": v.detected_entities,
                    "top_values": (
                        col.top_values if not v.is_pii else [{"value": "[REDACTED]", "count": -1}]
                    ),
                    "numeric_summary": col.numeric_summary,
                }
            )

        entity_counter: Counter[str] = Counter()
        for v in verdicts:
            for ent in v.detected_entities:
                entity_counter[ent] += v.masked_count

        if mode == "strict":
            payload: LLMPayload = StrictPayload(
                domain=domain,
                prompt_template_id=prompt_template_id,
                purpose=purpose,
                column_metadata=column_metadata,
                metric_values=metric_values or {},
                narrative_context=narrative_context,
            )
        else:
            redacted_samples: dict[str, list[str]] = {}
            for col in columns:
                v = verdict_by_col[col.name]
                if v.is_pii:
                    label = v.detected_entities[0] if v.detected_entities else "PII"
                    redacted_samples[col.name] = [f"[REDACTED:{label}]" for _ in col.sample_values]
                else:
                    redacted_samples[col.name] = [
                        _redact(s, self._recognizer.recognize(s)) for s in col.sample_values
                    ]
            payload = BalancedPayload(
                domain=domain,
                prompt_template_id=prompt_template_id,
                purpose=purpose,
                column_metadata=column_metadata,
                metric_values=metric_values or {},
                narrative_context=narrative_context,
                redacted_samples=redacted_samples,
            )

        audit = PrivacyAuditLog(
            columns_inspected=[c.name for c in columns],
            pii_columns=[v.column for v in verdicts if v.is_pii],
            entity_counts=dict(entity_counter),
            privacy_mode=mode,
        )

        return PrivacyOutcome(payload=payload, audit=audit, verdicts=verdicts)


__all__ = [
    "COLUMN_PII_THRESHOLD",
    "PII_COLUMN_NAME_HINTS",
    "ColumnPrivacyVerdict",
    "PrivacyAuditLog",
    "PrivacyFilter",
    "PrivacyMode",
    "PrivacyOutcome",
]
