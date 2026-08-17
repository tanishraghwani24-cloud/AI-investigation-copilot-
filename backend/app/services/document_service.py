"""Document processing service — Round 2 + Round 3.

Round 2: Real PDF text extraction for text-based PDFs using pypdf.
Round 3: OCR/Vision fallback for scanned/image-only documents,
         entity extraction, and transaction extraction.

Persists results through the DocumentRepository layer.

OCR/Vision uses the shared GeminiClient (generate_with_image).
Entity and transaction extraction uses deterministic pattern matching
via the extraction module — no AI calls for extraction.
"""

import io
import logging

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.schemas.investigation_state import ProcessingStatus
from app.services.extraction import extract_entities, extract_transactions

logger = logging.getLogger(__name__)

# Maximum characters for the deterministic summary/preview
_SUMMARY_MAX_CHARS = 500

# Maximum accepted upload size before PDF parsing or OCR is attempted.
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Minimum character threshold for "usable" text
_MIN_USABLE_TEXT_LENGTH = 10

# Supported image MIME types
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}

# OCR prompt for Gemini Vision
_OCR_PROMPT = (
    "Extract all text from this document image exactly as it appears. "
    "Return only the raw text content, preserving the reading order. "
    "Do not add any commentary, formatting instructions, or markdown."
)


def _failed_result(reason: str) -> dict:
    """Build a consistent failed result with its reason preserved."""
    return {
        "extracted_text": None,
        "summary": None,
        "processing_status": ProcessingStatus.FAILED,
        "error": reason,
    }


def _oversized_result(file_bytes: bytes) -> dict | None:
    """Return a failure result when bytes exceed the processing limit."""
    if len(file_bytes) <= _MAX_FILE_SIZE_BYTES:
        return None
    size_mb = len(file_bytes) / (1024 * 1024)
    limit_mb = _MAX_FILE_SIZE_BYTES / (1024 * 1024)
    return _failed_result(
        f"Document exceeds the maximum allowed size of {limit_mb:g} MiB "
        f"(received {size_mb:.2f} MiB)."
    )


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


def _has_usable_text(text: str) -> bool:
    """Determine if extracted text is meaningful.

    Text must be non-empty and contain at least ``_MIN_USABLE_TEXT_LENGTH``
    non-whitespace characters to be considered usable.

    Args:
        text: The extracted text to evaluate.

    Returns:
        True if the text is usable, False otherwise.
    """
    stripped = text.strip()
    if not stripped:
        return False
    # Check that there's enough meaningful content (not just whitespace/noise)
    non_whitespace = "".join(stripped.split())
    return len(non_whitespace) >= _MIN_USABLE_TEXT_LENGTH


def _is_image_file(file_name: str | None) -> bool:
    """Check if the filename indicates a supported image file.

    Args:
        file_name: The filename to check.

    Returns:
        True if the file is a supported image type.
    """
    if not file_name:
        return False
    import os
    ext = os.path.splitext(file_name)[1].lower()
    return ext in _IMAGE_EXTENSIONS


def _get_mime_type(file_name: str | None) -> str:
    """Determine MIME type from filename extension.

    Args:
        file_name: The filename to determine MIME type for.

    Returns:
        The MIME type string.
    """
    if not file_name:
        return "application/octet-stream"

    import os
    ext = os.path.splitext(file_name)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }
    return mime_map.get(ext, "application/octet-stream")


def _ocr_via_gemini(file_bytes: bytes, mime_type: str) -> str:
    """Extract text from an image/document via Gemini Vision.

    Uses the shared GeminiClient to send the document bytes
    to Gemini for OCR text extraction.

    Args:
        file_bytes: Raw bytes of the image or PDF file.
        mime_type: MIME type of the file.

    Returns:
        The OCR-extracted text.

    Raises:
        GeminiClientError: If the Gemini API call fails.
    """
    from app.services.gemini_client import get_gemini_client

    client = get_gemini_client()
    return client.generate_with_image(
        prompt=_OCR_PROMPT,
        image_bytes=file_bytes,
        mime_type=mime_type,
    )


