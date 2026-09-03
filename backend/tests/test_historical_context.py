"""Tests for Stage 2 Historical Context Integration."""

import pytest
from datetime import datetime, timedelta, timezone

from app.schemas.investigation_state import (
    Transaction,
    CaseInput,
    create_initial_state,
    CurrentStage,
)
from app.agents.context_agent import context_agent
from app.graph.workflow import run_investigation

@pytest.fixture
def test_state():
    case_input = CaseInput(
        transactions=[
            Transaction(
                transaction_id="TXN-TEST-CURR-01",
                amount=50000.0,
                currency="USD",
                timestamp=datetime.now(timezone.utc),
                sender_account="ACC-MOCK-001",
                receiver_account="UNKNOWN-OFFSHORE",
                transaction_type="WIRE",
                channel="ONLINE",
                location="Dubai, UAE",
            )
        ],
        alert_reason="High risk threshold"
    )
    return create_initial_state("CASE-TEST-HIST", case_input)


@pytest.mark.asyncio
async def test_historical_baseline_empty():
    """If no history is found, gracefully fallback."""
    case_input = CaseInput(
        transactions=[
            Transaction(
                transaction_id="TXN-NEW",
                amount=50.0,
                currency="USD",
                timestamp=datetime.now(timezone.utc),
                sender_account="ACC-NONEXISTENT",
                receiver_account="UNKNOWN",
                transaction_type="POS",
                channel="IN_PERSON",
                location="NY",
            )
        ]
    )
    state = create_initial_state("CASE-EMPTY", case_input)
    result = await context_agent(state)
    ci = result["context_intelligence"]
    
    assert ci.historical_baseline is not None
    assert ci.historical_baseline.transaction_count == 0


@pytest.mark.asyncio
async def test_historical_baseline_and_deviations(test_state):
    """If history is found, baseline is populated and deviations are generated."""
    # ACC-MOCK-001 is seeded by the mock bank seed script (idempotent).
    # If the DB is populated, we will see its baseline.
    result = await context_agent(test_state)
    ci = result["context_intelligence"]

    if ci.historical_baseline.transaction_count > 0:
        # We connected to the DB and got history.
        assert ci.historical_baseline.maximum_amount > 0
        assert "WIRE" in ci.historical_baseline.common_types or "ACH" in ci.historical_baseline.common_types
        
        # Current transaction is $50,000 to UNKNOWN-OFFSHORE from Dubai.
        # This should trigger deviations (high amount, new location, new counterparty).
        deviations = [a for a in ci.anomalies if "Deviation:" in a.description]
        assert len(deviations) > 0
        desc = deviations[0].description
        assert "offshore" in desc.lower() or "dubai" in desc.lower() or "amount" in desc.lower()
