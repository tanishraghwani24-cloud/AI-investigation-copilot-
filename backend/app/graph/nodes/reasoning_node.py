"""Investigation Reasoning node.

Delegates to the Reasoning Agent (Gemini-powered) to produce an
InvestigationReasoning object with a validated Hypothesis.

Round 2: Calls the Reasoning Agent which uses Gemini.
"""

from typing import Any

from app.agents.reasoning_agent import reasoning_agent
from app.schemas.investigation_state import (
    CurrentStage,
    InvestigationState,
)


def reasoning_node(state: Any) -> dict:
    """Execute the Investigation Reasoning step.

    Delegates to reasoning_agent() for hypothesis generation,
    then advances the stage to REASONING.
    """
    # Build an InvestigationState from the raw dict that LangGraph passes
    if isinstance(state, dict):
        investigation_state = InvestigationState(**state)
    else:
        investigation_state = state

    # Delegate to the Reasoning Agent
    agent_result = reasoning_agent(investigation_state)

    # Merge agent result with stage advancement
    agent_result["current_stage"] = CurrentStage.REASONING

    return agent_result
