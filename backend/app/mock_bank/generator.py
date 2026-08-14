"""Deterministic Mock Bank data generator.

Produces synthetic banking data (Customer, Account, Transactions, Alert)
using ``random.Random(seed)`` so that the same seed always yields
identical output.  No external APIs, no AI — pure Python.
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.mock_bank.models import Account, Customer, Transaction


# ============================================================
# Seed-stable data pools
# ============================================================

_FIRST_NAMES: list[str] = [
    "James", "Maria", "Robert", "Elena", "David",
    "Sophia", "Michael", "Olivia", "Daniel", "Amara",
    "William", "Priya", "Joseph", "Fatima", "Charles",
]

_LAST_NAMES: list[str] = [
    "Whitfield", "Vasquez", "Nakamura", "Patel", "Andersen",
    "Okonkwo", "Chen", "Morales", "Kim", "Al-Farsi",
    "Thompson", "Johansson", "Singh", "Rossi", "Muller",
]

_OCCUPATIONS: list[str] = [
    "Portfolio Manager", "Import/Export Consultant", "Software Engineer",
    "Financial Analyst", "Small Business Owner", "Medical Professional",
    "Real Estate Agent", "University Professor", "Retired",
    "Marketing Director",
]

_NATIONALITIES: list[str] = [
    "US", "GB", "CA", "AU", "DE", "JP", "IN", "BR", "FR", "SG",
]

_RISK_RATINGS: list[str] = ["LOW", "MEDIUM", "HIGH"]

_ACCOUNT_TYPES: list[str] = ["CHECKING", "SAVINGS", "BUSINESS"]

_TRANSACTION_TYPES: list[str] = ["WIRE", "ACH", "P2P", "CARD"]

_CHANNELS: list[str] = ["ONLINE", "ATM", "BRANCH", "MOBILE"]

_LOCATIONS: list[str] = [
    "New York, US", "London, GB", "Toronto, CA", "Sydney, AU",
    "Berlin, DE", "Tokyo, JP", "Mumbai, IN", "São Paulo, BR",
    "Paris, FR", "Singapore, SG",
]

_DESCRIPTIONS: list[str] = [
    "Invoice payment", "Supplier advance", "Investment deposit",
    "Rent payment", "Insurance premium", "Payroll transfer",
    "Equipment purchase", "Consulting fee", "Loan repayment",
    "Utility payment",
]

_STREET_NAMES: list[str] = [
    "Park Avenue", "Elm Street", "Main Street", "Oak Drive",
    "Maple Lane", "Cedar Road", "Pine Court", "Birch Boulevard",
    "Willow Way", "Spruce Circle",
]


# ============================================================
# Return type
# ============================================================


@dataclass(frozen=True)
class MockBankData:
    """Container for all generated Mock Bank data."""

    customer: Customer
    account: Account
    transactions: list[Transaction]
    alert_reason: str


# ============================================================
# Individual generators
# ============================================================


def generate_customer(seed: int) -> Customer:
    """Generate a deterministic Customer from the given seed.

    Args:
        seed: Integer seed for reproducible output.

    Returns:
        A fully populated ``Customer`` instance.
    """
    rng = random.Random(seed)

    first_name = rng.choice(_FIRST_NAMES)
    last_name = rng.choice(_LAST_NAMES)
    customer_id = f"CUST-{rng.randint(10000, 99999)}"

    # Deterministic date of birth (age 25-65)
    birth_year = rng.randint(1960, 2000)
    birth_month = rng.randint(1, 12)
    birth_day = rng.randint(1, 28)

    # Account open date (1-8 years ago from a fixed reference point)
    years_ago = rng.randint(1, 8)
    open_year = 2025 - years_ago
    open_month = rng.randint(1, 12)
    open_day = rng.randint(1, 28)

    street_number = rng.randint(100, 9999)
    street = rng.choice(_STREET_NAMES)
    city = rng.choice(_LOCATIONS).split(",")[0]

    return Customer(
        customer_id=customer_id,
        first_name=first_name,
        last_name=last_name,
        email=f"{first_name.lower()}.{last_name.lower()}@example.com",
        phone=f"+1-555-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
        date_of_birth=f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}",
        address=f"{street_number} {street}, {city}",
        nationality=rng.choice(_NATIONALITIES),
        occupation=rng.choice(_OCCUPATIONS),
        risk_rating=rng.choice(_RISK_RATINGS),
        created_at=datetime(open_year, open_month, open_day, tzinfo=timezone.utc),
    )


def generate_account(seed: int, customer_id: str) -> Account:
    """Generate a deterministic Account for the given customer.

    Args:
        seed: Integer seed for reproducible output.
        customer_id: The owning customer's identifier.

    Returns:
        A fully populated ``Account`` instance.
    """
    rng = random.Random(seed)

    account_id = f"ACC-{rng.randint(100000, 999999)}"
    account_type = rng.choice(_ACCOUNT_TYPES)
    balance = round(rng.uniform(1_000.0, 250_000.0), 2)

    # Opened 1-6 years ago
    years_ago = rng.randint(1, 6)
    open_year = 2025 - years_ago
    open_month = rng.randint(1, 12)
    open_day = rng.randint(1, 28)

    return Account(
        account_id=account_id,
        customer_id=customer_id,
        account_type=account_type,
        currency="USD",
        balance=balance,
        opened_at=datetime(open_year, open_month, open_day, tzinfo=timezone.utc),
        status="ACTIVE",
    )


def generate_transactions(
    seed: int,
    sender_account_id: str,
    count: int = 5,
) -> list[Transaction]:
    """Generate a deterministic list of Transactions.

    Args:
        seed: Integer seed for reproducible output.
        sender_account_id: The source account for all transactions.
        count: Number of transactions to generate (default 5).

    Returns:
        A list of ``Transaction`` instances ordered by timestamp.
    """
    rng = random.Random(seed)
    transactions: list[Transaction] = []

    # Fixed reference timestamp
    base_time = datetime(2025, 7, 15, 9, 0, 0, tzinfo=timezone.utc)

    for i in range(count):
        txn_id = f"TXN-{seed:04d}-{i + 1:03d}"
        receiver_id = f"ACC-{rng.randint(100000, 999999)}"
        txn_type = rng.choice(_TRANSACTION_TYPES)
        channel = rng.choice(_CHANNELS)
        location = rng.choice(_LOCATIONS)
        description = rng.choice(_DESCRIPTIONS)

        # Amount: most are moderate, but include occasional large ones
        if rng.random() < 0.3:
            # ~30% chance of a large transaction (> $10k)
            amount = round(rng.uniform(10_000.0, 75_000.0), 2)
        else:
            amount = round(rng.uniform(100.0, 9_999.0), 2)

        # Spread transactions across hours/minutes
        minutes_offset = rng.randint(0, 60) + i * rng.randint(15, 120)
        timestamp = base_time + timedelta(minutes=minutes_offset)

        transactions.append(
            Transaction(
                transaction_id=txn_id,
                sender_account_id=sender_account_id,
                receiver_account_id=receiver_id,
                amount=amount,
                currency="USD",
                transaction_type=txn_type,
                channel=channel,
                timestamp=timestamp,
                description=description,
                location=location,
                status="COMPLETED",
            )
        )

    # Sort by timestamp for consistency
    transactions.sort(key=lambda t: t.timestamp or base_time)
    return transactions


def generate_alert(seed: int, transactions: list[Transaction]) -> str:
    """Generate a deterministic alert reason from transaction data.

    Analyses the transaction list and produces a human-readable alert
    reason string that summarises why the case was flagged.

    Args:
        seed: Integer seed (unused for RNG but kept for API symmetry).
        transactions: The transactions associated with this case.

    Returns:
        A descriptive alert reason string.
    """
    total_amount = sum(t.amount for t in transactions)
    large_txns = [t for t in transactions if t.amount > 10_000.0]
    txn_count = len(transactions)

    parts: list[str] = []

    if large_txns:
        largest = max(large_txns, key=lambda t: t.amount)
        parts.append(
            f"Large transaction of ${largest.amount:,.2f} "
            f"({largest.transaction_type}) detected"
        )

    if txn_count >= 3:
        parts.append(
            f"{txn_count} transactions totalling ${total_amount:,.2f} "
            f"within a short time window"
        )

    if not parts:
        parts.append(
            f"Transaction activity of ${total_amount:,.2f} "
            f"flagged by automated rule engine"
        )

    return "; ".join(parts) + "."


# ============================================================
# Orchestrator
# ============================================================


def generate_investigation_data(seed: int) -> MockBankData:
    """Generate a complete set of Mock Bank data for one investigation.

    Produces a Customer, Account, list of Transactions, and an alert
    reason — all deterministically derived from ``seed``.

    Args:
        seed: Integer seed.  Same seed → identical output.

    Returns:
        A ``MockBankData`` dataclass with all generated data.
    """
    # Use offset seeds so sub-generators produce independent sequences
    customer = generate_customer(seed)
    account = generate_account(seed + 1000, customer.customer_id)
    transactions = generate_transactions(seed + 2000, account.account_id)
    alert_reason = generate_alert(seed, transactions)

    return MockBankData(
        customer=customer,
        account=account,
        transactions=transactions,
        alert_reason=alert_reason,
    )
