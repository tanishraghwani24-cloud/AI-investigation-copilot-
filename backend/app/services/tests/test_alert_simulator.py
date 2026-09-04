"""Tests for the Mock Bank incoming-transaction and alert simulator."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.context_agent import _LARGE_TXN_THRESHOLD
from app.models.mock_bank import MockBankAccount, MockBankAlert, MockBankTransaction
from app.services.alert_simulator import (
    ALERT_PREFIX,
    SIMULATED_TXN_PREFIX,
    AlertSimulator,
)


def _account(account_id: str = "ACC-MOCK-001") -> MockBankAccount:
    return MockBankAccount(account_id=account_id, customer_id="CUST-MOCK-001")


class _Session:
    """Minimal async session capturing what the simulator would persist."""

    def __init__(self, accounts: list[MockBankAccount]):
        self._accounts = accounts
        self.added: list[object] = []
        self.committed = False

    async def execute(self, _stmt):
        result = MagicMock()
        result.scalars.return_value.all.return_value = self._accounts
        return result

    async def scalar(self, _stmt):
        return 0

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.committed = False


@pytest.fixture()
def simulator():
    import random

    return AlertSimulator(rng=random.Random(1234))


class TestTransactionGeneration:
    def test_a_tick_creates_a_transaction_on_a_seeded_account(self, simulator):
        import asyncio

        session = _Session([_account()])
        transaction, _ = asyncio.run(simulator.simulate_once(session))

        assert isinstance(transaction, MockBankTransaction)
        assert transaction.account_id == "ACC-MOCK-001"
        assert session.committed

    def test_simulated_transaction_ids_are_unique(self, simulator):
        ids = {simulator._build_transaction(_account()).transaction_id for _ in range(200)}

        assert len(ids) == 200

    def test_simulated_transactions_are_labelled_so_pruning_spares_seed_data(self, simulator):
        assert simulator._build_transaction(_account()).transaction_id.startswith(
            SIMULATED_TXN_PREFIX
        )

    def test_transactions_carry_realistic_varying_detail(self, simulator):
        built = [simulator._build_transaction(_account()) for _ in range(40)]

        assert len({t.amount for t in built}) > 1
        assert len({t.transaction_type for t in built}) > 1
        assert len({t.channel for t in built}) > 1
        assert len({t.receiver_account_id for t in built}) > 1
        for transaction in built:
            assert transaction.amount > 0
            assert transaction.timestamp is not None
            assert transaction.currency == "USD"

    def test_timestamps_are_current(self, simulator):
        transaction = simulator._build_transaction(_account())
        delta = abs((datetime.now(timezone.utc) - transaction.timestamp).total_seconds())

        assert delta < 60

    def test_no_accounts_means_no_activity(self, simulator):
        import asyncio

        transaction, alert = asyncio.run(simulator.simulate_once(_Session([])))

        assert transaction is None and alert is None


class TestAlerting:
    def test_large_transactions_alert(self, simulator):
        transaction = simulator._build_transaction(_account())
        transaction.amount = _LARGE_TXN_THRESHOLD + 1

        assert simulator._should_alert(transaction) is True

    def test_small_transactions_do_not_alert(self, simulator):
        transaction = simulator._build_transaction(_account())
        transaction.amount = _LARGE_TXN_THRESHOLD - 1

        assert simulator._should_alert(transaction) is False

    def test_alert_ids_are_unique(self, simulator):
        transaction = simulator._build_transaction(_account())
        ids = {simulator._build_alert(transaction, _account()).alert_id for _ in range(200)}

        assert len(ids) == 200
        assert all(i.startswith(ALERT_PREFIX) for i in ids)

    def test_alert_is_derived_from_the_transaction_not_invented(self, simulator):
        transaction = simulator._build_transaction(_account())
        transaction.amount = 48_000.0
        transaction.transaction_type = "WIRE"

        alert = simulator._build_alert(transaction, _account())

        assert alert.transaction_id == transaction.transaction_id
        assert alert.account_id == transaction.account_id
        assert alert.customer_id == "CUST-MOCK-001"
        assert "48,000.00" in alert.reason
        assert alert.status == "OPEN"

    def test_severity_and_risk_scale_with_amount(self, simulator):
        low = simulator._build_transaction(_account())
        low.amount = _LARGE_TXN_THRESHOLD + 100
        high = simulator._build_transaction(_account())
        high.amount = _LARGE_TXN_THRESHOLD * 6

        low_alert = simulator._build_alert(low, _account())
        high_alert = simulator._build_alert(high, _account())

        assert high_alert.severity == "HIGH"
        assert low_alert.severity == "LOW"
        assert 0.0 <= low_alert.risk_score < high_alert.risk_score <= 1.0

    def test_one_alert_accompanies_at_most_one_transaction(self, simulator):
        import asyncio

        session = _Session([_account()])
        asyncio.run(simulator.simulate_once(session))

        transactions = [o for o in session.added if isinstance(o, MockBankTransaction)]
        alerts = [o for o in session.added if isinstance(o, MockBankAlert)]
        assert len(transactions) == 1
        assert len(alerts) <= 1
        if alerts:
            assert alerts[0].transaction_id == transactions[0].transaction_id

    def test_a_concurrent_duplicate_is_dropped_rather_than_raised_twice(self, simulator):
        import asyncio

        from sqlalchemy.exc import IntegrityError

        session = _Session([_account()])
        session.commit = AsyncMock(side_effect=IntegrityError("dup", None, Exception()))
        session.rollback = AsyncMock()

        transaction, alert = asyncio.run(simulator.simulate_once(session))

        assert transaction is None and alert is None
        session.rollback.assert_awaited_once()
