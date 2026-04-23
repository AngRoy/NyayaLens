"""In-memory `LLMClient` used by unit tests and offline demos.

Fixture-based: callers provide a dict mapping `(prompt_template_id, purpose)`
tuples to canned responses. Unknown keys raise an explicit error — tests
fail loudly rather than pretend a response existed.
"""

from __future__ import annotations

from typing import Any

from nyayalens.core._contracts.audit import AuditEvent, AuditSink
from nyayalens.core._contracts.llm import LLMClient, LLMPayload, PrivacyLogEntry


class MockLLMClientError(RuntimeError):
    """Raised when the mock has no fixture for a requested call."""


class MockLLMClient(LLMClient):
    """Deterministic fixture replay.

    Example:
        fixtures = {
            ("schema.detect.v1", "schema_detection"): {
                "sensitive_attributes": [
                    {"column": "Gender", "confidence": 0.98},
                ],
                "outcome_column": {"column": "Placed"},
                "feature_columns": ["CGPA"],
                "identifier_columns": ["Roll_No"],
            },
        }
        client = MockLLMClient(fixtures, audit_sink=sink)
        result = await client.generate_structured(payload, schema)
    """

    def __init__(
        self,
        structured_fixtures: dict[tuple[str, str], dict[str, Any]] | None = None,
        text_fixtures: dict[tuple[str, str], str] | None = None,
        *,
        audit_sink: AuditSink | None = None,
        backend_name: str = "mock-llm",
    ) -> None:
        self._structured = dict(structured_fixtures or {})
        self._text = dict(text_fixtures or {})
        self._audit_sink = audit_sink
        self._backend_name = backend_name
        self.calls: list[tuple[str, LLMPayload]] = []
        """Record of every call — tests assert on this."""

    # --- Fixture mutation helpers (for tests) ---

    def add_structured(
        self, prompt_template_id: str, purpose: str, response: dict[str, Any]
    ) -> None:
        self._structured[(prompt_template_id, purpose)] = response

    def add_text(self, prompt_template_id: str, purpose: str, response: str) -> None:
        self._text[(prompt_template_id, purpose)] = response

    # --- Protocol implementation ---

    async def generate_structured(
        self,
        payload: LLMPayload,
        json_schema: dict[str, Any],  # noqa: ARG002 — validated via protocol
        *,
        audit_id: str | None = None,
    ) -> dict[str, Any]:
        self._type_check(payload)
        key = (payload.prompt_template_id, payload.purpose)
        self.calls.append(("structured", payload))

        if key not in self._structured:
            raise MockLLMClientError(
                f"No structured fixture for {key}. "
                f"Add one with MockLLMClient.add_structured()."
            )

        await self._emit_privacy_log(payload, audit_id=audit_id)
        return self._structured[key]

    async def generate_text(
        self,
        payload: LLMPayload,
        *,
        audit_id: str | None = None,
    ) -> str:
        self._type_check(payload)
        key = (payload.prompt_template_id, payload.purpose)
        self.calls.append(("text", payload))

        if key not in self._text:
            raise MockLLMClientError(
                f"No text fixture for {key}. "
                f"Add one with MockLLMClient.add_text()."
            )

        await self._emit_privacy_log(payload, audit_id=audit_id)
        return self._text[key]

    # --- Internals ---

    @staticmethod
    def _type_check(payload: object) -> None:
        """Defence in depth for the mypy guarantee.

        `LLMPayload` is a type-only union; at runtime we verify the payload
        quacks right by checking for `.mode`. Even the mock refuses `str`.
        """
        if isinstance(payload, str) or not hasattr(payload, "mode"):
            raise TypeError(
                "LLMClient accepts LLMPayload only; received "
                f"{type(payload).__name__}. Construct a payload via PrivacyFilter."
            )

    async def _emit_privacy_log(
        self, payload: LLMPayload, *, audit_id: str | None
    ) -> None:
        if self._audit_sink is None:
            return
        entry = PrivacyLogEntry(
            audit_id=audit_id,
            purpose=payload.purpose,
            prompt_template_id=payload.prompt_template_id,
            model_backend=self._backend_name,
            mode=payload.mode,
        )
        # Privacy logs are audit events too.
        await self._audit_sink.write(
            AuditEvent(
                audit_id=audit_id,
                organization_id="",  # filled in by caller's middleware in real adapters
                action="privacy_log",
                user_id="system",
                user_name="mock_llm",
                user_role="system",
                details=entry.model_dump(),
            )
        )


__all__ = ["MockLLMClient", "MockLLMClientError"]
