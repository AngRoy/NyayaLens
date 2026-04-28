"""HTTP DTOs for the public-ish REST API consumed by the Flutter client.

The package mixes two surfaces:

- ``wire.*`` — the DTOs the FastAPI route layer actually returns today
  (matched 1:1 to what the Flutter client parses).
- The other modules (``audit``, ``bias``, ``probe``, ``recourse``,
  ``remediate``, ``report``, ``dataset``, ``govern``, ``evidence``) — the
  design-doc-aligned future shapes the API will graduate to as endpoints
  are reshaped.

Both are exported so the ``contract-test`` workflow exposes everything to
the Flutter golden-fixture parser.
"""

from nyayalens.models.api.audit import (
    AuditCreateRequest,
    AuditDetailResponse,
    AuditSummary,
    Mode,
    SignOffRequest,
    SignOffView,
)
from nyayalens.models.api.bias import (
    BiasGridCell,
    BiasGridResponse,
    ConflictView,
    ExplanationView,
    MetricResultView,
    ProxyFlagView,
)
from nyayalens.models.api.dataset import (
    DatasetPreview,
    DatasetUploadResponse,
    SchemaConfirmRequest,
    SchemaDetectionResponse,
    SchemaView,
    SensitiveAttrView,
)
from nyayalens.models.api.evidence import DataProvenance
from nyayalens.models.api.govern import AuditTrailEntryView
from nyayalens.models.api.probe import (
    JdScanRequest,
    JdScanResponse,
    PerturbationProbeRequest,
    PerturbationProbeResponse,
    ProbeVariantResult,
)
from nyayalens.models.api.recourse import (
    RecourseRequestCreate,
    RecourseRequestView,
    RecourseSummaryView,
)
from nyayalens.models.api.remediate import (
    RemediationApplyRequest,
    RemediationApproveRequest,
    RemediationResult,
)
from nyayalens.models.api.report import ReportStatusResponse
from nyayalens.models.api.wire import (
    AuditDetailWireResponse,
    AuditSummaryWireResponse,
    CreateAuditWireRequest,
    DatasetUploadWireResponse,
    DetectSchemaWireResponse,
    JdScanWireRequest,
    JdScanWireResponse,
    PerturbationWireRequest,
    PerturbationWireResponse,
    RecourseAssignWireRequest,
    RecourseRequestListWireResponse,
    RecourseRequestRecordWire,
    RecourseRequestWireBody,
    RecourseRequestWireResponse,
    RecourseResolveWireRequest,
    RecourseSummaryWireRequest,
    RecourseSummaryWireResponse,
    RemediateWireRequest,
    SignOffWireRequest,
)

__all__ = [
    "AuditCreateRequest",
    "AuditDetailResponse",
    "AuditDetailWireResponse",
    "AuditSummary",
    "AuditSummaryWireResponse",
    "AuditTrailEntryView",
    "BiasGridCell",
    "BiasGridResponse",
    "ConflictView",
    "CreateAuditWireRequest",
    "DataProvenance",
    "DatasetPreview",
    "DatasetUploadResponse",
    "DatasetUploadWireResponse",
    "DetectSchemaWireResponse",
    "ExplanationView",
    "JdScanRequest",
    "JdScanResponse",
    "JdScanWireRequest",
    "JdScanWireResponse",
    "MetricResultView",
    "Mode",
    "PerturbationProbeRequest",
    "PerturbationProbeResponse",
    "PerturbationWireRequest",
    "PerturbationWireResponse",
    "ProbeVariantResult",
    "ProxyFlagView",
    "RecourseAssignWireRequest",
    "RecourseRequestCreate",
    "RecourseRequestListWireResponse",
    "RecourseRequestRecordWire",
    "RecourseRequestView",
    "RecourseRequestWireBody",
    "RecourseRequestWireResponse",
    "RecourseResolveWireRequest",
    "RecourseSummaryView",
    "RecourseSummaryWireRequest",
    "RecourseSummaryWireResponse",
    "RemediateWireRequest",
    "RemediationApplyRequest",
    "RemediationApproveRequest",
    "RemediationResult",
    "ReportStatusResponse",
    "SchemaConfirmRequest",
    "SchemaDetectionResponse",
    "SchemaView",
    "SensitiveAttrView",
    "SignOffRequest",
    "SignOffView",
    "SignOffWireRequest",
]
