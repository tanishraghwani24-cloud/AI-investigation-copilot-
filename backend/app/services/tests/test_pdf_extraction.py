"""Tests for PDF text extraction (Harshita — Round 2).

Covers:
- Valid text PDF → extraction succeeds, extracted_text non-empty,
  summary populated, processing_status == EXTRACTED
- Corrupt/invalid PDF → no crash, processing_status == FAILED,
  error info preserved
- Empty PDF (no text) → processing_status == FAILED
- Summary truncation for long text

Tests are deterministic — no Gemini API, no external AI calls.
PDF fixtures are generated programmatically using pypdf.PdfWriter.
"""

import io

import pytest

from app.schemas.investigation_state import ProcessingStatus
from app.services.document_service import (
    _SUMMARY_MAX_CHARS,
    extract_text_from_pdf,
    generate_summary,
    process_pdf,
)


# ── Fixture Helpers ──────────────────────────────────────────────────


def _create_text_pdf(text: str) -> bytes:
    """Create a minimal valid PDF with the given text on one page.

    Uses raw PDF syntax to build a proper content stream that pypdf
    can extract text from via ``page.extract_text()``.

    Args:
        text: The text content to embed in the PDF.

    Returns:
        Raw bytes of the generated PDF.
    """
    # Escape special PDF string characters
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    text_bytes = safe.encode("latin-1", errors="replace")

    # Content stream: place text on the page
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

    # Calculate byte offsets for xref table
    offsets: list[int] = []
    pos = len(header)
    for obj in objects:
        offsets.append(pos)
        pos += len(obj)

    xref_pos = pos
    body = header + b"".join(objects)

    # Build xref table
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets:
        xref += f"{offset:010d} 00000 n \n".encode()

    trailer = (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_pos).encode()
        + b"\n%%EOF"
    )

    return body + xref + trailer


def _create_blank_pdf() -> bytes:
    """Create a minimal valid PDF with no text content.

    Returns:
        Raw bytes of a blank PDF.
    """
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()



# ============================================================
# Test 1 — Valid text PDF
# ============================================================


class TestValidTextPdfExtraction:
    """Tests for successful extraction from a valid text-based PDF."""

    def test_extraction_succeeds(self) -> None:
        """process_pdf returns EXTRACTED status for a valid text PDF."""
        pdf_bytes = _create_text_pdf("This is a test document for extraction.")
        result = process_pdf(pdf_bytes)
        assert result["processing_status"] == ProcessingStatus.EXTRACTED

    def test_extracted_text_is_non_empty(self) -> None:
        """extracted_text is populated and non-empty."""
        pdf_bytes = _create_text_pdf("Invoice #12345 dated 2025-01-15.")
        result = process_pdf(pdf_bytes)
        assert result["extracted_text"] is not None
        assert len(result["extracted_text"].strip()) > 0

    def test_extracted_text_contains_expected_content(self) -> None:
        """extracted_text contains the text that was placed in the PDF."""
        expected_text = "Transaction ID: TXN-9876 Amount: 5000.00"
        pdf_bytes = _create_text_pdf(expected_text)
        result = process_pdf(pdf_bytes)
        # The extracted text should contain the key content
        assert "TXN-9876" in result["extracted_text"]
        assert "5000" in result["extracted_text"]

    def test_summary_is_populated(self) -> None:
        """summary field is populated with a non-empty preview."""
        pdf_bytes = _create_text_pdf("Bank statement for account ending 4321.")
        result = process_pdf(pdf_bytes)
        assert result["summary"] is not None
        assert len(result["summary"].strip()) > 0

    def test_no_error_on_success(self) -> None:
        """No error is reported on successful extraction."""
        pdf_bytes = _create_text_pdf("Clean document.")
        result = process_pdf(pdf_bytes)
        assert result["error"] is None


# ============================================================
# Test 2 — Corrupt/invalid PDF
# ============================================================


