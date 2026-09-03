"""Compression measurement: compare OLD vs NEW prompt sizes for all three agents.

This test module computes exact character counts and estimated token counts
for the Reasoning, Compliance, and Decision agents, comparing the old
full-dump approach against the new compact approach.

NOTE: Token count is estimated at ~4 characters per token (standard BPE
approximation). Actual LLM tokenisation may vary.
"""

import json
from datetime import datetime

import pytest

from app.agents.reasoning_agent import (
    _build_compact_case as reasoning_compact_case,
    _build_compact_context as reasoning_compact_context,
    _build_prompt as reasoning_build_prompt,
)
from app.agents.compliance_agent import (
    _build_compact_case as compliance_compact_case,
    _build_compact_context as compliance_compact_context,
    _build_compact_reasoning as compliance_compact_reasoning,
    _build_prompt as compliance_build_prompt,
)
from app.agents.decision_agent import (
    _build_compact_case_context as decision_compact_case_context,
    _build_compact_compliance as decision_compact_compliance,
    _build_prompt as decision_build_prompt,
)
from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    BeneficiaryInfo,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CustomerProfile,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    DetectedAnomaly,
    DeviceInfo,
    EvidenceComplianceValidation,
    HistoricalBaseline,
    Hypothesis,
    InvestigationReasoning,
    MerchantInfo,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)

CHARS_PER_TOKEN = 4  # Standard BPE approximation


