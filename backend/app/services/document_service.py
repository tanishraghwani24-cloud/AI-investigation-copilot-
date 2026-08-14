"""Document processing service — Round 2.

Provides real PDF text extraction for text-based PDFs using pypdf.
Persists results through the DocumentRepository layer.

Does NOT implement:
- OCR / scanned-PDF processing
- Gemini Vision
- Entity extraction
- Transaction extraction
- AI-powered summarization

Those belong to future rounds.
"""

import io
import logging

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.schemas.investigation_state import ProcessingStatus

logger = logging.getLogger(__name__)

# Maximum characters for the deterministic summary/preview
_SUMMARY_MAX_CHARS = 500


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file's raw bytes.

    Uses pypdf to read each page and concatenate the extracted text.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        The concatenated text from all pages.

    Raises:
        PdfReadError: If the PDF is corrupt or unreadable.
        Exception: On any other unexpected extraction failure.
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages_text.append(page_text)
    return "\n".join(pages_text)


def generate_summary(text: str, max_chars: int = _SUMMARY_MAX_CHARS) -> str:
    """Generate a short deterministic preview of the extracted text.

    Truncates to ``max_chars`` characters and appends an ellipsis
    if the text is longer than the limit.

    This is intentionally simple — AI-powered summarization
    belongs to a future round.

    Args:
        text: The full extracted text.
        max_chars: Maximum character length for the preview.

    Returns:
        A truncated preview string.
    """
    cleaned = " ".join(text.split())  # Collapse whitespace
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rstrip() + "…"


def process_pdf(file_bytes: bytes) -> dict:
    """Process a PDF file: extract text, generate summary, determine status.

    This is the main entry point for PDF document processing.

    Args:
        file_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        A dict with keys:
            - ``extracted_text``: The extracted text (or None on failure).
            - ``summary``: A short preview (or None on failure).
            - ``processing_status``: ``ProcessingStatus.EXTRACTED`` or
              ``ProcessingStatus.FAILED``.
            - ``error``: Error message string if processing failed,
              otherwise None.
    """
    try:
        extracted_text = extract_text_from_pdf(file_bytes)

        if not extracted_text.strip():
            # PDF opened successfully but contains no extractable text
            # (e.g. scanned/image-only PDF). Mark as failed for now;
            # OCR support will handle these in a future round.
            return {
                "extracted_text": None,
                "summary": None,
                "processing_status": ProcessingStatus.FAILED,
                "error": "PDF contains no extractable text (may be scanned/image-only).",
            }

        summary = generate_summary(extracted_text)

        return {
            "extracted_text": extracted_text,
            "summary": summary,
            "processing_status": ProcessingStatus.EXTRACTED,
            "error": None,
        }

    except PdfReadError as exc:
        logger.warning("PDF extraction failed (corrupt/unreadable): %s", exc)
        return {
            "extracted_text": None,
            "summary": None,
            "processing_status": ProcessingStatus.FAILED,
            "error": f"PDF is corrupt or unreadable: {exc}",
        }
    except Exception as exc:
        logger.exception("Unexpected error during PDF extraction: %s", exc)
        return {
            "extracted_text": None,
            "summary": None,
            "processing_status": ProcessingStatus.FAILED,
            "error": f"Unexpected extraction error: {exc}",
        }
