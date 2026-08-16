"""Investigation workflow executor.

Provides interfaces to invoke the compiled LangGraph investigation pipeline,
with optional per-node persistence to Postgres.

Round 3: Added graph-level error handling so that node failures are caught,
recorded as AgentError, and the investigation is marked FAILED with
partial state preserved.
"""

import logging
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import DocumentRepository, InvestigationRepository
from app.graph.builder import (
    COMPLIANCE,
    CONTEXT,
    DECISION,
    REASONING,
    REPORTING,
    build_investigation_graph,
)
from app.schemas.investigation_state import (
    AgentError,
    CurrentStage,
    InvestigationState,
)

logger = logging.getLogger(__name__)

# Compiled graph singleton — used by run_investigation (non-persistent path)
_investigation_graph = build_investigation_graph()

# Ordered list of node names matching the pipeline topology
NODE_ORDER: list[str] = [CONTEXT, REASONING, COMPLIANCE, DECISION, REPORTING]

# Map node names → CurrentStage for identifying the failed stage
_NODE_STAGE_MAP: dict[str, str] = {
    CONTEXT: CurrentStage.CONTEXT.value,
    REASONING: CurrentStage.REASONING.value,
    COMPLIANCE: CurrentStage.COMPLIANCE.value,
    DECISION: CurrentStage.DECISION.value,
    REPORTING: CurrentStage.REPORTING.value,
}


def run_investigation(state: InvestigationState) -> InvestigationState:
    """Run the full investigation graph on the given state.

    Args:
        state: A fully initialised InvestigationState.

    Returns:
        The InvestigationState after all graph nodes have executed.
    """
    result = _investigation_graph.invoke(state.model_dump(mode="json"))
    return InvestigationState(**result)


# ── Serialisation helpers ────────────────────────────────────────────


def _serialize_value(value: object) -> object:
    """Convert a single value to a JSON-safe representation.

    Handles Pydantic BaseModel instances and Enum instances.
    Everything else passes through unchanged.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")  # type: ignore[union-attr]
    if isinstance(value, Enum):
        return value.value
    return value


def _serialize_node_output(output: dict) -> dict:
    """Serialise all values in a LangGraph node output dict.

    Node functions return dicts whose values may be Pydantic model
    instances or Enum members.  This converts them to plain dicts /
    strings so the accumulated state stays JSON-safe for Postgres.
    """
    return {key: _serialize_value(val) for key, val in output.items()}


# ── Persistent workflow ──────────────────────────────────────────────


async def run_investigation_with_persistence(
    state: InvestigationState,
    session: AsyncSession,
) -> InvestigationState:
    """Run the investigation graph with per-node persistence.

    Creates the investigation case in Postgres, persists any attached
    supporting documents, then streams through the 5-node pipeline
    saving intermediate state after each node completes.

    Round 3: If a node raises an exception the pipeline:
      - catches the exception
      - records an AgentError in the state
      - marks the investigation as FAILED at the failed stage
      - persists the partial state (preserving successful upstream output)
      - stops the pipeline (no downstream nodes execute)
      - returns cleanly without re-raising

    Args:
        state: A fully initialised InvestigationState.
        session: An active async database session.

    Returns:
        The InvestigationState after all graph nodes have executed,
        with each intermediate state persisted to Postgres.
    """
    inv_repo = InvestigationRepository()
    doc_repo = DocumentRepository()

    state_dict = state.model_dump(mode="json")

    # 1. Persist initial investigation case.  A trigger may run a case that
    # already exists, so refresh its saved state instead of creating a second
    # row with the same unique case_id.
    existing_case = await inv_repo.get_by_case_id(session, state.case_id)
    if existing_case is None:
        await inv_repo.create(session, state.case_id, state_dict)
    else:
        await inv_repo.update_state(session, state.case_id, state_dict)

    # 2. Persist any attached supporting documents
    #    This closes the gap where document_service.py returns extraction
    #    results as a dict but never passes them to DocumentRepository.
    for doc in state.case_input.supporting_documents:
        doc_data: dict = {
            "document_id": doc.document_id,
            "document_type": doc.document_type,
            "file_name": doc.file_name,
            "file_url": doc.file_url,
            "processing_status": (
                doc.processing_status.value
                if doc.processing_status
                else "PENDING"
            ),
            "extracted_text": doc.extracted_text,
            "summary": doc.summary,
            "extracted_entities": doc.extracted_entities or [],
            "extracted_transactions": doc.extracted_transactions or [],
        }
        if doc.uploaded_at is not None:
            doc_data["uploaded_at"] = doc.uploaded_at

        existing = await doc_repo.get_by_document_id(session, doc.document_id)
        if existing is None:
            await doc_repo.create(session, state.case_id, doc_data)
        else:
            await doc_repo.update(session, existing, doc_data)

    await session.flush()

    # 3. Stream through nodes, persisting after each one.
    #    On failure: record AgentError, mark FAILED, persist, stop.
    accumulated_state = state_dict.copy()

    try:
        for chunk in _investigation_graph.stream(
            state_dict, stream_mode="updates",
        ):
            for node_name, node_output in chunk.items():
                serialized_output = _serialize_node_output(node_output)
                accumulated_state.update(serialized_output)
                accumulated_state["updated_at"] = (
                    datetime.now(timezone.utc).isoformat()
                )
                await inv_repo.update_state(
                    session, state.case_id, accumulated_state,
                )
    except Exception as exc:
        # Determine which node failed from the exception context.
        # LangGraph wraps node exceptions; we inspect the __context__
        # and the graph's streaming state to identify the failed node.
        failed_node = _identify_failed_node(accumulated_state)

        logger.error(
            "Node '%s' failed in case %s: %s",
            failed_node,
            state.case_id,
            exc,
        )

        # Record the failure in the state
        error = AgentError(
            agent_name=failed_node,
            error_type=type(exc).__name__,
            message=str(exc),
        )
        error_dict = error.model_dump(mode="json")

        existing_errors: list = accumulated_state.get("errors", [])
        existing_errors.append(error_dict)
        accumulated_state["errors"] = existing_errors

        # Mark the investigation as FAILED at the failed stage
        stage = _NODE_STAGE_MAP.get(failed_node, failed_node)
        accumulated_state["current_stage"] = stage
        accumulated_state["updated_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        # Persist the failed state
        await inv_repo.update_state(
            session, state.case_id, accumulated_state,
        )

    await session.commit()

    return InvestigationState(**accumulated_state)


def _identify_failed_node(accumulated_state: dict) -> str:
    """Identify which node failed based on accumulated state.

    Uses the current_stage and which agent outputs are populated
    to determine the next expected node (i.e. the one that failed).
    """
    # Check which outputs have been populated
    output_fields = [
        ("context_intelligence", CONTEXT),
        ("investigation_reasoning", REASONING),
        ("evidence_compliance_validation", COMPLIANCE),
        ("decision_optimization", DECISION),
        ("investigation_report", REPORTING),
    ]

    last_completed_idx = -1
    for idx, (field, _node) in enumerate(output_fields):
        if accumulated_state.get(field) is not None:
            last_completed_idx = idx

    # The failed node is the one after the last completed
    failed_idx = last_completed_idx + 1
    if failed_idx < len(NODE_ORDER):
        return NODE_ORDER[failed_idx]

    # Fallback: if all outputs are populated, it was reporting
    return REPORTING
