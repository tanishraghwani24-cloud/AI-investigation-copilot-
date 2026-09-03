"""Seed the persistent Mock Bank with deterministic demo data.

Creates three customers with accounts and transaction history:
  - CUST-MOCK-001: Suspicious-history candidate (30 transactions)
  - CUST-MOCK-002: Legitimate low-risk candidate (20 transactions)
  - CUST-MOCK-003: Sparse/missing-data candidate (3 transactions)

Idempotent — running twice does NOT create duplicates.

Usage::

    python scripts/seed_mock_bank.py
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure the backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.mock_bank import (
    MockBankAccount,
    MockBankCustomer,
    MockBankTransaction,
)


# ── Seed data definitions ────────────────────────────────────────────


def _build_customer_1() -> tuple[
    MockBankCustomer, MockBankAccount, list[MockBankTransaction]
]:
    """Suspicious-history candidate with mixed normal and anomalous transactions."""
    customer = MockBankCustomer(
        customer_id="CUST-MOCK-001",
        name="Marcus Whitfield",
        email="marcus.whitfield@example.com",
        phone="+1-555-234-5678",
        address="4521 Park Avenue, New York",
        date_of_birth="1982-03-15",
        account_open_date="2019-06-01",
        risk_rating="MEDIUM",
        occupation="Import/Export Consultant",
        nationality="US",
    )

    account = MockBankAccount(
        account_id="ACC-MOCK-001",
        customer_id="CUST-MOCK-001",
        account_type="BUSINESS",
        currency="USD",
        status="ACTIVE",
    )

    base_time = datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    txns: list[MockBankTransaction] = []

    # 25 routine transactions (payroll, rent, utilities, etc.)
    routine_data = [
        ("Payroll deposit", 4500.00, "ACH", "ONLINE", "New York, US"),
        ("Office rent", 2200.00, "ACH", "ONLINE", "New York, US"),
        ("Utility payment", 185.50, "ACH", "ONLINE", "New York, US"),
        ("Supplier payment", 3200.00, "WIRE", "ONLINE", "New York, US"),
        ("Client invoice", 5800.00, "WIRE", "ONLINE", "New York, US"),
        ("Insurance premium", 450.00, "ACH", "ONLINE", "New York, US"),
        ("Office supplies", 320.00, "CARD", "ONLINE", "New York, US"),
        ("Payroll deposit", 4500.00, "ACH", "ONLINE", "New York, US"),
        ("Shipping costs", 780.00, "WIRE", "ONLINE", "New York, US"),
        ("Client invoice", 6100.00, "WIRE", "ONLINE", "New York, US"),
        ("Utility payment", 192.00, "ACH", "ONLINE", "New York, US"),
        ("Office rent", 2200.00, "ACH", "ONLINE", "New York, US"),
        ("Tax payment", 1850.00, "ACH", "BRANCH", "New York, US"),
        ("Supplier payment", 2950.00, "WIRE", "ONLINE", "New York, US"),
        ("Payroll deposit", 4500.00, "ACH", "ONLINE", "New York, US"),
        ("Business lunch", 125.00, "CARD", "MOBILE", "New York, US"),
        ("Software subscription", 299.00, "CARD", "ONLINE", "New York, US"),
        ("Client invoice", 7200.00, "WIRE", "ONLINE", "New York, US"),
        ("Office supplies", 410.00, "CARD", "ONLINE", "New York, US"),
        ("Payroll deposit", 4500.00, "ACH", "ONLINE", "New York, US"),
        ("Utility payment", 178.00, "ACH", "ONLINE", "New York, US"),
        ("Insurance premium", 450.00, "ACH", "ONLINE", "New York, US"),
        ("Shipping costs", 920.00, "WIRE", "ONLINE", "New York, US"),
        ("Client invoice", 5400.00, "WIRE", "ONLINE", "New York, US"),
        ("Office rent", 2200.00, "ACH", "ONLINE", "New York, US"),
    ]
    for i, (desc, amount, txn_type, channel, location) in enumerate(routine_data):
        txns.append(MockBankTransaction(
            transaction_id=f"TXN-MOCK-001-{i + 1:03d}",
            account_id="ACC-MOCK-001",
            receiver_account_id=f"ACC-EXT-{1000 + i}",
            amount=amount,
            currency="USD",
            transaction_type=txn_type,
            channel=channel,
            timestamp=base_time + timedelta(days=i * 3, hours=i % 8),
            description=desc,
            location=location,
            status="COMPLETED",
        ))

    # 5 anomalous transactions
    anomalous_data = [
        ("Overseas consulting fee", 48000.00, "WIRE", "ONLINE", "Cayman Islands"),
        ("Equipment purchase", 52500.00, "WIRE", "ONLINE", "Singapore, SG"),
        ("Rapid transfer", 67500.00, "WIRE", "ONLINE", "Dubai, AE"),
        ("Investment deposit", 41250.00, "WIRE", "ATM", "London, GB"),
        ("Cross-border settlement", 59900.00, "WIRE", "ONLINE", "Hong Kong, HK"),
    ]
    for i, (desc, amount, txn_type, channel, location) in enumerate(anomalous_data):
        txns.append(MockBankTransaction(
            transaction_id=f"TXN-MOCK-001-{26 + i:03d}",
            account_id="ACC-MOCK-001",
            receiver_account_id=f"ACC-OFFSHORE-{i + 1}",
            amount=amount,
            currency="USD",
            transaction_type=txn_type,
            channel=channel,
            timestamp=base_time + timedelta(days=80 + i, hours=2 + i),
            description=desc,
            location=location,
            status="COMPLETED",
        ))

    return customer, account, txns


def _build_customer_2() -> tuple[
    MockBankCustomer, MockBankAccount, list[MockBankTransaction]
]:
    """Legitimate low-risk candidate with consistent routine activity."""
    customer = MockBankCustomer(
        customer_id="CUST-MOCK-002",
        name="Sarah Chen",
        email="sarah.chen@example.com",
        phone="+1-555-876-5432",
        address="789 Maple Lane, San Francisco",
        date_of_birth="1990-11-22",
        account_open_date="2020-03-15",
        risk_rating="LOW",
        occupation="University Professor",
        nationality="US",
    )

    account = MockBankAccount(
        account_id="ACC-MOCK-002",
        customer_id="CUST-MOCK-002",
        account_type="CHECKING",
        currency="USD",
        status="ACTIVE",
    )

    base_time = datetime(2025, 1, 10, 8, 0, 0, tzinfo=timezone.utc)
    txns: list[MockBankTransaction] = []

    routine_data = [
        ("Salary deposit", 6200.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Rent payment", 1800.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Grocery shopping", 145.00, "CARD", "MOBILE", "San Francisco, US"),
        ("Electric bill", 95.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Internet service", 79.99, "ACH", "ONLINE", "San Francisco, US"),
        ("Gas station", 52.00, "CARD", "MOBILE", "San Francisco, US"),
        ("Salary deposit", 6200.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Rent payment", 1800.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Grocery shopping", 167.50, "CARD", "MOBILE", "San Francisco, US"),
        ("Health insurance", 320.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Streaming service", 15.99, "CARD", "ONLINE", "San Francisco, US"),
        ("Pharmacy", 42.00, "CARD", "MOBILE", "San Francisco, US"),
        ("Salary deposit", 6200.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Rent payment", 1800.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Grocery shopping", 132.00, "CARD", "MOBILE", "San Francisco, US"),
        ("Electric bill", 102.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Book purchase", 34.99, "CARD", "ONLINE", "San Francisco, US"),
        ("Coffee shop", 8.50, "CARD", "MOBILE", "San Francisco, US"),
        ("Salary deposit", 6200.00, "ACH", "ONLINE", "San Francisco, US"),
        ("Rent payment", 1800.00, "ACH", "ONLINE", "San Francisco, US"),
    ]
    for i, (desc, amount, txn_type, channel, location) in enumerate(routine_data):
        txns.append(MockBankTransaction(
            transaction_id=f"TXN-MOCK-002-{i + 1:03d}",
            account_id="ACC-MOCK-002",
            receiver_account_id=f"ACC-LOCAL-{2000 + i}",
            amount=amount,
            currency="USD",
            transaction_type=txn_type,
            channel=channel,
            timestamp=base_time + timedelta(days=i * 4, hours=9 + (i % 6)),
            description=desc,
            location=location,
            status="COMPLETED",
        ))

    return customer, account, txns


def _build_customer_3() -> tuple[
    MockBankCustomer, MockBankAccount, list[MockBankTransaction]
]:
    """Sparse/missing-data candidate for robustness testing."""
    customer = MockBankCustomer(
        customer_id="CUST-MOCK-003",
        name="A. Nakamura",
        email=None,
        phone=None,
        address=None,
        date_of_birth=None,
        account_open_date=None,
        risk_rating=None,
        occupation=None,
        nationality=None,
    )

    account = MockBankAccount(
        account_id="ACC-MOCK-003",
        customer_id="CUST-MOCK-003",
        account_type="SAVINGS",
        currency="USD",
        status="ACTIVE",
    )

    base_time = datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    txns = [
        MockBankTransaction(
            transaction_id="TXN-MOCK-003-001",
            account_id="ACC-MOCK-003",
            receiver_account_id=None,
            amount=1500.00,
            currency="USD",
            transaction_type="WIRE",
            channel="ONLINE",
            timestamp=base_time,
            description=None,
            location=None,
            status="COMPLETED",
        ),
        MockBankTransaction(
            transaction_id="TXN-MOCK-003-002",
            account_id="ACC-MOCK-003",
            receiver_account_id=None,
            amount=750.00,
            currency="USD",
            transaction_type="ACH",
            channel="ONLINE",
            timestamp=base_time + timedelta(days=15),
            description=None,
            location=None,
            status="COMPLETED",
        ),
        MockBankTransaction(
            transaction_id="TXN-MOCK-003-003",
            account_id="ACC-MOCK-003",
            receiver_account_id=None,
            amount=3200.00,
            currency="USD",
            transaction_type="WIRE",
            channel="BRANCH",
            timestamp=base_time + timedelta(days=30),
            description=None,
            location=None,
            status="COMPLETED",
        ),
    ]

    return customer, account, txns


# ── Seed runner ──────────────────────────────────────────────────────


async def _seed_customer(
    session: AsyncSession,
    customer: MockBankCustomer,
    account: MockBankAccount,
    transactions: list[MockBankTransaction],
) -> bool:
    """Insert a customer + account + transactions if the customer does not exist.

    Returns True if new records were inserted, False if already seeded.
    """
    existing = await session.execute(
        select(MockBankCustomer).where(
            MockBankCustomer.customer_id == customer.customer_id
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False

    session.add(customer)
    await session.flush()
    session.add(account)
    await session.flush()
    for txn in transactions:
        session.add(txn)
    await session.flush()
    return True


async def seed_mock_bank() -> None:
    """Populate the Mock Bank tables with deterministic demo data."""
    builders = [_build_customer_1, _build_customer_2, _build_customer_3]

    async with async_session_factory() as session:
        try:
            inserted = 0
            for build_fn in builders:
                customer, account, txns = build_fn()
                if await _seed_customer(session, customer, account, txns):
                    inserted += 1
                    print(
                        f"  + Seeded {customer.customer_id} "
                        f"({account.account_id}, {len(txns)} transactions)"
                    )
                else:
                    print(
                        f"  - {customer.customer_id} already exists, skipping"
                    )

            await session.commit()

            if inserted > 0:
                print(f"\nDone -- inserted {inserted} new customer(s).")
            else:
                print("\nNo new data inserted -- all customers already exist.")
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    print("Seeding Mock Bank data...\n")
    asyncio.run(seed_mock_bank())
