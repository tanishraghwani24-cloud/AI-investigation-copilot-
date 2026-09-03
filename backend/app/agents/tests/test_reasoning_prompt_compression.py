"""Tests for Reasoning Agent context compression.

Proves that:
1. The compressed prompt is smaller than the original full-dump prompt.
2. The compressed prompt preserves all transaction IDs and amounts.
3. The compressed prompt preserves customer, merchant, beneficiary identity.
4. The compressed prompt preserves anomaly IDs and descriptions.
5. The compressed prompt preserves risk scores and key indicators.
6. The compressed prompt preserves alert reason.
7. The compressed prompt preserves document IDs and evidence references.
8. The compressed prompt preserves device investigative facts.
9. Unnecessary fields (device browser/OS/IP, doc extracted_text,
   historical_baseline, customer PII) are excluded.
10. The compact builder handles sparse/missing state gracefully.
"""

import json
from datetime import datetime

import pytest

from app.agents.reasoning_agent import (
    _build_compact_case,
    _build_compact_context,
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
            customer_id="CUST-REAS-001",
            name="Reasoning Tester",
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
            merchant_id="MERCH-REAS-001",
            name="TestMerchant Ltd.",
            category="Cryptocurrency Exchange",
            country="KY",
            risk_level=SeverityLevel.HIGH,
            registered_date="2023-01-01",
        ),
        device_info=DeviceInfo(
            device_id="DEV-REAS-001",
            device_type="MOBILE",
            ip_address="192.168.1.1",
            geolocation="Bucharest, Romania",
            is_known_device=False,
            os="Android 14",
            browser="Chrome Mobile 126",
        ),
        beneficiary_info=BeneficiaryInfo(
            beneficiary_id="BEN-REAS-001",
            name="Offshore Corp Ltd.",
            account_number="ACC-KY-99999",
            bank_name="Cayman National Bank",
            country="KY",
            is_new=True,
            relationship="Investment Platform",
        ),
        transactions=[
            Transaction(
                transaction_id="TXN-REAS-001",
                amount=48500.0,
                currency="USD",
                timestamp=datetime(2026, 7, 15, 14, 30),
                sender_account="ACC-SRC-REAS",
                receiver_account="ACC-DST-REAS",
                transaction_type="WIRE",
                channel="ONLINE",
                description="Investment deposit - CryptoVault",
                location="New York, US",
            ),
        ],
        supporting_documents=[
            SupportingDocument(
                document_id="DOC-REAS-001",
                document_type="BANK_STATEMENT",
                file_name="statement.pdf",
                file_url="https://example.com/statement.pdf",
                uploaded_at=datetime(2026, 7, 15, 15, 0),
                summary="Monthly statement showing irregular transfers.",
                extracted_text="Account holder: Reasoning Tester. Wire transfers detected.",
                evidence_references=["EVID-REAS-001"],
            ),
        ],
    )
    state = create_initial_state("CASE-REAS-001", case_input)
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
                    anomaly_id="ANOM-REAS-001",
                    anomaly_type=AnomalyType.POINT,
                    severity=SeverityLevel.HIGH,
                    description="Transaction amount $48,500 exceeds historical maximum by 304%",
                    related_transactions=["TXN-REAS-001"],
                ),
            ],
            risk_score=0.88,
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
    old_data_section = (
        f"=== CASE DATA ===\n{case_json}\n\n"
        f"=== CONTEXT INTELLIGENCE ===\n{context_json}"
    )
    return len(old_data_section)


# ── Test: Prompt is smaller ──────────────────────────────────────────


class TestPromptCompression:
    """Prove the new prompt is smaller than the old full-dump prompt."""

    def test_prompt_is_shorter(self):
        state = _full_state()
        new_prompt = _build_prompt(state)
        old_data = _old_prompt_size(state)
        new_data_section = new_prompt.split("=== CASE DATA ===")[1].split("=== INSTRUCTIONS ===")[0]
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

    def test_minimum_case_reduction_percentage(self):
        """Compact case should be at least 25% smaller than full dump."""
        state = _full_state()
        compact = _build_compact_case(state)
        full_size = len(state.case_input.model_dump_json(indent=2))
        reduction = 1 - len(compact) / full_size
        assert reduction >= 0.25, f"Only {reduction:.1%} reduction, expected >= 25%"


# ── Test: Required information preserved ─────────────────────────────