class TestCorruptPdfExtraction:
    """Tests for graceful failure on corrupt or invalid PDF input."""

    def test_corrupt_pdf_does_not_crash(self) -> None:
        """Processing corrupt bytes does not raise an exception."""
        corrupt_bytes = b"this is definitely not a PDF file at all"
        # Should not raise
        result = process_pdf(corrupt_bytes)
        assert result is not None

    def test_corrupt_pdf_returns_failed_status(self) -> None:
        """Corrupt PDF gets processing_status=FAILED."""
        corrupt_bytes = b"\x00\x01\x02\x03 random garbage bytes"
        result = process_pdf(corrupt_bytes)
        assert result["processing_status"] == ProcessingStatus.FAILED

    def test_corrupt_pdf_preserves_error_info(self) -> None:
        """Error information is preserved for debugging."""
        corrupt_bytes = b"NOT_A_PDF"
        result = process_pdf(corrupt_bytes)
        assert result["error"] is not None
        assert len(result["error"]) > 0

    def test_corrupt_pdf_has_no_extracted_text(self) -> None:
        """Corrupt PDF has extracted_text=None."""
        corrupt_bytes = b"broken content"
        result = process_pdf(corrupt_bytes)
        assert result["extracted_text"] is None

    def test_corrupt_pdf_has_no_summary(self) -> None:
        """Corrupt PDF has summary=None."""
        corrupt_bytes = b"garbage"
        result = process_pdf(corrupt_bytes)
        assert result["summary"] is None

    def test_empty_bytes(self) -> None:
        """Empty byte string is handled gracefully."""
        result = process_pdf(b"")
        assert result["processing_status"] == ProcessingStatus.FAILED
        assert result["error"] is not None


# ============================================================
# Test 3 — Blank/empty PDF (valid structure, no text)
# ============================================================


class TestBlankPdfExtraction:
    """Tests for PDFs that are structurally valid but contain no text."""

    def test_blank_pdf_returns_failed(self) -> None:
        """A blank PDF with no text gets FAILED status."""
        blank_bytes = _create_blank_pdf()
        result = process_pdf(blank_bytes)
        assert result["processing_status"] == ProcessingStatus.FAILED

    def test_blank_pdf_error_mentions_no_text(self) -> None:
        """Error message indicates no extractable text."""
        blank_bytes = _create_blank_pdf()
        result = process_pdf(blank_bytes)
        assert result["error"] is not None
        assert "no extractable text" in result["error"].lower()


# ============================================================
# Test 4 — Summary generation
# ============================================================


class TestSummaryGeneration:
    """Tests for the deterministic summary/preview generation."""

    def test_short_text_not_truncated(self) -> None:
        """Text shorter than the limit is returned as-is (whitespace collapsed)."""
        short_text = "Short document text."
        summary = generate_summary(short_text)
        assert summary == short_text

    def test_long_text_is_truncated(self) -> None:
        """Text longer than the limit is truncated with ellipsis."""
        long_text = "A" * (_SUMMARY_MAX_CHARS + 100)
        summary = generate_summary(long_text)
        assert len(summary) <= _SUMMARY_MAX_CHARS + 1  # +1 for ellipsis char
        assert summary.endswith("…")

    def test_whitespace_is_collapsed(self) -> None:
        """Multiple whitespace characters are collapsed to single spaces."""
        text_with_spaces = "Hello    world\n\nnew   paragraph"
        summary = generate_summary(text_with_spaces)
        assert "  " not in summary
        assert "\n" not in summary

    def test_summary_preserves_content(self) -> None:
        """Summary preserves the beginning of the original content."""
        text = "Transaction report for Q4 2025. Total: $1,234,567."
        summary = generate_summary(text)
        assert "Transaction report" in summary


# ============================================================
# Test 5 — extract_text_from_pdf unit tests
# ============================================================


class TestExtractTextFromPdf:
    """Unit tests for the extract_text_from_pdf function."""

    def test_valid_pdf_returns_text(self) -> None:
        """Valid PDF bytes produce non-empty text."""
        pdf_bytes = _create_text_pdf("Hello from the PDF.")
        text = extract_text_from_pdf(pdf_bytes)
        assert len(text.strip()) > 0

    def test_corrupt_bytes_raises(self) -> None:
        """Corrupt bytes raise an appropriate error."""
        with pytest.raises(Exception):
            extract_text_from_pdf(b"not a pdf")
