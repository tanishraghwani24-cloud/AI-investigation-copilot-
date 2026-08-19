"""Tests for the document upload endpoint (updated for Round 2).

Covers:
- POST /api/investigations/{case_id}/documents returns HTTP 200
- Response is a valid SupportingDocument
- File is stored to the local filesystem
- Invalid case_id returns HTTP 404
- PDF files are processed (extraction attempted)
- Non-PDF files remain PENDING
- GET /api/investigations/{case_id}/documents lists uploaded documents
- Existing endpoints (health, investigations) still work

Round 2 changes:
- Database session is mocked (no real Postgres needed)
- In-memory document store is retired
- PDF uploads trigger extraction via document_service
"""

import io
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.api.routes import investigations as investigation_routes
from app.main import app
from app.schemas.investigation_state import ProcessingStatus, SupportingDocument

# Known case ID from the existing hardcoded investigation
VALID_CASE_ID = "CASE-2025-00042"

# Upload directory path (mirrors the route module)
_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"


# ── Mock database session ────────────────────────────────────────────

# Storage for mock repository — simulates Postgres in tests
_mock_db_store: dict[str, list[dict]] = {}


def _reset_mock_store() -> None:
    """Clear the mock database store."""
    _mock_db_store.clear()


class _MockDocumentRecord:
    """Lightweight stand-in for DocumentRecord ORM instances."""

    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


async def _mock_get_db_session():
    """Yield a mock async session that doesn't touch Postgres."""
    yield MagicMock()


