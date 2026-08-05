"""LangGraph investigation workflow builder.

Constructs and compiles the StateGraph that orchestrates all
investigation nodes in a fixed linear pipeline.
"""

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    compliance_node,
    context_node,
    decision_node,
    reasoning_node,
    reporting_node,
)
from app.schemas.investigation_state import InvestigationState

# -- Node identifiers --
CONTEXT = "context"
REASONING = "reasoning"
COMPLIANCE = "compliance"
DECISION = "decision"
REPORTING = "reporting"


def build_investigation_graph() -> StateGraph:
    """Build, wire, and compile the investigation StateGraph.

    Execution order:
        START → Context → Reasoning → Compliance → Decision → Reporting → END
    """
    graph = StateGraph(InvestigationState)

    # Register nodes
    graph.add_node(CONTEXT, context_node)
    graph.add_node(REASONING, reasoning_node)
    graph.add_node(COMPLIANCE, compliance_node)
    graph.add_node(DECISION, decision_node)
    graph.add_node(REPORTING, reporting_node)

    # Wire the linear pipeline
    graph.add_edge(START, CONTEXT)
    graph.add_edge(CONTEXT, REASONING)
    graph.add_edge(REASONING, COMPLIANCE)
    graph.add_edge(COMPLIANCE, DECISION)
    graph.add_edge(DECISION, REPORTING)
    graph.add_edge(REPORTING, END)

    return graph.compile()


# Compiled graph singleton
investigation_graph = build_investigation_graph()
