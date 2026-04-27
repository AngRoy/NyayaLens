"""Applicant-facing recourse summary — design doc §6.3 F9.

Aggregate, transparency-only document. Never includes individual scores or
rankings. Generated once per audit cycle from already-computed metrics +
mitigation result.

Imported by:
- `core/recourse/__init__.py` re-exports
- `api/audits.py:recourse-summary` (forthcoming)
- `core/report/pdf.py` (Part C of audit PDF, forthcoming)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime

from nyayalens.core.bias.metrics import MetricResult
from nyayalens.core.mitigate.reweighting import ReweightingResult

DEFAULT_REGULATORY_REFERENCES: list[str] = [
    "EU AI Act Article 86 — right to explanation for high-risk decisions.",
    "India AI Governance Sutra: People-First Governance.",
    "NIST AI RMF MANAGE 4.1 — incident response and recourse.",
]


@dataclass(frozen=True, slots=True)
class RecourseSummary:
    audit_id: str
    organization_name: str
    decision_cycle_label: str
    automated_tools_used: list[str]
    factor_categories: list[str]
    aggregate_statistics: dict[str, str]
    how_to_request_review: str
    contact_email: str
    regulatory_references: list[str] = field(
        default_factory=lambda: list(DEFAULT_REGULATORY_REFERENCES)
    )
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def _format_metric_pair(name: str, value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{name}={value:.2f}"


def build_recourse_summary(
    *,
    audit_id: str,
    organization_name: str,
    decision_cycle_label: str,
    metrics: list[MetricResult],
    factor_categories: list[str],
    automated_tools_used: list[str],
    contact_email: str,
    sla_business_days: int = 15,
    remediation: ReweightingResult | None = None,
    extra_regulatory_references: list[str] | None = None,
) -> RecourseSummary:
    """Compose the summary. Only reliable metrics are surfaced."""
    aggregate: dict[str, str] = {}
    for r in metrics:
        if not r.reliable or r.value is None:
            continue
        aggregate[r.metric] = _format_metric_pair(r.metric, r.value)

    if remediation is not None:
        aggregate["dir_after_mitigation"] = (
            "n/a" if math.isnan(remediation.dir_after) else f"{remediation.dir_after:.2f}"
        )

    how_to = (
        "If you believe an automated decision in this cycle was unfair, you "
        "can request a human review. Email "
        f"{contact_email} with a short description of the decision you'd "
        f"like reviewed. We aim to acknowledge requests within 5 business "
        f"days and respond with a resolution within {sla_business_days} "
        "business days."
    )

    refs = list(DEFAULT_REGULATORY_REFERENCES)
    if extra_regulatory_references:
        refs.extend(extra_regulatory_references)

    return RecourseSummary(
        audit_id=audit_id,
        organization_name=organization_name,
        decision_cycle_label=decision_cycle_label,
        automated_tools_used=list(automated_tools_used),
        factor_categories=list(factor_categories),
        aggregate_statistics=aggregate,
        how_to_request_review=how_to,
        contact_email=contact_email,
        regulatory_references=refs,
    )


__all__ = ["DEFAULT_REGULATORY_REFERENCES", "RecourseSummary", "build_recourse_summary"]
