"""Passthrough investigation workflow executor.

Mirrors ``workflow.run_investigation`` but uses the passthrough
graph where every node is a no-op.
"""

from app.graph.passthrough_builder import passthrough_graph
from app.schemas.investigation_state import InvestigationState


def run_passthrough_investigation(state: InvestigationState) -> InvestigationState:
    """Run the passthrough investigation graph on the given state.

    The returned state is identical to the input because every
    node is a no-op.

    Args:
        state: A fully initialised InvestigationState.

    Returns:
        The InvestigationState unchanged after all graph nodes executed.
    """
    result = passthrough_graph.invoke(state.model_dump(mode="json"))
    return InvestigationState(**result)
