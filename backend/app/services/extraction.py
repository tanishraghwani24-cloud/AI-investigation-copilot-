"""Structured extraction from document text — Round 3.

Provides regex/pattern-based entity and transaction extraction.
Both functions are deterministic — no AI calls, no hallucination.

Used by both text-PDF and OCR/scanned-PDF pipelines to produce
``extracted_entities`` and ``extracted_transactions`` for
the SupportingDocument schema.
"""

import re
from typing import List


# ============================================================
# Entity Extraction
# ============================================================

# Patterns for common account number formats
_ACCOUNT_PATTERNS = [
    re.compile(r"\bACCT[- ]?(\d{4,})\b", re.IGNORECASE),
    re.compile(r"\baccount\s*#?\s*[:\-]?\s*(\d{4,})\b", re.IGNORECASE),
    re.compile(r"\baccount\s+(?:number|no\.?|num\.?)\s*[:\-]?\s*(\d{4,})\b", re.IGNORECASE),
    re.compile(r"\b(\d{8,17})\b"),  # standalone 8-17 digit numbers (likely account numbers)
]

# Patterns for organizations — words ending with corporate suffixes
_ORG_SUFFIXES = (
    r"\b([A-Z][A-Za-z&\s]+(?:"
    r"Corporation|Corp\.?|Inc\.?|LLC|Ltd\.?|Limited|Bank|"
    r"Group|Holdings|Partners|Associates|Company|Co\.?|"
    r"Foundation|Trust|Securities|Capital|Financial|"
    r"International|Enterprises"
    r"))\b"
)
_ORG_PATTERN = re.compile(_ORG_SUFFIXES)

# Common titles that precede person names
_TITLE_PREFIXES = r"(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)"

# Person name pattern: optional title + capitalized first + last name(s)
# Matches "John Smith", "Dr. Jane Doe", "Mary Jane Watson"
_PERSON_PATTERN = re.compile(
    rf"(?:{_TITLE_PREFIXES}\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}})"
)

# Common false-positive names to filter out (month names, common words)
_FALSE_POSITIVE_NAMES = {
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday",
    "United States", "New York", "San Francisco", "Los Angeles",
    "Transaction Id", "Transaction Type", "Account Number",
    "Bank Statement", "Wire Transfer", "Credit Card",
    "Debit Card", "Date Range", "Total Amount",
    "Processing Status", "Document Type", "File Name",
}


def extract_entities(text: str) -> List[str]:
    """Extract named entities from document text.

    Identifies people, account numbers, and organizations using
    pattern matching.  Returns a deduplicated list of typed entity
    strings.  Returns an empty list when no entities are found.

    Args:
        text: The extracted document text to analyse.

    Returns:
        List of entity strings, e.g.
        ``["Person: John Smith", "Account: 12345678", "Org: ABC Corp"]``
    """
    if not text or not text.strip():
        return []

    entities: list[str] = []
    seen: set[str] = set()

    def _add(label: str) -> None:
        if label not in seen:
            seen.add(label)
            entities.append(label)

    # --- Accounts ---
    for pattern in _ACCOUNT_PATTERNS:
        for match in pattern.finditer(text):
            account_num = match.group(1)
            # Only include 8+ digit standalone numbers to avoid false positives
            if pattern == _ACCOUNT_PATTERNS[-1] and len(account_num) < 8:
                continue
            _add(f"Account: {account_num}")

    # --- Organizations ---
    for match in _ORG_PATTERN.finditer(text):
        org_name = match.group(1).strip()
        if len(org_name) > 3:  # Skip very short matches
            _add(f"Org: {org_name}")

    # --- People ---
    for match in _PERSON_PATTERN.finditer(text):
        name = match.group(1).strip()
        # Filter out false positives
        if name in _FALSE_POSITIVE_NAMES:
            continue
        # Filter out names that match an already-found org
        if any(name in org for org in seen if org.startswith("Org:")):
            continue
        if len(name.split()) >= 2:  # At least first + last name
            _add(f"Person: {name}")

    return entities


# ============================================================
# Transaction Extraction
# ============================================================

# Transaction ID patterns
_TXN_ID_PATTERNS = [
    re.compile(r"\b(TXN[- ]?\d{4,})\b", re.IGNORECASE),
    re.compile(r"\btransaction\s*#?\s*[:\-]?\s*([A-Z0-9\-]{4,})\b", re.IGNORECASE),
    re.compile(r"\b(REF[- ]?\d{4,})\b", re.IGNORECASE),
    re.compile(r"\breference\s*#?\s*[:\-]?\s*([A-Z0-9\-]{4,})\b", re.IGNORECASE),
    re.compile(r"\b(WIRE[- ]?\d{4,})\b", re.IGNORECASE),
    re.compile(r"\b(ACH[- ]?\d{4,})\b", re.IGNORECASE),
    re.compile(r"\b(PMT[- ]?\d{4,})\b", re.IGNORECASE),
]

# Amount patterns — currency symbol + number or number + currency code
_AMOUNT_PATTERNS = [
    re.compile(r"([\$€£¥]\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"),
    re.compile(r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(USD|EUR|GBP|JPY|CAD|AUD|CHF)\b"),
    re.compile(r"\b(USD|EUR|GBP|JPY|CAD|AUD|CHF)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"),
]

# Date patterns
_DATE_PATTERNS = [
    re.compile(r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b"),  # 2025-01-15
    re.compile(r"\b(\d{2}[-/]\d{2}[-/]\d{4})\b"),  # 01/15/2025
    re.compile(
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
        r"\s+\d{4})\b",
        re.IGNORECASE,
    ),  # 15 January 2025
    re.compile(
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
        r"\s+\d{1,2},?\s+\d{4})\b",
        re.IGNORECASE,
    ),  # January 15, 2025
]


def extract_transactions(text: str) -> List[str]:
    """Extract transaction references from document text.

    Identifies transaction IDs, monetary amounts, and dates using
    pattern matching.  Returns a deduplicated list of transaction
    reference strings.  Returns an empty list when no transactions
    are found.

    Args:
        text: The extracted document text to analyse.

    Returns:
        List of transaction reference strings, e.g.
        ``["TXN: TXN-9876", "Amount: $5,000.00", "Date: 2025-01-15"]``
    """
    if not text or not text.strip():
        return []

    transactions: list[str] = []
    seen: set[str] = set()

    def _add(label: str) -> None:
        if label not in seen:
            seen.add(label)
            transactions.append(label)

    # --- Transaction IDs ---
    for pattern in _TXN_ID_PATTERNS:
        for match in pattern.finditer(text):
            txn_id = match.group(1).strip()
            if len(txn_id) >= 4:
                _add(f"TXN: {txn_id}")

    # --- Amounts ---
    for pattern in _AMOUNT_PATTERNS:
        for match in pattern.finditer(text):
            # Reconstruct the full amount string
            groups = match.groups()
            if len(groups) == 1:
                amount_str = groups[0].strip()
            else:
                amount_str = " ".join(g for g in groups if g).strip()
            _add(f"Amount: {amount_str}")

    # --- Dates ---
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            date_str = match.group(1).strip()
            _add(f"Date: {date_str}")

    return transactions
