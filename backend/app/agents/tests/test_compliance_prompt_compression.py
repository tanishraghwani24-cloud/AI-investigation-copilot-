"""Tests for Compliance Agent context compression.

Proves that:
1. The compressed prompt is smaller than the original full-dump prompt.
2. The compressed prompt preserves all transaction IDs and exact amounts.
3. The compressed prompt preserves customer, merchant, beneficiary identity.
4. The compressed prompt preserves anomaly IDs and descriptions.
5. The compressed prompt preserves risk scores and key indicators.
6. The compressed prompt preserves alert reason.
7. The compressed prompt preserves hypothesis IDs, confidence, evidence.
8. The compressed prompt preserves document evidence references.
9. Unnecessary fields (customer PII, device browser/OS/IP,
   historical_baseline, reasoning status/summary) are excluded.
10. The compact builder handles sparse/missing state gracefully.
"""

import json
from datetime import datetime

import pytest

from app.agents.compliance_agent import (
    _build_compact_case,
    _build_compact_context,
    _build_compact_reasoning,
    _build_prompt,
)
from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    BeneficiaryInfo,
    CaseInput,
    ContextIntelligence,
    CustomerProfile,
    DetectedAnomaly,
    DeviceInfo,
    HistoricalBaseline,
    Hypothesis,
    InvestigationReasoning,
    MerchantInfo,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


# ── Fixtures ────────────────────────────────────────────────────────────


def _full_state():
    """Build a realistic state with all fields populated."""
    case_input = CaseInput(
        alert_reason="Suspicious cross-border wire to high-risk jurisdiction",
        customer_profile=CustomerProfile(
            customer_id="CUST-COMP-001",
            name="Compliance Tester",
            email="tester@example.com",
            phone="+1-555-0100",
            address="123 Test Street",
            date_of_birth="1990-01-01",
            account_open_date="2020-06-01",
            risk_rating="HIGH",
            occupation="Software Engineer",
            nationality="US",
        ),
        merchant_info=MerchantInfo(
            merchant_id="MERCH-COMP-001",
            name="TestMerchant Ltd.",
            category="Cryptocurrency Exchange",
            country="KY",
            risk_level=SeverityLevel.HIGH,
            registered_date="2023-01-01",
        ),
        device_info=DeviceInfo(
            device_id="DEV-COMP-001",
            device_type="MOBILE",
            ip_address="192.168.1.1",
            geolocation="Bucharest, Romania",
            is_known_device=False,
            os="Android 14",
            browser="Chrome Mobile 126",
        ),
        beneficiary_info=BeneficiaryInfo(
            beneficiary_id="BEN-COMP-001",
            name="Offshore Corp Ltd.",
            account_number="ACC-KY-99999",
            bank_name="Cayman National Bank",
            country="KY",
            is_new=True,
            relationship="Investment Platform",
        ),
        transactions=[
            Transaction(
                transaction_id="TXN-COMP-001",
                amount=48500.0,
                currency="USD",
                timestamp=datetime(2026, 7, 15, 14, 30),
                sender_account="ACC-SRC-COMP",
                receiver_account="ACC-DST-COMP",
                transaction_type="WIRE",
                channel="ONLINE",
                description="Investment deposit - CryptoVault",
                location="New York, US",
            ),
        ],
        supporting_documents=[
            SupportingDocument(
                document_id="DOC-COMP-001",
                document_type="BANK_STATEMENT",
                file_name="statement.pdf",
                file_url="https://example.com/statement.pdf",
                uploaded_at=datetime(2026, 7, 15, 15, 0),
                summary="Monthly statement showing irregular transfers.",
                extracted_text="Account holder: Compliance Tester. Wire transfers detected.",
                evidence_references=["EVID-COMP-001", "EVID-COMP-002"],
                extracted_transactions=["TXN-COMP-001"],
            ),
        ],
    )
    state = create_initial_state("CASE-COMP-001", case_input)
    return state.model_copy(update={
        "context_intelligence": ContextIntelligence(
            status=AgentStatus.COMPLETED,
            context_summary="High-risk transaction detected involving cross-border wire.",
            key_indicators=[
                "Large cross-border transfer ($48,500 USD)",
                "First-time beneficiary in high-risk jurisdiction (KY)",
            ],
            historical_baseline=HistoricalBaseline(
                transaction_count=47,
                average_amount=3250.0,
                maximum_amount=12000.0,
                common_types=["ACH", "CARD"],
                common_channels=["ONLINE"],
                common_locations=["New York, US"],
                common_counterparties=["ACC-US-1234567"],
            ),
            anomalies=[
                DetectedAnomaly(
                    anomaly_id="ANOM-COMP-001",
                    anomaly_type=AnomalyType.POINT,
                    severity=SeverityLevel.HIGH,
                    description="Transaction amount $48,500 exceeds historical maximum by 304%",
                    related_transactions=["TXN-COMP-001"],
                ),
            ],
            risk_score=0.88,
        ),
        "investigation_reasoning": InvestigationReasoning(
            status=AgentStatus.COMPLETED,
            hypotheses=[
                Hypothesis(
                    hypothesis_id="HYP-COMP-001",
                    title="Potential Account Takeover",
                    description="Unknown device and geolocation mismatch suggest compromise.",
                    confidence=0.72,
                    supporting_evidence=["TXN-COMP-001", "ANOM-COMP-001"],
                    contradicting_evidence=["DOC-COMP-001"],
                ),
            ],
            reasoning_summary="Competing hypotheses generated for compliance review.",
            recommended_actions=["Verify customer identity", "Contact customer"],
        ),
    })


