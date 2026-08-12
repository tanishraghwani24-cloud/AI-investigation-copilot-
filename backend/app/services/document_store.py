"""In-memory document metadata store.

Provides a temporary storage layer for SupportingDocument objects,
keyed by case_id.  This is a Round 1 placeholder — persistent
database storage will be added in a future round.

Thread safety note: This module-level dict is adequate for the
single-process dev server used in Round 1.
"""

from app.schemas.investigation_state import SupportingDocument


# ── In-memory store: case_id → list of SupportingDocument ──────────
_document_store: dict[str, list[SupportingDocument]] = {}


def add_document(case_id: str, document: SupportingDocument) -> None:
    """Store a SupportingDocument for the given case.

    Args:
        case_id: The investigation case identifier.
        document: The SupportingDocument metadata to store.
    """
    if case_id not in _document_store:
        _document_store[case_id] = []
    _document_store[case_id].append(document)


def get_documents(case_id: str) -> list[SupportingDocument]:
    """Retrieve all documents for a given case.

    Args:
        case_id: The investigation case identifier.

    Returns:
        List of SupportingDocument objects, or empty list if none exist.
    """
    return _document_store.get(case_id, [])


def get_document(case_id: str, document_id: str) -> SupportingDocument | None:
    """Retrieve a single document by case_id and document_id.

    Args:
        case_id: The investigation case identifier.
        document_id: The unique document identifier.

    Returns:
        The SupportingDocument if found, otherwise None.
    """
    for doc in _document_store.get(case_id, []):
        if doc.document_id == document_id:
            return doc
    return None


def clear_store() -> None:
    """Clear the entire in-memory store.

    Useful for test isolation.
    """
    _document_store.clear()
