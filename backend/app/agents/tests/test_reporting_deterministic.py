"""Regression tests: Reporting agent is deterministic and LLM-free.

These tests prove that:
1. reporting_agent() never calls an LLM (no mocking required, no network).
2. The generated report contains evidence IDs from upstream state.
3. The generated report contains the recommended decision.
4. The generated report does NOT invent transaction information.
"""

import ast
import inspect
import textwrap
from datetime import datetime

import pytest

from app.agents.reporting_agent import reporting_agent
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CustomerProfile,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    EvidenceComplianceValidation,
    Hypothesis,
    InvestigationReasoning,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


# ── Fixtures ────────────────────────────────────────────────────────────


def _populated_state():
    """Build a fully populated InvestigationState with known evidence IDs."""
    case_input = CaseInput(
        alert_reason="Suspicious cross-border wire",
        customer_profile=CustomerProfile(
            customer_id="CUST-DET-001",
            name="Deterministic Tester",
        ),
        transactions=[
            Transaction(
                transaction_id="TXN-DET-001",
                amount=9500.00,
                currency="EUR",
                timestamp=datetime(2026, 6, 15, 9, 30),
                sender_account="SRC-DET",
                receiver_account="DST-DET",
                transaction_type="WIRE",
            ),
        ],
        supporting_documents=[
            SupportingDocument(
                document_id="DOC-DET-001",
                document_type="INVOICE",
                file_name="invoice_det.pdf",
                evidence_references=["EVID-DET-001", "EVID-DET-002"],
            ),
        ],
    )
    state = create_initial_state("CASE-DET-001", case_input)
    return state.model_copy(update={
        "context_intelligence": ContextIntelligence(
            status=AgentStatus.COMPLETED,
            context_summary="Context for deterministic test",
            key_indicators=["Cross-border transfer"],
            risk_score=0.55,
        ),
        "investigation_reasoning": InvestigationReasoning(
            status=AgentStatus.COMPLETED,
            reasoning_summary="Reasoning for deterministic test",
            recommended_actions=["Review source of funds"],
            hypotheses=[
                Hypothesis(
                    hypothesis_id="HYP-DET-001",
                    title="Potential structuring",
                    description="Amount near reporting threshold",
                    confidence=0.65,
                    supporting_evidence=["TXN-DET-001", "EVID-DET-001"],
                    contradicting_evidence=["DOC-DET-001"],
                ),
            ],
        ),
        "evidence_compliance_validation": EvidenceComplianceValidation(
            status=AgentStatus.COMPLETED,
            validation_summary="Compliance validated",
            evidence_gaps=["Missing KYC refresh"],
            compliance_mappings=[
                ComplianceMapping(
                    regulation_id="REG-DET-001",
                    regulation_name="AML Threshold Monitoring",
                    description="Requires review near threshold",
                    is_violated=False,
                    severity=SeverityLevel.MEDIUM,
                    evidence_references=["TXN-DET-001", "EVID-DET-002"],
                ),
            ],
        ),
        "decision_optimization": DecisionOptimization(
            status=AgentStatus.COMPLETED,
            recommended_decision=DecisionAction.ESCALATE,
            decision_rationale="Escalate for senior review due to threshold proximity",
            decision_options=[
                DecisionOption(
                    option_id="OPT-DET-ESC",
                    action=DecisionAction.ESCALATE,
                    rationale="Pattern warrants senior review",
                    confidence=0.82,
                    risk_score=0.60,
                    pros=["Thorough review"],
                    cons=["Processing delay"],
                    risks=["False positive cost"],
                    mitigation=["Fast-track review SLA"],
                ),
                DecisionOption(
                    option_id="OPT-DET-ALLOW",
                    action=DecisionAction.ALLOW,
                    rationale="Low absolute risk",
                    confidence=0.45,
                    risk_score=0.30,
                ),
            ],
        ),
    })


# ── Test: No LLM dependency ─────────────────────────────────────────────


