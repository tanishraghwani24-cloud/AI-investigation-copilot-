from app.schemas.investigation_state import AgentStatus, InvestigationReport
from app.services.report_pdf_service import render_investigation_report_pdf


def test_renders_the_persisted_report_text_as_a_pdf() -> None:
    report = InvestigationReport(
        status=AgentStatus.COMPLETED,
        executive_summary="Escalate the case.",
        detailed_narrative="Evidence supports an immediate hold.",
    )

    pdf = render_investigation_report_pdf("CASE-PDF-001", report)

    assert pdf.startswith(b"%PDF-1.4")
    assert b"CASE-PDF-001" in pdf
    assert b"Escalate the case." in pdf
    assert b"Evidence supports an immediate hold." in pdf
