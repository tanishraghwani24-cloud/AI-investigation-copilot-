"""Investigation API routes.

Provides the persisted investigation REST API.
"""

from datetime import datetime, timezone
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory, get_db_session
from app.mock_bank.generator import MockBankScenario, generate_investigation_data
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    CustomerProfile,
    InvestigationState,
    Transaction,
    CurrentStage,
    create_initial_state,
)
from app.services.investigation_service import InvestigationService

router = APIRouter()
logger = logging.getLogger(__name__)

CaseIdPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
        description="Investigation case identifier.",
    ),
]


class InvestigationRunResponse(BaseModel):
    """Immediate acknowledgement returned when a run is scheduled."""

    case_id: str
    status: AgentStatus
    current_stage: CurrentStage
    message: str

# ── Default seed for deterministic generation ────────────────────────
_DEFAULT_SEED: int = 42

# ── Service instance ─────────────────────────────────────────────────
_investigation_service = InvestigationService()


def _build_investigation_state(
    seed: int,
    scenario: MockBankScenario | str = MockBankScenario.DEFAULT,
) -> InvestigationState:
    """Build an InvestigationState from generated Mock Bank data.

    Maps mock_bank models into the schema-layer types used by the
    investigation pipeline.

    Args:
        seed: Integer seed for deterministic generation.

    Returns:
        A fully initialised InvestigationState ready for pipeline
        execution.
    """
    data = generate_investigation_data(seed, scenario=scenario)
    customer = data.customer
    account = data.account

    # Map mock_bank.Customer → schemas.CustomerProfile
    customer_profile = CustomerProfile(
        customer_id=customer.customer_id,
        name=f"{customer.first_name} {customer.last_name}",
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        date_of_birth=customer.date_of_birth,
        account_open_date=(
            customer.created_at.strftime("%Y-%m-%d")
            if customer.created_at
            else None
        ),
        risk_rating=customer.risk_rating,
        occupation=customer.occupation,
        nationality=customer.nationality,
    )

    # Map mock_bank.Transaction list → schemas.Transaction list
    schema_transactions: list[Transaction] = []
    for txn in data.transactions:
        schema_transactions.append(
            Transaction(
                transaction_id=txn.transaction_id,
                amount=txn.amount,
                currency=txn.currency,
                timestamp=(
                    txn.timestamp
                    if txn.timestamp
                    else datetime.now(timezone.utc)
                ),
                sender_account=txn.sender_account_id,
                receiver_account=txn.receiver_account_id,
                transaction_type=txn.transaction_type,
                channel=txn.channel,
                description=txn.description,
                location=txn.location,
            )
        )

    case_input = CaseInput(
        transactions=schema_transactions,
        customer_profile=customer_profile,
        alert_reason=data.alert_reason,
    )

    # Use deterministic case ID from seed
    selected_scenario = MockBankScenario(scenario)
    case_id = f"CASE-2025-{seed:05d}"
    if selected_scenario is not MockBankScenario.DEFAULT:
        case_id = f"{case_id}-{selected_scenario.value.upper()}"

    return create_initial_state(case_id=case_id, case_input=case_input)


@router.post("/investigations", response_model=InvestigationState)
async def create_investigation(
    scenario: MockBankScenario = Query(default=MockBankScenario.DEFAULT),
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationState:
    """Create a new investigation case.

    Persists a deterministic Mock Bank case input (seed=42). Agent outputs
    are populated only when the investigation is subsequently run.
    """
    state = _build_investigation_state(_DEFAULT_SEED, scenario=scenario)
    return await _investigation_service.create_investigation(
        state.case_id,
        state.case_input,
        db,
    )


@router.get("/investigations", response_model=list[InvestigationState])
async def list_investigations(
    status: CurrentStage | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> list[InvestigationState]:
    """List persisted investigations with optional stage filtering."""
    return await _investigation_service.list_investigations(
        db,
        status=status,
        offset=offset,
        limit=limit,
    )


@router.get("/investigations/{case_id}", response_model=InvestigationState)
async def get_investigation(
    case_id: CaseIdPath,
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationState:
    """Retrieve the current persisted investigation state.

    Polls the persistence layer for the investigation identified by
    ``case_id`` and returns the full InvestigationState.

    Delegates to the InvestigationService for retrieval.

    Args:
        case_id: The investigation case identifier.
        db: Async database session (injected).

    Returns:
        The persisted InvestigationState.

    Raises:
        HTTPException 404: If no investigation exists with the given case_id.
    """
    state = await _investigation_service.get_investigation(case_id, db)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation not found: {case_id}",
        )

    return state


async def _run_investigation_background(case_id: str) -> None:
    """Execute a scheduled investigation using an independent DB session."""
    try:
        async with async_session_factory() as session:
            try:
                state = await _investigation_service.run_investigation(case_id, session)
                if state is None:
                    logger.error("Scheduled investigation disappeared: %s", case_id)
                await session.commit()
            except Exception as exc:
                await session.rollback()
                try:
                    await _investigation_service.record_background_failure(
                        case_id,
                        exc,
                        session,
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()
                    logger.exception(
                        "Could not persist background failure for investigation %s",
                        case_id,
                    )
                logger.exception("Background investigation failed: %s", case_id)
    except Exception:
        logger.exception("Could not open a session for investigation %s", case_id)


@router.post(
    "/investigations/{case_id}/run",
    response_model=InvestigationRunResponse,
    status_code=202,
)
async def run_investigation(
    case_id: CaseIdPath,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationRunResponse:
    """Acknowledge a run and execute the existing graph in the background."""
    started = await _investigation_service.start_investigation(case_id, db)
    if started is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation not found: {case_id}",
        )

    state, scheduled = started
    if scheduled:
        background_tasks.add_task(_run_investigation_background, case_id)
        message = "Investigation execution started in the background. Poll this resource for progress."
    else:
        message = "Investigation execution is already in progress. Poll this resource for progress."

    return InvestigationRunResponse(
        case_id=state.case_id,
        status=AgentStatus.IN_PROGRESS,
        current_stage=state.current_stage,
        message=message,
    )
