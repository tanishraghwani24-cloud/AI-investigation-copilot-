"""Investigation API routes.

Provides the POST /api/investigations endpoint that returns a
deterministic InvestigationState built from synthetic Mock Bank data.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.mock_bank.generator import generate_investigation_data
from app.schemas.investigation_state import (
    CaseInput,
    CustomerProfile,
    InvestigationState,
    Transaction,
    create_initial_state,
)

router = APIRouter()

# ── Default seed for deterministic generation ────────────────────────
_DEFAULT_SEED: int = 42


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


# Pre-build for deterministic endpoint responses
_GENERATED_STATE: InvestigationState = _build_investigation_state(_DEFAULT_SEED)


@router.post("/investigations", response_model=InvestigationState)
async def create_investigation() -> InvestigationState:
    """Create a new investigation case.

    Returns a deterministic InvestigationState built from synthetic
    Mock Bank data (seed=42).  The case input contains generated
    customer, account, and transaction data.  Agent outputs are
    populated when the LangGraph pipeline is subsequently executed.
    """
    return _GENERATED_STATE
