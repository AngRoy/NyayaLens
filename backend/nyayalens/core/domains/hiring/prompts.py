"""Hiring-domain prompt context strings.

Composed at call time with the domain-agnostic templates in
`core/explain/prompts.py`. Indian conventions (caste category, branch,
roll-number patterns) are explicit so Gemini disambiguates correctly.

Imported by:
- `core/domains/hiring/__init__.py` re-exports
- `core/domains/hiring/registry.py` HiringDomain.explain_context
"""

from __future__ import annotations

HIRING_DOMAIN_CONTEXT: str = (
    "Context for this audit: a hiring or campus-placement decision pipeline. "
    "Sensitive attributes typically include gender, age, caste/category "
    "(General, OBC, SC, ST), religion, disability, and marital status. "
    "Indian datasets often label caste as 'Category' or 'Caste' and may use "
    "'Quota' for reservation status. The outcome column is usually a placement "
    "indicator (Placed / Not Placed) or a hiring decision (Hired / Rejected). "
    "Reference threshold heritage: the 80% rule (DIR >= 0.80) derives from US "
    "EEOC Uniform Guidelines and is widely adopted as an engineering "
    "reference. The other thresholds (|SPD| < 0.10, |EOD| < 0.10, "
    "consistency > 0.80, calibration < 0.05) are common engineering reference "
    "points, not legal standards. Always present findings as evidence to "
    "investigate, never as a determination of fairness."
)

HIRING_SCHEMA_HINT: str = (
    "When detecting schema, prefer:\n"
    "  - Sensitive attributes: gender (Male/Female/Other), age (numeric or "
    "bracket), category (General/OBC/SC/ST), religion, disability, "
    "marital_status, nationality.\n"
    "  - Outcome columns: 'Placed', 'Selected', 'Hired', 'Result', "
    "'Decision', 'Outcome', 'Status'. Positive outcome is typically the "
    "value indicating selection (1, 'Yes', 'Placed', 'Hired').\n"
    "  - Identifier columns: 'Name', 'Roll_No', 'RollNo', 'Email', "
    "'Phone', 'Mobile', 'Aadhaar', 'PAN', 'Student_ID', 'Employee_ID'. "
    "These must NEVER be used as features.\n"
    "  - Score columns: 'Score', 'Probability', 'P_Hire'; 'CGPA' is a "
    "feature, not a score.\n"
    "Set confidence < 0.6 when unsure; the UI will force a human to confirm."
)


__all__ = ["HIRING_DOMAIN_CONTEXT", "HIRING_SCHEMA_HINT"]
