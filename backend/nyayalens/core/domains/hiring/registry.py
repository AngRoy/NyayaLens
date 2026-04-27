"""HiringDomain plug — bundles prompts + templates for one injectable handle.

Imported by:
- `core/domains/__init__.py` re-exports `HiringDomain`
- `core/domains/hiring/__init__.py` re-exports `HiringDomain`
- `api/deps.py` (forthcoming) constructs and injects this object
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nyayalens.core.domains.hiring.prompts import (
    HIRING_DOMAIN_CONTEXT,
    HIRING_SCHEMA_HINT,
)
from nyayalens.core.domains.hiring.templates import (
    HIRING_FACTOR_CATEGORIES,
    HIRING_REGULATORY_REFERENCES,
)


@dataclass(frozen=True, slots=True)
class HiringDomain:
    name: str = "hiring"
    explain_context: str = HIRING_DOMAIN_CONTEXT
    schema_hint: str = HIRING_SCHEMA_HINT
    factor_categories: list[str] = field(default_factory=lambda: list(HIRING_FACTOR_CATEGORIES))
    regulatory_references: list[str] = field(
        default_factory=lambda: list(HIRING_REGULATORY_REFERENCES)
    )


__all__ = ["HiringDomain"]
