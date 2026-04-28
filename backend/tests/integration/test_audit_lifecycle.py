"""End-to-end happy-path: upload → analyze → remediate → sign-off → report.

This is the demo spine. If this passes, the live demo flow works.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nyayalens.adapters.mock_llm import MockLLMClient
from nyayalens.api import deps
from nyayalens.main import create_app

DEMO_CSV = (
    Path(__file__).resolve().parents[3] / "shared" / "sample_data" / "placement_synthetic.csv"
)


def _seed_mock_llm() -> MockLLMClient:
    mock = MockLLMClient(audit_sink=None, backend_name="mock-llm")
    # Schema-detection fixture aligned with the synthetic placement CSV.
    mock.add_structured(
        "schema.detect.v1",
        "schema_detection",
        {
            "sensitive_attributes": [
                {
                    "column": "Gender",
                    "category": "gender",
                    "confidence": 0.98,
                    "rationale": "Column 'Gender' has values Male/Female.",
                },
                {
                    "column": "Category",
                    "category": "caste",
                    "confidence": 0.92,
                    "rationale": "Column 'Category' uses reservation labels.",
                },
            ],
            "outcome_column": {
                "column": "Placed",
                "positive_value": 1,
                "confidence": 0.99,
            },
            "feature_columns": [
                "CGPA",
                "Backlogs",
                "Internships",
                "Projects",
                "Branch",
            ],
            "identifier_columns": ["Roll_No", "Name", "Email"],
            "score_column": "Score",
        },
    )
    return mock


@pytest.fixture
def client() -> TestClient:
    deps._state = None
    deps._audit_sink = None
    deps._storage = None
    deps._pii = None
    deps._privacy_filter = None
    deps._llm = None
    deps._domain = None

    mock = _seed_mock_llm()

    app = create_app()
    app.dependency_overrides[deps.get_llm] = lambda: mock

    return TestClient(app)


@pytest.fixture
def demo_csv() -> bytes:
    if not DEMO_CSV.exists():
        pytest.skip(f"Demo CSV missing at {DEMO_CSV}")
    return DEMO_CSV.read_bytes()


@pytest.mark.integration
def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.integration
def test_full_audit_lifecycle(client: TestClient, demo_csv: bytes) -> None:
    # 1. Upload dataset
    r = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("placement.csv", demo_csv, "text/csv")},
        data={"domain": "hiring"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    dataset_id = body["dataset_id"]
    assert body["row_count"] > 0

    # 2. Detect schema
    r = client.post(f"/api/v1/datasets/{dataset_id}/detect-schema")
    assert r.status_code == 200, r.text
    schema = r.json()
    sens_cols = [s["column"] for s in schema["sensitive_attributes"]]
    assert "Gender" in sens_cols
    assert schema["outcome_column"]["column"] == "Placed"

    # 3. Create audit
    r = client.post(
        "/api/v1/audits",
        json={
            "title": "Synthetic placement audit",
            "dataset_id": dataset_id,
            "domain": "hiring",
            "mode": "audit",
            "provenance_kind": "synthetic",
            "provenance_label": "Synthetic seeded for demo",
            "sensitive_attributes": ["Gender", "Category"],
            "outcome_column": "Placed",
            "positive_value": 1,
            "score_column": "Score",
            "feature_columns": ["CGPA", "Backlogs", "Internships", "Projects"],
            "identifier_columns": ["Roll_No", "Name", "Email"],
        },
    )
    assert r.status_code == 200, r.text
    audit_id = r.json()["audit_id"]

    # 4. Analyze
    r = client.post(f"/api/v1/audits/{audit_id}/analyze")
    assert r.status_code == 200, r.text
    detail = r.json()
    metric_names = {m["metric"] for m in detail["metrics"]}
    assert {"spd", "dir", "eod"}.issubset(metric_names), detail["metrics"]
    assert detail["summary"]["status"] == "ready_for_review"
    assert len(detail["heatmap_cells"]) >= len(detail["sensitive_attributes"])
    dir_cell = next(
        (c for c in detail["heatmap_cells"] if c["metric"] == "dir" and c["attribute"] == "Gender"),
        None,
    )
    assert dir_cell is not None
    assert dir_cell["value"] is not None
    assert dir_cell["value"] < 0.80

    # 5. Remediate
    r = client.post(
        f"/api/v1/audits/{audit_id}/remediate",
        json={
            "target_attribute": "Gender",
            "justification": "Address gender disparity per F7 reweighting.",
        },
    )
    assert r.status_code == 200, r.text
    rem = r.json()["remediation"]
    assert rem is not None
    # Demo seed has a documented Female/Male disparity; reweighting must
    # measure that disparity (DIR < 0.80) and provably equalise rates
    # (Kamiran/Calders aligns group rates to P(y=1), so post-DIR == 1.0).
    assert rem["dir_before"] < 0.80
    assert rem["dir_after"] == pytest.approx(1.0, abs=1e-9)

    # 6. Sign off
    r = client.post(
        f"/api/v1/audits/{audit_id}/sign-off",
        json={
            "notes": "Reviewed disparity; accepting reweighting tradeoff.",
            "confirmed": True,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["sign_off"] is not None
    assert r.json()["summary"]["status"] == "signed_off"

    # 7. Generate report
    r = client.post(f"/api/v1/audits/{audit_id}/report/generate")
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["size_bytes"] > 1000

    # 8. Fetch the PDF
    r = client.get(f"/api/v1/audits/{audit_id}/report")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:4] == b"%PDF"

    # 9. Audit-trail records the lifecycle
    r = client.get("/api/v1/audit-trail")
    assert r.status_code == 200
    actions = {e["action"] for e in r.json()}
    expected = {
        "dataset_uploaded",
        "schema_detected",
        "schema_confirmed",
        "analysis_completed",
        "mitigation_applied",
        "signoff_completed",
        "report_generated",
    }
    assert expected.issubset(actions)


@pytest.mark.integration
def test_jd_scan_endpoint(client: TestClient) -> None:
    r = client.post(
        "/api/v1/probes/job-description",
        json={
            "job_title": "Software Engineer",
            "job_description": (
                "We are looking for a fearless, aggressive rockstar engineer "
                "who is a digital native and can lead the team."
            ),
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    flagged = {f["phrase"] for f in body["flagged_phrases"]}
    assert {
        "fearless",
        "aggressive",
        "rockstar",
        "digital native",
        "leader",
    } & flagged or {"fearless", "aggressive", "rockstar"} & flagged
    assert body["inclusivity_score"] < 0.5
