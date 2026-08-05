"""Test: Workflow structure validation.

Verifies that the LangGraph investigation pipeline compiles, executes
without crashing, and returns a valid InvestigationState. Does NOT
perform content validation — that belongs in test_investigation_graph.py.
"""

from datetime import datetime

from app.graph.workflow import run_investigation
from app.schemas import (
    CaseInput,
    CustomerProfile,
    InvestigationState,
    Transaction,
    create_initial_state,
)


def test_workflow_structure() -> None:
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

    initial_state = create_initial_state(
        case_id="CASE-STRUCT-001",
        case_input=case_input,
    )

    # --- Execute ---
    result = run_investigation(initial_state)

    # --- Structure assertions only ---
    assert isinstance(result, InvestigationState), (
        "run_investigation must return an InvestigationState"
    )
    assert result.case_id == "CASE-STRUCT-001"

    print("[OK] Graph compiled successfully.")
    print("[OK] Workflow executed without crashing.")
    print("[OK] run_investigation() returned an InvestigationState.")


if __name__ == "__main__":
    test_workflow_structure()
