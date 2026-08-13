"""Decision Optimization node.

Delegates to the Decision Agent to produce DecisionOption objects.
No AI or external API calls — all values are deterministic placeholders.

Round 2: Calls the Decision Agent skeleton.
"""

from typing import Any

from app.agents.decision_agent import decision_agent
from app.schemas.investigation_state import (
    CurrentStage,
    InvestigationState,
)


def decision_node(state: Any) -> dict:
    """Execute the Decision Optimization step.

    Delegates to decision_agent() for decision option generation,
    then advances the stage to DECISION.
    """
    # Build an InvestigationState from the raw dict that LangGraph passes
    if isinstance(state, dict):
        investigation_state = InvestigationState(**state)
    else:
        investigation_state = state

    # Delegate to the Decision Agent
    agent_result = decision_agent(investigation_state)

    # Merge agent result with stage advancement
    agent_result["current_stage"] = CurrentStage.DECISION

    return agent_result
