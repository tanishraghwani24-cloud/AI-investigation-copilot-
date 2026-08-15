"""Investigation workflow executor.

Provides interfaces to invoke the compiled LangGraph investigation pipeline,
with optional per-node persistence to Postgres.
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import DocumentRepository, InvestigationRepository
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

    This closes the Round 2 gap where ``document_service`` extracted
    text but never persisted the result through ``DocumentRepository``.
    Supporting documents listed in ``case_input`` are now written to
    the ``document_records`` table before the pipeline begins.

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

    # 1. Persist initial investigation case
    await inv_repo.create(session, state.case_id, state_dict)

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

    # 3. Stream through nodes, persisting after each one
    accumulated_state = state_dict.copy()

    for chunk in investigation_graph.stream(
        state_dict, stream_mode="updates",
    ):
        for _node_name, node_output in chunk.items():
            serialized_output = _serialize_node_output(node_output)
            accumulated_state.update(serialized_output)
            accumulated_state["updated_at"] = (
                datetime.now(timezone.utc).isoformat()
            )
            await inv_repo.update_state(
                session, state.case_id, accumulated_state,
            )

    await session.commit()

    return InvestigationState(**accumulated_state)
