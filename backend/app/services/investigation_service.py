"""Investigation service layer.

Orchestrates investigation creation, graph execution, and retrieval
through the repository and graph layers. API routes delegate to this
service rather than coordinating repository + graph directly.

Round 3: Tanish — service layer completion.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import InvestigationRepository
from app.graph.workflow import run_investigation_with_persistence
from app.schemas.investigation_state import (
    CaseInput,
    CurrentStage,
    InvestigationState,
    create_initial_state,
)

logger = logging.getLogger(__name__)


class InvestigationService:
    """Service layer between API routes and repository/graph.

    Responsibilities:
      - Create initial investigation state from case input.
      - Invoke the graph pipeline with per-node persistence.
      - Retrieve persisted investigations via the repository.

    Does NOT contain agent logic or graph wiring.
    """

    def __init__(
        self,
        investigation_repo: InvestigationRepository | None = None,
    ) -> None:
        self._repo = investigation_repo or InvestigationRepository()

    async def create_investigation(
        self,
        case_id: str,
        case_input: CaseInput,
        session: AsyncSession,
    ) -> InvestigationState:
        """Create and persist an initial investigation without running it.

        Creation is idempotent for a case ID so the existing deterministic
        Mock Bank create endpoint remains compatible with repeated requests.
        """
        existing = await self.get_investigation(case_id, session)
        if existing is not None:
            return existing

        state = create_initial_state(case_id=case_id, case_input=case_input)
        await self._repo.create(session, case_id, state.model_dump(mode="json"))
        return state

    async def create_and_run_investigation(
        self,
        case_id: str,
        case_input: CaseInput,
        session: AsyncSession,
    ) -> InvestigationState:
        """Create a new investigation and run the full pipeline.

        1. Build initial InvestigationState.
        2. Invoke the graph with per-node persistence.
        3. Return the resulting state.

        Args:
            case_id: Unique investigation case identifier.
            case_input: Raw case input data.
            session: Active async database session.

        Returns:
            The InvestigationState after the pipeline has completed
            (successfully or with a recorded failure).
        """
        state = create_initial_state(case_id=case_id, case_input=case_input)

        logger.info("Starting investigation pipeline for case %s", case_id)

        result_state = await run_investigation_with_persistence(state, session)

        logger.info(
            "Investigation pipeline completed for case %s — stage: %s",
            case_id,
            result_state.current_stage.value,
        )

        return result_state

    async def get_investigation(
        self,
        case_id: str,
        session: AsyncSession,
    ) -> InvestigationState | None:
        """Retrieve a persisted investigation by case_id.

        Args:
            case_id: The investigation case identifier.
            session: Active async database session.

        Returns:
            The reconstructed InvestigationState, or None if not found.
        """
        record = await self._repo.get_by_case_id(session, case_id)
        if record is None:
            return None

        return InvestigationState.model_validate(record.state_json)

    async def list_investigations(
        self,
        session: AsyncSession,
        *,
        status: CurrentStage | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[InvestigationState]:
        """Return persisted investigations, optionally filtered by stage."""
        records = await self._repo.list_all(
            session,
            status=status.value if status is not None else None,
            offset=offset,
            limit=limit,
        )
        return [
            InvestigationState.model_validate(record.state_json)
            for record in records
            if record.state_json is not None
        ]

    async def run_investigation(
        self,
        case_id: str,
        session: AsyncSession,
    ) -> InvestigationState | None:
        """Run the graph for an already persisted investigation."""
        state = await self.get_investigation(case_id, session)
        if state is None:
            return None

        logger.info("Starting investigation pipeline for existing case %s", case_id)
        return await run_investigation_with_persistence(state, session)
