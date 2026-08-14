"""Tests for the Mock Bank deterministic data generator.

Covers:
- Deterministic output (same seed → same data)
- Different seeds → different data
- Output validity (models, values, types)
- Transaction value constraints
- Valid enums and dates
"""

from datetime import datetime

from app.mock_bank.generator import (
    MockBankData,
    generate_account,
    generate_alert,
    generate_customer,
    generate_investigation_data,
    generate_transactions,
)
from app.mock_bank.models import Account, Customer, Transaction


# ── TEST 1: Deterministic output ─────────────────────────────────────


class TestDeterministicOutput:
    """Same seed always produces identical data."""

    def test_customer_deterministic(self) -> None:
        """Same seed → identical customer."""
        c1 = generate_customer(42)
        c2 = generate_customer(42)
        assert c1.model_dump() == c2.model_dump()

    def test_account_deterministic(self) -> None:
        """Same seed → identical account."""
        a1 = generate_account(42, "CUST-001")
        a2 = generate_account(42, "CUST-001")
        assert a1.model_dump() == a2.model_dump()

    def test_transactions_deterministic(self) -> None:
        """Same seed → identical transactions."""
        t1 = generate_transactions(42, "ACC-001")
        t2 = generate_transactions(42, "ACC-001")
        assert len(t1) == len(t2)
        for a, b in zip(t1, t2):
            assert a.model_dump() == b.model_dump()

    def test_alert_deterministic(self) -> None:
        """Same seed → identical alert."""
        txns = generate_transactions(42, "ACC-001")
        a1 = generate_alert(42, txns)
        a2 = generate_alert(42, txns)
        assert a1 == a2

    def test_full_investigation_data_deterministic(self) -> None:
        """Same seed → identical MockBankData."""
        d1 = generate_investigation_data(42)
        d2 = generate_investigation_data(42)
        assert d1.customer.model_dump() == d2.customer.model_dump()
        assert d1.account.model_dump() == d2.account.model_dump()
        assert d1.alert_reason == d2.alert_reason
        assert len(d1.transactions) == len(d2.transactions)
        for a, b in zip(d1.transactions, d2.transactions):
            assert a.model_dump() == b.model_dump()


# ── TEST 2: Different seeds → different data ─────────────────────────


class TestDifferentSeeds:
    """Different seeds produce different data."""

    def test_different_customers(self) -> None:
        """Different seeds → different customer IDs."""
        c1 = generate_customer(42)
        c2 = generate_customer(99)
        assert c1.customer_id != c2.customer_id

    def test_different_accounts(self) -> None:
        """Different seeds → different account IDs."""
        a1 = generate_account(42, "CUST-001")
        a2 = generate_account(99, "CUST-001")
        assert a1.account_id != a2.account_id

    def test_different_transactions(self) -> None:
        """Different seeds → different transaction IDs."""
        t1 = generate_transactions(42, "ACC-001")
        t2 = generate_transactions(99, "ACC-001")
        ids1 = {t.transaction_id for t in t1}
        ids2 = {t.transaction_id for t in t2}
        assert ids1 != ids2

    def test_different_investigation_data(self) -> None:
        """Different seeds → different investigation data."""
        d1 = generate_investigation_data(42)
        d2 = generate_investigation_data(99)
        assert d1.customer.customer_id != d2.customer.customer_id


# ── TEST 3: Valid model types ────────────────────────────────────────


class TestValidModels:
    """Generated objects are valid Pydantic models."""

    def test_customer_is_valid(self) -> None:
        """generate_customer returns a valid Customer."""
        c = generate_customer(42)
        assert isinstance(c, Customer)

    def test_account_is_valid(self) -> None:
        """generate_account returns a valid Account."""
        a = generate_account(42, "CUST-001")
        assert isinstance(a, Account)

    def test_transactions_are_valid(self) -> None:
        """generate_transactions returns valid Transaction instances."""
        txns = generate_transactions(42, "ACC-001")
        assert len(txns) > 0
        for t in txns:
            assert isinstance(t, Transaction)

    def test_investigation_data_is_valid(self) -> None:
        """generate_investigation_data returns a valid MockBankData."""
        data = generate_investigation_data(42)
        assert isinstance(data, MockBankData)
        assert isinstance(data.customer, Customer)
        assert isinstance(data.account, Account)
        assert isinstance(data.alert_reason, str)
        assert all(isinstance(t, Transaction) for t in data.transactions)