@pytest.fixture(autouse=True)
def _override_dependencies():
    """Override the DB session dependency globally for these tests."""
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = _mock_get_db_session
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset mock store and clean upload directory before each test."""
    _reset_mock_store()
    if _UPLOAD_DIR.exists():
        shutil.rmtree(_UPLOAD_DIR)
    yield
    _reset_mock_store()
    if _UPLOAD_DIR.exists():
        shutil.rmtree(_UPLOAD_DIR)


def _make_mock_create(store: dict[str, list[dict]]):
    """Create a mock DocumentRepository.create that stores records."""

    async def _create(session, case_id, document_data):
        record = _MockDocumentRecord(case_id=case_id, **document_data)
        if case_id not in store:
            store[case_id] = []
        store[case_id].append(document_data)
        return record

    return _create


def _make_mock_list_by_case(store: dict[str, list[dict]]):
    """Create a mock DocumentRepository.list_by_case that reads from store."""

    async def _list_by_case(session, case_id):
        return [
            _MockDocumentRecord(case_id=case_id, **d)
            for d in store.get(case_id, [])
        ]

    return _list_by_case


# Patch the repository instance used by the route module
_create_patcher = patch(
    "app.api.routes.documents._doc_repo.create",
    side_effect=_make_mock_create(_mock_db_store),
)
_list_patcher = patch(
    "app.api.routes.documents._doc_repo.list_by_case",
    side_effect=_make_mock_list_by_case(_mock_db_store),
)


@pytest.fixture(autouse=True)
def _patch_repo():
    """Patch repository methods for all tests."""
    with _create_patcher, _list_patcher:
        yield


client = TestClient(app)


def _make_test_file(
    filename: str = "test_document.pdf",
    content: bytes = b"fake pdf content for testing",
) -> tuple[str, io.BytesIO, str]:
    """Create a test file tuple for upload."""
    return (filename, io.BytesIO(content), "application/pdf")


class TestDocumentUploadEndpoint:
    """POST /api/investigations/{case_id}/documents tests."""

    def test_upload_returns_http_200(self) -> None:
        """Upload endpoint returns HTTP 200."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
            data={"document_type": "INVOICE"},
        )
        assert response.status_code == 200

    def test_returns_valid_supporting_document(self) -> None:
        """Response validates against the SupportingDocument schema."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
            data={"document_type": "INVOICE"},
        )
        doc = SupportingDocument.model_validate(response.json())
        assert doc.document_id is not None
        assert len(doc.document_id) > 0

    def test_pdf_with_fake_content_gets_failed_status(self) -> None:
        """A .pdf file with non-PDF content gets processing_status=FAILED."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
            data={"document_type": "BANK_STATEMENT"},
        )
        doc = SupportingDocument.model_validate(response.json())
        # Fake bytes are not a valid PDF → extraction fails
        assert doc.processing_status == ProcessingStatus.FAILED

    def test_non_pdf_file_gets_pending_status(self) -> None:
        """A non-PDF file (.txt) gets processing_status=PENDING."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": ("report.txt", io.BytesIO(b"some text"), "text/plain")},
            data={"document_type": "OTHER"},
        )
        doc = SupportingDocument.model_validate(response.json())
        assert doc.processing_status == ProcessingStatus.PENDING

    def test_document_type_is_set(self) -> None:
        """Document type from form data is reflected in the response."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
            data={"document_type": "ID_SCAN"},
        )
        doc = SupportingDocument.model_validate(response.json())
        assert doc.document_type == "ID_SCAN"

    def test_file_name_is_preserved(self) -> None:
        """Original filename is preserved in the response."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file(filename="my_invoice.pdf")},
            data={"document_type": "INVOICE"},
        )
        doc = SupportingDocument.model_validate(response.json())
        assert doc.file_name == "my_invoice.pdf"

    def test_file_url_is_set(self) -> None:
        """Response includes a file URL/path."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
        )
        doc = SupportingDocument.model_validate(response.json())
        assert doc.file_url is not None
        assert len(doc.file_url) > 0

    def test_uploaded_at_is_set(self) -> None:
        """Response includes an uploaded_at timestamp."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
        )
        doc = SupportingDocument.model_validate(response.json())
        assert doc.uploaded_at is not None

    def test_file_stored_to_disk(self) -> None:
        """Raw file is written to the local filesystem."""
        test_content = b"unique test content for disk check"
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file(content=test_content)},
        )
        doc = SupportingDocument.model_validate(response.json())

        assert doc.file_url is not None
        stored_path = Path(doc.file_url)
        assert stored_path.exists(), f"File not found at {stored_path}"
        assert stored_path.read_bytes() == test_content

    def test_invalid_case_id_returns_404(self) -> None:
        """Upload to a non-existent case returns HTTP 404."""
        response = client.post(
            "/api/investigations/CASE-DOES-NOT-EXIST/documents",
            files={"file": _make_test_file()},
        )
        assert response.status_code == 404

    def test_document_persisted_and_retrievable(self) -> None:
        """Document is persisted via repository and retrievable via GET."""
        # Upload a document
        upload_response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
            data={"document_type": "INVOICE"},
        )
        uploaded_doc = SupportingDocument.model_validate(upload_response.json())

        # List documents
        list_response = client.get(
            f"/api/investigations/{VALID_CASE_ID}/documents",
        )
        assert list_response.status_code == 200
        docs = list_response.json()
        assert len(docs) == 1
        assert docs[0]["document_id"] == uploaded_doc.document_id

    def test_non_pdf_fields_remain_empty(self) -> None:
        """Non-PDF upload: entity/transaction/evidence fields remain empty."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": ("report.txt", io.BytesIO(b"text"), "text/plain")},
        )
        doc = SupportingDocument.model_validate(response.json())

        # These fields should remain empty — no extraction for non-PDF
        assert doc.extracted_text is None
        assert doc.summary is None
        assert doc.extracted_entities == []
        assert doc.extracted_transactions == []
        assert doc.evidence_references == []

    def test_default_document_type(self) -> None:
        """When document_type is not provided, defaults to OTHER."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
        )
        doc = SupportingDocument.model_validate(response.json())
        assert doc.document_type == "OTHER"

    def test_unique_document_ids(self) -> None:
        """Each uploaded document gets a unique ID."""
        ids = set()
        for _ in range(3):
            response = client.post(
                f"/api/investigations/{VALID_CASE_ID}/documents",
                files={"file": _make_test_file()},
            )
            doc = SupportingDocument.model_validate(response.json())
            ids.add(doc.document_id)
        assert len(ids) == 3


class TestListDocumentsEndpoint:
    """GET /api/investigations/{case_id}/documents tests."""

    def test_empty_list_for_new_case(self) -> None:
        """Listing documents for a case with no uploads returns empty list."""
        response = client.get(
            f"/api/investigations/{VALID_CASE_ID}/documents",
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_invalid_case_id_returns_404(self) -> None:
        """Listing documents for a non-existent case returns 404."""
        response = client.get(
            "/api/investigations/CASE-DOES-NOT-EXIST/documents",
        )
        assert response.status_code == 404


class TestExistingEndpointsStillWork:
    """Ensure existing Round 1 endpoints are not broken."""

    def test_health_still_works(self) -> None:
        """GET /api/health returns HTTP 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_investigations_still_works(self) -> None:
        """POST /api/investigations returns HTTP 200."""
        persisted_state = investigation_routes._build_investigation_state(42)
        with patch.object(
            investigation_routes._investigation_service,
            "create_investigation",
            new=AsyncMock(return_value=persisted_state),
        ):
            response = client.post("/api/investigations")
        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == VALID_CASE_ID