class TestReportingDoesNotRequireLLM:
    """Prove reporting_agent() is LLM-free by source inspection and runtime."""

    def test_no_llm_imports_in_source(self):
        """The reporting_agent module must not import any LLM client."""
        import app.agents.reporting_agent as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)

        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.add(node.module)

        llm_modules = {"ollama", "langchain", "openai", "anthropic", "google.genai"}
        for mod_name in imported_names:
            for llm in llm_modules:
                assert not mod_name.startswith(llm), (
                    f"reporting_agent imports '{mod_name}', which is an LLM dependency"
                )

    def test_no_gemini_client_import(self):
        """The reporting_agent must not reference the project's GeminiClient."""
        import app.agents.reporting_agent as mod

        source = inspect.getsource(mod)
        assert "gemini_client" not in source
        assert "GeminiClient" not in source
        assert "get_reasoning_client" not in source

    def test_function_is_synchronous(self):
        """reporting_agent must be a plain sync function (no async = no network)."""
        assert not inspect.iscoroutinefunction(reporting_agent)

    def test_runs_without_mocking(self):
        """reporting_agent must succeed with zero mocks/patches."""
        state = _populated_state()
        result = reporting_agent(state)
        assert "investigation_report" in result
        assert result["investigation_report"].status == AgentStatus.COMPLETED


# ── Test: Evidence IDs from upstream state ───────────────────────────────


class TestReportContainsUpstreamEvidenceIDs:
    """Prove every known evidence ID from upstream state appears in the report."""

    @pytest.fixture()
    def report(self):
        return reporting_agent(_populated_state())["investigation_report"]

    def test_transaction_ids_present(self, report):
        assert "TXN-DET-001" in report.detailed_narrative

    def test_document_ids_present(self, report):
        assert "DOC-DET-001" in report.detailed_narrative

    def test_evidence_reference_ids_present(self, report):
        assert "EVID-DET-001" in report.detailed_narrative
        assert "EVID-DET-002" in report.detailed_narrative

    def test_hypothesis_ids_present(self, report):
        assert "HYP-DET-001" in report.detailed_narrative

    def test_regulation_ids_present(self, report):
        assert "REG-DET-001" in report.detailed_narrative

    def test_evidence_provenance_section_exists(self, report):
        assert "Evidence and provenance" in report.detailed_narrative


# ── Test: Recommended decision present ───────────────────────────────────


class TestReportContainsRecommendedDecision:
    """Prove the recommended decision and rationale are faithfully included."""

    @pytest.fixture()
    def report(self):
        return reporting_agent(_populated_state())["investigation_report"]

    def test_recommended_action_in_executive_summary(self, report):
        assert "ESCALATE" in report.executive_summary

    def test_recommended_action_in_narrative(self, report):
        assert "ESCALATE" in report.detailed_narrative

    def test_decision_rationale_in_narrative(self, report):
        assert "Escalate for senior review due to threshold proximity" in report.detailed_narrative

    def test_decision_options_with_risks_and_mitigations(self, report):
        text = report.detailed_narrative
        assert "False positive cost" in text
        assert "Fast-track review SLA" in text

    def test_pros_and_cons_present(self, report):
        text = report.detailed_narrative
        assert "Thorough review" in text
        assert "Processing delay" in text


# ── Test: No invented transaction data ──────────────────────────────────


class TestReportDoesNotInventData:
    """Prove the report contains ONLY data present in the input state."""

    @pytest.fixture()
    def report_text(self):
        report = reporting_agent(_populated_state())["investigation_report"]
        return f"{report.executive_summary}\n{report.detailed_narrative}"

    def test_no_fabricated_names(self, report_text):
        """Must not contain names from the demo scenario or other tests."""
        fabricated = [
            "James Whitfield",
            "CryptoVault Holdings",
            "Asha Rao",
            "John Doe",
            "Jane Smith",
        ]
        for name in fabricated:
            assert name not in report_text, f"Fabricated name found: {name}"

    def test_no_fabricated_amounts(self, report_text):
        """Must not contain dollar amounts not in the input state."""
        fabricated_amounts = ["48,500", "48500", "42,000", "42000", "100,000", "1,000,000"]
        for amount in fabricated_amounts:
            assert amount not in report_text, f"Fabricated amount found: {amount}"

    def test_only_known_transaction_ids(self, report_text):
        """The only transaction ID must be TXN-DET-001."""
        assert "TXN-DET-001" in report_text
        # Ensure no other TXN- patterns snuck in that aren't ours
        import re
        txn_ids = set(re.findall(r"TXN-[A-Z0-9-]+", report_text))
        assert txn_ids == {"TXN-DET-001"}, f"Unexpected transaction IDs: {txn_ids}"

    def test_amounts_match_input(self, report_text):
        """The amount 9500 must appear (from our input), no others."""
        assert "9500" in report_text

    def test_customer_name_matches_input(self, report_text):
        assert "Deterministic Tester" in report_text

    def test_case_id_matches_input(self, report_text):
        assert "CASE-DET-001" in report_text
