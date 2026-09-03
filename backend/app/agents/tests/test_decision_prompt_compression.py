"""Tests for Decision Agent context compression.

Proves that:
1. The compressed prompt is smaller than the original full-dump prompt.
2. The compressed prompt preserves all transaction IDs and amounts.
3. The compressed prompt preserves customer, merchant, beneficiary identity.
4. The compressed prompt preserves anomaly IDs and descriptions.
5. The compressed prompt preserves risk scores and key indicators.
6. The compressed prompt preserves alert reason.
7. The full investigation_reasoning is still present.
8. Unnecessary fields (device browser, doc extracted_text, historical_baseline,
   behavioral_biometrics, face_verification) are excluded.
9. The compact builder handles sparse/missing state gracefully.
"""

import json
from datetime import datetime

import pytest

from app.agents.decision_agent import (
    _build_compact_case_context,
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
            name="Compression Tester",
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
                extracted_text="Account holder: Compression Tester. Wire transfers detected.",
                evidence_references=["EVID-COMP-001"],
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
            reasoning_summary="Competing hypotheses generated.",
            recommended_actions=["Verify customer identity", "Contact customer"],
        ),
    })


def _old_prompt_size(state) -> int:
    """Compute what the prompt size WOULD have been with the old approach."""
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
    # Reconstruct the old prompt template (same instructions portion)
    old_data_section = (
        f"=== CASE DATA ===\n{case_json}\n\n"
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
        new_data_section = new_prompt.split("=== CASE SUMMARY AND CONTEXT ===")[1].split("=== INSTRUCTIONS ===")[0]
        # The new data section must be meaningfully smaller
        assert len(new_data_section) < old_data, (
            f"New data section ({len(new_data_section)} chars) is not smaller "
            f"than old ({old_data} chars)"
        )

    def test_compact_context_is_smaller_than_full_dumps(self):
        state = _full_state()
        compact = _build_compact_case_context(state)
        full_case = state.case_input.model_dump_json(indent=2)
        full_context = state.context_intelligence.model_dump_json(indent=2)
        assert len(compact) < len(full_case) + len(full_context), (
            f"Compact ({len(compact)}) should be smaller than "
            f"case ({len(full_case)}) + context ({len(full_context)})"
        )

    def test_minimum_reduction_percentage(self):
        """Compact context should be at least 25% smaller than full dumps."""
        state = _full_state()
        compact = _build_compact_case_context(state)
        full_size = len(state.case_input.model_dump_json(indent=2)) + len(
            state.context_intelligence.model_dump_json(indent=2)
        )
        reduction = 1 - len(compact) / full_size
        assert reduction >= 0.25, f"Only {reduction:.1%} reduction, expected >= 25%"


# ── Test: Required information preserved ─────────────────────────────


class TestPreservesRequiredInformation:
    """Prove all decision-critical information is retained in the prompt."""

    @pytest.fixture()
    def prompt(self):
        return _build_prompt(_full_state())

    @pytest.fixture()
    def compact(self):
        return _build_compact_case_context(_full_state())

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

    # Customer identity
    def test_customer_id_present(self, prompt):
        assert "CUST-COMP-001" in prompt

    def test_customer_name_present(self, prompt):
        assert "Compression Tester" in prompt

    def test_customer_risk_rating_present(self, prompt):
        assert "HIGH" in prompt

    # Merchant identity
    def test_merchant_id_present(self, prompt):
        assert "MERCH-COMP-001" in prompt

    def test_merchant_country_present(self, compact):
        parsed = json.loads(compact)
        assert parsed["merchant"]["country"] == "KY"

    def test_merchant_risk_level_present(self, compact):
        parsed = json.loads(compact)
        assert parsed["merchant"]["risk_level"] == "HIGH"

    # Beneficiary identity
    def test_beneficiary_id_present(self, prompt):
        assert "BEN-COMP-001" in prompt

    def test_beneficiary_is_new_present(self, compact):
        parsed = json.loads(compact)
        assert parsed["beneficiary"]["is_new"] is True

    def test_beneficiary_country_present(self, compact):
        parsed = json.loads(compact)
        assert parsed["beneficiary"]["country"] == "KY"

    # Alert reason
    def test_alert_reason_present(self, prompt):
        assert "Suspicious cross-border wire" in prompt

    # Anomalies
    def test_anomaly_id_present(self, prompt):
        assert "ANOM-COMP-001" in prompt

    def test_anomaly_description_present(self, prompt):
        assert "exceeds historical maximum" in prompt

    def test_anomaly_related_transactions_present(self, compact):
        parsed = json.loads(compact)
        assert "TXN-COMP-001" in parsed["anomalies"][0]["related_transactions"]

    # Risk score
    def test_risk_score_present(self, compact):
        parsed = json.loads(compact)
        assert parsed["risk_score"] == 0.88

    # Key indicators
    def test_key_indicators_present(self, prompt):
        assert "Large cross-border transfer" in prompt

    # Investigation reasoning (full)
    def test_hypothesis_id_present(self, prompt):
        assert "HYP-COMP-001" in prompt

    def test_hypothesis_title_present(self, prompt):
        assert "Potential Account Takeover" in prompt

    def test_hypothesis_confidence_present(self, prompt):
        assert "0.72" in prompt

    def test_supporting_evidence_present(self, prompt):
        assert "TXN-COMP-001" in prompt
        assert "ANOM-COMP-001" in prompt

    def test_contradicting_evidence_present(self, prompt):
        assert "DOC-COMP-001" in prompt


# ── Test: Unnecessary fields excluded ────────────────────────────────


class TestExcludesUnnecessaryFields:
    """Prove bloating fields are NOT in the compact context."""

    @pytest.fixture()
    def compact(self):
        return _build_compact_case_context(_full_state())

    def test_no_customer_email(self, compact):
        assert "tester@example.com" not in compact

    def test_no_customer_phone(self, compact):
        assert "+1-555-0100" not in compact

    def test_no_customer_address(self, compact):
        assert "123 Test Street" not in compact

    def test_no_customer_dob(self, compact):
        assert "1990-01-01" not in compact

    def test_no_customer_occupation(self, compact):
        assert "Software Engineer" not in compact

    def test_no_device_browser(self, compact):
        assert "Chrome Mobile" not in compact

    def test_no_device_os(self, compact):
        assert "Android 14" not in compact

    def test_no_device_ip(self, compact):
        assert "192.168.1.1" not in compact

    def test_no_device_geolocation(self, compact):
        assert "Bucharest" not in compact

    def test_no_document_extracted_text(self, compact):
        assert "Wire transfers detected" not in compact

    def test_no_document_file_url(self, compact):
        assert "example.com/statement.pdf" not in compact

    def test_no_document_summary(self, compact):
        assert "irregular transfers" not in compact

    def test_no_historical_baseline(self, compact):
        assert "average_amount" not in compact
        assert "maximum_amount" not in compact
        assert "transaction_count" not in compact

    def test_no_beneficiary_account_number(self, compact):
        assert "ACC-KY-99999" not in compact

    def test_no_beneficiary_bank_name(self, compact):
        assert "Cayman National Bank" not in compact

    def test_no_merchant_registered_date(self, compact):
        assert "2023-01-01" not in compact


# ── Test: Sparse/missing state handled gracefully ────────────────────


class TestSparseStateHandling:
    """Prove the compact builder handles missing upstream data."""

    def test_empty_case_input(self):
        state = create_initial_state("CASE-SPARSE", CaseInput())
        compact = _build_compact_case_context(state)
        parsed = json.loads(compact)
        assert parsed["transactions"] == []
        assert "customer" not in parsed
        assert "merchant" not in parsed
        assert "beneficiary" not in parsed

    def test_no_context_intelligence(self):
        state = create_initial_state("CASE-NO-CTX", CaseInput(
            alert_reason="Test alert",
            transactions=[Transaction(
                transaction_id="TXN-SPARSE",
                amount=100,
                timestamp=datetime(2026, 1, 1),
                sender_account="SRC",
                receiver_account="DST",
                transaction_type="WIRE",
            )],
        ))
        compact = _build_compact_case_context(state)
        parsed = json.loads(compact)
        assert "risk_score" not in parsed
        assert "anomalies" not in parsed
        assert parsed["alert_reason"] == "Test alert"
        assert parsed["transactions"][0]["transaction_id"] == "TXN-SPARSE"

    def test_no_reasoning(self):
        state = create_initial_state("CASE-NO-REAS", CaseInput())
        prompt = _build_prompt(state)
        assert "{}" in prompt  # reasoning_json falls back to empty

    def test_prompt_still_valid_with_sparse_state(self):
        state = create_initial_state("CASE-MINIMAL", CaseInput())
        prompt = _build_prompt(state)
        assert "CASE SUMMARY AND CONTEXT" in prompt
        assert "INVESTIGATION REASONING" in prompt
        assert "INSTRUCTIONS" in prompt
