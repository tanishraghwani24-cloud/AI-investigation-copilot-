"""LangGraph passthrough pipeline builder.

Constructs and compiles a StateGraph identical in structure to the
main investigation graph, but every node is a no-op that passes
``InvestigationState`` through unchanged.

Exists as a separate module because modifying the existing builder
would break the hardcoded-data nodes used by Round 1 tests.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes.passthrough import (
    compliance_passthrough,
    context_passthrough,
    decision_passthrough,
    reasoning_passthrough,
    reporting_passthrough,
)
from app.schemas.investigation_state import InvestigationState

# -- Node identifiers (same names as the main pipeline) --
CONTEXT = "context"
REASONING = "reasoning"
COMPLIANCE = "compliance"
DECISION = "decision"
REPORTING = "reporting"


def build_passthrough_graph() -> CompiledStateGraph:
    """Build, wire, and compile the passthrough StateGraph.

    Execution order:
        START → Context → Reasoning → Compliance → Decision → Reporting → END

    Every node returns the state unchanged.
    """
    graph = StateGraph(InvestigationState)

    graph.add_node(CONTEXT, context_passthrough)
    graph.add_node(REASONING, reasoning_passthrough)
    graph.add_node(COMPLIANCE, compliance_passthrough)
    graph.add_node(DECISION, decision_passthrough)
    graph.add_node(REPORTING, reporting_passthrough)

    graph.add_edge(START, CONTEXT)
    graph.add_edge(CONTEXT, REASONING)
    graph.add_edge(REASONING, COMPLIANCE)
    graph.add_edge(COMPLIANCE, DECISION)
    graph.add_edge(DECISION, REPORTING)
    graph.add_edge(REPORTING, END)

    return graph.compile()


# Compiled passthrough graph singleton
passthrough_graph = build_passthrough_graph()
