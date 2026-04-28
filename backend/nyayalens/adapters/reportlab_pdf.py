"""ReportLab-based PDF renderer for `AuditReportData`.

Lives in `adapters/` because ReportLab is forbidden in `core/` by ADR 0001
and the import-graph contract test. The function takes pure data and
returns bytes — no filesystem.

Imported by:
- `api/audits.py:report/generate` POST endpoint (forthcoming)
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from nyayalens.core.report.composer import AuditReportData, AuditSection


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            name="NyayaTitle",
            parent=base["Title"],
            fontSize=20,
            leading=24,
            spaceAfter=14,
            textColor=colors.HexColor("#1E2A44"),
        ),
        "subtitle": ParagraphStyle(
            name="NyayaSubtitle",
            parent=base["Heading2"],
            fontSize=14,
            leading=18,
            spaceAfter=8,
            textColor=colors.HexColor("#1E2A44"),
        ),
        "heading": ParagraphStyle(
            name="NyayaHeading",
            parent=base["Heading3"],
            fontSize=12,
            leading=15,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#1E2A44"),
        ),
        "body": ParagraphStyle(
            name="NyayaBody",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
        ),
        "caption": ParagraphStyle(
            name="NyayaCaption",
            parent=base["Italic"],
            fontSize=9,
            leading=11,
            textColor=colors.grey,
        ),
    }


def _section_to_flowables(section: AuditSection, styles: dict[str, ParagraphStyle]) -> list[Any]:
    flow: list[Any] = [Paragraph(section.heading, styles["heading"])]
    for para in section.body:
        flow.append(Paragraph(para.replace("\n", "<br/>"), styles["body"]))
    if section.table:
        tbl = Table(section.table, hAlign="LEFT")
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E2A44")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        flow.append(Spacer(1, 6))
        flow.append(tbl)
    flow.append(Spacer(1, 6))
    return flow


def render_audit_report(data: AuditReportData) -> bytes:
    """Render the full PDF for one audit. Returns the file bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"NyayaLens Audit — {data.audit_title}",
        author="NyayaLens",
    )
    styles = _styles()
    story: list[Any] = []

    # Cover
    story.append(Paragraph("NyayaLens — Audit Report", styles["title"]))
    story.append(Paragraph(f"Organization: {data.organization_name}", styles["subtitle"]))
    story.append(Paragraph(f"Audit: {data.audit_title}", styles["subtitle"]))
    story.append(
        Paragraph(
            f"Domain: {data.domain} &nbsp;·&nbsp; "
            f"Mode: {data.mode} &nbsp;·&nbsp; "
            f"Provenance: {data.provenance_kind} ({data.provenance_label})",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            f"Generated: {data.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            styles["caption"],
        )
    )
    story.append(Spacer(1, 24))

    story.append(Paragraph("Part A — Audit Findings", styles["title"]))
    for section in data.part_a_audit:
        story.extend(_section_to_flowables(section, styles))

    if data.part_b_probe:
        story.append(PageBreak())
        story.append(Paragraph("Part B - Probe Findings", styles["title"]))
        for section in data.part_b_probe:
            story.extend(_section_to_flowables(section, styles))

    story.append(PageBreak())

    story.append(Paragraph("Part C — Governance Record", styles["title"]))
    for section in data.part_c_governance:
        story.extend(_section_to_flowables(section, styles))

    story.append(PageBreak())

    story.append(Paragraph("Appendix — Methodology", styles["title"]))
    for section in data.methodology_appendix:
        story.extend(_section_to_flowables(section, styles))

    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "This report is interpretive guidance to support human decision-"
            "making. It is not legal, ethical, or compliance advice.",
            styles["caption"],
        )
    )

    doc.build(story)
    return buf.getvalue()


__all__ = ["render_audit_report"]
