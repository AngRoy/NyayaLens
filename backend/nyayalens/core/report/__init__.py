"""Audit-report composer.

`core/report/composer.py` produces an `AuditReportData` dataclass — the
domain-pure description of what should appear in the PDF. The actual
ReportLab rendering lives in `adapters/reportlab_pdf.py` so the import
graph stays clean (see ADR 0001).
"""

from nyayalens.core.report.composer import (
    AuditReportData,
    AuditSection,
    build_audit_report,
)

__all__ = ["AuditReportData", "AuditSection", "build_audit_report"]
