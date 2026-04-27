"""Hiring-domain text templates: applicant factor categories + regulatory refs.

Imported by:
- `core/domains/hiring/__init__.py` re-exports
- `core/domains/hiring/registry.py` HiringDomain.factor_categories
- `api/audits.py:recourse-summary` (forthcoming)
"""

from __future__ import annotations

HIRING_FACTOR_CATEGORIES: list[str] = [
    "Academic performance (e.g. CGPA, backlogs)",
    "Demonstrated experience (internships, projects, prior work)",
    "Domain alignment between candidate and role",
    "Submitted application materials (resume, cover note)",
    "Aggregate fairness statistics for the cycle (this report)",
]

HIRING_REGULATORY_REFERENCES: list[str] = [
    "EU AI Act Article 86 — right to explanation in high-risk employment decisions.",
    "EU AI Act Article 10 — bias testing for high-risk AI systems.",
    "India AI Governance Sutra: Fairness & Equity.",
    "India AI Governance Sutra: People-First Governance.",
    "NIST AI RMF MANAGE 4.1 — incident response and recourse.",
    "NYC Local Law 144 — annual bias audit for AEDTs.",
]


__all__ = ["HIRING_FACTOR_CATEGORIES", "HIRING_REGULATORY_REFERENCES"]
