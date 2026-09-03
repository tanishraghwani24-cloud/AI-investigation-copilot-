"""Tests for the Decision Agent — Round 4 Recommendation and Deepening.

Covers:
- Exactly one recommended decision is selected.
- The recommended decision is one of the four generated options.
- decision_rationale is populated and not generic.
- Every option has >=2 pros, cons, risks, and mitigation entries.
- Implementation works with mocked Gemini output.
"""

from unittest.mock import patch

from app.agents.decision_agent import (
    _DecisionOptionsResponse,
    decision_agent,
)
from app.agents.tests.test_decision_agent_options import (
    MOCK_OPTIONS,
    _make_test_state,
)
from app.schemas.investigation_state import DecisionAction

# Enhance the mock options to have >=2 items for pros, cons, risks, mitigations
DEEP_MOCK_OPTIONS = []
for opt in MOCK_OPTIONS:
    new_opt = opt.model_copy(deep=True)
    new_opt.pros.append("Second pro added for Round 4 testing.")
    new_opt.cons.append("Second con added for Round 4 testing.")
    new_opt.risks.append("Second risk added for Round 4 testing.")
    new_opt.mitigation.append("Second mitigation added for Round 4 testing.")
    DEEP_MOCK_OPTIONS.append(new_opt)

MOCK_RESPONSE = _DecisionOptionsResponse(
    options=DEEP_MOCK_OPTIONS,
    recommended_decision=DecisionAction.HOLD,
    decision_rationale="Holding is recommended because it balances risk mitigation while investigations proceed, preserving the customer relationship better than blocking.",
)


class TestDecisionRecommendation:
    """Tests for Round 4 Decision Agent requirements."""

    def test_one_recommendation_selected(self) -> None:
        """Exactly one recommended option is selected."""
        state = _make_test_state()
        with patch("app.agents.decision_agent.get_reasoning_client") as mock:
            mock.return_value.generate.return_value = MOCK_RESPONSE
            result = decision_agent(state)

        decision_opt = result["decision_optimization"]
        assert decision_opt.recommended_decision == DecisionAction.HOLD
        assert decision_opt.recommended_decision in [opt.action for opt in decision_opt.decision_options]

    def test_decision_rationale_populated(self) -> None:
        """decision_rationale is populated and not generic."""
        state = _make_test_state()
        with patch("app.agents.decision_agent.get_reasoning_client") as mock:
            mock.return_value.generate.return_value = MOCK_RESPONSE
            result = decision_agent(state)

        rationale = result["decision_optimization"].decision_rationale
        assert rationale is not None
        assert len(rationale) > 20
        assert "Holding is recommended" in rationale

    def test_deepened_fields_have_at_least_two_entries(self) -> None:
        """Every option has >=2 pros, cons, risks, and mitigations."""
        state = _make_test_state()
        with patch("app.agents.decision_agent.get_reasoning_client") as mock:
            mock.return_value.generate.return_value = MOCK_RESPONSE
            result = decision_agent(state)

        for opt in result["decision_optimization"].decision_options:
            assert len(opt.pros) >= 2
            assert len(opt.cons) >= 2
            assert len(opt.risks) >= 2
            assert len(opt.mitigation) >= 2
