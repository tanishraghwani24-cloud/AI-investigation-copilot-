"""Round 5 coverage for the complete, evidence-aware reporting agent."""

from datetime import datetime

from app.agents.reporting_agent import reporting_agent
from app.graph.nodes.reporting_node import reporting_node
from app.schemas.investigation_state import (
    AgentStatus, AnomalyType, CaseInput, ComplianceMapping, ContextIntelligence,
    CurrentStage, CustomerProfile, DecisionAction, DecisionOptimization,
    DecisionOption, DetectedAnomaly, EvidenceComplianceValidation, Hypothesis,
    InvestigationReasoning, SeverityLevel, SupportingDocument, Transaction,
    create_initial_state,
)


def _complete_state():
    state = create_initial_state("CASE-R5-901", CaseInput(
        alert_reason="Unusual cross-border transfer pattern",
        customer_profile=CustomerProfile(customer_id="CUST-R5", name="Asha Rao", risk_rating="HIGH"),
        transactions=[Transaction(transaction_id="TXN-R5", amount=42000, currency="USD", timestamp=datetime(2026, 2, 3, 10), sender_account="SRC-R5", receiver_account="DST-R5", transaction_type="WIRE")],
        supporting_documents=[SupportingDocument(document_id="DOC-R5", document_type="BANK_STATEMENT", file_name="statement.pdf", evidence_references=["EVID-R5"])],
    ))
    return state.model_copy(update={
        "context_intelligence": ContextIntelligence(status=AgentStatus.COMPLETED, context_summary="Transfers deviate from stated profile", risk_score=.82, key_indicators=["Rapid international movement"], anomalies=[DetectedAnomaly(anomaly_id="ANOM-R5", anomaly_type=AnomalyType.NETWORK, severity=SeverityLevel.HIGH, description="New destination network", related_transactions=["TXN-R5"])]),
        "investigation_reasoning": InvestigationReasoning(status=AgentStatus.COMPLETED, reasoning_summary="Evidence supports further review", recommended_actions=["Verify source of funds"], hypotheses=[Hypothesis(hypothesis_id="HYP-R5", title="Possible layering", description="Pattern is consistent with layering but not conclusive", confidence=.73, supporting_evidence=["TXN-R5", "EVID-R5"], contradicting_evidence=["DOC-R5"])]),
        "evidence_compliance_validation": EvidenceComplianceValidation(status=AgentStatus.COMPLETED, validation_summary="Traceable review complete", evidence_gaps=["No source-of-funds document"], compliance_mappings=[ComplianceMapping(regulation_id="AML-R5", regulation_name="AML monitoring", description="Transaction requires review", is_violated=False, severity=SeverityLevel.MEDIUM, evidence_references=["TXN-R5", "EVID-R5"]), ComplianceMapping(regulation_id="KYC-R5", regulation_name="KYC completeness", description="Insufficient evidence to confirm KYC completeness.", is_violated=False, severity=SeverityLevel.LOW)]),
        "decision_optimization": DecisionOptimization(status=AgentStatus.COMPLETED, recommended_decision=DecisionAction.HOLD, decision_rationale="Hold pending source-of-funds verification", decision_options=[DecisionOption(option_id="OPT-HOLD", action=DecisionAction.HOLD, rationale="Preserves funds during review", confidence=.86, risk_score=.77, pros=["Limits exposure"], cons=["Customer delay"], risks=["False positive"], mitigation=["Expedite review"])])
    })


def test_full_state_produces_traceable_polished_report():
    report = reporting_agent(_complete_state())["investigation_report"]
    text = report.detailed_narrative

    for expected in ("CASE-R5-901", "Asha Rao", "Context and reasoning findings", "Possible layering", "TXN-R5", "EVID-R5", "AML-R5", "KYC completeness", "Insufficient evidence", "HOLD", "Hold pending source-of-funds verification", "No source-of-funds document", "Expedite review"):
        assert expected in text
    assert report.status == AgentStatus.COMPLETED
    assert report.graphs is not None
    assert "James Whitfield" not in text


def test_sparse_state_is_safe_and_preserves_graph_contract():
    state = create_initial_state("CASE-SPARSE", CaseInput())
    report = reporting_agent(state)["investigation_report"]

    assert "CASE-SPARSE" in report.executive_summary
    assert "Unavailable" in report.detailed_narrative
    assert "None provided" in report.detailed_narrative
    result = reporting_node(state.model_dump())
    assert result["current_stage"] == CurrentStage.DONE
    assert result["investigation_report"].status == AgentStatus.COMPLETED


def test_compliance_without_references_is_explicitly_unsupported():
    state = _complete_state()
    compliance = state.evidence_compliance_validation.model_copy(update={
        "compliance_mappings": [ComplianceMapping(regulation_id="REG-NO-EVID", regulation_name="Unverified finding", description="Upstream finding", severity=SeverityLevel.LOW)]
    })
    text = reporting_agent(state.model_copy(update={"evidence_compliance_validation": compliance}))["investigation_report"].detailed_narrative

    assert "REG-NO-EVID" in text
    assert "Insufficient evidence — no evidence references were supplied" in text
