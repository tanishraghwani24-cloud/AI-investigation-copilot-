"""Investigation workflow executor.

Provides a simple interface to invoke the compiled LangGraph
investigation pipeline.
"""

from app.graph.builder import investigation_graph
from app.schemas.investigation_state import InvestigationState


def run_investigation(state: InvestigationState) -> InvestigationState:
    """Run the full investigation graph on the given state.

    Args:
        state: A fully initialised InvestigationState.

    Returns:
        The InvestigationState after all graph nodes have executed.
    """
    result = investigation_graph.invoke(state.model_dump(mode="json"))
    return InvestigationState(**result)
