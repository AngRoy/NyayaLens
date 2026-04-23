"""LLM client contract — privacy enforced at the type boundary.

See ADR 0005. Raw strings cannot reach the LLM adapter: the only way to
construct an `LLMPayload` is through `core.schema.pii.PrivacyFilter`, which
applies column-level PII scrubbing before producing a payload.

Three modes correspond to design doc §14.2:

  - **Strict:**    only aggregate metadata (column names, types, distributions).
  - **Balanced:**  sanitized metadata + redacted sample values.
  - **Local:**     full data, permitted only when routed to a local Gemma model.

Each mode is a distinct Pydantic model so mypy can statically verify that
callers send the right shape to the right endpoint.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class _BasePayload(BaseModel):
    """Common fields every LLM payload carries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: Literal["strict", "balanced", "local"]
    """Which privacy mode this payload was constructed under."""

    domain: str = Field(
        default="hiring",
        description="Domain layer (see core.domains) — used to select prompt packs.",
    )

    prompt_template_id: str = Field(
        description=(
            "Stable ID of the prompt template being rendered. Recorded in the "
            "privacy log so an auditor can reproduce the exact call."
        ),
    )

    purpose: str = Field(
        description=(
            "Short human-readable purpose (e.g. 'schema_detection', "
            "'explain_dir', 'probe_perturbation'). Logged, not sent to the LLM."
        ),
    )


class StrictPayload(_BasePayload):
    """Strictest privacy mode.

    Only aggregate column metadata and/or pre-computed metric values are sent
    to the LLM. No row-level data — not even redacted.
    """

    mode: Literal["strict"] = "strict"

    column_metadata: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Per-column summary: name, inferred dtype, null count, cardinality, "
            "distribution summary (e.g. min/max/mean for numeric, top-k counts "
            "for categorical). Never raw cells."
        ),
    )

    metric_values: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Pre-computed metric numbers from the bias engine, injected into the "
            "prompt so the LLM translates rather than generates numbers."
        ),
    )

    narrative_context: str = Field(
        default="",
        description=(
            "Free text authored by NyayaLens itself (no user data). For example, "
            "a domain-specific framing paragraph from core.domains.*.prompts."
        ),
    )


class BalancedPayload(_BasePayload):
    """Default privacy mode.

    Same as Strict plus a handful of redacted sample values per column
    (after the PII Pre-Scrubber has masked/hashed sensitive fields).
    """

    mode: Literal["balanced"] = "balanced"

    column_metadata: list[dict[str, Any]] = Field(default_factory=list)
    metric_values: dict[str, Any] = Field(default_factory=dict)
    narrative_context: str = ""

    redacted_samples: dict[str, list[str]] = Field(
        default_factory=dict,
        description=(
            "Per-column list of up to N sample values with PII masked "
            "(e.g. email -> '[REDACTED:EMAIL]', Aadhaar -> '[REDACTED:AADHAAR]'). "
            "Non-PII columns pass through; PII columns are always redacted."
        ),
    )


class LocalPayload(_BasePayload):
    """Local-only mode — full data may appear, but the call must route to a local model.

    Used exclusively by `adapters.gemma.LocalGemmaAdapter` (post-MVP). Raising
    this payload with a cloud adapter is a runtime error — the adapter checks
    its destination in `__init__` and refuses payloads it cannot handle.
    """

    mode: Literal["local"] = "local"

    full_rows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Full row data — ONLY valid when the destination is a local model.",
    )


# Discriminated union. `LLMClient.generate_*` accepts this type and nothing else.
# Passing a bare `str` is a mypy error.
LLMPayload = StrictPayload | BalancedPayload | LocalPayload


class PrivacyLogEntry(BaseModel):
    """Emitted by the adapter on every LLM call; goes to the audit sink."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    audit_id: str | None = Field(
        default=None,
        description="Enclosing audit, if the call is part of one.",
    )
    purpose: str
    prompt_template_id: str
    model_backend: str = Field(description="e.g. 'gemini-flash-latest' or 'gemma-4-local'.")
    mode: Literal["strict", "balanced", "local"]
    columns_inspected: list[str] = Field(default_factory=list)
    pii_masked: dict[str, int] = Field(
        default_factory=dict,
        description="Map entity_type -> count of cells masked.",
    )
    input_token_count: int | None = None
    output_token_count: int | None = None
    duration_ms: int | None = None
    retry_attempts: int = 0
    grounding_validated: bool | None = None


@runtime_checkable
class LLMClient(Protocol):
    """Protocol that every LLM adapter must implement.

    Adapters live in `nyayalens.adapters`; the only place in the codebase
    permitted to import third-party SDKs. `core/` modules depend on this
    protocol, never on a concrete adapter class.
    """

    async def generate_structured(
        self,
        payload: LLMPayload,
        json_schema: dict[str, Any],
        *,
        audit_id: str | None = None,
    ) -> dict[str, Any]:
        """Return a dict that conforms to `json_schema`.

        Raises:
            TypeError: if `payload` is not an `LLMPayload` instance.
                (mypy should catch this statically; the runtime check is
                defense in depth.)
        """
        ...

    async def generate_text(
        self,
        payload: LLMPayload,
        *,
        audit_id: str | None = None,
    ) -> str:
        """Return the model's textual response for the given payload."""
        ...


__all__ = [
    "BalancedPayload",
    "LLMClient",
    "LLMPayload",
    "LocalPayload",
    "PrivacyLogEntry",
    "StrictPayload",
]
