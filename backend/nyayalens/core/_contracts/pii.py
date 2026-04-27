"""PII-recognition contract — keeps `core/` SDK-free per ADR 0001.

Concrete implementations live in `adapters/presidio_pii.py` (uses
presidio-analyzer's pattern recognizers — see ADR 0003). `core/schema/pii.py`
depends on this protocol, never on Presidio directly.

Imported by:
- `core/schema/pii.py` PrivacyFilter
- `adapters/presidio_pii.py` concrete recognizer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PIIMatch:
    """One detected PII span in a string."""

    entity_type: str  # e.g. "EMAIL_ADDRESS", "IN_AADHAAR", "IN_PAN"
    start: int
    end: int
    score: float
    recognizer: str = ""


@runtime_checkable
class PIIRecognizer(Protocol):
    """Detect PII spans in text. Stateless. Concrete impl uses Presidio."""

    def recognize(self, text: str) -> list[PIIMatch]:
        """Return zero-or-more PII matches in `text`."""
        ...

    @property
    def supported_entities(self) -> list[str]:
        """Entity-type names this recognizer can produce (for logging)."""
        ...


__all__ = ["PIIMatch", "PIIRecognizer"]