class TestPreservesRequiredInformation:
    """Prove all investigation-relevant information is retained in the prompt."""

    @pytest.fixture()
    def prompt(self):
        return _build_prompt(_full_state())

    @pytest.fixture()
    def compact_case(self):
        return _build_compact_case(_full_state())

    @pytest.fixture()
    def compact_context(self):
        return _build_compact_context(_full_state())

    # Transaction traceability
    def test_transaction_id_present(self, prompt):
        assert "TXN-REAS-001" in prompt

    def test_transaction_amount_present(self, prompt):
        assert "48500" in prompt

    def test_transaction_currency_present(self, prompt):
        assert "USD" in prompt

    def test_transaction_type_present(self, prompt):
        assert "WIRE" in prompt

    def test_sender_account_present(self, prompt):
        assert "ACC-SRC-REAS" in prompt

    def test_receiver_account_present(self, prompt):
        assert "ACC-DST-REAS" in prompt

    def test_transaction_channel_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["transactions"][0]["channel"] == "ONLINE"

    def test_transaction_description_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert "CryptoVault" in parsed["transactions"][0]["description"]

    def test_transaction_location_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["transactions"][0]["location"] == "New York, US"

    # Customer identity
    def test_customer_id_present(self, prompt):
        assert "CUST-REAS-001" in prompt

    def test_customer_name_present(self, prompt):
        assert "Reasoning Tester" in prompt

    def test_customer_risk_rating_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["customer"]["risk_rating"] == "HIGH"

    # Merchant identity
    def test_merchant_id_present(self, prompt):
        assert "MERCH-REAS-001" in prompt

    def test_merchant_country_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["merchant"]["country"] == "KY"

    def test_merchant_risk_level_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["merchant"]["risk_level"] == "HIGH"

    def test_merchant_category_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["merchant"]["category"] == "Cryptocurrency Exchange"

    # Beneficiary identity
    def test_beneficiary_id_present(self, prompt):
        assert "BEN-REAS-001" in prompt

    def test_beneficiary_is_new_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["beneficiary"]["is_new"] is True

    def test_beneficiary_country_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["beneficiary"]["country"] == "KY"

    # Device investigative facts
    def test_device_id_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["device"]["device_id"] == "DEV-REAS-001"

    def test_device_type_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["device"]["device_type"] == "MOBILE"

    def test_device_geolocation_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["device"]["geolocation"] == "Bucharest, Romania"

    def test_device_is_known_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert parsed["device"]["is_known_device"] is False

    # Alert reason
    def test_alert_reason_present(self, prompt):
        assert "Suspicious cross-border wire" in prompt

    # Document evidence
    def test_document_id_present(self, prompt):
        assert "DOC-REAS-001" in prompt

    def test_document_evidence_references_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert "EVID-REAS-001" in parsed["supporting_documents"][0]["evidence_references"]

    def test_document_summary_present(self, compact_case):
        parsed = json.loads(compact_case)
        assert "irregular transfers" in parsed["supporting_documents"][0]["summary"]

    # Anomalies
    def test_anomaly_id_present(self, prompt):
        assert "ANOM-REAS-001" in prompt

    def test_anomaly_description_present(self, prompt):
        assert "exceeds historical maximum" in prompt

    def test_anomaly_related_transactions_present(self, compact_context):
        parsed = json.loads(compact_context)
        assert "TXN-REAS-001" in parsed["anomalies"][0]["related_transactions"]

    # Risk score
    def test_risk_score_present(self, compact_context):
        parsed = json.loads(compact_context)
        assert parsed["risk_score"] == 0.88

    # Key indicators
    def test_key_indicators_present(self, prompt):
        assert "Large cross-border transfer" in prompt

    # Context summary
    def test_context_summary_present(self, compact_context):
        parsed = json.loads(compact_context)
        assert "High-risk transaction" in parsed["context_summary"]


# ── Test: Unnecessary fields excluded ────────────────────────────────


class TestExcludesUnnecessaryFields:
    """Prove bloating fields are NOT in the compact output."""

    @pytest.fixture()
    def compact_case(self):
        return _build_compact_case(_full_state())

    @pytest.fixture()
    def compact_context(self):
        return _build_compact_context(_full_state())

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

    def test_no_customer_nationality(self, compact_case):
        assert "nationality" not in compact_case

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

    # Beneficiary bank details
    def test_no_beneficiary_account_number(self, compact_case):
        assert "ACC-KY-99999" not in compact_case

    def test_no_beneficiary_bank_name(self, compact_case):
        assert "Cayman National Bank" not in compact_case

    # Merchant registered_date
    def test_no_merchant_registered_date(self, compact_case):
        assert "2023-01-01" not in compact_case


# ── Test: Sparse/missing state handled gracefully ────────────────────


class TestSparseStateHandling:
    """Prove the compact builder handles missing upstream data."""

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
        compact = _build_compact_context(state)
        assert compact == "{}"

    def test_context_without_anomalies(self):
        state = create_initial_state("CASE-NO-ANOM", CaseInput())
        state = state.model_copy(update={
            "context_intelligence": ContextIntelligence(
                status=AgentStatus.COMPLETED,
                context_summary="Low risk",
                risk_score=0.1,
            ),
        })
        compact = _build_compact_context(state)
        parsed = json.loads(compact)
        assert parsed["risk_score"] == 0.1
        assert "anomalies" not in parsed

    def test_prompt_still_valid_with_sparse_state(self):
        state = create_initial_state("CASE-MINIMAL", CaseInput())
        prompt = _build_prompt(state)
        assert "CASE DATA" in prompt
        assert "CONTEXT INTELLIGENCE" in prompt
        assert "INSTRUCTIONS" in prompt
