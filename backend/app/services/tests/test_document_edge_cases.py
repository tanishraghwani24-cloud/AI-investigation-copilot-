"""Round 6 document processing edge-case tests."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.repository import DocumentRepository, InvestigationRepository
from app.db.session import Base
from app.schemas.investigation_state import (
    CaseInput,
    ProcessingStatus,
    create_initial_state,
)
from app.services.document_service import (
    _MAX_FILE_SIZE_BYTES,
    process_document,
)


@pytest_asyncio.fixture
async def db_session():
    """Provide an isolated database for document association assertions."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session
    await engine.dispose()


def _document_data(document_id: str, result: dict) -> dict:
    """Map a processing result to the existing document repository shape."""
    return {
        "document_id": document_id,
        "document_type": "BANK_STATEMENT",
        "file_name": f"{document_id}.pdf",
        "uploaded_at": datetime.now(timezone.utc),
        "processing_status": result["processing_status"].value,
        "extracted_text": result["extracted_text"],
        "summary": result["summary"],
        "extracted_entities": result.get("extracted_entities", []),
        "extracted_transactions": result.get("extracted_transactions", []),
    }


def test_corrupt_document_returns_failed_with_reason():
    result = process_document(b"not a readable PDF", "corrupt.pdf")

    assert result["processing_status"] == ProcessingStatus.FAILED
    assert result["error"]
    assert "corrupt" in result["error"].lower() or "unexpected" in result["error"].lower()
    assert result["summary"] == result["error"]
    assert result["extracted_text"] is None
    assert result["extracted_entities"] == []
    assert result["extracted_transactions"] == []


def test_oversized_document_fails_before_extraction_or_ocr():
    oversized_bytes = b"x" * (_MAX_FILE_SIZE_BYTES + 1)

    with patch(
        "app.services.document_service.process_pdf",
        side_effect=AssertionError("PDF extraction must not run"),
    ), patch(
        "app.services.document_service.process_image",
        side_effect=AssertionError("OCR must not run"),
    ):
        result = process_document(oversized_bytes, "oversized.pdf")

    assert result["processing_status"] == ProcessingStatus.FAILED
    assert result["error"]
    assert "maximum allowed size" in result["error"].lower()
    assert result["summary"] == result["error"]
    assert result["extracted_entities"] == []
    assert result["extracted_transactions"] == []


@pytest.mark.asyncio
async def test_multiple_documents_keep_independent_records(db_session):
    state = create_initial_state("CASE-MULTI-DOC", CaseInput())
    await InvestigationRepository().create(
        db_session,
        state.case_id,
        state.model_dump(mode="json"),
    )

    with patch(
        "app.services.document_service.extract_text_from_pdf",
        side_effect=["First document has distinct content.", "Second document has other content."],
    ):
        first = process_document(b"first", "first.pdf")
        second = process_document(b"second", "second.pdf")

    repository = DocumentRepository()
    await repository.create(db_session, state.case_id, _document_data("DOC-FIRST", first))
    await repository.create(db_session, state.case_id, _document_data("DOC-SECOND", second))
    await db_session.commit()

    records = await repository.list_by_case(db_session, state.case_id)
    assert [record.document_id for record in records] == ["DOC-FIRST", "DOC-SECOND"]
    assert [record.processing_status for record in records] == ["EXTRACTED", "EXTRACTED"]
    assert records[0].extracted_text != records[1].extracted_text
    assert records[0].summary != records[1].summary


def test_mixed_valid_and_failed_documents_are_isolated():
    with patch(
        "app.services.document_service.extract_text_from_pdf",
        return_value="A valid document with transaction TXN-VALID-001.",
    ):
        valid = process_document(b"valid bytes", "valid.pdf")
    failed = process_document(b"corrupt bytes", "failed.pdf")

    assert valid["processing_status"] == ProcessingStatus.EXTRACTED
    assert valid["extracted_text"]
    assert failed["processing_status"] == ProcessingStatus.FAILED
    assert failed["error"]
    assert failed["summary"] == failed["error"]
    assert failed["extracted_text"] is None
    assert valid["processing_status"] != failed["processing_status"]
