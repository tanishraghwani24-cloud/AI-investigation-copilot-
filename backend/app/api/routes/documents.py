"""Document upload routes.

Provides the POST /api/investigations/{case_id}/documents endpoint
for uploading supporting documents to an investigation case.

Round 2: Accepts a file, stores it to the local filesystem, extracts
text from PDF files using pypdf, persists the SupportingDocument via
DocumentRepository → Postgres.  The Round 1 in-memory store is retired.

Round 3: Adds OCR/Vision fallback for scanned PDFs, image upload
support, entity extraction, and transaction extraction.  All extracted
data is persisted to the database.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path as ApiPath, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import DocumentRepository
from app.db.session import get_db_session
from app.schemas.investigation_state import (
    ProcessingStatus,
    SupportingDocument,
)
from app.services.document_service import process_document

router = APIRouter()

CaseIdPath = Annotated[
    str,
    ApiPath(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
        description="Investigation case identifier.",
    ),
]
DocumentTypeForm = Annotated[
    str,
    Form(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Document type label, for example INVOICE or BANK_STATEMENT.",
    ),
]

# ── Known case IDs for Round 1 validation ────────────────────────────
# The existing investigations endpoint returns a hardcoded mock with
# this case_id.  We also maintain a module-level set that can be
# extended at runtime (e.g. when a new investigation is created).
_KNOWN_CASE_IDS: set[str] = {"CASE-2025-00042"}

# ── Upload directory ─────────────────────────────────────────────────
_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"

# ── Repository instance ──────────────────────────────────────────────
_doc_repo = DocumentRepository()


def _ensure_upload_dir(case_id: str) -> Path:
    """Create the upload directory for a case if it doesn't exist."""
    case_dir = _UPLOAD_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def _is_pdf(filename: str | None) -> bool:
    """Check if the filename indicates a PDF file."""
    if not filename:
        return False
    return filename.lower().endswith(".pdf")


def _is_image(filename: str | None) -> bool:
    """Check if the filename indicates a supported image file."""
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


def _is_processable(filename: str | None) -> bool:
    """Check if the file can be processed (PDF or image)."""
    return _is_pdf(filename) or _is_image(filename)


@router.post(
    "/investigations/{case_id}/documents",
    response_model=SupportingDocument,
)
async def upload_document(
    case_id: CaseIdPath,
    file: UploadFile = File(...),
    document_type: DocumentTypeForm = "OTHER",
    db: AsyncSession = Depends(get_db_session),
) -> SupportingDocument:
    """Upload a supporting document for an investigation case.

    Accepts a file upload, stores the raw file to the local filesystem,
    and persists a DocumentRecord via the repository.

    For PDF files: text extraction is attempted using pypdf.  If no
    usable text is found (scanned/image-only PDF), OCR/Vision fallback
    is triggered via GeminiClient.

    For image files: OCR/Vision is used to extract text.

    After text extraction (from either path), entity and transaction
    extraction runs on the resulting text.

    Non-PDF, non-image files are stored with processing_status = PENDING.

    Args:
        case_id: The investigation case identifier.
        file: The uploaded file.
        document_type: Type of document (e.g. INVOICE, ID_SCAN, BANK_STATEMENT).
        db: Async database session (injected).

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

    # -- Build file URL (local path) --
    file_url = str(file_path)

    # -- Prepare document data --
    now = datetime.now(timezone.utc)
    document_data: dict = {
        "document_id": document_id,
        "document_type": document_type,
        "file_name": file.filename,
        "file_url": file_url,
        "uploaded_at": now,
        "processing_status": ProcessingStatus.PENDING.value,
        "extracted_text": None,
        "summary": None,
        "extracted_entities": [],
        "extracted_transactions": [],
    }

    # -- Process document (PDF, image, or other) --
    if _is_processable(file.filename):
        result = process_document(contents, file.filename or "")
        document_data["extracted_text"] = result["extracted_text"]
        document_data["summary"] = result["summary"]
        document_data["processing_status"] = result["processing_status"].value
        document_data["extracted_entities"] = result.get("extracted_entities", [])
        document_data["extracted_transactions"] = result.get("extracted_transactions", [])

    # -- Persist via repository --
    record = await _doc_repo.create(db, case_id, document_data)

    # -- Build and return SupportingDocument response --
    return SupportingDocument(
        document_id=record.document_id,
        document_type=record.document_type,
        file_name=record.file_name,
        file_url=record.file_url,
        uploaded_at=record.uploaded_at,
        extracted_text=record.extracted_text,
        summary=record.summary,
        extracted_entities=getattr(record, "extracted_entities", None) or [],
        extracted_transactions=getattr(record, "extracted_transactions", None) or [],
        processing_status=ProcessingStatus(record.processing_status),
    )


@router.get(
    "/investigations/{case_id}/documents",
    response_model=list[SupportingDocument],
)
async def list_documents(
    case_id: CaseIdPath,
    db: AsyncSession = Depends(get_db_session),
) -> list[SupportingDocument]:
    """List all documents for an investigation case.

    Args:
        case_id: The investigation case identifier.
        db: Async database session (injected).

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

    records = await _doc_repo.list_by_case(db, case_id)
    return [
        SupportingDocument(
            document_id=r.document_id,
            document_type=r.document_type,
            file_name=r.file_name,
            file_url=r.file_url,
            uploaded_at=r.uploaded_at,
            extracted_text=r.extracted_text,
            summary=r.summary,
            extracted_entities=getattr(r, "extracted_entities", None) or [],
            extracted_transactions=getattr(r, "extracted_transactions", None) or [],
            processing_status=ProcessingStatus(r.processing_status),
        )
        for r in records
    ]