def _old_prompt_size(state) -> int:
    """Compute what the prompt size WOULD have been with the old full-dump approach."""
    case_json = state.case_input.model_dump_json(indent=2)
    context_json = (
        state.context_intelligence.model_dump_json(indent=2)
        if state.context_intelligence
        else "{}"
    )
    reasoning_json = (
        state.investigation_reasoning.model_dump_json(indent=2)
        if state.investigation_reasoning
        else "{}"
    )
    old_data_section = (
        f"=== CASE INPUT ===\n{case_json}\n\n"
        f"=== CONTEXT INTELLIGENCE ===\n{context_json}\n\n"
        f"=== INVESTIGATION REASONING ===\n{reasoning_json}"
    )
    return len(old_data_section)


# ── Test: Prompt is smaller ──────────────────────────────────────────


class TestPromptCompression:
    """Prove the new prompt is smaller than the old full-dump prompt."""

    def test_prompt_is_shorter(self):
        state = _full_state()
        new_prompt = _build_prompt(state)
        old_data = _old_prompt_size(state)
        new_data_section = new_prompt.split("=== CASE INPUT ===")[1].split("=== INSTRUCTIONS ===")[0]
        assert len(new_data_section) < old_data, (
            f"New data section ({len(new_data_section)} chars) is not smaller "
            f"than old ({old_data} chars)"
        )

    def test_compact_case_is_smaller_than_full_dump(self):
        state = _full_state()
        compact = _build_compact_case(state)
        full_case = state.case_input.model_dump_json(indent=2)
        assert len(compact) < len(full_case), (
            f"Compact ({len(compact)}) should be smaller than full ({len(full_case)})"
        )

    def test_compact_context_is_smaller_than_full_dump(self):
        state = _full_state()
        compact = _build_compact_context(state)
        full_context = state.context_intelligence.model_dump_json(indent=2)
        assert len(compact) < len(full_context), (
            f"Compact ({len(compact)}) should be smaller than full ({len(full_context)})"
        )

    def test_compact_reasoning_is_smaller_than_full_dump(self):
        state = _full_state()
        compact = _build_compact_reasoning(state)
        full_reasoning = state.investigation_reasoning.model_dump_json(indent=2)
        assert len(compact) < len(full_reasoning), (
            f"Compact ({len(compact)}) should be smaller than full ({len(full_reasoning)})"
        )

    def test_minimum_case_reduction_percentage(self):
        """Compact case should be at least 25% smaller than full dump."""
        state = _full_state()
        compact = _build_compact_case(state)
        full_size = len(state.case_input.model_dump_json(indent=2))
        reduction = 1 - len(compact) / full_size
        assert reduction >= 0.25, f"Only {reduction:.1%} reduction, expected >= 25%"


# ── Test: Required information preserved ─────────────────────────────


