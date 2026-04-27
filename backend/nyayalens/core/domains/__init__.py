"""Domain layer — pluggable per design §6.2.

Each domain plugs domain-specific prompt context, recourse templates, and
regulatory references into the otherwise domain-agnostic core. v1 ships
hiring; future domains (lending, admissions) drop in alongside.
"""

from nyayalens.core.domains.hiring.registry import HiringDomain

__all__ = ["HiringDomain"]
