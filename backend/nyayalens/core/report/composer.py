"""PDF audit-report composer — design doc §6.3 F10.

Builds a UI- and renderer-agnostic `AuditReportData`:

  Part A — Audit Findings (real/public data)
  Part B — Probe Findings (LLM-generated scenarios)
  Part C — Governance Record (mitigation, sign-off, recourse)

Imported by:
- `core/report/__init__.py` re-exports
- `api/audits.py:report/generate` POST endpoint (forthcoming)
- `adapters/reportlab_pdf.py` (forthcoming) consumes the data to render bytes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from nyayalens.core.bias.conflicts import Conflict
from nyayalens.core.bias.metrics import MetricResult
from nyayalens.core.bias.proxies import ProxyFlag
from nyayalens.core.explain.validator import Explanation
from nyayalens.core.llm_probe.job_description import JdScanResult
from nyayalens.core.llm_probe.resume_screening import PerturbationProbeResult
from nyayalens.core.mitigate.reweighting import ReweightingResult
from nyayalens.core.recourse.summary import RecourseSummary


@dataclass(frozen=True, slots=True)
class AuditSection:
    """One numbered section in the PDF."""

    heading: str
    body: list[str]
    table: list[list[str]] | None = None


@dataclass(frozen=True, slots=True)
class AuditReportData:
    """The full PDF payload."""

    organization_name: str
    audit_id: str
    audit_title: str
    domain: str
    mode: str  # "audit" | "probe"
    provenance_label: str
    provenance_kind: str

    part_a_audit: list[AuditSection]
    part_b_probe: list[AuditSection]
    part_c_governance: list[AuditSection]

    methodology_appendix: list[AuditSection]
    sign_off: dict[str, Any] | None
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def _format_metric_row(r: MetricResult) -> list[str]:
    if r.value is None or not r.reliable:
        return [r.metric, "n/a", str(r.threshold or ""), r.reason or ""]
    return [
        r.metric,
        f"{r.value:.4f}",
        str(r.threshold or ""),
        f"priv: {r.privileged or '?'} / unpriv: {r.unprivileged or '?'}",
    ]


def build_audit_report(
    *,
    organization_name: str,
    audit_id: str,
    audit_title: str,
    domain: str,
    mode: str,
    provenance_label: str,
    provenance_kind: str,
    schema_summary: dict[str, Any],
    metrics: list[MetricResult],
    explanations: list[Explanation],
    conflicts: list[Conflict],
    proxy_flags: list[ProxyFlag],
    remediation: ReweightingResult | None,
    perturbation_probe: PerturbationProbeResult | None,
    jd_scan: JdScanResult | None,
    recourse: RecourseSummary | None,
    sign_off: dict[str, Any] | None,
) -> AuditReportData:
    """Compose the section list for the PDF."""
    section_number = 1

    def heading(title: str) -> str:
        nonlocal section_number
        value = f"{section_number}. {title}"
        section_number += 1
        return value

    # ----- Part A: Audit findings -----
    part_a: list[AuditSection] = []
    part_a.append(
        AuditSection(
            heading=heading("Executive Summary"),
            body=[
                f"Audit '{audit_title}' was conducted on {provenance_label} "
                f"({provenance_kind} data) within the {domain} domain.",
                f"Mode: {mode}. Sensitive attributes assessed: "
                + ", ".join(schema_summary.get("sensitive_attributes", []) or ["(none)"]),
            ],
        )
    )
    part_a.append(
        AuditSection(
            heading=heading("Dataset Overview"),
            body=[
                f"Outcome column: {schema_summary.get('outcome_column', 'n/a')}",
                f"Feature columns: {len(schema_summary.get('feature_columns', []))}",
                "Identifier columns (excluded): "
                + ", ".join(schema_summary.get("identifier_columns", []) or ["(none)"]),
            ],
        )
    )
    part_a.append(
        AuditSection(
            heading=heading("Fairness Metrics"),
            body=[
                "Each metric is reported with the reference threshold and the "
                "privileged/unprivileged groups on this dataset."
            ],
            table=[["Metric", "Value", "Threshold", "Notes"]]
            + [_format_metric_row(m) for m in metrics],
        )
    )
    part_a.append(
        AuditSection(
            heading=heading("Per-Metric Explanations"),
            body=[
                f"{e.metric} on {e.attribute}: {e.summary}\n  {e.interpretation}"
                for e in explanations
            ],
        )
    )
    part_a.append(
        AuditSection(
            heading=heading("Metric-Conflict Analysis"),
            body=(
                [
                    f"{c.metric_a} vs {c.metric_b}: {c.description}\n  {c.recommendation}"
                    for c in conflicts
                ]
                or ["No metric conflicts surfaced for this audit."]
            ),
        )
    )
    part_a.append(
        AuditSection(
            heading=heading("Proxy-Feature Flags"),
            body=(
                [
                    f"{f.feature} → {f.sensitive_attribute} via {f.method} at "
                    f"{f.strength:.2f} ({f.severity})"
                    for f in proxy_flags
                ]
                or ["No features crossed the proxy-correlation threshold."]
            ),
        )
    )

    # ----- Part B: Probe findings -----
    part_b: list[AuditSection] = []
    if perturbation_probe is not None:
        rows = [["Variant", "Score", "Flagged phrases"]]
        for v in perturbation_probe.variants:
            rows.append(
                [
                    v.label,
                    "n/a" if v.score is None else f"{v.score:.1f}",
                    ", ".join(v.flagged_phrases) or "—",
                ]
            )
        part_b.append(
            AuditSection(
                heading=heading("LLM Demographic Perturbation"),
                body=[
                    f"Role: {perturbation_probe.role}",
                    f"Maximum score difference across variants: "
                    f"{perturbation_probe.max_score_difference:.2f}",
                    perturbation_probe.interpretation,
                ],
                table=rows,
            )
        )
    if jd_scan is not None:
        part_b.append(
            AuditSection(
                heading=heading("Job-Description Bias Scan"),
                body=[
                    f"Inclusivity score: {jd_scan.inclusivity_score:.2f}",
                    "Flagged phrases: "
                    + (", ".join(f.phrase for f in jd_scan.flagged_phrases) or "—"),
                    *jd_scan.rewrite_suggestions,
                ],
            )
        )
    # ----- Part C: Governance record -----
    part_c: list[AuditSection] = []
    if remediation is not None:
        dir_before = "n/a" if remediation.dir_before is None else f"{remediation.dir_before:.4f}"
        dir_after = "n/a" if remediation.dir_after is None else f"{remediation.dir_after:.4f}"
        part_c.append(
            AuditSection(
                heading=heading("Mitigation"),
                body=[
                    "Strategy: reweighting (Kamiran/Calders 2012).",
                    f"DIR before mitigation: {dir_before}",
                    f"DIR after mitigation: {dir_after}",
                    f"Estimated accuracy delta: {remediation.accuracy_estimate_delta:+.4f}",
                ],
            )
        )
    else:
        part_c.append(
            AuditSection(
                heading=heading("Mitigation"),
                body=["No mitigation was applied for this audit."],
            )
        )

    if sign_off:
        part_c.append(
            AuditSection(
                heading=heading("Human Accountability"),
                body=[
                    f"Reviewer: {sign_off.get('reviewer_name', '?')} "
                    f"({sign_off.get('reviewer_role', '?')})",
                    f"Signed at: {sign_off.get('signed_at', '?')}",
                    f"Notes: {sign_off.get('notes', '(none)')}",
                ],
            )
        )
    else:
        part_c.append(
            AuditSection(
                heading=heading("Human Accountability"),
                body=["This audit has not yet been signed off."],
            )
        )

    if recourse is not None:
        part_c.append(
            AuditSection(
                heading=heading("Applicant Recourse"),
                body=[
                    "Aggregate statistics provided to applicants:",
                    *[f"  - {k}: {v}" for k, v in recourse.aggregate_statistics.items()],
                    "How to request review:",
                    f"  {recourse.how_to_request_review}",
                ],
            )
        )

    part_c.append(
        AuditSection(
            heading=heading("Regulatory Alignment"),
            body=[
                "EU AI Act Article 10 — bias testing.",
                "EU AI Act Article 14 — human oversight.",
                "India AI Governance Sutras — fairness, accountability, recourse.",
                "NIST AI RMF — MAP, MEASURE, MANAGE, GOVERN coverage.",
            ],
        )
    )

    methodology = [
        AuditSection(
            heading="A. Methodology",
            body=[
                "Metrics implemented as pure NumPy/Pandas functions and validated "
                "against AIF360 / Fairlearn fixtures. See repository NOTICE for "
                "attribution.",
                "Privacy: all LLM payloads pass through the PrivacyFilter (typed "
                "envelopes; raw row data never reaches the LLM in Audit Mode).",
                "Probe Mode: LLM scenario probes are reported only when a probe "
                "run is part of the audit scope. Audit Mode findings and Probe "
                "Mode findings are never mixed.",
                "Mitigation: Kamiran/Calders 2012 reweighting; before/after rates "
                "computed directly from the empirical data.",
                "Grounding: every digit in a Gemini explanation is verified against "
                "injected metric values; failure falls back to a deterministic template.",
            ],
        )
    ]

    return AuditReportData(
        organization_name=organization_name,
        audit_id=audit_id,
        audit_title=audit_title,
        domain=domain,
        mode=mode,
        provenance_label=provenance_label,
        provenance_kind=provenance_kind,
        part_a_audit=part_a,
        part_b_probe=part_b,
        part_c_governance=part_c,
        methodology_appendix=methodology,
        sign_off=sign_off,
    )


__all__ = ["AuditReportData", "AuditSection", "build_audit_report"]