class TestPreservesRequiredInformation:
    """Prove all compliance-relevant information is retained in the prompt."""

    @pytest.fixture()
    def prompt(self):
        return _build_prompt(_full_state())

    @pytest.fixture()
    def compact_case(self):
        return _build_compact_case(_full_state())

    @pytest.fixture()
    def compact_context(self):
        return _build_compact_context(_full_state())

    @pytest.fixture()
    def compact_reasoning(self):
        return _build_compact_reasoning(_full_state())

    # Transaction traceability
    def test_transaction_id_present(self, prompt):
        assert "TXN-COMP-001" in prompt

    def test_transaction_amount_present(self, prompt):
        assert "48500" in prompt

    def test_transaction_currency_present(self, prompt):
        assert "USD" in prompt

    def test_transaction_type_present(self, prompt):
        assert "WIRE" in prompt

    def test_sender_account_present(self, prompt):
        assert "ACC-SRC-COMP" in prompt

    def test_receiver_account_present(self, prompt):
        assert "ACC-DST-COMP" in prompt

    def test_transaction_channel_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["transactions"][0]["channel"] == "ONLINE"

    # Customer identity
    def test_customer_id_present(self, prompt):
        assert "CUST-COMP-001" in prompt

    def test_customer_name_present(self, prompt):
        assert "Compliance Tester" in prompt

    def test_customer_risk_rating_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["customer"]["risk_rating"] == "HIGH"

    # Merchant identity
    def test_merchant_id_present(self, prompt):
        assert "MERCH-COMP-001" in prompt

    def test_merchant_country_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["merchant"]["country"] == "KY"

    def test_merchant_risk_level_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["merchant"]["risk_level"] == "HIGH"

    # Beneficiary identity
    def test_beneficiary_id_present(self, prompt):
        assert "BEN-COMP-001" in prompt

    def test_beneficiary_is_new_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["beneficiary"]["is_new"] is True

    def test_beneficiary_country_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["beneficiary"]["country"] == "KY"

    # Alert reason
    def test_alert_reason_present(self, prompt):
        assert "Suspicious cross-border wire" in prompt

    # Document evidence
    def test_document_id_present(self, prompt):
        assert "DOC-COMP-001" in prompt

    def test_document_evidence_references_present(self, compact_case):
        parsed = json.loads(compact_case)
        refs = parsed["supporting_documents"][0]["evidence_references"]
        assert "EVID-COMP-001" in refs
        assert "EVID-COMP-002" in refs

    def test_document_extracted_transactions_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert "TXN-COMP-001" in parsed["supporting_documents"][0]["extracted_transactions"]

    # Anomalies
    def test_anomaly_id_present(self, prompt):
        assert "ANOM-COMP-001" in prompt

    def test_anomaly_description_present(self, prompt):
        assert "exceeds historical maximum" in prompt

    def test_anomaly_related_transactions_present(self, compact_context):
        parsed = json.loads(compact_context)
        assert "TXN-COMP-001" in parsed["anomalies"][0]["related_transactions"]

    # Risk score
    def test_risk_score_present(self, compact_context):
        parsed = json.loads(compact_context)
        assert parsed["risk_score"] == 0.88

    # Key indicators
    def test_key_indicators_present(self, prompt):
        assert "Large cross-border transfer" in prompt

    # Hypothesis traceability
    def test_hypothesis_id_present(self, prompt):
        assert "HYP-COMP-001" in prompt

    def test_hypothesis_title_present(self, compact_reasoning):
        parsed = json.loads(compact_reasoning)
        assert parsed["hypotheses"][0]["title"] == "Potential Account Takeover"

    def test_hypothesis_confidence_present(self, compact_reasoning):
        parsed = json.loads(compact_reasoning)
        assert parsed["hypotheses"][0]["confidence"] == 0.72

    def test_hypothesis_supporting_evidence_present(self, compact_reasoning):
        parsed = json.loads(compact_reasoning)
        evidence = parsed["hypotheses"][0]["supporting_evidence"]
        assert "TXN-COMP-001" in evidence
        assert "ANOM-COMP-001" in evidence

    def test_hypothesis_contradicting_evidence_present(self, compact_reasoning):
        parsed = json.loads(compact_reasoning)
        assert "DOC-COMP-001" in parsed["hypotheses"][0]["contradicting_evidence"]

    def test_recommended_actions_present(self, compact_reasoning):
        parsed = json.loads(compact_reasoning)
        assert "Verify customer identity" in parsed["recommended_actions"]


