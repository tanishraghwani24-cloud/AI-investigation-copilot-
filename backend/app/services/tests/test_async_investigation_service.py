"""Focused tests for the persisted async-run marker."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ContextIntelligence,
    CurrentStage,
    InvestigationState,
    create_initial_state,
)
from app.services.investigation_service import InvestigationService


@pytest.mark.asyncio
async def test_start_investigation_persists_in_progress_marker() -> None:
    state = create_initial_state("CASE-MARKER-001", CaseInput())
    record = MagicMock(state_json=state.model_dump(mode="json"))
    repository = MagicMock()
    repository.get_by_case_id = AsyncMock(return_value=record)
    repository.update_state = AsyncMock()
    session = AsyncMock()
    service = InvestigationService(investigation_repo=repository)

    started = await service.start_investigation("CASE-MARKER-001", session)

    assert started is not None
    marked_state, scheduled = started
    assert scheduled is True
    assert marked_state.current_stage == CurrentStage.CONTEXT
    assert marked_state.context_intelligence is not None
    assert marked_state.context_intelligence.status == AgentStatus.IN_PROGRESS
    repository.update_state.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_second_start_does_not_schedule_competing_run() -> None:
    state = create_initial_state("CASE-MARKER-002", CaseInput())
    state.current_stage = CurrentStage.CONTEXT
    state.context_intelligence = ContextIntelligence(status=AgentStatus.IN_PROGRESS)
    record = MagicMock(state_json=state.model_dump(mode="json"))
    repository = MagicMock()
    repository.get_by_case_id = AsyncMock(return_value=record)
    repository.update_state = AsyncMock()
    session = AsyncMock()
    service = InvestigationService(investigation_repo=repository)

    started = await service.start_investigation("CASE-MARKER-002", session)

    assert started is not None
    returned_state, scheduled = started
    assert returned_state.case_id == "CASE-MARKER-002"
    assert scheduled is False
    repository.update_state.assert_not_awaited()
    session.commit.assert_not_awaited()
