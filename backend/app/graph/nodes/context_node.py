"""Context & Evidence Intelligence node.

Delegates to the Context Agent to produce a ContextIntelligence object.
No AI or external API calls — all values are deterministic.

Round 2: Calls the Context Agent (pure-Python analysis).
"""

from typing import Any

from app.agents.context_agent import context_agent
from app.schemas.investigation_state import (
    CurrentStage,
    InvestigationState,
)


async def context_node(state: Any) -> dict:
    """Execute the Context & Evidence Intelligence step.

    Delegates to context_agent() for context intelligence generation,
    then advances the stage to CONTEXT.
    """
    # Build an InvestigationState from the raw dict that LangGraph passes
    if isinstance(state, dict):
        investigation_state = InvestigationState(**state)
    else:
        investigation_state = state

    # Delegate to the Context Agent
    agent_result = await context_agent(investigation_state)

    # Merge agent result with stage advancement
    agent_result["current_stage"] = CurrentStage.CONTEXT

    return agent_result