def _full_state():
    """Build a fully-populated state for measurement."""
    case_input = CaseInput(
        alert_reason="Suspicious cross-border wire to high-risk jurisdiction",
        customer_profile=CustomerProfile(
            customer_id="CUST-MEAS-001",
            name="Measurement Tester",
            email="measure@example.com",
            phone="+1-555-0200",
            address="456 Measure Avenue",
            date_of_birth="1985-03-15",
            account_open_date="2019-01-15",
            risk_rating="HIGH",
            occupation="Financial Analyst",
            nationality="US",
        ),
        merchant_info=MerchantInfo(
            merchant_id="MERCH-MEAS-001",
            name="CryptoExchange Inc.",
            category="Cryptocurrency Exchange",
            country="KY",
            risk_level=SeverityLevel.HIGH,
            registered_date="2022-06-01",
        ),
        device_info=DeviceInfo(
            device_id="DEV-MEAS-001",
            device_type="MOBILE",
            ip_address="10.0.0.1",
            geolocation="Bucharest, Romania",
            is_known_device=False,
            os="iOS 18",
            browser="Safari Mobile",
        ),
        beneficiary_info=BeneficiaryInfo(
            beneficiary_id="BEN-MEAS-001",
            name="Offshore Holdings Ltd.",
            account_number="ACC-KY-MEAS",
            bank_name="Grand Cayman Trust",
            country="KY",
            is_new=True,
            relationship="Investment Platform",
        ),
        transactions=[
            Transaction(
                transaction_id="TXN-MEAS-001",
                amount=48500.0,
                currency="USD",
                timestamp=datetime(2026, 7, 15, 14, 30),
                sender_account="ACC-SRC-MEAS",
                receiver_account="ACC-DST-MEAS",
                transaction_type="WIRE",
                channel="ONLINE",
                description="Investment deposit - CryptoVault",
                location="New York, US",
            ),
            Transaction(
                transaction_id="TXN-MEAS-002",
                amount=15000.0,
                currency="USD",
                timestamp=datetime(2026, 7, 16, 9, 0),
                sender_account="ACC-SRC-MEAS",
                receiver_account="ACC-DST-MEAS-2",
                transaction_type="WIRE",
                channel="ONLINE",
                description="Supplementary transfer",
                location="New York, US",
            ),
        ],
        supporting_documents=[
            SupportingDocument(
                document_id="DOC-MEAS-001",
                document_type="BANK_STATEMENT",
                file_name="statement_july.pdf",
                file_url="https://example.com/docs/statement_july.pdf",
                uploaded_at=datetime(2026, 7, 15, 15, 0),
                summary="Monthly statement showing irregular wire transfers to offshore accounts.",
                extracted_text="Account holder: Measurement Tester. Multiple wire transfers detected to Cayman Islands beneficiaries. Total outflows exceed $63,500 in July.",
                evidence_references=["EVID-MEAS-001", "EVID-MEAS-002"],
                extracted_transactions=["TXN-MEAS-001", "TXN-MEAS-002"],
            ),
        ],
    )
    state = create_initial_state("CASE-MEAS-001", case_input)
    return state.model_copy(update={
        "context_intelligence": ContextIntelligence(
            status=AgentStatus.COMPLETED,
            context_summary="High-risk cross-border transaction pattern detected with multiple transfers to first-time offshore beneficiary.",
            key_indicators=[
                "Large cross-border transfer ($48,500 USD)",
                "First-time beneficiary in high-risk jurisdiction (KY)",
                "Multiple transfers within 24 hours totalling $63,500",
            ],
            historical_baseline=HistoricalBaseline(
                transaction_count=47,
                average_amount=3250.0,
                maximum_amount=12000.0,
                common_types=["ACH", "CARD"],
                common_channels=["ONLINE"],
                common_locations=["New York, US"],
                common_counterparties=["ACC-US-1234567", "ACC-US-7654321"],
            ),
            anomalies=[
                DetectedAnomaly(
                    anomaly_id="ANOM-MEAS-001",
                    anomaly_type=AnomalyType.POINT,
                    severity=SeverityLevel.HIGH,
                    description="Transaction amount $48,500 exceeds historical maximum ($12,000) by 304%",
                    related_transactions=["TXN-MEAS-001"],
                ),
                DetectedAnomaly(
                    anomaly_id="ANOM-MEAS-002",
                    anomaly_type=AnomalyType.BEHAVIORAL,
                    severity=SeverityLevel.MEDIUM,
                    description="Two high-value transfers within 24h to new beneficiary — unusual velocity",
                    related_transactions=["TXN-MEAS-001", "TXN-MEAS-002"],
                ),
            ],
            risk_score=0.91,
        ),
        "investigation_reasoning": InvestigationReasoning(
            status=AgentStatus.COMPLETED,
            hypotheses=[
                Hypothesis(
                    hypothesis_id="HYP-MEAS-001",
                    title="Potential Account Takeover",
                    description="Unknown mobile device from Romania initiating large transfers to Cayman beneficiary suggests credential compromise.",
                    confidence=0.72,
                    supporting_evidence=["TXN-MEAS-001", "TXN-MEAS-002", "ANOM-MEAS-001"],
                    contradicting_evidence=["DOC-MEAS-001"],
                ),
                Hypothesis(
                    hypothesis_id="HYP-MEAS-002",
                    title="Authorized High-Risk Investment",
                    description="Customer may be making legitimate but high-risk cryptocurrency investment through an offshore exchange.",
                    confidence=0.45,
                    supporting_evidence=["DOC-MEAS-001"],
                    contradicting_evidence=["ANOM-MEAS-001", "ANOM-MEAS-002"],
                ),
            ],
            reasoning_summary="Two competing hypotheses generated: account takeover vs authorized investment. Evidence favours compromise scenario.",
            recommended_actions=[
                "Verify customer identity via phone callback",
                "Contact customer to confirm transaction intent",
                "Review device fingerprint history",
            ],
        ),
        "evidence_compliance_validation": EvidenceComplianceValidation(
            status=AgentStatus.COMPLETED,
            compliance_mappings=[
                ComplianceMapping(
                    regulation_id="REG-MEAS-001",
                    regulation_name="CTR Threshold Monitoring",
                    description="Combined transfers ($63,500) exceed $10,000 CTR threshold — CTR filing required",
                    is_violated=False,
                    severity=SeverityLevel.HIGH,
                    evidence_references=["TXN-MEAS-001", "TXN-MEAS-002"],
                ),
                ComplianceMapping(
                    regulation_id="REG-MEAS-002",
                    regulation_name="EDD for High-Risk Jurisdictions",
                    description="Beneficiary in Cayman Islands (FATF grey-list adjacent) requires Enhanced Due Diligence",
                    is_violated=False,
                    severity=SeverityLevel.MEDIUM,
                    evidence_references=["BEN-MEAS-001"],
                ),
            ],
            evidence_gaps=[
                "No source-of-funds documentation available",
                "No KYC refresh within 12 months",
            ],
            validation_summary="Two compliance concerns identified; CTR threshold exceeded, EDD required for Cayman beneficiary.",
        ),
    })


