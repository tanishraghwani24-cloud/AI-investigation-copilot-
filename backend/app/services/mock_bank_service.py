"""Mock Bank query service.

Provides read-only access to the persistent Mock Bank data stored
in PostgreSQL.  All methods accept the existing ``AsyncSession``
from ``app.db.session.get_db_session``.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mock_bank import (
    MockBankAccount,
    MockBankCustomer,
    MockBankTransaction,
)


class MockBankService:
    """Data-access layer for the persistent Mock Bank."""

    async def get_customer(
        self,
        session: AsyncSession,
        customer_id: str,
    ) -> MockBankCustomer | None:
        """Retrieve a customer by their external customer_id."""
        stmt = select(MockBankCustomer).where(
            MockBankCustomer.customer_id == customer_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_account(
        self,
        session: AsyncSession,
        account_id: str,
    ) -> MockBankAccount | None:
        """Retrieve an account by its external account_id."""
        stmt = select(MockBankAccount).where(
            MockBankAccount.account_id == account_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_transaction(
        self,
        session: AsyncSession,
        transaction_id: str,
    ) -> MockBankTransaction | None:
        """Retrieve a single transaction by its external transaction_id."""
        stmt = select(MockBankTransaction).where(
            MockBankTransaction.transaction_id == transaction_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_account_transactions(
        self,
        session: AsyncSession,
        account_id: str,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[MockBankTransaction]:
        """Return transactions for an account, ordered chronologically.

        Args:
            session: Active async database session.
            account_id: The account to retrieve transactions for.
            start_date: Optional lower bound (inclusive) on timestamp.
            end_date: Optional upper bound (inclusive) on timestamp.

        Returns:
            A list of MockBankTransaction records sorted by timestamp.
        """
        stmt = (
            select(MockBankTransaction)
            .where(MockBankTransaction.account_id == account_id)
        )
        if start_date is not None:
            stmt = stmt.where(MockBankTransaction.timestamp >= start_date)
        if end_date is not None:
            stmt = stmt.where(MockBankTransaction.timestamp <= end_date)
        stmt = stmt.order_by(MockBankTransaction.timestamp)

        result = await session.execute(stmt)
        return list(result.scalars().all())
