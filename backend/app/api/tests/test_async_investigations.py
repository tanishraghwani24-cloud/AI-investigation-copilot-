"""Round 6 tests for trigger acknowledgement, polling, and failures."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import investigations as investigation_routes
from app.db.session import get_db_session
from app.main import app
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ContextIntelligence,
    CurrentStage,
    create_initial_state,
)


async def _mock_db_session():
    yield MagicMock()


def _state(case_id: str, status: AgentStatus = AgentStatus.NOT_STARTED):
    state = create_initial_state(case_id, CaseInput())
    if status is not AgentStatus.NOT_STARTED:
        state.context_intelligence = ContextIntelligence(status=status)
        state.current_stage = CurrentStage.CONTEXT
    return state


@pytest.fixture
def api_client():
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = _mock_db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)


def test_trigger_acknowledges_scheduled_background_run(api_client: TestClient) -> None:
    started = _state("CASE-ASYNC-001", AgentStatus.IN_PROGRESS)
    with patch.object(
        investigation_routes._investigation_service,
        "start_investigation",
        new=AsyncMock(return_value=(started, True)),
    ), patch.object(
        investigation_routes,
        "_run_investigation_background",
        new=AsyncMock(),
    ) as background:
        response = api_client.post("/api/investigations/CASE-ASYNC-001/run")

    assert response.status_code == 202
    assert response.json()["status"] == "IN_PROGRESS"
    assert response.json()["current_stage"] == "CONTEXT"
    background.assert_awaited_once_with("CASE-ASYNC-001")


def test_polling_exposes_running_then_terminal_state(api_client: TestClient) -> None:
    running = _state("CASE-POLL-001", AgentStatus.IN_PROGRESS)
    completed = _state("CASE-POLL-001")
    completed.current_stage = CurrentStage.DONE

    with patch.object(
        investigation_routes._investigation_service,
        "get_investigation",
        new=AsyncMock(side_effect=[running, completed]),
    ):
        first = api_client.get("/api/investigations/CASE-POLL-001")
        second = api_client.get("/api/investigations/CASE-POLL-001")

    assert first.status_code == 200
    assert first.json()["current_stage"] == "CONTEXT"
    assert first.json()["context_intelligence"]["status"] == "IN_PROGRESS"
    assert second.status_code == 200
    assert second.json()["current_stage"] == "DONE"


@pytest.mark.asyncio
async def test_background_helper_runs_existing_service_pipeline() -> None:
    session = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)
    completed = _state("CASE-BACKGROUND-001")
    completed.current_stage = CurrentStage.DONE

    with patch.object(
        investigation_routes,
        "async_session_factory",
        return_value=session_context,
    ), patch.object(
        investigation_routes._investigation_service,
        "run_investigation",
        new=AsyncMock(return_value=completed),
    ) as run:
        await investigation_routes._run_investigation_background("CASE-BACKGROUND-001")

    run.assert_awaited_once_with("CASE-BACKGROUND-001", session)
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_background_failure_is_captured_without_escaping() -> None:
    session = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=None)

    with patch.object(
        investigation_routes,
        "async_session_factory",
        return_value=session_context,
    ), patch.object(
        investigation_routes._investigation_service,
        "run_investigation",
        new=AsyncMock(side_effect=RuntimeError("controlled background failure")),
    ), patch.object(
        investigation_routes._investigation_service,
        "record_background_failure",
        new=AsyncMock(),
    ) as record_failure:
        await investigation_routes._run_investigation_background("CASE-FAIL-001")

    session.rollback.assert_awaited_once()
    record_failure.assert_awaited_once()
