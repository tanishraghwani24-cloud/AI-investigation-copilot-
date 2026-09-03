"""Tests for the persistent Mock Bank (Stage 1).

Covers ORM model behaviour, MockBankService queries, API endpoints,
and seed-script idempotency.  All tests use an in-memory SQLite
database so no PostgreSQL connection is required.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.session import Base
from app.models.mock_bank import (
    MockBankAccount,
    MockBankCustomer,
    MockBankTransaction,
)
from app.services.mock_bank_service import MockBankService

# ── Fixtures ─────────────────────────────────────────────────────────

_TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    echo=False,
    future=True,
)

_TestSessionFactory = async_sessionmaker(
    bind=_TEST_ENGINE,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db_session():
    """Yield an async session backed by a fresh in-memory SQLite database."""
    # Enable foreign key support in SQLite
    @event.listens_for(_TEST_ENGINE.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with _TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _TestSessionFactory() as session:
        yield session

    async with _TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def _make_customer(customer_id: str = "CUST-TEST-001", **overrides):
    """Helper to build a MockBankCustomer with sensible defaults."""
    defaults = dict(
        customer_id=customer_id,
        name="Test User",
        email="test@example.com",
        phone="+1-555-000-0000",
        address="123 Test St",
        date_of_birth="1990-01-01",
        account_open_date="2020-01-01",
        risk_rating="LOW",
        occupation="Engineer",
        nationality="US",
    )
    defaults.update(overrides)
    return MockBankCustomer(**defaults)


def _make_account(
    account_id: str = "ACC-TEST-001",
    customer_id: str = "CUST-TEST-001",
    **overrides,
):
    """Helper to build a MockBankAccount with sensible defaults."""
    defaults = dict(
        account_id=account_id,
        customer_id=customer_id,
        account_type="CHECKING",
        currency="USD",
        status="ACTIVE",
    )
    defaults.update(overrides)
    return MockBankAccount(**defaults)


def _make_transaction(
    transaction_id: str = "TXN-TEST-001",
    account_id: str = "ACC-TEST-001",
    **overrides,
):
    """Helper to build a MockBankTransaction with sensible defaults."""
    defaults = dict(
        transaction_id=transaction_id,
        account_id=account_id,
        receiver_account_id="ACC-EXT-999",
        amount=100.0,
        currency="USD",
        transaction_type="WIRE",
        channel="ONLINE",
        timestamp=datetime(2025, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        description="Test transaction",
        location="New York, US",
        status="COMPLETED",
    )
    defaults.update(overrides)
    return MockBankTransaction(**defaults)


# =====================================================================
# 1. ORM Model Tests
# =====================================================================


class TestMockBankModels:
    """Verify ORM model persistence and relationships."""

    @pytest.mark.asyncio
    async def test_customer_persistence(self, db_session: AsyncSession):
        """A customer can be created and retrieved."""
        customer = _make_customer()
        db_session.add(customer)
        await db_session.flush()

        assert customer.customer_id == "CUST-TEST-001"
        assert customer.name == "Test User"
        assert customer.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_account_persistence(self, db_session: AsyncSession):
        """An account can be created with a FK to its customer."""
        db_session.add(_make_customer())
        await db_session.flush()

        account = _make_account()
        db_session.add(account)
        await db_session.flush()

        assert account.account_id == "ACC-TEST-001"
        assert account.customer_id == "CUST-TEST-001"
        assert account.account_type == "CHECKING"

    @pytest.mark.asyncio
    async def test_transaction_persistence(self, db_session: AsyncSession):
        """A transaction can be created with a FK to its account."""
        db_session.add(_make_customer())
        await db_session.flush()
        db_session.add(_make_account())
        await db_session.flush()

        txn = _make_transaction()
        db_session.add(txn)
        await db_session.flush()

        assert txn.transaction_id == "TXN-TEST-001"
        assert txn.amount == 100.0
        assert txn.account_id == "ACC-TEST-001"

    @pytest.mark.asyncio
    async def test_customer_uniqueness(self, db_session: AsyncSession):
        """Duplicate customer_id raises an integrity error."""
        from sqlalchemy.exc import IntegrityError

        db_session.add(_make_customer("CUST-DUP"))
        await db_session.flush()

        db_session.add(_make_customer("CUST-DUP"))
        with pytest.raises(IntegrityError):
            await db_session.flush()

    @pytest.mark.asyncio
    async def test_account_uniqueness(self, db_session: AsyncSession):
        """Duplicate account_id raises an integrity error."""
        from sqlalchemy.exc import IntegrityError

        db_session.add(_make_customer())
        await db_session.flush()

        db_session.add(_make_account("ACC-DUP"))
        await db_session.flush()

        db_session.add(_make_account("ACC-DUP"))
        with pytest.raises(IntegrityError):
            await db_session.flush()

    @pytest.mark.asyncio
    async def test_transaction_uniqueness(self, db_session: AsyncSession):
        """Duplicate transaction_id raises an integrity error."""
        from sqlalchemy.exc import IntegrityError

        db_session.add(_make_customer())
        await db_session.flush()
        db_session.add(_make_account())
        await db_session.flush()

        db_session.add(_make_transaction("TXN-DUP"))
        await db_session.flush()

        db_session.add(_make_transaction("TXN-DUP"))
        with pytest.raises(IntegrityError):
            await db_session.flush()

    @pytest.mark.asyncio
    async def test_nullable_fields(self, db_session: AsyncSession):
        """A customer with all nullable fields as None persists correctly."""
        customer = _make_customer(
            customer_id="CUST-SPARSE",
            name="Sparse User",
            email=None,
            phone=None,
            address=None,
            date_of_birth=None,
            account_open_date=None,
            risk_rating=None,
            occupation=None,
            nationality=None,
        )
        db_session.add(customer)
        await db_session.flush()

        assert customer.customer_id == "CUST-SPARSE"
        assert customer.email is None
        assert customer.nationality is None


# =====================================================================
# 2. MockBankService Tests
# =====================================================================


class TestMockBankService:
    """Verify the query service layer."""

    @pytest_asyncio.fixture
    async def seeded_session(self, db_session: AsyncSession):
        """Seed a customer + account + 5 transactions for service tests."""
        db_session.add(_make_customer())
        await db_session.flush()

        db_session.add(_make_account())
        await db_session.flush()

        base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(5):
            db_session.add(
                _make_transaction(
                    transaction_id=f"TXN-SVC-{i + 1:03d}",
                    timestamp=base + timedelta(days=i),
                    amount=100.0 * (i + 1),
                )
            )
        await db_session.flush()
        return db_session

    @pytest.mark.asyncio
    async def test_get_customer(self, seeded_session: AsyncSession):
        svc = MockBankService()
        result = await svc.get_customer(seeded_session, "CUST-TEST-001")
        assert result is not None
        assert result.customer_id == "CUST-TEST-001"

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, seeded_session: AsyncSession):
        svc = MockBankService()
        result = await svc.get_customer(seeded_session, "CUST-MISSING")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_account(self, seeded_session: AsyncSession):
        svc = MockBankService()
        result = await svc.get_account(seeded_session, "ACC-TEST-001")
        assert result is not None
        assert result.account_id == "ACC-TEST-001"

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, seeded_session: AsyncSession):
        svc = MockBankService()
        result = await svc.get_account(seeded_session, "ACC-MISSING")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_transaction(self, seeded_session: AsyncSession):
        svc = MockBankService()
        result = await svc.get_transaction(seeded_session, "TXN-SVC-001")
        assert result is not None
        assert result.transaction_id == "TXN-SVC-001"

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, seeded_session: AsyncSession):
        svc = MockBankService()
        result = await svc.get_transaction(seeded_session, "TXN-MISSING")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_account_transactions(self, seeded_session: AsyncSession):
        svc = MockBankService()
        results = await svc.get_account_transactions(seeded_session, "ACC-TEST-001")
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_account_transactions_chronological(self, seeded_session: AsyncSession):
        """Transactions are returned sorted by timestamp."""
        svc = MockBankService()
        results = await svc.get_account_transactions(seeded_session, "ACC-TEST-001")
        timestamps = [r.timestamp for r in results]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    async def test_account_transactions_date_filter(self, seeded_session: AsyncSession):
        """Date range filtering returns the correct subset."""
        svc = MockBankService()
        start = datetime(2025, 6, 2, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 6, 4, 0, 0, 0, tzinfo=timezone.utc)
        results = await svc.get_account_transactions(
            seeded_session, "ACC-TEST-001", start_date=start, end_date=end,
        )
        # Days 2 and 3 fall within the range (June 2 and June 3)
        assert len(results) == 2
        for r in results:
            # SQLite strips timezone info; compare date portion only
            ts = r.timestamp.replace(tzinfo=None) if r.timestamp else None
            assert ts is not None
            assert ts >= start.replace(tzinfo=None)
            assert ts <= end.replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_account_transactions_empty_account(self, db_session: AsyncSession):
        """An account with no transactions returns an empty list."""
        db_session.add(_make_customer())
        await db_session.flush()
        db_session.add(_make_account())
        await db_session.flush()

        svc = MockBankService()
        results = await svc.get_account_transactions(db_session, "ACC-TEST-001")
        assert results == []


# =====================================================================
# 3. API Route Tests
# =====================================================================


class TestMockBankAPI:
    """Verify the Mock Bank REST API endpoints."""

    @pytest_asyncio.fixture
    async def seeded_session(self, db_session: AsyncSession):
        """Seed data for API tests."""
        db_session.add(_make_customer())
        await db_session.flush()
        db_session.add(_make_account())
        await db_session.flush()

        base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(3):
            db_session.add(
                _make_transaction(
                    transaction_id=f"TXN-API-{i + 1:03d}",
                    timestamp=base + timedelta(days=i),
                    amount=500.0 * (i + 1),
                )
            )
        await db_session.flush()
        return db_session

    @pytest.mark.asyncio
    async def test_get_customer_endpoint(self, seeded_session: AsyncSession):
        """GET /mock-bank/customers/{id} returns customer data."""
        from app.api.routes.mock_bank import get_customer as _get_customer

        # We call the route function directly with the test session
        from unittest.mock import AsyncMock

        result = await _get_customer("CUST-TEST-001", db=seeded_session)
        assert result.customer_id == "CUST-TEST-001"

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, seeded_session: AsyncSession):
        """GET /mock-bank/customers/{id} returns 404 for unknown ID."""
        from fastapi import HTTPException
        from app.api.routes.mock_bank import get_customer as _get_customer

        with pytest.raises(HTTPException) as exc_info:
            await _get_customer("CUST-MISSING", db=seeded_session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_account_endpoint(self, seeded_session: AsyncSession):
        """GET /mock-bank/accounts/{id} returns account data."""
        from app.api.routes.mock_bank import get_account as _get_account

        result = await _get_account("ACC-TEST-001", db=seeded_session)
        assert result.account_id == "ACC-TEST-001"

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, seeded_session: AsyncSession):
        """GET /mock-bank/accounts/{id} returns 404 for unknown ID."""
        from fastapi import HTTPException
        from app.api.routes.mock_bank import get_account as _get_account

        with pytest.raises(HTTPException) as exc_info:
            await _get_account("ACC-MISSING", db=seeded_session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_account_transactions_endpoint(self, seeded_session: AsyncSession):
        """GET /mock-bank/accounts/{id}/transactions returns transaction list."""
        from app.api.routes.mock_bank import get_account_transactions as _get_txns

        results = await _get_txns("ACC-TEST-001", start_date=None, end_date=None, db=seeded_session)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_account_transactions_not_found(self, seeded_session: AsyncSession):
        """GET /mock-bank/accounts/{id}/transactions returns 404 for unknown account."""
        from fastapi import HTTPException
        from app.api.routes.mock_bank import get_account_transactions as _get_txns

        with pytest.raises(HTTPException) as exc_info:
            await _get_txns("ACC-MISSING", start_date=None, end_date=None, db=seeded_session)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_transaction_endpoint(self, seeded_session: AsyncSession):
        """GET /mock-bank/transactions/{id} returns transaction data."""
        from app.api.routes.mock_bank import get_transaction as _get_txn

        result = await _get_txn("TXN-API-001", db=seeded_session)
        assert result.transaction_id == "TXN-API-001"
        assert result.amount == 500.0

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, seeded_session: AsyncSession):
        """GET /mock-bank/transactions/{id} returns 404 for unknown ID."""
        from fastapi import HTTPException
        from app.api.routes.mock_bank import get_transaction as _get_txn

        with pytest.raises(HTTPException) as exc_info:
            await _get_txn("TXN-MISSING", db=seeded_session)
        assert exc_info.value.status_code == 404


# =====================================================================
# 4. Seed Idempotency Tests
# =====================================================================


class TestSeedIdempotency:
    """Verify seed helpers are idempotent."""

    @pytest.mark.asyncio
    async def test_seed_creates_data(self, db_session: AsyncSession):
        """_seed_customer inserts a customer + account + transactions."""
        from scripts.seed_mock_bank import _build_customer_1, _seed_customer

        customer, account, txns = _build_customer_1()
        inserted = await _seed_customer(db_session, customer, account, txns)
        assert inserted is True

        svc = MockBankService()
        result = await svc.get_customer(db_session, "CUST-MOCK-001")
        assert result is not None

        history = await svc.get_account_transactions(db_session, "ACC-MOCK-001")
        assert len(history) == 30  # 25 routine + 5 anomalous

    @pytest.mark.asyncio
    async def test_seed_idempotent(self, db_session: AsyncSession):
        """Running _seed_customer twice does not create duplicates."""
        from scripts.seed_mock_bank import _build_customer_2, _seed_customer

        customer, account, txns = _build_customer_2()

        first = await _seed_customer(db_session, customer, account, txns)
        assert first is True

        # Rebuild fresh objects for the second insert attempt
        customer2, account2, txns2 = _build_customer_2()
        second = await _seed_customer(db_session, customer2, account2, txns2)
        assert second is False

        # Still only 20 transactions
        svc = MockBankService()
        history = await svc.get_account_transactions(db_session, "ACC-MOCK-002")
        assert len(history) == 20

    @pytest.mark.asyncio
    async def test_seed_customer_3_sparse(self, db_session: AsyncSession):
        """Sparse customer seeds correctly with null fields."""
        from scripts.seed_mock_bank import _build_customer_3, _seed_customer

        customer, account, txns = _build_customer_3()
        await _seed_customer(db_session, customer, account, txns)

        svc = MockBankService()
        result = await svc.get_customer(db_session, "CUST-MOCK-003")
        assert result is not None
        assert result.email is None
        assert result.phone is None
        assert result.nationality is None

        history = await svc.get_account_transactions(db_session, "ACC-MOCK-003")
        assert len(history) == 3
