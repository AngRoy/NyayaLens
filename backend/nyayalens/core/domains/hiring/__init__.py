"""Hiring domain plug — design doc §6.2."""

from nyayalens.core.domains.hiring.prompts import (
    HIRING_DOMAIN_CONTEXT,
    HIRING_SCHEMA_HINT,
)
from nyayalens.core.domains.hiring.registry import HiringDomain
from nyayalens.core.domains.hiring.templates import (
    HIRING_FACTOR_CATEGORIES,
    HIRING_REGULATORY_REFERENCES,
)

__all__ = [
    "HIRING_DOMAIN_CONTEXT",
    "HIRING_FACTOR_CATEGORIES",
    "HIRING_REGULATORY_REFERENCES",
    "HIRING_SCHEMA_HINT",
    "HiringDomain",
]
