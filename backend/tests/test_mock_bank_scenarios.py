"""Round 6 deterministic Mock Bank scenario coverage."""

import pytest

from app.mock_bank.generator import (
    MockBankScenario,
    generate_investigation_data,
)


def _dump(data):
    return {
        "customer": data.customer.model_dump(mode="json"),
        "account": data.account.model_dump(mode="json"),
        "transactions": [txn.model_dump(mode="json") for txn in data.transactions],
        "alert_reason": data.alert_reason,
    }


def test_high_risk_scenario_is_deterministic_and_distinct() -> None:
    first = generate_investigation_data(42, MockBankScenario.HIGH_RISK)
    second = generate_investigation_data(42, "high-risk")

    assert _dump(first) == _dump(second)
    assert first.customer.risk_rating == "HIGH"
    assert first.account.balance < max(txn.amount for txn in first.transactions)
    assert all(txn.amount > 10_000 for txn in first.transactions)


def test_low_risk_scenario_is_deterministic_and_distinct() -> None:
    first = generate_investigation_data(42, MockBankScenario.LOW_RISK)
    second = generate_investigation_data(42, MockBankScenario.LOW_RISK)

    assert _dump(first) == _dump(second)
    assert first.customer.risk_rating == "LOW"
    assert all(txn.amount < 10_000 for txn in first.transactions)
    assert first.account.balance > sum(txn.amount for txn in first.transactions)


def test_missing_data_scenario_is_intentional_and_deterministic() -> None:
    first = generate_investigation_data(42, MockBankScenario.MISSING_DATA)
    second = generate_investigation_data(42, MockBankScenario.MISSING_DATA)

    assert _dump(first) == _dump(second)
    assert first.customer.email is None
    assert first.customer.risk_rating is None
    assert first.account.opened_at is None
    assert len(first.transactions) < 5
    assert all(txn.description is None and txn.location is None for txn in first.transactions)


def test_scenarios_are_materially_different() -> None:
    high = generate_investigation_data(42, MockBankScenario.HIGH_RISK)
    low = generate_investigation_data(42, MockBankScenario.LOW_RISK)
    missing = generate_investigation_data(42, MockBankScenario.MISSING_DATA)

    assert _dump(high) != _dump(low)
    assert _dump(low) != _dump(missing)
    assert _dump(high) != _dump(missing)


def test_invalid_scenario_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown Mock Bank scenario"):
        generate_investigation_data(42, "not-a-scenario")