# ── TEST 4: Transaction value constraints ────────────────────────────


class TestTransactionValues:
    """Generated transactions have valid field values."""

    def test_positive_amounts(self) -> None:
        """All transaction amounts are positive."""
        txns = generate_transactions(42, "ACC-001", count=10)
        for t in txns:
            assert t.amount > 0

    def test_valid_currency(self) -> None:
        """All transactions have a valid currency code."""
        txns = generate_transactions(42, "ACC-001")
        for t in txns:
            assert t.currency == "USD"

    def test_sender_account_matches(self) -> None:
        """Sender account matches the provided account ID."""
        txns = generate_transactions(42, "ACC-TEST-99")
        for t in txns:
            assert t.sender_account_id == "ACC-TEST-99"

    def test_default_count(self) -> None:
        """Default count produces 5 transactions."""
        txns = generate_transactions(42, "ACC-001")
        assert len(txns) == 5

    def test_custom_count(self) -> None:
        """Custom count produces the specified number of transactions."""
        txns = generate_transactions(42, "ACC-001", count=10)
        assert len(txns) == 10

    def test_timestamps_are_valid(self) -> None:
        """All transactions have valid timestamps."""
        txns = generate_transactions(42, "ACC-001")
        for t in txns:
            assert t.timestamp is not None
            assert isinstance(t.timestamp, datetime)

    def test_transactions_sorted_by_time(self) -> None:
        """Transactions are sorted chronologically."""
        txns = generate_transactions(42, "ACC-001")
        timestamps = [t.timestamp for t in txns]
        assert timestamps == sorted(timestamps)


# ── TEST 5: Valid enums and field values ─────────────────────────────


class TestValidEnums:
    """Generated data uses valid enum/field values."""

    def test_valid_transaction_types(self) -> None:
        """Transaction types are from the expected set."""
        valid = {"WIRE", "ACH", "P2P", "CARD"}
        txns = generate_transactions(42, "ACC-001", count=20)
        for t in txns:
            assert t.transaction_type in valid

    def test_valid_channels(self) -> None:
        """Channels are from the expected set."""
        valid = {"ONLINE", "ATM", "BRANCH", "MOBILE"}
        txns = generate_transactions(42, "ACC-001", count=20)
        for t in txns:
            assert t.channel in valid

    def test_valid_account_types(self) -> None:
        """Account type is from the expected set."""
        valid = {"CHECKING", "SAVINGS", "BUSINESS"}
        a = generate_account(42, "CUST-001")
        assert a.account_type in valid

    def test_valid_risk_rating(self) -> None:
        """Customer risk rating is from the expected set."""
        valid = {"LOW", "MEDIUM", "HIGH"}
        c = generate_customer(42)
        assert c.risk_rating in valid

    def test_account_status_is_active(self) -> None:
        """Generated accounts are ACTIVE."""
        a = generate_account(42, "CUST-001")
        assert a.status == "ACTIVE"

    def test_transaction_status_is_completed(self) -> None:
        """Generated transactions are COMPLETED."""
        txns = generate_transactions(42, "ACC-001")
        for t in txns:
            assert t.status == "COMPLETED"


# ── TEST 6: Alert generation ────────────────────────────────────────


class TestAlertGeneration:
    """Alert reason string is well-formed."""

    def test_alert_is_non_empty(self) -> None:
        """Alert reason is a non-empty string."""
        txns = generate_transactions(42, "ACC-001")
        alert = generate_alert(42, txns)
        assert isinstance(alert, str)
        assert len(alert) > 0

    def test_alert_ends_with_period(self) -> None:
        """Alert reason ends with a period."""
        txns = generate_transactions(42, "ACC-001")
        alert = generate_alert(42, txns)
        assert alert.endswith(".")


# ── TEST 7: Account balance and dates ────────────────────────────────


class TestAccountConstraints:
    """Account-level constraints are satisfied."""

    def test_positive_balance(self) -> None:
        """Account balance is positive."""
        a = generate_account(42, "CUST-001")
        assert a.balance > 0

    def test_opened_at_is_valid(self) -> None:
        """Account opened_at is a valid datetime."""
        a = generate_account(42, "CUST-001")
        assert a.opened_at is not None
        assert isinstance(a.opened_at, datetime)

    def test_customer_created_at(self) -> None:
        """Customer created_at is a valid datetime."""
        c = generate_customer(42)
        assert c.created_at is not None
        assert isinstance(c.created_at, datetime)
