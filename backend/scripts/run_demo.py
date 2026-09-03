"""AI Investigation Copilot — Demo Runner.

Standalone script that builds a realistic fraud case, executes the
full investigation pipeline, and prints a clean summary followed
by the complete JSON state.

Usage:
    python scripts/run_demo.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure the backend root is on sys.path so absolute imports work
# regardless of where the script is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.workflow import run_investigation
from app.schemas import (
    BeneficiaryInfo,
    CaseInput,
    CustomerProfile,
    DeviceInfo,
    MerchantInfo,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


def build_demo_case() -> tuple[str, CaseInput]:
    """Build a realistic dummy fraud investigation case."""

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

    return "CASE-2025-08-00347", case_input


def print_separator(title: str = "") -> None:
    """Print a separator line with an optional centred title."""
    width = 60
    if title:
        print(f"\n{'=' * width}")
        print(f"  {title}")
        print(f"{'=' * width}")
    else:
        print(f"{'=' * width}")


        print(f"\n{'=' * width}")


async def main() -> None:
    """Run the full investigation demo."""

    print_separator("AI Investigation Copilot")
    print("\n  Running Investigation...\n")

    # Build case
    case_id, case_input = build_demo_case()
    initial_state = create_initial_state(case_id=case_id, case_input=case_input)

    # 4. Run the pipeline
    print("\nRunning AI Investigation Pipeline...")
    start_time = time.time()

    # Note: run_investigation is an async function
    result = await run_investigation(initial_state)

    duration = time.time() - start_time

    # Agent status checks
    agents = [
        ("Context Agent", result.context_intelligence),
        ("Investigation Reasoning", result.investigation_reasoning),
        ("Compliance Validation", result.evidence_compliance_validation),
        ("Decision Optimization", result.decision_optimization),
        ("Reporting", result.investigation_report),
    ]

    for name, agent_output in agents:
        if agent_output is not None and agent_output.status.value == "COMPLETED":
            print(f"  + {name}")
        else:
            print(f"  - {name} (not completed)")

    # Recommended Decision
    if result.decision_optimization and result.decision_optimization.recommended_decision:
        print_separator("Recommended Decision")
        print(f"\n  {result.decision_optimization.recommended_decision.value}\n")

        if result.decision_optimization.decision_rationale:
            print(f"  {result.decision_optimization.decision_rationale}\n")

    # Executive Summary
    if result.investigation_report and result.investigation_report.executive_summary:
        print_separator("Executive Summary")
        print(f"\n  {result.investigation_report.executive_summary}\n")

    # Hypotheses
    if result.investigation_reasoning and result.investigation_reasoning.hypotheses:
        print_separator("Hypotheses")
        for hyp in result.investigation_reasoning.hypotheses:
            print(f"\n  [{hyp.confidence:.0%}] {hyp.title}")
            print(f"        {hyp.description[:100]}...")

    # Compliance
    if result.evidence_compliance_validation and result.evidence_compliance_validation.compliance_mappings:
        print_separator("Compliance Findings")
        for cm in result.evidence_compliance_validation.compliance_mappings:
            violated = "VIOLATED" if cm.is_violated else "OK"
            print(f"\n  [{cm.severity.value}] {cm.regulation_name} - {violated}")

    # Timeline
    if (
        result.investigation_report
        and result.investigation_report.graphs
        and result.investigation_report.graphs.investigation_timeline
    ):
        print_separator("Investigation Timeline")
        for event in result.investigation_report.graphs.investigation_timeline:
            stage_label = event.stage.value if event.stage else "N/A"
            print(f"  {event.timestamp.strftime('%H:%M:%S')}  [{stage_label}]  {event.event_name}")

    # Final stage
    print_separator("Result")
    print(f"\n  Case ID:       {result.case_id}")
    print(f"  Final Stage:   {result.current_stage.value}")
    print(f"  Errors:        {len(result.errors)}")

    # Full JSON
    print_separator("Complete InvestigationState (JSON)")
    print(json.dumps(result.model_dump(mode="json"), indent=2))

    print_separator()
    print("  Investigation complete.\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
