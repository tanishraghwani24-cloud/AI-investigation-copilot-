"""Investigation API routes.

Provides the persisted investigation REST API.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.mock_bank.generator import generate_investigation_data
from app.schemas.investigation_state import (
    CaseInput,
    CustomerProfile,
    InvestigationState,
    Transaction,
    CurrentStage,
    create_initial_state,
)
from app.services.investigation_service import InvestigationService

router = APIRouter()

# ── Default seed for deterministic generation ────────────────────────
_DEFAULT_SEED: int = 42

# ── Service instance ─────────────────────────────────────────────────
_investigation_service = InvestigationService()


def _build_investigation_state(seed: int) -> InvestigationState:
    """Build an InvestigationState from generated Mock Bank data.

    Maps mock_bank models into the schema-layer types used by the
    investigation pipeline.

    Args:
        seed: Integer seed for deterministic generation.

    Returns:
        A fully initialised InvestigationState ready for pipeline
        execution.
    """
    data = generate_investigation_data(seed)
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
    case_id = f"CASE-2025-{seed:05d}"

    return create_initial_state(case_id=case_id, case_input=case_input)


@router.post("/investigations", response_model=InvestigationState)
async def create_investigation(
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationState:
    """Create a new investigation case.

    Persists a deterministic Mock Bank case input (seed=42). Agent outputs
    are populated only when the investigation is subsequently run.
    """
    state = _build_investigation_state(_DEFAULT_SEED)
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
    case_id: str,
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


@router.post(
    "/investigations/{case_id}/run",
    response_model=InvestigationState,
)
async def run_investigation(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationState:
    """Synchronously execute the existing investigation's graph pipeline."""
    state = await _investigation_service.run_investigation(case_id, db)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation not found: {case_id}",
        )
    return state
