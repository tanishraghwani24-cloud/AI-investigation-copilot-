import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def _bypass_api_auth():
    """Bypass the shared-secret API auth dependency for the existing suite.

    These tests exercise business logic via TestClient and predate the
    P1 API-auth hardening; they were never written to supply X-API-Key.
    Auth itself (missing/invalid/valid credential, open health route) is
    verified separately — see app/api/tests/test_api_auth.py.
    """
    from app.main import app
    from app.core.security import require_api_key

    app.dependency_overrides[require_api_key] = lambda: None
    yield
    app.dependency_overrides.pop(require_api_key, None)


@pytest.fixture(autouse=True)
def _demo_mode_off_by_default():
    """Pin DEMO_MODE off so results never depend on a developer's local .env.

    A machine running the demo has DEMO_MODE=true in .env, which would
    otherwise swap real clients for the deterministic stand-in mid-suite and
    silently change behaviour (blank-PDF OCR, for one). Tests that want demo
    mode set it explicitly.
    """
    from app.core.config import settings

    previous = getattr(settings, "DEMO_MODE", False)
    settings.DEMO_MODE = False
    yield
    settings.DEMO_MODE = previous


@pytest.fixture(autouse=True)
def _alert_simulator_off_by_default():
    """Keep the Mock Bank simulator out of the suite.

    TestClient runs the app's startup hooks, so leaving the simulator enabled
    would spawn a background loop writing simulated transactions and alerts
    during unrelated tests. Simulator tests drive it directly instead.
    """
    from app.core.config import settings

    previous = getattr(settings, "MOCK_BANK_SIMULATOR_ENABLED", True)
    settings.MOCK_BANK_SIMULATOR_ENABLED = False
    yield
    settings.MOCK_BANK_SIMULATOR_ENABLED = previous


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Reset the in-memory rate limiter between tests.

    TestClient reuses a fixed client IP, so without this, sequential tests
    hitting a rate-limited route (e.g. document upload) would trip each
    other's limits.
    """
    from app.core.rate_limit import _hits

    _hits.clear()
    yield
    _hits.clear()


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
