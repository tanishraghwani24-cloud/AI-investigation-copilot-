"""Document upload routes.

Provides the POST /api/investigations/{case_id}/documents endpoint
for uploading supporting documents to an investigation case.

Round 1: Accepts a file, stores it to the local filesystem, creates
a SupportingDocument with processing_status=PENDING, and stores the
metadata in the in-memory document store.  No extraction, parsing,
OCR, or AI analysis.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.investigation_state import (
    ProcessingStatus,
    SupportingDocument,
)
from app.services.document_store import add_document, get_documents

router = APIRouter()

# ── Known case IDs for Round 1 validation ────────────────────────────
# The existing investigations endpoint returns a hardcoded mock with
# this case_id.  We also maintain a module-level set that can be
# extended at runtime (e.g. when a new investigation is created).
_KNOWN_CASE_IDS: set[str] = {"CASE-2025-00042"}

# ── Upload directory ─────────────────────────────────────────────────
_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"


def _ensure_upload_dir(case_id: str) -> Path:
    """Create the upload directory for a case if it doesn't exist."""
    case_dir = _UPLOAD_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


@router.post(
    "/investigations/{case_id}/documents",
    response_model=SupportingDocument,
)
async def upload_document(
    case_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(default="OTHER"),
) -> SupportingDocument:
    """Upload a supporting document for an investigation case.

    Accepts a file upload, stores the raw file to the local filesystem,
    creates a SupportingDocument record with processing_status=PENDING,
    and stores it in the in-memory document store.

    No document extraction, parsing, or analysis is performed.
    Those will be added in future rounds.

    Args:
        case_id: The investigation case identifier.
        file: The uploaded file.
        document_type: Type of document (e.g. INVOICE, ID_SCAN, BANK_STATEMENT).

    Returns:
        The created SupportingDocument metadata.

    Raises:
        HTTPException 404: If the case_id is not found.
    """
    # -- Validate case exists --
    if case_id not in _KNOWN_CASE_IDS:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation case not found: {case_id}",
        )

    # -- Generate unique document ID --
    document_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"

    # -- Store raw file to local filesystem --
    case_dir = _ensure_upload_dir(case_id)
    file_extension = os.path.splitext(file.filename or "")[1] if file.filename else ""
    stored_filename = f"{document_id}{file_extension}"
    file_path = case_dir / stored_filename

    contents = await file.read()
    file_path.write_bytes(contents)

    # -- Build file URL (local path for Round 1) --
    file_url = str(file_path)

    # -- Create SupportingDocument with PENDING status --
    now = datetime.now(timezone.utc)
    document = SupportingDocument(
        document_id=document_id,
        document_type=document_type,
        file_name=file.filename,
        file_url=file_url,
        uploaded_at=now,
        processing_status=ProcessingStatus.PENDING,
    )

    # -- Store metadata in the in-memory store --
    add_document(case_id, document)

    return document


@router.get(
    "/investigations/{case_id}/documents",
    response_model=list[SupportingDocument],
)
async def list_documents(case_id: str) -> list[SupportingDocument]:
    """List all documents for an investigation case.

    Args:
        case_id: The investigation case identifier.

    Returns:
        List of SupportingDocument metadata objects.

    Raises:
        HTTPException 404: If the case_id is not found.
    """
    if case_id not in _KNOWN_CASE_IDS:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation case not found: {case_id}",
        )

    return get_documents(case_id)
