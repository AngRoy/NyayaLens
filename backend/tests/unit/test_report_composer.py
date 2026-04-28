from nyayalens.core.report.composer import build_audit_report


def test_audit_report_omits_probe_part_when_no_probe_was_run() -> None:
    report = build_audit_report(
        organization_name="Demo Org",
        audit_id="audit-1",
        audit_title="Placement audit",
        domain="hiring",
        mode="audit",
        provenance_label="placement.csv",
        provenance_kind="synthetic",
        schema_summary={
            "sensitive_attributes": ["gender"],
            "outcome_column": "selected",
            "feature_columns": ["score"],
            "identifier_columns": [],
        },
        metrics=[],
        explanations=[],
        conflicts=[],
        proxy_flags=[],
        remediation=None,
        perturbation_probe=None,
        jd_scan=None,
        recourse=None,
        sign_off=None,
    )

    assert report.part_b_probe == []
    assert report.part_c_governance[0].heading == "7. Mitigation"
    assert "Probe Mode:" in report.methodology_appendix[0].body[2]
