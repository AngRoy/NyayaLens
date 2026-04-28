"""In-memory adapter implementations.

Used by:
- Tests under `backend/tests/`
- Local-dev mode when no Firebase emulator is configured
- Demo mode for offline runs

All implement protocols from `core/_contracts/`.
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import BinaryIO

from nyayalens.core._contracts.audit import AuditEvent, AuditSink
from nyayalens.core._contracts.pii import PIIMatch, PIIRecognizer
from nyayalens.core._contracts.storage import StorageClient


class InMemoryAuditSink(AuditSink):
    """Append-only in-memory audit-trail writer."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def write(self, event: AuditEvent) -> None:
        self.events.append(event)

    async def write_batch(self, events: list[AuditEvent]) -> None:
        self.events.extend(events)


class InMemoryStorage(StorageClient):
    """Dict-backed `StorageClient`. URLs are pseudo (`mem://<path>`)."""

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def upload(
        self,
        path: str,
        content: BinaryIO | bytes,
        *,
        content_type: str | None = None,
    ) -> str:
        if isinstance(content, bytes | bytearray):
            self._store[path] = bytes(content)
        else:
            self._store[path] = content.read()
        return f"mem://{path}"

    async def download(self, path: str) -> bytes:
        if path not in self._store:
            raise FileNotFoundError(path)
        return self._store[path]

    async def exists(self, path: str) -> bool:
        return path in self._store

    async def delete(self, path: str) -> None:
        self._store.pop(path, None)

    async def signed_url(
        self,
        path: str,
        *,
        expires_in: timedelta = timedelta(minutes=15),
    ) -> str:
        return f"mem://{path}?signed=1"

    def get(self, path: str) -> bytes | None:
        """Test helper — direct read."""
        return self._store.get(path)


# ---- PII recognizer (stdlib only — no Presidio) -------------------------

# Phone matcher accepts:
#   - Indian bare 10-digit starting with 6-9 (`9876543210`)
#   - Indian E.164 with optional space/hyphen (`+91 9876543210`)
#   - Generic international E.164: `+CC` plus 7-14 digits with optional
#     internal spaces/hyphens (e.g. `+1 415 555 0123`, `+44 20 7946 0958`,
#     `+33 1 42 86 82 00`).
# 7-digit minimum body avoids matching short numeric spans (pins, years).
_PHONE_RE = re.compile(r"(?:\+\d{1,3}[-\s]?(?:\d[-\s]?){6,13}\d|(?:\+?91[-\s]?)?[6-9]\d{9})")

_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL_ADDRESS": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "PHONE_NUMBER": _PHONE_RE,
    "IN_AADHAAR": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "IN_PAN": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "IN_ROLL_NO": re.compile(r"\b\d{2}[A-Z]{2,3}\d{3,4}\b"),
    "URL": re.compile(r"https?://[\w./%-]+"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "IP_ADDRESS": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


class RegexPIIRecognizer(PIIRecognizer):
    """Pattern-only PII recogniser. Use the Presidio adapter in prod for breadth."""

    def __init__(self, extra: dict[str, re.Pattern[str]] | None = None) -> None:
        self._patterns = dict(_PII_PATTERNS)
        if extra:
            self._patterns.update(extra)

    def recognize(self, text: str) -> list[PIIMatch]:
        out: list[PIIMatch] = []
        for entity, pat in self._patterns.items():
            for m in pat.finditer(text):
                out.append(
                    PIIMatch(
                        entity_type=entity,
                        start=m.start(),
                        end=m.end(),
                        score=0.85,
                        recognizer="regex",
                    )
                )
        return out

    @property
    def supported_entities(self) -> list[str]:
        return sorted(self._patterns.keys())


__all__ = ["InMemoryAuditSink", "InMemoryStorage", "RegexPIIRecognizer"]