def process_pdf(file_bytes: bytes) -> dict:
    """Process a PDF file: extract text, generate summary, determine status.

    This is the main entry point for PDF document processing.
    Maintained for backward compatibility with Round 2.

    For scanned/image-only PDFs with no extractable text, this function
    now attempts OCR via Gemini Vision as a fallback.

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
    oversized = _oversized_result(file_bytes)
    if oversized is not None:
        return oversized

    try:
        extracted_text = extract_text_from_pdf(file_bytes)

        if not _has_usable_text(extracted_text):
            # PDF opened successfully but contains no extractable text
            # (e.g. scanned/image-only PDF).  Attempt OCR fallback.
            try:
                ocr_text = _ocr_via_gemini(file_bytes, "application/pdf")
                if ocr_text and ocr_text.strip():
                    extracted_text = ocr_text
                else:
                    return _failed_result(
                        "PDF contains no extractable text; "
                        "OCR produced no usable text from scanned PDF."
                    )
            except Exception as ocr_exc:
                logger.warning("OCR fallback failed: %s", ocr_exc)
                return _failed_result(
                    f"PDF contains no extractable text and OCR failed: {ocr_exc}"
                )

        summary = generate_summary(extracted_text)

        return {
            "extracted_text": extracted_text,
            "summary": summary,
            "processing_status": ProcessingStatus.EXTRACTED,
            "error": None,
        }

    except PdfReadError as exc:
        logger.warning("PDF extraction failed (corrupt/unreadable): %s", exc)
        return _failed_result(f"PDF is corrupt or unreadable: {exc}")
    except Exception as exc:
        logger.exception("Unexpected error during PDF extraction: %s", exc)
        return _failed_result(f"Unexpected extraction error: {exc}")


def process_image(file_bytes: bytes, file_name: str) -> dict:
    """Process an image file: OCR text extraction, summary, status.

    Routes image uploads through the Gemini Vision OCR path.

    Args:
        file_bytes: Raw bytes of the uploaded image file.
        file_name: Original filename (used to determine MIME type).

    Returns:
        A dict with the same structure as ``process_pdf``.
    """
    oversized = _oversized_result(file_bytes)
    if oversized is not None:
        return oversized

    mime_type = _get_mime_type(file_name)

    try:
        ocr_text = _ocr_via_gemini(file_bytes, mime_type)

        if not ocr_text or not ocr_text.strip():
            return _failed_result("OCR produced no usable text from image.")

        summary = generate_summary(ocr_text)

        return {
            "extracted_text": ocr_text,
            "summary": summary,
            "processing_status": ProcessingStatus.EXTRACTED,
            "error": None,
        }

    except Exception as exc:
        logger.exception("Image OCR failed: %s", exc)
        return _failed_result(f"Image OCR failed: {exc}")


def process_document(file_bytes: bytes, file_name: str) -> dict:
    """Process a document through the full pipeline.

    Unified entry point for Round 3 that handles:
    1. Text extraction (PDF text or OCR/Vision fallback)
    2. Entity extraction
    3. Transaction extraction

    Both text-PDF and OCR paths feed into the same shared
    extraction logic.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        file_name: Original filename.

    Returns:
        A dict with keys:
            - ``extracted_text``
            - ``summary``
            - ``processing_status``
            - ``error``
            - ``extracted_entities``
            - ``extracted_transactions``
    """
    # Reject oversized input before dispatching to parsing or OCR.
    oversized = _oversized_result(file_bytes)
    if oversized is not None:
        oversized["extracted_entities"] = []
        oversized["extracted_transactions"] = []
        oversized["summary"] = oversized["error"]
        return oversized

    # Step 1: Text extraction
    if _is_image_file(file_name):
        result = process_image(file_bytes, file_name)
    elif file_name and file_name.lower().endswith(".pdf"):
        result = process_pdf(file_bytes)
    else:
        # Unsupported file type — no extraction
        return {
            "extracted_text": None,
            "summary": None,
            "processing_status": ProcessingStatus.PENDING,
            "error": None,
            "extracted_entities": [],
            "extracted_transactions": [],
        }

    # Step 2: Entity & transaction extraction (shared for both paths)
    extracted_text = result.get("extracted_text")
    if extracted_text and result["processing_status"] == ProcessingStatus.EXTRACTED:
        result["extracted_entities"] = extract_entities(extracted_text)
        result["extracted_transactions"] = extract_transactions(extracted_text)
    else:
        result["extracted_entities"] = []
        result["extracted_transactions"] = []

    # The upload path persists ``summary`` and the frozen document model has
    # no dedicated error column. Preserve failed processing reasons there.
    if (
        result["processing_status"] == ProcessingStatus.FAILED
        and not result.get("summary")
        and result.get("error")
    ):
        result["summary"] = result["error"]

    return result
