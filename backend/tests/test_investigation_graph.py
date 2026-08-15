"""Test: Full investigation pipeline validation.

Creates a realistic dummy fraud case, runs the complete LangGraph
pipeline, and validates every agent output section.
"""

import json
from datetime import datetime

from app.graph.workflow import run_investigation
from app.schemas import (
    AgentStatus,
    BeneficiaryInfo,
    CaseInput,
    CurrentStage,
    CustomerProfile,
    DeviceInfo,
    InvestigationState,
    MerchantInfo,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


def test_full_investigation_pipeline() -> None:
    """Run the complete pipeline with a realistic fraud case and validate.

    Scenario:
      - $48,500 wire to a first-time beneficiary
      - High-risk crypto exchange in the Cayman Islands
      - Unknown device geolocated in Romania (customer in New York)
      - Recently opened merchant account
    """

    # -- Build realistic case input --
    transaction = Transaction(
        transaction_id="TXN-2025-0819-00347",
        amount=48_500.00,
        currency="USD",
        timestamp=datetime(2025, 8, 19, 14, 32, 11),
        sender_account="ACC-US-8821004",
        receiver_account="ACC-KY-5529183",
        transaction_type="WIRE",
        channel="ONLINE",
        description="Investment deposit - CryptoVault Holdings",
        location="New York, US",
    )

    customer = CustomerProfile(
        customer_id="CUST-90215",
        name="James Whitfield",
        email="j.whitfield@email.com",
        phone="+1-212-555-0173",
        address="350 Park Avenue, New York, NY 10022",
        date_of_birth="1983-04-12",
        account_open_date="2019-06-15",
        risk_rating="MEDIUM",
        occupation="Portfolio Manager",
        nationality="US",
    )

    merchant = MerchantInfo(
        merchant_id="MERCH-KY-7741",
        name="CryptoVault Holdings Ltd.",
        category="Cryptocurrency Exchange",
        country="KY",
        risk_level=SeverityLevel.HIGH,
        registered_date="2023-01-20",
    )

    device = DeviceInfo(
        device_id="DEV-UNKNOWN-8812",
        device_type="MOBILE",
        ip_address="185.220.101.34",
        geolocation="Bucharest, Romania",
        is_known_device=False,
        os="Android 14",
        browser="Chrome Mobile 126",
    )

    beneficiary = BeneficiaryInfo(
        beneficiary_id="BEN-KY-3319",
        name="CryptoVault Holdings Ltd.",
        account_number="ACC-KY-5529183",
        bank_name="Cayman National Bank",
        country="KY",
        is_new=True,
        relationship="Investment Platform",
    )

    supporting_doc = SupportingDocument(
        document_id="DOC-2025-0441",
        document_type="BANK_STATEMENT",
        file_name="whitfield_aug2025_statement.pdf",
        uploaded_at=datetime(2025, 8, 19, 15, 0, 0),
        summary="Monthly statement showing irregular outbound transfers.",
    )

    case_input = CaseInput(
        transactions=[transaction],
        customer_profile=customer,
        merchant_info=merchant,
        device_info=device,
        beneficiary_info=beneficiary,
        supporting_documents=[supporting_doc],
        alert_reason=(
            "Large wire transfer to a first-time beneficiary in a high-risk "
            "jurisdiction, initiated from an unknown device with geolocation "
            "mismatch (device in Romania, customer based in New York)."
        ),
    )

    initial_state = create_initial_state(
        case_id="CASE-2025-08-00347",
        case_input=case_input,
    )

    # -- Execute pipeline --
    result: InvestigationState = run_investigation(initial_state)

    # -- Pretty-print full state --
    print(json.dumps(result.model_dump(mode="json"), indent=2))

    # -- Validate result type and stage --
    assert isinstance(result, InvestigationState)
    assert result.current_stage == CurrentStage.DONE
    print("\n[OK] Context Agent Complete")

    # -- Context Intelligence --
    assert result.context_intelligence is not None
    assert result.context_intelligence.status == AgentStatus.COMPLETED
    print("[OK] Reasoning Agent Complete")

    # -- Investigation Reasoning --
    assert result.investigation_reasoning is not None
    assert result.investigation_reasoning.status == AgentStatus.COMPLETED
    assert len(result.investigation_reasoning.hypotheses) >= 1
    print("[OK] Compliance Agent Complete")

    # -- Evidence & Compliance Validation --
    assert result.evidence_compliance_validation is not None
    assert result.evidence_compliance_validation.status == AgentStatus.COMPLETED
    print("[OK] Decision Agent Complete")

    # -- Decision Optimization --
    assert result.decision_optimization is not None
    assert result.decision_optimization.status == AgentStatus.COMPLETED
    assert len(result.decision_optimization.decision_options) == 4
    # Round 3: recommendation belongs to Round 4.
    # assert result.decision_optimization.recommended_decision is not None
    print("[OK] Reporting Agent Complete")

    # -- Investigation Report --
    assert result.investigation_report is not None
    assert result.investigation_report.status == AgentStatus.COMPLETED

    # Report graphs
    graphs = result.investigation_report.graphs
    assert graphs is not None
    assert graphs.entity_relationship_graph is not None
    assert graphs.reasoning_graph is not None
    assert graphs.decision_comparison_graph is not None
    assert len(graphs.investigation_timeline) > 0

    # -- Timestamps and errors --
    assert result.created_at is not None
    assert result.updated_at is not None
    assert result.errors == []

    print("[OK] Investigation Completed Successfully")


if __name__ == "__main__":
    test_full_investigation_pipeline()
