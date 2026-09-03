import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_gemini_boundary(request):
    """Globally mock the Gemini boundary for offline tests to prevent live API calls.
    
    This fulfills the requirement: 'Offline tests must mock the Gemini boundary.'
    """
    # Do not mock if testing the Gemini client itself or running grounding tests!
    if "test_gemini_client" in str(request.node.fspath) or "grounding" in str(request.node.fspath):
        yield
        return
        
    def fake_generate(self, prompt, response_schema=None):
        if response_schema is None:
            return "Fake plain text response"
            
        schema_name = response_schema.__name__
        
        if schema_name == "ContextIntelligence":
            from app.schemas.investigation_state import ContextIntelligence, AgentStatus
            return ContextIntelligence(
                status=AgentStatus.COMPLETED,
                context_summary="Fake summary",
                key_indicators=["Fake indicator"],
                anomalies=[],
                risk_score=0.5
            )
        elif schema_name == "HypothesesResponse":
            from app.agents.reasoning_agent import HypothesesResponse
            from app.schemas.investigation_state import Hypothesis
            return HypothesesResponse(
                hypotheses=[
                    Hypothesis(
                        hypothesis_id="HYP-FAKE",
                        title="Fake Hypothesis",
                        description="Fake description",
                        confidence=0.9,
                        supporting_evidence=["E1"],
                        contradicting_evidence=["E2"]
                    )
                ]
            )
        elif schema_name == "EvidenceComplianceValidation":
            from app.schemas.investigation_state import EvidenceComplianceValidation, AgentStatus
            return EvidenceComplianceValidation(
                status=AgentStatus.COMPLETED,
                compliance_mappings=[],
                evidence_gaps=[],
                validation_summary="Fake compliance validation",
            )
        elif schema_name == "_DecisionOptionsResponse":
            from app.agents.decision_agent import _DecisionOptionsResponse
            from app.schemas.investigation_state import DecisionAction, DecisionOption
            return _DecisionOptionsResponse(
                options=[
                    DecisionOption(option_id="OPT-ESCALATE", action=DecisionAction.ESCALATE, rationale="e", confidence=0.9, risk_score=0.9, pros=["p1", "p2"], cons=["c1", "c2"], risks=["r1", "r2"], mitigation=["m1", "m2"]),
                    DecisionOption(option_id="OPT-ALLOW", action=DecisionAction.ALLOW, rationale="a", confidence=0.8, risk_score=0.1, pros=["p1", "p2"], cons=["c1", "c2"], risks=["r1", "r2"], mitigation=["m1", "m2"]),
                    DecisionOption(option_id="OPT-HOLD", action=DecisionAction.HOLD, rationale="h", confidence=0.8, risk_score=0.5, pros=["p1", "p2"], cons=["c1", "c2"], risks=["r1", "r2"], mitigation=["m1", "m2"]),
                    DecisionOption(option_id="OPT-BLOCK", action=DecisionAction.BLOCK, rationale="b", confidence=0.8, risk_score=0.8, pros=["p1", "p2"], cons=["c1", "c2"], risks=["r1", "r2"], mitigation=["m1", "m2"])
                ],
                recommended_decision=DecisionAction.HOLD,
                decision_rationale="why hold"
            )
        elif schema_name == "InvestigationReport":
            from app.schemas.investigation_state import InvestigationReport, AgentStatus
            return InvestigationReport(
                status=AgentStatus.COMPLETED,
                executive_summary="Fake executive summary",
                detailed_narrative="Fake detailed narrative",
            )
            
        raise ValueError(f"Mock does not know how to handle schema: {schema_name}")

    mock_client = MagicMock()
    mock_client.generate.side_effect = lambda prompt, response_schema=None: fake_generate(
        mock_client, prompt, response_schema
    )

    # Patch agent-local factories before a real Gemini client is constructed.
    with patch(
        "app.agents.reasoning_agent.get_reasoning_client",
        return_value=mock_client,
    ), patch(
        "app.agents.compliance_agent.get_reasoning_client",
        return_value=mock_client,
    ), patch(
        "app.agents.decision_agent.get_reasoning_client",
        return_value=mock_client,
    ):
        yield
