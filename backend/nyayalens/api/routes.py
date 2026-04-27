"""All HTTP routes for NyayaLens v1.

Sections:
  1. Datasets — upload, detect-schema
  2. Audits   — create, list, get, analyze, remediate, sign-off
  3. Probes   — JD bias scan, demographic perturbation
  4. Recourse — file requests, generate summary
  5. Reports  — generate + fetch PDF
  6. Audit trail — list events

Imported by:
- `nyayalens/main.py` via `app.include_router(routes.router, prefix='/api/v1')`
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict, Field

from nyayalens.adapters.reportlab_pdf import render_audit_report
from nyayalens.api.deps import (
    CurrentUser,
    get_app_state,
    get_audit_writer,
    get_current_user,
    get_domain,
    get_llm,
    get_privacy_filter,
    get_storage,
)
from nyayalens.api.state import AppState, StoredAudit
from nyayalens.core._contracts.llm import LLMClient, LLMPayload, StrictPayload
from nyayalens.core._contracts.storage import StorageClient
from nyayalens.core.bias.conflicts import detect_conflicts
from nyayalens.core.bias.heatmap import Thresholds, assemble_heatmap
from nyayalens.core.bias.proxies import detect_proxies
from nyayalens.core.bias.registry import METRICS
from nyayalens.core.domains.hiring.registry import HiringDomain
from nyayalens.core.explain.validator import explain_metric, template_fallback
from nyayalens.core.govern.audit import AuditWriter
from nyayalens.core.govern.rbac import Permission, require
from nyayalens.core.llm_probe.job_description import scan_job_description
from nyayalens.core.llm_probe.resume_screening import (
    Variation,
    run_perturbation_probe,
)
from nyayalens.core.mitigate.reweighting import apply_reweighting
from nyayalens.core.recourse.summary import build_recourse_summary
from nyayalens.core.report.composer import build_audit_report
from nyayalens.core.schema.detector import SchemaDetector
from nyayalens.core.schema.parser import parse_dataset
from nyayalens.core.schema.pii import PrivacyFilter

router = APIRouter()


def _require(user: CurrentUser, perm: Permission) -> None:
    try:
        require(user.role, perm)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


# ============================================================================
# 1. Datasets
# ============================================================================


class DatasetUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    row_count: int
    column_count: int
    columns: list[dict[str, Any]]
    sample_rows: list[dict[str, Any]]


@router.post(
    "/datasets/upload",
    response_model=DatasetUploadResponse,
    tags=["datasets"],
)
async def upload_dataset(
    file: Annotated[UploadFile, File(...)],
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    audit: Annotated[AuditWriter, Depends(get_audit_writer)],
    domain: Annotated[str, Form()] = "hiring",
) -> DatasetUploadResponse:
    _require(user, "audit.create")
    if file.size is not None and file.size > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Dataset exceeds 100MB limit.",
        )
    raw = await file.read()
    parsed = parse_dataset(raw, filename=file.filename or "upload.csv")
    dataset_id = state.put_dataset(parsed, filename=file.filename or "upload.csv")
    await audit.write(
        "dataset_uploaded",
        details={"dataset_id": dataset_id, "filename": file.filename, "domain": domain},
    )
    return DatasetUploadResponse(
        dataset_id=dataset_id,
        row_count=parsed.row_count,
        column_count=len(parsed.columns),
        columns=[
            {
                "name": c.name,
                "dtype": c.dtype,
                "null_count": c.null_count,
                "unique_count": c.unique_count,
                "sample_values": c.sample_values,
            }
            for c in parsed.columns
        ],
        sample_rows=parsed.sample_rows,
    )


class DetectSchemaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    needs_review: bool
    sensitive_attributes: list[dict[str, Any]]
    outcome_column: dict[str, Any] | None
    feature_columns: list[str]
    identifier_columns: list[str]
    score_column: str | None


@router.post(
    "/datasets/{dataset_id}/detect-schema",
    response_model=DetectSchemaResponse,
    tags=["datasets"],
)
async def detect_schema(
    dataset_id: str,
    state: Annotated[AppState, Depends(get_app_state)],
    privacy: Annotated[PrivacyFilter, Depends(get_privacy_filter)],
    llm: Annotated[LLMClient, Depends(get_llm)],
    domain: Annotated[HiringDomain, Depends(get_domain)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    audit: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> DetectSchemaResponse:
    _require(user, "audit.create")
    ds = state.get_dataset(dataset_id)
    if ds is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dataset not found")
    detector = SchemaDetector(llm, privacy)
    try:
        result = await detector.detect(
            ds.parsed,
            domain=domain.name,
            narrative_context=domain.schema_hint,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Schema detection failed: {exc}",
        ) from exc

    await audit.write(
        "schema_detected",
        details={"dataset_id": dataset_id, "needs_review": result.needs_review},
    )
    return DetectSchemaResponse(
        dataset_id=dataset_id,
        needs_review=result.needs_review,
        sensitive_attributes=[
            {
                "column": s.column,
                "category": s.category,
                "confidence": s.confidence,
                "rationale": s.rationale,
            }
            for s in result.sensitive_attributes
        ],
        outcome_column=(
            None
            if result.outcome is None
            else {
                "column": result.outcome.column,
                "positive_value": result.outcome.positive_value,
                "confidence": result.outcome.confidence,
            }
        ),
        feature_columns=result.feature_columns,
        identifier_columns=result.identifier_columns,
        score_column=result.score_column,
    )


# ============================================================================
# 2. Audits
# ============================================================================


class CreateAuditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    dataset_id: str
    domain: str = "hiring"
    mode: str = "audit"
    provenance_kind: str = "synthetic"
    provenance_label: str = "Synthetic seeded demo"
    sensitive_attributes: list[str]
    outcome_column: str
    positive_value: Any = 1
    score_column: str | None = None
    feature_columns: list[str] = Field(default_factory=list)
    identifier_columns: list[str] = Field(default_factory=list)


class AuditSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    title: str
    status: str
    mode: str
    domain: str
    provenance_kind: str
    provenance_label: str


def _audit_summary(a: StoredAudit) -> AuditSummaryResponse:
    return AuditSummaryResponse(
        audit_id=a.audit_id,
        title=a.title,
        status=a.status,
        mode=a.mode,
        domain=a.domain,
        provenance_kind=a.provenance_kind,
        provenance_label=a.provenance_label,
    )


@router.post("/audits", response_model=AuditSummaryResponse, tags=["audits"])
async def create_audit(
    body: CreateAuditRequest,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    audit_writer: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> AuditSummaryResponse:
    _require(user, "audit.create")
    ds = state.get_dataset(body.dataset_id)
    if ds is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dataset not found")

    audit_id = uuid4().hex
    stored = StoredAudit(
        audit_id=audit_id,
        organization_id=user.organization_id,
        title=body.title,
        domain=body.domain,
        mode=body.mode,
        provenance_kind=body.provenance_kind,
        provenance_label=body.provenance_label,
        dataset_id=body.dataset_id,
        status="schema_pending",
        created_by_uid=user.uid,
    )
    stored._confirmed_schema = {
        "sensitive_attributes": body.sensitive_attributes,
        "outcome_column": body.outcome_column,
        "positive_value": body.positive_value,
        "score_column": body.score_column,
        "feature_columns": body.feature_columns,
        "identifier_columns": body.identifier_columns,
    }
    state.put_audit(stored)
    await audit_writer.write(
        "schema_confirmed",
        audit_id=audit_id,
        details={"sensitive_attributes": body.sensitive_attributes},
    )
    return _audit_summary(stored)


@router.get("/audits", response_model=list[AuditSummaryResponse], tags=["audits"])
async def list_audits(
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[AuditSummaryResponse]:
    _require(user, "audit.view")
    return [_audit_summary(a) for a in state.list_audits(user.organization_id)]


class AuditDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: AuditSummaryResponse
    sensitive_attributes: list[str] = Field(default_factory=list)
    outcome_column: str | None = None
    metrics: list[dict[str, Any]] = Field(default_factory=list)
    heatmap_cells: list[dict[str, Any]] = Field(default_factory=list)
    explanations: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    proxies: list[dict[str, Any]] = Field(default_factory=list)
    remediation: dict[str, Any] | None = None
    sign_off: dict[str, Any] | None = None
    has_report: bool = False


def _metric_to_dict(m: Any) -> dict[str, Any]:
    return {
        "metric": m.metric,
        "value": m.value,
        "threshold": m.threshold,
        "threshold_direction": m.threshold_direction,
        "privileged": m.privileged,
        "unprivileged": m.unprivileged,
        "group_values": m.group_values,
        "sample_sizes": m.sample_sizes,
        "reliable": m.reliable,
        "reason": m.reason,
    }


def _explanation_to_dict(e: Any) -> dict[str, Any]:
    return {
        "metric": e.metric,
        "attribute": e.attribute,
        "summary": e.summary,
        "interpretation": e.interpretation,
        "possible_root_causes": e.possible_root_causes,
        "investigation_prompts": e.investigation_prompts,
        "disclaimer": e.disclaimer,
        "grounded": e.grounded,
        "backend": e.backend,
    }


def _audit_detail(a: StoredAudit) -> AuditDetailResponse:
    schema = getattr(a, "_confirmed_schema", {}) or {}
    return AuditDetailResponse(
        summary=_audit_summary(a),
        sensitive_attributes=list(schema.get("sensitive_attributes", [])),
        outcome_column=schema.get("outcome_column"),
        metrics=[_metric_to_dict(m) for m in a.metrics],
        heatmap_cells=(
            []
            if a.heatmap is None
            else [
                {
                    "attribute": c.attribute,
                    "metric": c.metric,
                    "value": c.value,
                    "severity": c.severity,
                    "note": c.note,
                }
                for c in a.heatmap.cells
            ]
        ),
        explanations=[_explanation_to_dict(e) for e in a.explanations],
        conflicts=[
            {
                "metric_a": c.metric_a,
                "metric_b": c.metric_b,
                "description": c.description,
                "recommendation": c.recommendation,
            }
            for c in a.conflicts
        ],
        proxies=[
            {
                "feature": p.feature,
                "sensitive_attribute": p.sensitive_attribute,
                "method": p.method,
                "strength": p.strength,
                "severity": p.severity,
                "note": p.note,
            }
            for p in a.proxies
        ],
        remediation=(
            None
            if a.remediation is None
            else {
                "strategy": "reweighting",
                "spd_before": a.remediation.spd_before,
                "spd_after": a.remediation.spd_after,
                "dir_before": a.remediation.dir_before,
                "dir_after": a.remediation.dir_after,
                "rates_before": a.remediation.rates_before,
                "rates_after": a.remediation.rates_after,
                "accuracy_estimate_delta": a.remediation.accuracy_estimate_delta,
                "group_weight_summary": a.remediation.group_weight_summary,
            }
        ),
        sign_off=a.sign_off,
        has_report=a.report_pdf is not None,
    )


@router.get("/audits/{audit_id}", response_model=AuditDetailResponse, tags=["audits"])
async def get_audit(
    audit_id: str,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AuditDetailResponse:
    _require(user, "audit.view")
    a = state.get_audit(audit_id)
    if a is None or a.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audit not found")
    return _audit_detail(a)


@router.post(
    "/audits/{audit_id}/analyze",
    response_model=AuditDetailResponse,
    tags=["audits"],
)
async def analyze_audit(
    audit_id: str,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    audit_writer: Annotated[AuditWriter, Depends(get_audit_writer)],
    privacy: Annotated[PrivacyFilter, Depends(get_privacy_filter)],
    llm: Annotated[LLMClient, Depends(get_llm)],
    domain: Annotated[HiringDomain, Depends(get_domain)],
) -> AuditDetailResponse:
    _require(user, "audit.create")
    a = state.get_audit(audit_id)
    if a is None or a.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audit not found")
    if a.dataset_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no dataset")
    ds = state.get_dataset(a.dataset_id)
    if ds is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dataset gone")

    schema = getattr(a, "_confirmed_schema", None)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="audit has no confirmed schema",
        )

    df = ds.parsed.df
    sensitive = [c for c in schema["sensitive_attributes"] if c in df.columns]
    outcome_col = schema["outcome_column"]
    if outcome_col not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"outcome column {outcome_col!r} not in dataset",
        )

    heatmap = assemble_heatmap(
        df,
        sensitive_attributes=sensitive,
        outcome_column=outcome_col,
        positive_value=schema.get("positive_value", 1),
        score_column=schema.get("score_column"),
        feature_columns=schema.get("feature_columns") or [],
        thresholds=Thresholds(),
    )

    conflicts = detect_conflicts(heatmap.detailed)
    proxies = detect_proxies(
        df,
        sensitive_columns=sensitive,
        feature_columns=schema.get("feature_columns") or [],
    )

    explanations: list[Any] = []

    def _payload_factory(
        *,
        prompt_template_id: str,
        purpose: str,
        metric_values: dict[str, Any],
        narrative_context: str,
    ) -> LLMPayload:
        outcome = privacy.build_payload(
            df,
            ds.parsed.columns,
            prompt_template_id=prompt_template_id,
            purpose=purpose,
            domain=domain.name,
            mode="balanced",
            narrative_context=narrative_context,
            metric_values=metric_values,
        )
        return outcome.payload

    for attr in sensitive:
        result = next((r for r in heatmap.detailed if r.metric == "dir"), None)
        if result is None:
            continue
        meta = METRICS["dir"]
        try:
            explanation = await explain_metric(
                llm=llm,
                payload_factory=_payload_factory,
                result=result,
                attribute=attr,
                metric_display=meta["display_name"],
                domain_context=domain.explain_context,
                backend_name="gemini",
                audit_id=audit_id,
            )
        except Exception:
            explanation = template_fallback(
                result, attribute=attr, metric_display=meta["display_name"]
            )
        explanations.append(explanation)

    state.update_audit(
        audit_id,
        status="ready_for_review",
        metrics=heatmap.detailed,
        heatmap=heatmap,
        explanations=explanations,
        conflicts=conflicts,
        proxies=proxies,
    )
    await audit_writer.write(
        "analysis_completed",
        audit_id=audit_id,
        details={
            "metric_count": len(heatmap.detailed),
            "conflict_count": len(conflicts),
            "proxy_count": len(proxies),
        },
    )

    refreshed = state.get_audit(audit_id)
    assert refreshed is not None
    return _audit_detail(refreshed)


class RemediateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_attribute: str
    justification: str = Field(min_length=10)


@router.post(
    "/audits/{audit_id}/remediate",
    response_model=AuditDetailResponse,
    tags=["audits"],
)
async def remediate_audit(
    audit_id: str,
    body: RemediateRequest,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    audit_writer: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> AuditDetailResponse:
    _require(user, "remediation.apply")
    a = state.get_audit(audit_id)
    if a is None or a.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audit not found")
    if a.dataset_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no dataset")
    ds = state.get_dataset(a.dataset_id)
    if ds is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dataset gone")
    schema = getattr(a, "_confirmed_schema", None) or {}
    outcome_col = schema.get("outcome_column")
    if outcome_col is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no outcome col")

    result = apply_reweighting(
        ds.parsed.df,
        sensitive_column=body.target_attribute,
        outcome_column=outcome_col,
        positive_value=schema.get("positive_value", 1),
    )
    state.update_audit(audit_id, remediation=result, status="remediated")
    await audit_writer.write(
        "mitigation_applied",
        audit_id=audit_id,
        details={
            "strategy": "reweighting",
            "target_attribute": body.target_attribute,
            "dir_before": result.dir_before,
            "dir_after": result.dir_after,
            "justification": body.justification,
        },
    )
    refreshed = state.get_audit(audit_id)
    assert refreshed is not None
    return _audit_detail(refreshed)


class SignOffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str = Field(min_length=10)
    confirmed: bool


@router.post(
    "/audits/{audit_id}/sign-off",
    response_model=AuditDetailResponse,
    tags=["audits"],
)
async def sign_off_audit(
    audit_id: str,
    body: SignOffRequest,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    audit_writer: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> AuditDetailResponse:
    _require(user, "audit.signoff")
    if not body.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="must confirm to sign off",
        )
    a = state.get_audit(audit_id)
    if a is None or a.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audit not found")
    sign_off = {
        "reviewer_uid": user.uid,
        "reviewer_name": user.name,
        "reviewer_role": user.role,
        "signed_at": datetime.now(UTC).isoformat(),
        "notes": body.notes,
    }
    state.update_audit(audit_id, sign_off=sign_off, status="signed_off")
    await audit_writer.write(
        "signoff_completed",
        audit_id=audit_id,
        details=sign_off,
    )
    refreshed = state.get_audit(audit_id)
    assert refreshed is not None
    return _audit_detail(refreshed)


# ============================================================================
# 3. Probes
# ============================================================================


class JdScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(min_length=2)
    job_description: str = Field(min_length=20)


class JdScanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str
    inclusivity_score: float
    flagged_phrases: list[dict[str, Any]]
    rewrite_suggestions: list[str]


@router.post(
    "/probes/job-description",
    response_model=JdScanResponse,
    tags=["probes"],
)
async def jd_scan(
    body: JdScanRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> JdScanResponse:
    _require(user, "audit.create")
    result = scan_job_description(body.job_title, body.job_description)
    return JdScanResponse(
        job_title=result.job_title,
        inclusivity_score=result.inclusivity_score,
        flagged_phrases=[
            {"phrase": p.phrase, "category": p.category, "suggestion": p.suggestion}
            for p in result.flagged_phrases
        ],
        rewrite_suggestions=result.rewrite_suggestions,
    )


class PerturbationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    criteria: str
    candidate_profile_template: str
    variations: list[dict[str, Any]] = Field(min_length=2, max_length=10)
    audit_id: str | None = None


class PerturbationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    probe_id: str
    role: str
    variants: list[dict[str, Any]]
    max_score_difference: float
    score_variance: float
    flagged_pattern_summary: list[str]
    interpretation: str
    backend: str


@router.post(
    "/probes/perturbation",
    response_model=PerturbationResponse,
    tags=["probes"],
)
async def perturbation_probe(
    body: PerturbationRequest,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    llm: Annotated[LLMClient, Depends(get_llm)],
    domain: Annotated[HiringDomain, Depends(get_domain)],
    audit_writer: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> PerturbationResponse:
    _require(user, "audit.create")

    def factory(
        *,
        prompt_template_id: str,
        purpose: str,
        narrative_context: str,
    ) -> LLMPayload:
        return StrictPayload(
            domain=domain.name,
            prompt_template_id=prompt_template_id,
            purpose=purpose,
            narrative_context=narrative_context,
        )

    variations = [
        Variation(label=str(v.get("label", "?")), markers=dict(v.get("markers", {})))
        for v in body.variations
    ]
    try:
        result = await run_perturbation_probe(
            llm=llm,
            payload_factory=factory,
            role=body.role,
            criteria=body.criteria,
            candidate_profile_template=body.candidate_profile_template,
            variations=variations,
            backend_name="gemini",
            audit_id=body.audit_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Perturbation probe failed: {exc}",
        ) from exc

    pid = state.put_probe(
        {
            "role": result.role,
            "max_score_difference": result.max_score_difference,
            "score_variance": result.score_variance,
            "interpretation": result.interpretation,
        }
    )
    await audit_writer.write(
        "analysis_completed",
        audit_id=body.audit_id,
        details={
            "probe_id": pid,
            "max_score_difference": result.max_score_difference,
        },
    )
    return PerturbationResponse(
        probe_id=pid,
        role=result.role,
        variants=[
            {
                "label": v.label,
                "markers": v.markers,
                "response_text": v.response_text,
                "score": v.score,
                "flagged_phrases": v.flagged_phrases,
            }
            for v in result.variants
        ],
        max_score_difference=result.max_score_difference,
        score_variance=result.score_variance,
        flagged_pattern_summary=result.flagged_pattern_summary,
        interpretation=result.interpretation,
        backend=result.backend,
    )


# ============================================================================
# 4. Recourse
# ============================================================================


class RecourseSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_cycle_label: str = Field(min_length=2)
    organization_name: str = Field(min_length=2)
    contact_email: str
    sla_business_days: int = 15
    extra_regulatory_references: list[str] = Field(default_factory=list)


class RecourseSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    organization_name: str
    decision_cycle_label: str
    factor_categories: list[str]
    aggregate_statistics: dict[str, str]
    automated_tools_used: list[str]
    how_to_request_review: str
    contact_email: str
    regulatory_references: list[str]


@router.post(
    "/audits/{audit_id}/recourse-summary",
    response_model=RecourseSummaryResponse,
    tags=["recourse"],
)
async def recourse_summary(
    audit_id: str,
    body: RecourseSummaryRequest,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    domain: Annotated[HiringDomain, Depends(get_domain)],
) -> RecourseSummaryResponse:
    _require(user, "audit.view")
    a = state.get_audit(audit_id)
    if a is None or a.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audit not found")
    summary = build_recourse_summary(
        audit_id=audit_id,
        organization_name=body.organization_name,
        decision_cycle_label=body.decision_cycle_label,
        metrics=a.metrics,
        factor_categories=domain.factor_categories,
        automated_tools_used=["NyayaLens fairness audit", "Gemini schema detection"],
        contact_email=body.contact_email,
        sla_business_days=body.sla_business_days,
        remediation=a.remediation,
        extra_regulatory_references=body.extra_regulatory_references,
    )
    state.update_audit(audit_id, recourse=summary)
    return RecourseSummaryResponse(
        audit_id=summary.audit_id,
        organization_name=summary.organization_name,
        decision_cycle_label=summary.decision_cycle_label,
        factor_categories=summary.factor_categories,
        aggregate_statistics=summary.aggregate_statistics,
        automated_tools_used=summary.automated_tools_used,
        how_to_request_review=summary.how_to_request_review,
        contact_email=summary.contact_email,
        regulatory_references=summary.regulatory_references,
    )


class RecourseRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    applicant_identifier: str
    contact_email: str
    request_type: str = "human_review"
    body: str = Field(min_length=10, max_length=2000)


class RecourseRequestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: str = "pending"


@router.post(
    "/recourse-requests",
    response_model=RecourseRequestResponse,
    tags=["recourse"],
)
async def file_recourse(
    body: RecourseRequestBody,
    audit_writer: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> RecourseRequestResponse:
    request_id = uuid4().hex
    await audit_writer.write(
        "recourse_filed",
        audit_id=body.audit_id,
        details={
            "request_id": request_id,
            "applicant_identifier": body.applicant_identifier,
            "contact_email": body.contact_email,
            "request_type": body.request_type,
            "body": body.body,
        },
    )
    return RecourseRequestResponse(request_id=request_id)


# ============================================================================
# 5. Reports
# ============================================================================


@router.post("/audits/{audit_id}/report/generate", tags=["reports"])
async def generate_report(
    audit_id: str,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    storage: Annotated[StorageClient, Depends(get_storage)],
    audit_writer: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> dict[str, Any]:
    _require(user, "report.generate")
    a = state.get_audit(audit_id)
    if a is None or a.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audit not found")

    schema = getattr(a, "_confirmed_schema", {}) or {}
    data = build_audit_report(
        organization_name=a.organization_id,
        audit_id=audit_id,
        audit_title=a.title,
        domain=a.domain,
        mode=a.mode,
        provenance_label=a.provenance_label,
        provenance_kind=a.provenance_kind,
        schema_summary={
            "sensitive_attributes": schema.get("sensitive_attributes", []),
            "outcome_column": schema.get("outcome_column"),
            "feature_columns": schema.get("feature_columns", []),
            "identifier_columns": schema.get("identifier_columns", []),
        },
        metrics=a.metrics,
        explanations=a.explanations,
        conflicts=a.conflicts,
        proxy_flags=a.proxies,
        remediation=a.remediation,
        perturbation_probe=None,
        jd_scan=None,
        recourse=a.recourse,
        sign_off=a.sign_off,
    )
    pdf_bytes = render_audit_report(data)
    state.update_audit(audit_id, report_pdf=pdf_bytes)
    path = f"reports/{a.organization_id}/{audit_id}/audit_report.pdf"
    await storage.upload(path, pdf_bytes, content_type="application/pdf")
    url = await storage.signed_url(path)
    await audit_writer.write(
        "report_generated",
        audit_id=audit_id,
        details={"path": path, "size_bytes": len(pdf_bytes)},
    )
    return {"audit_id": audit_id, "size_bytes": len(pdf_bytes), "download_url": url}


@router.get("/audits/{audit_id}/report", tags=["reports"])
async def fetch_report(
    audit_id: str,
    state: Annotated[AppState, Depends(get_app_state)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Response:
    _require(user, "report.view")
    a = state.get_audit(audit_id)
    if a is None or a.organization_id != user.organization_id or a.report_pdf is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")
    return Response(
        content=a.report_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="audit-{audit_id}.pdf"',
        },
    )


# ============================================================================
# 6. Audit trail
# ============================================================================


@router.get("/audit-trail", tags=["governance"])
async def list_audit_trail(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    sink_writer: Annotated[AuditWriter, Depends(get_audit_writer)],
) -> list[dict[str, Any]]:
    """Return the in-memory audit trail. Replaced by Firestore in production."""
    _require(user, "audit.view")
    inner = getattr(sink_writer, "_sink", None)
    events = getattr(inner, "events", []) or []
    return [
        {
            "event_id": str(e.event_id),
            "audit_id": e.audit_id,
            "organization_id": e.organization_id,
            "action": e.action,
            "user_id": e.user_id,
            "user_name": e.user_name,
            "user_role": e.user_role,
            "timestamp": e.timestamp.isoformat(),
            "details": e.details,
        }
        for e in events
        if e.organization_id == user.organization_id
    ]


__all__ = ["router"]
