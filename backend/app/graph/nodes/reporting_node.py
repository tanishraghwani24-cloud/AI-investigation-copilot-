"""Reporting node for the investigation graph."""

from typing import Any

from app.agents.reporting_agent import reporting_agent
from app.schemas.investigation_state import CurrentStage, InvestigationState


def reporting_node(state: Any) -> dict:
    """Delegate report assembly to the Reporting Agent and finish the graph."""
    investigation_state = InvestigationState(**state) if isinstance(state, dict) else state
    agent_result = reporting_agent(investigation_state)
    agent_result["current_stage"] = CurrentStage.DONE
    return agent_result
