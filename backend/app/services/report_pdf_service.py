"""Small dependency-free PDF renderer for persisted investigation reports."""

from __future__ import annotations

from textwrap import wrap

from app.schemas.investigation_state import InvestigationReport


def _pdf_text(value: str) -> bytes:
    """Encode a PDF string without treating report text as PDF syntax."""
    return (
        value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        .encode("latin-1", "replace")
    )


def _report_lines(case_id: str, report: InvestigationReport) -> list[str]:
    lines = ["Investigation Report", f"Case ID: {case_id}", ""]
    if report.executive_summary:
        lines.extend(["Executive Summary", *wrap(report.executive_summary, width=88), ""])
    if report.detailed_narrative:
        lines.append("Detailed Narrative")
        for paragraph in report.detailed_narrative.splitlines() or [report.detailed_narrative]:
            lines.extend(wrap(paragraph, width=88) or [""])
    return lines


def render_investigation_report_pdf(case_id: str, report: InvestigationReport) -> bytes:
    """Render the reporting agent's real text into a downloadable PDF."""
    lines = _report_lines(case_id, report)
    page_lines = [lines[index : index + 48] for index in range(0, len(lines), 48)] or [[""]]
    font_id = 3 + 2 * len(page_lines)
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [" + b" ".join(
            f"{3 + index * 2} 0 R".encode() for index in range(len(page_lines))
        ) + f"] /Count {len(page_lines)} >>".encode(),
    ]

    for page_index, lines_on_page in enumerate(page_lines):
        page_id = 3 + page_index * 2
        content_id = page_id + 1
        content = b"BT /F1 10 Tf 50 760 Td 14 TL\n" + b"\n".join(
            b"(" + _pdf_text(line) + b") Tj T*" for line in lines_on_page
        ) + b"\nET"
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode()
        )
        objects.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id, value in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{object_id} 0 obj\n".encode())
        document.extend(value)
        document.extend(b"\nendobj\n")
    xref_offset = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    document.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    document.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode())
    return bytes(document)
