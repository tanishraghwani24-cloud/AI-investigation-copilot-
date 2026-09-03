"""Tests for compliance data flowing into the Decision Agent prompt.

Proves that:
1. Compliance findings (regulation_id, regulation_name, is_violated, severity,
   evidence_references) reach the Decision prompt.
2. Evidence gaps from compliance reach the Decision prompt.
3. Validation summary from compliance reaches the Decision prompt.
4. Unnecessary compliance fields (status, description) are excluded.
5. The prompt remains substantially smaller than the original uncompressed prompt.
6. Missing/sparse compliance data is handled safely.
7. The compact compliance builder produces valid JSON.
"""

import json
from datetime import datetime

import pytest

from app.agents.decision_agent import (
    _build_compact_compliance,
    _build_prompt,
)
from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    BeneficiaryInfo,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CustomerProfile,
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


# ── Fixtures ────────────────────────────────────────────────────────────


def _full_state_with_compliance():
    """Build a realistic state with all fields populated, including compliance."""
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
                evidence_references=["EVID-COMP-001"],
            ),
        ],
    )
    state = create_initial_state("CASE-COMP-002", case_input)
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
        "evidence_compliance_validation": EvidenceComplianceValidation(
            status=AgentStatus.COMPLETED,
            compliance_mappings=[
                ComplianceMapping(
                    regulation_id="AML-2023-04",
                    regulation_name="Anti-Money Laundering Reporting",
                    description=(
                        "Cross-border wire transfer of $48,500 to KY jurisdiction "
                        "triggers mandatory AML reporting under BSA/AML regulations. "
                        "Transaction TXN-COMP-001 exceeds the $10,000 CTR threshold."
                    ),
                    is_violated=True,
                    severity=SeverityLevel.HIGH,
                    evidence_references=["TXN-COMP-001", "ANOM-COMP-001"],
                ),
                ComplianceMapping(
                    regulation_id="KYC-2024-01",
                    regulation_name="Know Your Customer Due Diligence",
                    description=(
                        "Customer CUST-COMP-001 is rated HIGH risk. "
                        "Enhanced due diligence required for high-risk customers."
                    ),
                    is_violated=False,
                    severity=SeverityLevel.MEDIUM,
                    evidence_references=["DOC-COMP-001"],
                ),
            ],
            evidence_gaps=[
                "No source-of-funds documentation available",
                "No identity verification document on file",
            ],
            validation_summary=(
                "2 compliance findings identified. 1 violation (AML reporting). "
                "2 evidence gaps require resolution before case closure."
            ),
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
    old_data_section = (
        f"=== CASE DATA ===\n{case_json}\n\n"
        f"=== CONTEXT INTELLIGENCE ===\n{context_json}\n\n"
        f"=== INVESTIGATION REASONING ===\n{reasoning_json}"
    )
    return len(old_data_section)


# ── Test: Compliance findings reach prompt ───────────────────────────


class TestComplianceReachesPrompt:
    """Prove compliance data is included in the Decision prompt."""

    @pytest.fixture()
    def prompt(self):
        return _build_prompt(_full_state_with_compliance())

    @pytest.fixture()
    def compact(self):
        return _build_compact_compliance(_full_state_with_compliance())

    # Regulation identity
    def test_regulation_id_present(self, prompt):
        assert "AML-2023-04" in prompt

    def test_regulation_name_present(self, prompt):
        assert "Anti-Money Laundering Reporting" in prompt

    def test_second_regulation_id_present(self, prompt):
        assert "KYC-2024-01" in prompt

    def test_second_regulation_name_present(self, prompt):
        assert "Know Your Customer Due Diligence" in prompt

    # Violation status
    def test_violated_regulation_marked_true(self, compact):
        parsed = json.loads(compact)
        aml = parsed["compliance_mappings"][0]
        assert aml["is_violated"] is True

    def test_non_violated_regulation_marked_false(self, compact):
        parsed = json.loads(compact)
        kyc = parsed["compliance_mappings"][1]
        assert kyc["is_violated"] is False

    # Severity
    def test_severity_preserved(self, compact):
        parsed = json.loads(compact)
        assert parsed["compliance_mappings"][0]["severity"] == "HIGH"
        assert parsed["compliance_mappings"][1]["severity"] == "MEDIUM"

    # Evidence IDs
    def test_evidence_references_in_aml_mapping(self, compact):
        parsed = json.loads(compact)
        refs = parsed["compliance_mappings"][0]["evidence_references"]
        assert "TXN-COMP-001" in refs
        assert "ANOM-COMP-001" in refs

    def test_evidence_references_in_kyc_mapping(self, compact):
        parsed = json.loads(compact)
        refs = parsed["compliance_mappings"][1]["evidence_references"]
        assert "DOC-COMP-001" in refs

    # Evidence gaps
    def test_evidence_gaps_present(self, prompt):
        assert "No source-of-funds documentation" in prompt

    def test_second_evidence_gap_present(self, prompt):
        assert "No identity verification document" in prompt

    def test_evidence_gaps_in_compact(self, compact):
        parsed = json.loads(compact)
        assert len(parsed["evidence_gaps"]) == 2

    # Validation summary
    def test_validation_summary_present(self, prompt):
        assert "2 compliance findings" in prompt

    def test_validation_summary_in_compact(self, compact):
        parsed = json.loads(compact)
        assert "violation" in parsed["validation_summary"].lower()

    # Prompt section header
    def test_compliance_section_header_in_prompt(self, prompt):
        assert "=== COMPLIANCE FINDINGS ===" in prompt


# ── Test: Unnecessary compliance fields excluded ─────────────────────


class TestExcludesUnnecessaryComplianceFields:
    """Prove verbose/lifecycle compliance fields are NOT in the compact output."""

    @pytest.fixture()
    def compact(self):
        return _build_compact_compliance(_full_state_with_compliance())

    def test_no_agent_status(self, compact):
        """Agent lifecycle status should not be in compact compliance."""
        parsed = json.loads(compact)
        assert "status" not in parsed

    def test_no_mapping_description(self, compact):
        """Verbose mapping descriptions should not be in compact compliance."""
        parsed = json.loads(compact)
        for mapping in parsed["compliance_mappings"]:
            assert "description" not in mapping

    def test_no_bsa_aml_regulations_text(self, compact):
        """Full regulation description text should not appear."""
        assert "BSA/AML regulations" not in compact

    def test_no_enhanced_due_diligence_text(self, compact):
        """Full KYC description text should not appear."""
        assert "Enhanced due diligence" not in compact


# ── Test: Prompt still smaller than old uncompressed ─────────────────


class TestPromptStillSmaller:
    """Even with compliance data added, the prompt remains smaller than the
    original uncompressed approach (which never had compliance at all)."""

    def test_prompt_with_compliance_smaller_than_old_uncompressed(self):
        state = _full_state_with_compliance()
        new_prompt = _build_prompt(state)
        old_size = _old_prompt_size(state)
        # The new prompt data sections (compact case + compliance + reasoning)
        # should still be smaller than old full-dump (case + context + reasoning)
        # even though compliance is added, because the compression of case+context
        # more than compensates.
        new_data = new_prompt.split("=== CASE SUMMARY AND CONTEXT ===")[1].split("=== INSTRUCTIONS ===")[0]
        assert len(new_data) < old_size, (
            f"New data section ({len(new_data)} chars) is not smaller "
            f"than old uncompressed ({old_size} chars)"
        )


# ── Test: Sparse/missing compliance data handled safely ──────────────


class TestSparseComplianceHandling:
    """Prove the compact compliance builder handles missing data gracefully."""

    def test_no_compliance_returns_empty_json(self):
        """When evidence_compliance_validation is None, returns '{}'."""
        state = create_initial_state("CASE-NO-COMPL", CaseInput())
        compact = _build_compact_compliance(state)
        assert compact == "{}"

    def test_empty_compliance_mappings(self):
        """When compliance has no mappings, the list is empty."""
        state = create_initial_state("CASE-EMPTY-COMPL", CaseInput())
        state = state.model_copy(update={
            "evidence_compliance_validation": EvidenceComplianceValidation(
                status=AgentStatus.COMPLETED,
                compliance_mappings=[],
                evidence_gaps=[],
            ),
        })
        compact = _build_compact_compliance(state)
        parsed = json.loads(compact)
        assert parsed["compliance_mappings"] == []
        assert parsed["evidence_gaps"] == []

    def test_no_validation_summary_omitted(self):
        """When validation_summary is None, it is omitted from compact output."""
        state = create_initial_state("CASE-NO-SUMM", CaseInput())
        state = state.model_copy(update={
            "evidence_compliance_validation": EvidenceComplianceValidation(
                status=AgentStatus.COMPLETED,
                compliance_mappings=[],
                evidence_gaps=["Some gap"],
            ),
        })
        compact = _build_compact_compliance(state)
        parsed = json.loads(compact)
        assert "validation_summary" not in parsed

    def test_prompt_still_builds_without_compliance(self):
        """_build_prompt works when compliance is None."""
        state = create_initial_state("CASE-NO-COMPL-PROMPT", CaseInput())
        prompt = _build_prompt(state)
        assert "COMPLIANCE FINDINGS" in prompt
        assert "{}" in prompt  # compliance section is empty JSON

    def test_compact_compliance_is_valid_json(self):
        """Compact compliance output is always valid JSON."""
        state = _full_state_with_compliance()
        compact = _build_compact_compliance(state)
        parsed = json.loads(compact)
        assert isinstance(parsed, dict)

    def test_compliance_with_empty_evidence_refs(self):
        """A mapping with no evidence_references produces an empty list."""
        state = create_initial_state("CASE-EMPTY-REFS", CaseInput())
        state = state.model_copy(update={
            "evidence_compliance_validation": EvidenceComplianceValidation(
                status=AgentStatus.COMPLETED,
                compliance_mappings=[
                    ComplianceMapping(
                        regulation_id="REG-001",
                        regulation_name="Test Regulation",
                        is_violated=False,
                        severity=SeverityLevel.LOW,
                        evidence_references=[],
                    ),
                ],
                evidence_gaps=[],
            ),
        })
        compact = _build_compact_compliance(state)
        parsed = json.loads(compact)
        assert parsed["compliance_mappings"][0]["evidence_references"] == []