class TestReasoningMeasurement:
    """Measure Reasoning Agent prompt compression."""

    def test_reasoning_prompt_reduction(self):
        state = _full_state()

        # OLD approach
        old_case = state.case_input.model_dump_json(indent=2)
        old_context = state.context_intelligence.model_dump_json(indent=2)
        old_data_size = len(old_case) + len(old_context)

        # NEW approach
        new_case = reasoning_compact_case(state)
        new_context = reasoning_compact_context(state)
        new_data_size = len(new_case) + len(new_context)

        reduction_pct = (1 - new_data_size / old_data_size) * 100
        old_tokens = old_data_size // CHARS_PER_TOKEN
        new_tokens = new_data_size // CHARS_PER_TOKEN
        token_savings = old_tokens - new_tokens

        print(f"\n{'='*60}")
        print(f"REASONING AGENT COMPRESSION MEASUREMENT")
        print(f"{'='*60}")
        print(f"OLD case data:    {len(old_case):>6} chars")
        print(f"NEW case data:    {len(new_case):>6} chars")
        print(f"OLD context data: {len(old_context):>6} chars")
        print(f"NEW context data: {len(new_context):>6} chars")
        print(f"{'-'*60}")
        print(f"OLD total data:   {old_data_size:>6} chars  (~{old_tokens} tokens)")
        print(f"NEW total data:   {new_data_size:>6} chars  (~{new_tokens} tokens)")
        print(f"REDUCTION:        {old_data_size - new_data_size:>6} chars  ({reduction_pct:.1f}%)")
        print(f"TOKEN SAVINGS:    ~{token_savings} tokens")
        print(f"{'='*60}")

        assert new_data_size < old_data_size
        assert reduction_pct >= 25, f"Only {reduction_pct:.1f}% reduction"


class TestComplianceMeasurement:
    """Measure Compliance Agent prompt compression."""

    def test_compliance_prompt_reduction(self):
        state = _full_state()

        # OLD approach
        old_case = state.case_input.model_dump_json(indent=2)
        old_context = state.context_intelligence.model_dump_json(indent=2)
        old_reasoning = state.investigation_reasoning.model_dump_json(indent=2)
        old_data_size = len(old_case) + len(old_context) + len(old_reasoning)

        # NEW approach
        new_case = compliance_compact_case(state)
        new_context = compliance_compact_context(state)
        new_reasoning = compliance_compact_reasoning(state)
        new_data_size = len(new_case) + len(new_context) + len(new_reasoning)

        reduction_pct = (1 - new_data_size / old_data_size) * 100
        old_tokens = old_data_size // CHARS_PER_TOKEN
        new_tokens = new_data_size // CHARS_PER_TOKEN
        token_savings = old_tokens - new_tokens

        print(f"\n{'='*60}")
        print(f"COMPLIANCE AGENT COMPRESSION MEASUREMENT")
        print(f"{'='*60}")
        print(f"OLD case data:      {len(old_case):>6} chars")
        print(f"NEW case data:      {len(new_case):>6} chars")
        print(f"OLD context data:   {len(old_context):>6} chars")
        print(f"NEW context data:   {len(new_context):>6} chars")
        print(f"OLD reasoning data: {len(old_reasoning):>6} chars")
        print(f"NEW reasoning data: {len(new_reasoning):>6} chars")
        print(f"{'-'*60}")
        print(f"OLD total data:     {old_data_size:>6} chars  (~{old_tokens} tokens)")
        print(f"NEW total data:     {new_data_size:>6} chars  (~{new_tokens} tokens)")
        print(f"REDUCTION:          {old_data_size - new_data_size:>6} chars  ({reduction_pct:.1f}%)")
        print(f"TOKEN SAVINGS:      ~{token_savings} tokens")
        print(f"{'='*60}")

        assert new_data_size < old_data_size
        assert reduction_pct >= 25, f"Only {reduction_pct:.1f}% reduction"