# ── Test: Unnecessary fields excluded ────────────────────────────────


class TestExcludesUnnecessaryFields:
    """Prove bloating fields are NOT in the compact output."""

    @pytest.fixture()
    def compact_case(self):
        return _build_compact_case(_full_state())

    @pytest.fixture()
    def compact_context(self):
        return _build_compact_context(_full_state())

    @pytest.fixture()
    def compact_reasoning(self):
        return _build_compact_reasoning(_full_state())

    # Customer PII
    def test_no_customer_email(self, compact_case):
        assert "tester@example.com" not in compact_case

    def test_no_customer_phone(self, compact_case):
        assert "+1-555-0100" not in compact_case

    def test_no_customer_address(self, compact_case):
        assert "123 Test Street" not in compact_case

    def test_no_customer_dob(self, compact_case):
        assert "1990-01-01" not in compact_case

    def test_no_customer_occupation(self, compact_case):
        assert "Software Engineer" not in compact_case

    # Device browser/OS/IP
    def test_no_device_browser(self, compact_case):
        assert "Chrome Mobile" not in compact_case

    def test_no_device_os(self, compact_case):
        assert "Android 14" not in compact_case

    def test_no_device_ip(self, compact_case):
        assert "192.168.1.1" not in compact_case

    # Document bloat
    def test_no_document_extracted_text(self, compact_case):
        assert "Wire transfers detected" not in compact_case

    def test_no_document_file_url(self, compact_case):
        assert "example.com/statement.pdf" not in compact_case

    def test_no_document_file_name(self, compact_case):
        assert "statement.pdf" not in compact_case

    # Historical baseline
    def test_no_historical_baseline(self, compact_context):
        assert "average_amount" not in compact_context
        assert "maximum_amount" not in compact_context
        assert "transaction_count" not in compact_context

    # Context status
    def test_no_context_status(self, compact_context):
        assert "NOT_STARTED" not in compact_context
        assert "COMPLETED" not in compact_context

    # Reasoning status/summary
    def test_no_reasoning_status(self, compact_reasoning):
        assert "NOT_STARTED" not in compact_reasoning
        assert "COMPLETED" not in compact_reasoning

    def test_no_reasoning_summary(self, compact_reasoning):
        assert "Competing hypotheses generated" not in compact_reasoning

    # Beneficiary bank details
    def test_no_beneficiary_account_number(self, compact_case):
        assert "ACC-KY-99999" not in compact_case

    def test_no_beneficiary_bank_name(self, compact_case):
        assert "Cayman National Bank" not in compact_case


# ── Test: Sparse/missing state handled gracefully ────────────────────


class TestSparseStateHandling:
    """Prove the compact builders handle missing upstream data."""

    def test_empty_case_input(self):
        state = create_initial_state("CASE-SPARSE", CaseInput())
        compact = _build_compact_case(state)
        parsed = json.loads(compact)
        assert parsed["transactions"] == []
        assert "customer" not in parsed
        assert "merchant" not in parsed
        assert "beneficiary" not in parsed
        assert "device" not in parsed

    def test_no_context_intelligence(self):
        state = create_initial_state("CASE-NO-CTX", CaseInput())
        compact = _build_compact_context(state)
        assert compact == "{}"

    def test_no_reasoning(self):
        state = create_initial_state("CASE-NO-REAS", CaseInput())
        compact = _build_compact_reasoning(state)
        assert compact == "{}"

    def test_reasoning_without_recommended_actions(self):
        state = create_initial_state("CASE-NO-ACT", CaseInput())
        state = state.model_copy(update={
            "investigation_reasoning": InvestigationReasoning(
                status=AgentStatus.COMPLETED,
                hypotheses=[],
            ),
        })
        compact = _build_compact_reasoning(state)
        parsed = json.loads(compact)
        assert parsed["hypotheses"] == []
        assert "recommended_actions" not in parsed

    def test_prompt_still_valid_with_sparse_state(self):
        state = create_initial_state("CASE-MINIMAL", CaseInput())
        prompt = _build_prompt(state)
        assert "CASE INPUT" in prompt
        assert "CONTEXT INTELLIGENCE" in prompt
        assert "INVESTIGATION REASONING" in prompt
        assert "INSTRUCTIONS" in prompt
