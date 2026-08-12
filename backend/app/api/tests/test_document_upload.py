"""Tests for the document upload skeleton endpoint (Harshita — Round 1).

Covers:
- POST /api/investigations/{case_id}/documents returns HTTP 200
- Response is a valid SupportingDocument with processing_status=PENDING
- File is stored to the local filesystem
- Invalid case_id returns HTTP 404
- Document metadata is stored in the in-memory store
- GET /api/investigations/{case_id}/documents lists uploaded documents
- No extraction or analysis occurs (fields remain empty/None)
- Existing endpoints (health, investigations) still work
"""

import io
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.investigation_state import ProcessingStatus, SupportingDocument
from app.services.document_store import clear_store

client = TestClient(app)

# Known case ID from the existing hardcoded investigation
VALID_CASE_ID = "CASE-2025-00042"

# Upload directory path (mirrors the route module)
_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset in-memory store and clean upload directory before each test."""
    clear_store()
    # Clean upload directory if it exists
    if _UPLOAD_DIR.exists():
        shutil.rmtree(_UPLOAD_DIR)
    yield
    # Cleanup after test
    clear_store()
    if _UPLOAD_DIR.exists():
        shutil.rmtree(_UPLOAD_DIR)


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

    def test_processing_status_is_pending(self) -> None:
        """Newly uploaded document has processing_status=PENDING."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
            data={"document_type": "BANK_STATEMENT"},
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

    def test_document_stored_in_memory(self) -> None:
        """Document metadata is retrievable from the in-memory store via GET."""
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

    def test_no_extraction_occurs(self) -> None:
        """No text extraction, entity extraction, or analysis is performed."""
        response = client.post(
            f"/api/investigations/{VALID_CASE_ID}/documents",
            files={"file": _make_test_file()},
        )
        doc = SupportingDocument.model_validate(response.json())

        # These fields should remain empty — no processing in Round 1
        assert doc.summary is None
        assert doc.extracted_text is None
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

    def test_multiple_uploads(self) -> None:
        """Multiple documents can be uploaded to the same case."""
        for i in range(3):
            response = client.post(
                f"/api/investigations/{VALID_CASE_ID}/documents",
                files={"file": _make_test_file(filename=f"doc_{i}.pdf")},
            )
            assert response.status_code == 200

        # All three should be listed
        list_response = client.get(
            f"/api/investigations/{VALID_CASE_ID}/documents",
        )
        docs = list_response.json()
        assert len(docs) == 3

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
        response = client.post("/api/investigations")
        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == VALID_CASE_ID
