"""Test: Investigation State creation with a realistic fraud case."""

import json
from datetime import datetime

from app.schemas import (
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


def test_create_initial_state_realistic_case() -> None:
    """Create an InvestigationState from a realistic high-risk case.

    Scenario:
      - Large wire transfer of $48,500 to a first-time beneficiary
      - High-risk merchant (crypto exchange in the Cayman Islands)
      - Unknown device with a mismatched geolocation
      - Customer has a MEDIUM risk rating
    """

    transaction = Transaction(
        transaction_id="TXN-2025-0819-00347",
        amount=48_500.00,
        currency="USD",
        timestamp=datetime(2025, 8, 19, 14, 32, 11),
        sender_account="ACC-US-8821004",
        receiver_account="ACC-KY-5529183",
        transaction_type="WIRE",
        channel="ONLINE",
        description="Investment deposit – CryptoVault Holdings",
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

    # --- Create the initial state ---
    state: InvestigationState = create_initial_state(
        case_id="CASE-2025-08-00347",
        case_input=case_input,
    )

    # --- Pretty-print the resulting JSON ---
    print(json.dumps(state.model_dump(mode="json"), indent=2))

    # --- Assertions ---
    assert isinstance(state, InvestigationState)
    assert state.current_stage == CurrentStage.INTAKE
    assert state.case_id == "CASE-2025-08-00347"
    assert state.context_intelligence is None
    assert state.investigation_reasoning is None
    assert state.evidence_compliance_validation is None
    assert state.decision_optimization is None
    assert state.investigation_report is None
    assert state.errors == []
    assert len(state.case_input.transactions) == 1
    assert state.case_input.transactions[0].amount == 48_500.00
    assert state.case_input.beneficiary_info is not None
    assert state.case_input.beneficiary_info.is_new is True
    assert state.case_input.device_info is not None
    assert state.case_input.device_info.is_known_device is False

    print("\n[OK] InvestigationState created and validated successfully.")


if __name__ == "__main__":
    test_create_initial_state_realistic_case()
