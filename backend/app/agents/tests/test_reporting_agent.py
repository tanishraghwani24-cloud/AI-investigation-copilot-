"""Tests for state-derived Reporting Agent output."""

from datetime import datetime

from app.agents.reporting_agent import reporting_agent
from app.graph.nodes.reporting_node import reporting_node
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CurrentStage,
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


def _state(case_id: str, customer_id: str, transaction_id: str, action: DecisionAction):
    case_input = CaseInput(
        transactions=[Transaction(
            transaction_id=transaction_id,
            amount=1250.0,
            timestamp=datetime(2026, 1, 2, 12, 0),
            sender_account=f"SRC-{case_id}",
            receiver_account=f"DST-{case_id}",
            transaction_type="WIRE",
        )],
        customer_profile=CustomerProfile(customer_id=customer_id, name=f"Customer {customer_id}"),
        supporting_documents=[SupportingDocument(
            document_id=f"DOC-{case_id}",
            document_type="BANK_STATEMENT",
            evidence_references=[f"EVID-{case_id}"],
        )],
        alert_reason=f"Alert for {case_id}",
    )
    state = create_initial_state(case_id, case_input)
    return state.model_copy(update={
        "context_intelligence": ContextIntelligence(
            status=AgentStatus.COMPLETED,
            context_summary=f"Context for {case_id}",
            key_indicators=[f"Indicator {case_id}"],
            risk_score=0.6,
        ),
        "investigation_reasoning": InvestigationReasoning(
            status=AgentStatus.COMPLETED,
            hypotheses=[Hypothesis(
                hypothesis_id=f"HYP-{case_id}",
                title=f"Hypothesis {case_id}",
                description=f"Reasoning for {case_id}",
                confidence=0.7,
                supporting_evidence=[transaction_id],
            )],
        ),
        "evidence_compliance_validation": EvidenceComplianceValidation(
            status=AgentStatus.COMPLETED,
            compliance_mappings=[ComplianceMapping(
                regulation_id=f"REG-{case_id}",
                regulation_name=f"Rule {case_id}",
                severity=SeverityLevel.MEDIUM,
                evidence_references=[f"EVID-{case_id}"],
            )],
        ),
        "decision_optimization": DecisionOptimization(
            status=AgentStatus.COMPLETED,
            decision_options=[DecisionOption(
                option_id=f"OPT-{case_id}",
                action=action,
                rationale=f"Rationale for {case_id}",
                confidence=0.8,
            )],
            recommended_decision=action,
            decision_rationale=f"Decision rationale for {case_id}",
        ),
    })


def test_reporting_agent_uses_actual_state_and_preserves_outputs():
    state = _state("CASE-A", "CUST-A", "TXN-A", DecisionAction.HOLD)

    report = reporting_agent(state)["investigation_report"]

    assert report.executive_summary is not None
    assert "CASE-A" in report.executive_summary
    assert "Customer CUST-A" in report.detailed_narrative
    assert "Hypothesis CASE-A" in report.detailed_narrative
    assert "Rule CASE-A" in report.detailed_narrative
    assert "HOLD" in report.detailed_narrative
    assert "Decision rationale for CASE-A" in report.detailed_narrative
    assert "EVID-CASE-A" in report.detailed_narrative


def test_reporting_agent_does_not_insert_demo_case_data():
    report = reporting_agent(_state("CASE-UNIQUE", "CUST-UNIQUE", "TXN-UNIQUE", DecisionAction.ALLOW))["investigation_report"]
    text = f"{report.executive_summary}\n{report.detailed_narrative}"

    assert "James Whitfield" not in text
    assert "CryptoVault Holdings" not in text
    assert "48,500" not in text


def test_different_investigations_produce_different_reports():
    first = reporting_agent(_state("CASE-ONE", "CUST-ONE", "TXN-ONE", DecisionAction.HOLD))["investigation_report"]
    second = reporting_agent(_state("CASE-TWO", "CUST-TWO", "TXN-TWO", DecisionAction.BLOCK))["investigation_report"]

    assert first.executive_summary != second.executive_summary
    assert first.detailed_narrative != second.detailed_narrative
    assert first.graphs.decision_comparison_graph != second.graphs.decision_comparison_graph


def test_reporting_node_integrates_with_graph_state_contract():
    state = _state("CASE-NODE", "CUST-NODE", "TXN-NODE", DecisionAction.ESCALATE)

    result = reporting_node(state.model_dump())

    assert result["current_stage"] == CurrentStage.DONE
    assert result["investigation_report"].status == AgentStatus.COMPLETED