class TestDecisionMeasurement:
    """Measure Decision Agent prompt compression (existing, for comparison)."""

    def test_decision_prompt_reduction(self):
        state = _full_state()

        # OLD approach
        old_case = state.case_input.model_dump_json(indent=2)
        old_context = (
            state.context_intelligence.model_dump_json(indent=2)
            if state.context_intelligence else "{}"
        )
        old_data_size = len(old_case) + len(old_context)

        # NEW approach (Decision uses _build_compact_case_context which
        # combines case + context into a single compact JSON)
        new_combined = decision_compact_case_context(state)
        new_data_size = len(new_combined)

        reduction_pct = (1 - new_data_size / old_data_size) * 100
        old_tokens = old_data_size // CHARS_PER_TOKEN
        new_tokens = new_data_size // CHARS_PER_TOKEN
        token_savings = old_tokens - new_tokens

        print(f"\n{'='*60}")
        print(f"DECISION AGENT COMPRESSION MEASUREMENT")
        print(f"{'='*60}")
        print(f"OLD case+context: {old_data_size:>6} chars  (~{old_tokens} tokens)")
        print(f"NEW case+context: {new_data_size:>6} chars  (~{new_tokens} tokens)")
        print(f"REDUCTION:        {old_data_size - new_data_size:>6} chars  ({reduction_pct:.1f}%)")
        print(f"TOKEN SAVINGS:    ~{token_savings} tokens")
        print(f"{'='*60}")

        assert new_data_size < old_data_size


class TestCombinedSummary:
    """Print a combined summary of all three agents."""

    def test_combined_reduction_summary(self):
        state = _full_state()

        # Reasoning
        r_old = len(state.case_input.model_dump_json(indent=2)) + len(
            state.context_intelligence.model_dump_json(indent=2))
        r_new = len(reasoning_compact_case(state)) + len(reasoning_compact_context(state))

        # Compliance
        c_old = (len(state.case_input.model_dump_json(indent=2)) +
                 len(state.context_intelligence.model_dump_json(indent=2)) +
                 len(state.investigation_reasoning.model_dump_json(indent=2)))
        c_new = (len(compliance_compact_case(state)) +
                 len(compliance_compact_context(state)) +
                 len(compliance_compact_reasoning(state)))

        # Decision
        d_old = (len(state.case_input.model_dump_json(indent=2)) +
                 len(state.context_intelligence.model_dump_json(indent=2)))
        d_new = len(decision_compact_case_context(state))

        total_old = r_old + c_old + d_old
        total_new = r_new + c_new + d_new

        print(f"\n{'='*60}")
        print(f"COMBINED COMPRESSION SUMMARY (ALL 3 LLM AGENTS)")
        print(f"{'='*60}")
        print(f"{'Agent':<15} {'OLD':>8} {'NEW':>8} {'Saved':>8} {'Reduction':>10}")
        print(f"{'-'*60}")
        print(f"{'Reasoning':<15} {r_old:>8} {r_new:>8} {r_old-r_new:>8} {(1-r_new/r_old)*100:>9.1f}%")
        print(f"{'Compliance':<15} {c_old:>8} {c_new:>8} {c_old-c_new:>8} {(1-c_new/c_old)*100:>9.1f}%")
        print(f"{'Decision':<15} {d_old:>8} {d_new:>8} {d_old-d_new:>8} {(1-d_new/d_old)*100:>9.1f}%")
        print(f"{'-'*60}")
        print(f"{'TOTAL':<15} {total_old:>8} {total_new:>8} {total_old-total_new:>8} {(1-total_new/total_old)*100:>9.1f}%")
        print(f"{'Est. tokens':<15} {total_old//4:>8} {total_new//4:>8} {(total_old-total_new)//4:>8}")
        print(f"{'='*60}")

        assert total_new < total_old
