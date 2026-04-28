"""Gemini API adapter — concrete `LLMClient` implementing ADR 0005.

Backed by the `google-genai` SDK (the maintained successor to the
deprecated `google-generativeai`). Accepts only typed `LLMPayload`
envelopes; raw strings raise a runtime TypeError (mypy catches them
earlier). Every call emits a `PrivacyLogEntry` to the injected audit sink.

Imported by:
- `api/deps.py` — production dependency wiring
- never by `core/` (forbidden by ADR 0001 / `tests/contract/test_import_graph.py`)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any
from uuid import uuid4

from google import genai
from google.genai import types as genai_types
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from nyayalens.core._contracts.audit import AuditEvent, AuditSink
from nyayalens.core._contracts.llm import (
    BalancedPayload,
    LLMClient,
    LLMPayload,
    LocalPayload,
    PrivacyLogEntry,
    StrictPayload,
)

log = logging.getLogger(__name__)


class GeminiCallError(RuntimeError):
    """Raised when Gemini returns malformed JSON or repeatedly fails."""


def _payload_to_text(payload: LLMPayload) -> str:
    """Render a typed payload as the prompt string Gemini will see."""
    if isinstance(payload, LocalPayload):
        raise GeminiCallError("GeminiAdapter cannot send LocalPayload data to a cloud model.")

    parts: list[str] = []
    parts.append(payload.narrative_context.strip())

    if isinstance(payload, StrictPayload | BalancedPayload):
        if payload.metric_values:
            parts.append("\nMetric values (use these exact numbers):")
            parts.append(json.dumps(payload.metric_values, indent=2, default=str))

        if payload.column_metadata:
            parts.append("\nColumn metadata:")
            parts.append(json.dumps(payload.column_metadata, indent=2, default=str))

    if isinstance(payload, BalancedPayload) and payload.redacted_samples:
        parts.append("\nRedacted sample values (PII removed):")
        parts.append(json.dumps(payload.redacted_samples, indent=2, default=str))

    return "\n".join(parts).strip()


class GeminiAdapter(LLMClient):
    """`LLMClient` backed by `google-genai`."""

    def __init__(
        self,
        *,
        api_key: str,
        text_model: str = "gemini-2.5-flash",
        structured_model: str = "gemini-2.5-pro",
        temperature: float = 0.2,
        audit_sink: AuditSink | None = None,
        organization_id: str = "",
        max_concurrent: int = 1,
    ) -> None:
        if not api_key:
            raise ValueError("GeminiAdapter requires a non-empty api_key.")
        self._client = genai.Client(api_key=api_key)
        self._text_model_name = text_model
        self._structured_model_name = structured_model
        self._temperature = temperature
        self._audit = audit_sink
        self._org = organization_id
        self._sema = asyncio.Semaphore(max_concurrent)

    @staticmethod
    def _type_check(payload: object) -> None:
        if isinstance(payload, str) or not hasattr(payload, "mode"):
            raise TypeError(
                "GeminiAdapter accepts LLMPayload only; received "
                f"{type(payload).__name__}. Use PrivacyFilter to construct one."
            )

    async def generate_structured(
        self,
        payload: LLMPayload,
        json_schema: dict[str, Any],
        *,
        audit_id: str | None = None,
    ) -> dict[str, Any]:
        self._type_check(payload)
        prompt = _payload_to_text(payload)
        prompt = (
            prompt
            + "\n\nReturn ONLY a JSON object that matches this schema:\n"
            + json.dumps(json_schema, indent=2)
        )
        text, attempts, dur_ms = await self._call_with_retry(
            model=self._structured_model_name,
            prompt=prompt,
            response_mime_type="application/json",
        )
        try:
            obj = json.loads(_strip_code_fence(text))
        except json.JSONDecodeError as exc:
            log.warning("Gemini structured response was not JSON: %r", text[:300])
            raise GeminiCallError(
                f"Gemini returned non-JSON for structured request: {exc}"
            ) from exc
        await self._emit_privacy_log(
            payload,
            audit_id=audit_id,
            retry_attempts=attempts,
            dur_ms=dur_ms,
            backend=self._structured_model_name,
        )
        return obj if isinstance(obj, dict) else {"value": obj}

    async def generate_text(
        self,
        payload: LLMPayload,
        *,
        audit_id: str | None = None,
    ) -> str:
        self._type_check(payload)
        prompt = _payload_to_text(payload)
        text, attempts, dur_ms = await self._call_with_retry(
            model=self._text_model_name,
            prompt=prompt,
            response_mime_type="text/plain",
        )
        await self._emit_privacy_log(
            payload,
            audit_id=audit_id,
            retry_attempts=attempts,
            dur_ms=dur_ms,
            backend=self._text_model_name,
        )
        return text

    async def _call_with_retry(
        self,
        *,
        model: str,
        prompt: str,
        response_mime_type: str,
    ) -> tuple[str, int, int]:
        attempts = 0
        start = time.perf_counter()
        config = genai_types.GenerateContentConfig(
            temperature=self._temperature,
            response_mime_type=response_mime_type,
        )
        async with self._sema:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(Exception),
                reraise=True,
            ):
                with attempt:
                    attempts += 1
                    response = await self._client.aio.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config,
                    )
                    text: str = getattr(response, "text", "") or ""
                    if not text:
                        raise GeminiCallError("Empty response from Gemini.")
                    dur_ms = int((time.perf_counter() - start) * 1000)
                    return text, attempts, dur_ms
        raise GeminiCallError("Gemini retry loop exhausted unexpectedly.")

    async def _emit_privacy_log(
        self,
        payload: LLMPayload,
        *,
        audit_id: str | None,
        retry_attempts: int,
        dur_ms: int,
        backend: str,
    ) -> None:
        if self._audit is None:
            return
        entry = PrivacyLogEntry(
            audit_id=audit_id,
            purpose=payload.purpose,
            prompt_template_id=payload.prompt_template_id,
            model_backend=backend,
            mode=payload.mode,
            duration_ms=dur_ms,
            retry_attempts=retry_attempts,
        )
        try:
            await self._audit.write(
                AuditEvent(
                    event_id=uuid4(),
                    audit_id=audit_id,
                    organization_id=self._org,
                    action="privacy_log",
                    user_id="system",
                    user_name="gemini_adapter",
                    user_role="system",
                    details=entry.model_dump(),
                )
            )
        except Exception as exc:
            log.warning("Failed to write privacy log: %s", exc)


def _strip_code_fence(text: str) -> str:
    """Gemini sometimes wraps JSON in ```json ... ``` fences. Strip them."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
    if s.endswith("```"):
        s = s.rsplit("```", 1)[0]
    return s.strip()


__all__ = ["GeminiAdapter", "GeminiCallError"]
