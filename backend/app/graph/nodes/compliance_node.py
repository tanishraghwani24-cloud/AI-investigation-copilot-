"""Evidence & Compliance Validation node."""

from typing import Any

from app.agents.compliance_agent import compliance_agent
from app.schemas.investigation_state import CurrentStage, InvestigationState


def compliance_node(state: Any) -> dict:
    """Delegate compliance validation and advance the investigation stage."""
    investigation_state = InvestigationState(**state) if isinstance(state, dict) else state
    agent_result = compliance_agent(investigation_state)
    agent_result["current_stage"] = CurrentStage.COMPLIANCE
    return agent_result
