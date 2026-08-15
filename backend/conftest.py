import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_gemini_boundary(request):
    """Globally mock the Gemini boundary for offline tests to prevent live API calls.
    
    This fulfills the requirement: 'Offline tests must mock the Gemini boundary.'
    """
    # Do not mock if testing the Gemini client itself!
    if "test_gemini_client" in str(request.node.fspath):
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
                policy_violations=[],
                regulatory_flags=[],
                missing_information=["None"]
            )
        elif schema_name == "_DecisionOptionsResponse":
            from app.agents.decision_agent import _DecisionOptionsResponse
            from app.schemas.investigation_state import DecisionOption
            return _DecisionOptionsResponse(
                options=[
                    DecisionOption(option_id="OPT-ESCALATE", action="ESCALATE", rationale="a", risk_mitigation=["b"], estimated_impact="c", confidence=0.9, risk_score=0.9, pros=["p"], cons=["c"], risks=["r"], mitigation=["m"]),
                    DecisionOption(option_id="OPT-APPROVE", action="ALLOW", rationale="a", risk_mitigation=["b"], estimated_impact="c", confidence=0.8, risk_score=0.1, pros=["p"], cons=["c"], risks=["r"], mitigation=["m"]),
                    DecisionOption(option_id="OPT-HOLD", action="HOLD", rationale="a", risk_mitigation=["b"], estimated_impact="c", confidence=0.8, risk_score=0.5, pros=["p"], cons=["c"], risks=["r"], mitigation=["m"]),
                    DecisionOption(option_id="OPT-BLOCK", action="BLOCK", rationale="a", risk_mitigation=["b"], estimated_impact="c", confidence=0.8, risk_score=0.8, pros=["p"], cons=["c"], risks=["r"], mitigation=["m"])
                ]
            )
        elif schema_name == "InvestigationReport":
            from app.schemas.investigation_state import InvestigationReport, AgentStatus, GraphData
            return InvestigationReport(
                status=AgentStatus.COMPLETED,
                executive_summary="Fake executive summary",
                case_timeline=["Event 1"],
                evidence_log=["Evidence 1"],
                graphs=GraphData(
                    entity_relationship_graph="Fake graph",
                    reasoning_graph="Fake graph",
                    decision_comparison_graph="Fake graph",
                    investigation_timeline=["Fake timeline"]
                )
            )
            
        raise ValueError(f"Mock does not know how to handle schema: {schema_name}")

    # Patch the generate method on the GeminiClient class
    with patch("app.services.gemini_client.GeminiClient.generate", new=fake_generate):
        yield
