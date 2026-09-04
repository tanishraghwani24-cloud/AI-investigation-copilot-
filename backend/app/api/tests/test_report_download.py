from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    CurrentStage,
    InvestigationReport,
    InvestigationState,
)


async def _mock_db_session():
    yield MagicMock()


@pytest.fixture
def api_client():
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = _mock_db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


def _state(stage: CurrentStage = CurrentStage.DONE) -> InvestigationState:
    return InvestigationState(
        case_id="CASE-PDF-001",
        case_input=CaseInput(transactions=[]),
        current_stage=stage,
        investigation_report=InvestigationReport(
            status=AgentStatus.COMPLETED,
            executive_summary="Escalate the case.",
            detailed_narrative="Evidence supports an immediate hold.",
            generated_at=datetime.now(timezone.utc),
        ),
    )


def test_downloads_completed_persisted_report_as_pdf(api_client: TestClient) -> None:
    with patch(
        "app.api.routes.investigations._investigation_service.get_investigation",
        new_callable=AsyncMock,
        return_value=_state(),
    ):
        response = api_client.get("/api/investigations/CASE-PDF-001/report/download.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "CASE-PDF-001-report.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-1.4")
    assert b"Evidence supports an immediate hold." in response.content


def test_pdf_is_unavailable_before_investigation_completion(api_client: TestClient) -> None:
    with patch(
        "app.api.routes.investigations._investigation_service.get_investigation",
        new_callable=AsyncMock,
        return_value=_state(CurrentStage.REPORTING),
    ):
        response = api_client.get("/api/investigations/CASE-PDF-001/report/download.pdf")

    assert response.status_code == 404
