"""In-process state store for the MVP.

Holds parsed datasets, schema-detection results, and audit records keyed by
their IDs. Replaced by the Firestore-backed store at production time —
the API surface is identical (CRUD-style methods).

Imported by:
- `api/deps.py` (forthcoming)
- All route files via the `current_state` dependency
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Literal
from uuid import uuid4

from nyayalens.core.bias.heatmap import HeatmapResult
from nyayalens.core.bias.metrics import MetricResult
from nyayalens.core.explain.validator import Explanation
from nyayalens.core.mitigate.reweighting import ReweightingResult
from nyayalens.core.recourse.summary import RecourseSummary
from nyayalens.core.schema.detector import SchemaDetectionResult
from nyayalens.core.schema.parser import ParsedDataset

RecourseStatus = Literal[
    "pending",
    "in_review",
    "resolved_upheld",
    "resolved_overturned",
    "resolved_referred",
]
RecourseRequestType = Literal["human_review", "explanation", "appeal"]


@dataclass
class StoredAudit:
    audit_id: str
    organization_id: str
    title: str
    domain: str
    mode: str
    provenance_kind: str
    provenance_label: str
    status: str = "draft"
    dataset_id: str | None = None
    _confirmed_schema: dict[str, Any] = field(default_factory=dict)
    schema: SchemaDetectionResult | None = None
    heatmap: HeatmapResult | None = None
    metrics: list[MetricResult] = field(default_factory=list)
    explanations: list[Explanation] = field(default_factory=list)
    proxies: list[Any] = field(default_factory=list)
    conflicts: list[Any] = field(default_factory=list)
    remediation: ReweightingResult | None = None
    sign_off: dict[str, Any] | None = None
    tradeoff: dict[str, Any] | None = None
    recourse: RecourseSummary | None = None
    report_pdf: bytes | None = None
    created_by_uid: str = "demo-user"


@dataclass
class StoredDataset:
    dataset_id: str
    filename: str
    parsed: ParsedDataset


@dataclass
class StoredRecourseRequest:
    request_id: str
    audit_id: str
    organization_id: str
    applicant_identifier: str
    contact_email: str
    request_type: RecourseRequestType
    body: str
    status: RecourseStatus = "pending"
    assigned_to_uid: str | None = None
    assigned_to_name: str | None = None
    reviewer_notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None


class AppState:
    """Thread-safe in-memory state. One instance per app boot."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, StoredDataset] = {}
        self._audits: dict[str, StoredAudit] = {}
        self._probes: dict[str, dict[str, Any]] = {}
        self._recourse_requests: dict[str, StoredRecourseRequest] = {}

    # -- datasets --

    def put_dataset(self, parsed: ParsedDataset, *, filename: str) -> str:
        with self._lock:
            ds_id = uuid4().hex
            self._datasets[ds_id] = StoredDataset(
                dataset_id=ds_id, filename=filename, parsed=parsed
            )
            return ds_id

    def get_dataset(self, dataset_id: str) -> StoredDataset | None:
        with self._lock:
            return self._datasets.get(dataset_id)

    # -- audits --

    def put_audit(self, audit: StoredAudit) -> str:
        with self._lock:
            self._audits[audit.audit_id] = audit
            return audit.audit_id

    def get_audit(self, audit_id: str) -> StoredAudit | None:
        with self._lock:
            return self._audits.get(audit_id)

    def update_audit(self, audit_id: str, **changes: Any) -> StoredAudit | None:
        allowed = {f.name for f in fields(StoredAudit)}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(
                f"unknown StoredAudit field(s): {sorted(unknown)}; allowed: {sorted(allowed)}"
            )
        with self._lock:
            audit = self._audits.get(audit_id)
            if audit is None:
                return None
            for k, v in changes.items():
                setattr(audit, k, v)
            return audit

    def list_audits(self, organization_id: str) -> list[StoredAudit]:
        with self._lock:
            return [a for a in self._audits.values() if a.organization_id == organization_id]

    # -- probes --

    def put_probe(self, payload: dict[str, Any]) -> str:
        with self._lock:
            pid = uuid4().hex
            self._probes[pid] = {**payload, "probe_id": pid}
            return pid

    def get_probe(self, probe_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._probes.get(probe_id)

    # -- recourse requests --

    def put_recourse_request(self, request: StoredRecourseRequest) -> str:
        with self._lock:
            self._recourse_requests[request.request_id] = request
            return request.request_id

    def get_recourse_request(self, request_id: str) -> StoredRecourseRequest | None:
        with self._lock:
            return self._recourse_requests.get(request_id)

    def list_recourse_requests(self, organization_id: str) -> list[StoredRecourseRequest]:
        with self._lock:
            return [
                r for r in self._recourse_requests.values() if r.organization_id == organization_id
            ]

    def update_recourse_request(
        self, request_id: str, **changes: Any
    ) -> StoredRecourseRequest | None:
        allowed = {f.name for f in fields(StoredRecourseRequest)}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(
                f"unknown StoredRecourseRequest field(s): {sorted(unknown)}; "
                f"allowed: {sorted(allowed)}"
            )
        with self._lock:
            request = self._recourse_requests.get(request_id)
            if request is None:
                return None
            for k, v in changes.items():
                setattr(request, k, v)
            return request


__all__ = [
    "AppState",
    "RecourseRequestType",
    "RecourseStatus",
    "StoredAudit",
    "StoredDataset",
    "StoredRecourseRequest",
]
