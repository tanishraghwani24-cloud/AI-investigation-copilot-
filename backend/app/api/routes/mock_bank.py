"""Mock Bank API routes.

Exposes the persistent Mock Bank data through a read-only REST API.
"""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.mock_bank.models import (
    Account as AccountResponse,
    Customer as CustomerResponse,
    Transaction as TransactionResponse,
)
from app.services.mock_bank_service import MockBankService

router = APIRouter(tags=["mock-bank"])

_service = MockBankService()

CustomerIdPath = Annotated[str, Path(min_length=1, description="Customer identifier")]
AccountIdPath = Annotated[str, Path(min_length=1, description="Account identifier")]
TransactionIdPath = Annotated[str, Path(min_length=1, description="Transaction identifier")]


@router.get("/mock-bank/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: CustomerIdPath,
    db: AsyncSession = Depends(get_db_session),
) -> CustomerResponse:
    """Retrieve a Mock Bank customer by customer_id."""
    record = await _service.get_customer(db, customer_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer not found: {customer_id}",
        )
    return CustomerResponse(
        customer_id=record.customer_id,
        first_name=record.name.split(" ", 1)[0] if record.name else "",
        last_name=record.name.split(" ", 1)[1] if record.name and " " in record.name else "",
        email=record.email,
        phone=record.phone,
        address=record.address,
        date_of_birth=record.date_of_birth,
        nationality=record.nationality,
        occupation=record.occupation,
        risk_rating=record.risk_rating,
        created_at=record.created_at,
    )


@router.get("/mock-bank/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: AccountIdPath,
    db: AsyncSession = Depends(get_db_session),
) -> AccountResponse:
    """Retrieve a Mock Bank account by account_id."""
    record = await _service.get_account(db, account_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )
    return AccountResponse(
        account_id=record.account_id,
        customer_id=record.customer_id,
        account_type=record.account_type,
        currency=record.currency,
        balance=0.0,  # Balance is not stored in the persistent model
        status=record.status,
    )


@router.get(
    "/mock-bank/accounts/{account_id}/transactions",
    response_model=list[TransactionResponse],
)
async def get_account_transactions(
    account_id: AccountIdPath,
    start_date: Optional[datetime] = Query(default=None, description="Filter: start date (inclusive)"),
    end_date: Optional[datetime] = Query(default=None, description="Filter: end date (inclusive)"),
    db: AsyncSession = Depends(get_db_session),
) -> list[TransactionResponse]:
    """Retrieve transaction history for a Mock Bank account."""
    # Verify the account exists first
    account = await _service.get_account(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )

    records = await _service.get_account_transactions(
        db, account_id, start_date=start_date, end_date=end_date,
    )
    return [
        TransactionResponse(
            transaction_id=r.transaction_id,
            sender_account_id=r.account_id,
            receiver_account_id=r.receiver_account_id or "",
            amount=r.amount,
            currency=r.currency,
            transaction_type=r.transaction_type,
            channel=r.channel,
            timestamp=r.timestamp,
            description=r.description,
            location=r.location,
            status=r.status,
        )
        for r in records
    ]


@router.get(
    "/mock-bank/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
async def get_transaction(
    transaction_id: TransactionIdPath,
    db: AsyncSession = Depends(get_db_session),
) -> TransactionResponse:
    """Retrieve a single Mock Bank transaction by transaction_id."""
    record = await _service.get_transaction(db, transaction_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction not found: {transaction_id}",
        )
    return TransactionResponse(
        transaction_id=record.transaction_id,
        sender_account_id=record.account_id,
        receiver_account_id=record.receiver_account_id or "",
        amount=record.amount,
        currency=record.currency,
        transaction_type=record.transaction_type,
        channel=record.channel,
        timestamp=record.timestamp,
        description=record.description,
        location=record.location,
        status=record.status,
    )
