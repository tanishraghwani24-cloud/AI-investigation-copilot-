"""Test: Workflow structure validation.

Verifies that the LangGraph investigation pipeline compiles, executes
without crashing, and returns a valid InvestigationState. Does NOT
perform content validation — that belongs in test_investigation_graph.py.
"""

from datetime import datetime

from app.graph.workflow import run_investigation
from app.schemas.investigation_state import (
    CaseInput,
    CurrentStage,
    CustomerProfile,
    InvestigationState,
    Transaction,
    create_initial_state,
)
import pytest


def _make_minimal_state() -> InvestigationState:
    """Verify graph compilation, execution, and return type."""

    transaction = Transaction(
        transaction_id="TXN-STRUCT-001",
        amount=1000.00,
        currency="USD",
        timestamp=datetime(2025, 1, 15, 10, 0, 0),
        sender_account="ACC-SRC-001",
        receiver_account="ACC-DST-001",
        transaction_type="WIRE",
        channel="ONLINE",
    )

    case_input = CaseInput(
        transactions=[transaction],
        customer_profile=CustomerProfile(
            customer_id="CUST-STRUCT-001",
            name="Structure Test Customer",
        ),
        alert_reason="Automated test - workflow structure validation.",
    )

    return create_initial_state(
        case_id="CASE-STRUCT-001",
        case_input=case_input,
    )


@pytest.mark.asyncio
async def test_workflow_structure() -> None:
    """Verify that the full graph executes without crashing and returns an InvestigationState."""
    print("\n[INFO] Starting test_workflow_structure...")
    initial_state = _make_minimal_state()

    result = await run_investigation(initial_state)

    assert isinstance(result, InvestigationState)
    assert result.current_stage == CurrentStage.DONE

    assert result.context_intelligence is not None
    assert result.investigation_reasoning is not None
    assert result.evidence_compliance_validation is not None
    assert result.decision_optimization is not None
    assert result.investigation_report is not None

    print("[OK] run_investigation() returned an InvestigationState.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_workflow_structure())
