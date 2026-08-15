"""Tests for OCR/Vision fallback (Harshita — Round 3).

Covers:
- Scanned/blank PDF triggers OCR fallback (mocked Gemini)
- OCR produces non-empty extracted_text
- Successful OCR → processing_status == EXTRACTED
- Failed OCR → processing_status == FAILED
- Image file routes through OCR
- Both paths (text PDF and OCR) feed into entity/transaction extraction

All Gemini calls are mocked — tests do not require a live API key.
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfWriter

from app.schemas.investigation_state import ProcessingStatus
from app.services.document_service import (
    _has_usable_text,
    _is_image_file,
    _ocr_via_gemini,
    process_document,
    process_image,
    process_pdf,
)


# ── Fixture Helpers ──────────────────────────────────────────────────


def _create_blank_pdf() -> bytes:
    """Create a minimal valid PDF with no text content (simulates scanned PDF).

    Returns:
        Raw bytes of a blank PDF.
    """
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _create_text_pdf(text: str) -> bytes:
    """Create a minimal valid PDF with the given text on one page.

    Uses raw PDF syntax to build a proper content stream.

    Args:
        text: The text content to embed in the PDF.

    Returns:
        Raw bytes of the generated PDF.
    """
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    text_bytes = safe.encode("latin-1", errors="replace")

    stream = b"BT /F1 12 Tf 72 720 Td (" + text_bytes + b") Tj ET"
    stream_len = len(stream)

    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    obj4 = (
        b"4 0 obj\n<< /Length "
        + str(stream_len).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream\nendobj\n"
    )
    obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

    header = b"%PDF-1.4\n"
    objects = [obj1, obj2, obj3, obj4, obj5]

    offsets: list[int] = []
    pos = len(header)
    for obj in objects:
        offsets.append(pos)
        pos += len(obj)

    xref_pos = pos
    body = header + b"".join(objects)

    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets:
        xref += f"{offset:010d} 00000 n \n".encode()

    trailer = (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_pos).encode()
        + b"\n%%EOF"
    )

    return body + xref + trailer


def _create_simple_image() -> bytes:
    """Create a minimal PNG image for testing.

    Returns:
        Raw bytes of a 1x1 white PNG.
    """
    from PIL import Image

    img = Image.new("RGB", (100, 30), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ============================================================
# Test: Usable text detection
# ============================================================


class TestUsableTextDetection:
    """Tests for _has_usable_text()."""

    def test_normal_text_is_usable(self) -> None:
        """Normal text is detected as usable."""
        assert _has_usable_text("This is a normal document with enough text.")

    def test_empty_string_not_usable(self) -> None:
        """Empty string is not usable."""
        assert not _has_usable_text("")

    def test_whitespace_only_not_usable(self) -> None:
        """Whitespace-only text is not usable."""
        assert not _has_usable_text("   \n\t  ")

    def test_short_noise_not_usable(self) -> None:
        """Very short text (< threshold) is not usable."""
        assert not _has_usable_text("ab")

    def test_threshold_boundary(self) -> None:
        """Text at exactly the threshold is usable."""
        assert _has_usable_text("a" * 10)


# ============================================================
# Test: Image file detection
# ============================================================


class TestImageFileDetection:
    """Tests for _is_image_file()."""

    def test_png_is_image(self) -> None:
        assert _is_image_file("scan.png")

    def test_jpg_is_image(self) -> None:
        assert _is_image_file("photo.jpg")

    def test_jpeg_is_image(self) -> None:
        assert _is_image_file("photo.jpeg")

    def test_tiff_is_image(self) -> None:
        assert _is_image_file("scan.tiff")

    def test_pdf_is_not_image(self) -> None:
        assert not _is_image_file("document.pdf")

    def test_txt_is_not_image(self) -> None:
        assert not _is_image_file("notes.txt")

    def test_none_is_not_image(self) -> None:
        assert not _is_image_file(None)


# ============================================================
# Test: OCR fallback for scanned PDFs
# ============================================================


class TestOcrFallbackScannedPdf:
    """Tests for OCR fallback when pypdf finds no text."""

    @patch("app.services.document_service._ocr_via_gemini")
    def test_blank_pdf_triggers_ocr(self, mock_ocr: MagicMock) -> None:
        """A blank PDF (no text layer) triggers the OCR fallback."""
        mock_ocr.return_value = "OCR extracted text from scanned document"
        blank_bytes = _create_blank_pdf()
        result = process_pdf(blank_bytes)

        mock_ocr.assert_called_once()
        assert result["processing_status"] == ProcessingStatus.EXTRACTED
        assert result["extracted_text"] == "OCR extracted text from scanned document"

    @patch("app.services.document_service._ocr_via_gemini")
    def test_ocr_text_is_non_empty(self, mock_ocr: MagicMock) -> None:
        """OCR produces non-empty extracted_text."""
        mock_ocr.return_value = "Invoice #12345 from John Smith to ABC Corporation"
        blank_bytes = _create_blank_pdf()
        result = process_pdf(blank_bytes)

        assert result["extracted_text"] is not None
        assert len(result["extracted_text"].strip()) > 0

    @patch("app.services.document_service._ocr_via_gemini")
    def test_ocr_text_contains_expected_content(self, mock_ocr: MagicMock) -> None:
        """OCR extracted_text contains the expected content."""
        expected = "Account 98765432 balance $10,000.00"
        mock_ocr.return_value = expected
        blank_bytes = _create_blank_pdf()
        result = process_pdf(blank_bytes)

        assert "98765432" in result["extracted_text"]
        assert "10,000" in result["extracted_text"]

    @patch("app.services.document_service._ocr_via_gemini")
    def test_ocr_success_has_summary(self, mock_ocr: MagicMock) -> None:
        """Successful OCR also produces a summary."""
        mock_ocr.return_value = "Some extracted text from the scanned page"
        blank_bytes = _create_blank_pdf()
        result = process_pdf(blank_bytes)

        assert result["summary"] is not None
        assert len(result["summary"].strip()) > 0

    @patch("app.services.document_service._ocr_via_gemini")
    def test_ocr_failure_returns_failed(self, mock_ocr: MagicMock) -> None:
        """OCR failure results in FAILED status."""
        mock_ocr.side_effect = Exception("Gemini API unavailable")
        blank_bytes = _create_blank_pdf()
        result = process_pdf(blank_bytes)

        assert result["processing_status"] == ProcessingStatus.FAILED
        assert result["error"] is not None
        assert "OCR failed" in result["error"]

    @patch("app.services.document_service._ocr_via_gemini")
    def test_ocr_empty_result_returns_failed(self, mock_ocr: MagicMock) -> None:
        """OCR returning empty text results in FAILED status."""
        mock_ocr.return_value = ""
        blank_bytes = _create_blank_pdf()
        result = process_pdf(blank_bytes)

        assert result["processing_status"] == ProcessingStatus.FAILED

    def test_text_pdf_does_not_trigger_ocr(self) -> None:
        """A text-based PDF does NOT trigger OCR."""
        text = "This is a text-based PDF with enough content to be usable by the pipeline."
        pdf_bytes = _create_text_pdf(text)

        with patch("app.services.document_service._ocr_via_gemini") as mock_ocr:
            result = process_pdf(pdf_bytes)
            mock_ocr.assert_not_called()
            assert result["processing_status"] == ProcessingStatus.EXTRACTED


# ============================================================
# Test: Image file OCR
# ============================================================


class TestImageOcr:
    """Tests for image file processing via OCR."""

    @patch("app.services.document_service._ocr_via_gemini")
    def test_image_routes_through_ocr(self, mock_ocr: MagicMock) -> None:
        """Image files are processed via OCR/Vision."""
        mock_ocr.return_value = "Text extracted from the image"
        image_bytes = _create_simple_image()
        result = process_image(image_bytes, "scan.png")

        mock_ocr.assert_called_once()
        assert result["processing_status"] == ProcessingStatus.EXTRACTED
        assert result["extracted_text"] == "Text extracted from the image"

    @patch("app.services.document_service._ocr_via_gemini")
    def test_image_ocr_failure(self, mock_ocr: MagicMock) -> None:
        """Failed image OCR returns FAILED status."""
        mock_ocr.side_effect = Exception("Vision API error")
        image_bytes = _create_simple_image()
        result = process_image(image_bytes, "scan.png")

        assert result["processing_status"] == ProcessingStatus.FAILED
        assert result["error"] is not None


# ============================================================
# Test: Unified process_document entry point
# ============================================================


class TestProcessDocument:
    """Tests for the unified process_document() pipeline."""

    @patch("app.services.document_service._ocr_via_gemini")
    def test_pdf_with_text_extracts_entities(self, mock_ocr: MagicMock) -> None:
        """Text PDF → extraction → entities populated."""
        text = "John Smith sent payment of TXN-1234 for amount to Acme Corporation entity identification."
        pdf_bytes = _create_text_pdf(text)
        result = process_document(pdf_bytes, "invoice.pdf")

        mock_ocr.assert_not_called()
        assert result["processing_status"] == ProcessingStatus.EXTRACTED
        assert "extracted_entities" in result
        assert "extracted_transactions" in result

    @patch("app.services.document_service._ocr_via_gemini")
    def test_scanned_pdf_extracts_entities(self, mock_ocr: MagicMock) -> None:
        """Scanned PDF → OCR → extraction → entities populated."""
        mock_ocr.return_value = (
            "John Smith sent $5,000.00 via TXN-9876 to ABC Corporation "
            "on 2025-07-01 from account 12345678."
        )
        blank_bytes = _create_blank_pdf()
        result = process_document(blank_bytes, "scanned.pdf")

        mock_ocr.assert_called_once()
        assert result["processing_status"] == ProcessingStatus.EXTRACTED
        assert len(result["extracted_entities"]) > 0
        assert len(result["extracted_transactions"]) > 0

    @patch("app.services.document_service._ocr_via_gemini")
    def test_image_extracts_entities(self, mock_ocr: MagicMock) -> None:
        """Image → OCR → extraction → entities populated."""
        mock_ocr.return_value = (
            "Payment to Jane Doe account 87654321 REF-5555 $2,000.00"
        )
        image_bytes = _create_simple_image()
        result = process_document(image_bytes, "receipt.png")

        assert result["processing_status"] == ProcessingStatus.EXTRACTED
        assert len(result["extracted_entities"]) > 0
        assert len(result["extracted_transactions"]) > 0

    def test_unsupported_file_remains_pending(self) -> None:
        """Non-PDF, non-image files stay PENDING with empty extraction."""
        result = process_document(b"some text content", "report.txt")

        assert result["processing_status"] == ProcessingStatus.PENDING
        assert result["extracted_entities"] == []
        assert result["extracted_transactions"] == []

    @patch("app.services.document_service._ocr_via_gemini")
    def test_failed_extraction_has_empty_entities(self, mock_ocr: MagicMock) -> None:
        """Failed extraction → entities and transactions are empty."""
        result = process_document(b"corrupt garbage", "bad.pdf")

        assert result["processing_status"] == ProcessingStatus.FAILED
        assert result["extracted_entities"] == []
        assert result["extracted_transactions"] == []

    @patch("app.services.document_service._ocr_via_gemini")
    def test_both_paths_use_shared_extraction(self, mock_ocr: MagicMock) -> None:
        """Text PDF and OCR PDF both produce entities in the same format."""
        # Path 1: text PDF
        text = "Jane Doe account 55667788 TXN-1111 payment of some documentation text for pipeline."
        pdf_bytes = _create_text_pdf(text)
        result_text = process_document(pdf_bytes, "text.pdf")

        # Path 2: OCR PDF
        mock_ocr.return_value = "Jane Doe account 55667788 TXN-1111 payment"
        blank_bytes = _create_blank_pdf()
        result_ocr = process_document(blank_bytes, "scanned.pdf")

        # Both should have entities in the same typed format
        for result in [result_text, result_ocr]:
            if result["extracted_entities"]:
                for e in result["extracted_entities"]:
                    assert ": " in e, f"Missing type prefix: {e}"
            if result["extracted_transactions"]:
                for t in result["extracted_transactions"]:
                    assert ": " in t, f"Missing type prefix: {t}"
