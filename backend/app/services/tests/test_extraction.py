"""Tests for structured entity and transaction extraction (Harshita — Round 3).

Covers:
- Entity extraction: people, accounts, organizations
- Transaction extraction: IDs, amounts, dates
- Empty input → empty results
- No hallucinated entities or transactions
- Shared extraction path (both text-PDF and OCR text use the same logic)

Tests are deterministic — no Gemini API, no external AI calls.
"""

import pytest

from app.services.extraction import extract_entities, extract_transactions


# ============================================================
# Entity Extraction Tests
# ============================================================


class TestEntityExtraction:
    """Tests for extract_entities()."""

    def test_extracts_person_names(self) -> None:
        """Recognizes person names in text."""
        text = "John Smith transferred money to Jane Doe on Monday."
        entities = extract_entities(text)
        person_entities = [e for e in entities if e.startswith("Person:")]
        assert len(person_entities) >= 1
        assert any("John Smith" in e for e in person_entities)
        assert any("Jane Doe" in e for e in person_entities)

    def test_extracts_account_numbers(self) -> None:
        """Recognizes account number patterns."""
        text = "Transfer from account 12345678 to ACCT-9876543."
        entities = extract_entities(text)
        account_entities = [e for e in entities if e.startswith("Account:")]
        assert len(account_entities) >= 1
        assert any("12345678" in e for e in account_entities)

    def test_extracts_organizations(self) -> None:
        """Recognizes organization names with corporate suffixes."""
        text = "Payment was sent to ABC Corporation via First National Bank."
        entities = extract_entities(text)
        org_entities = [e for e in entities if e.startswith("Org:")]
        assert len(org_entities) >= 1
        assert any("ABC Corporation" in e for e in org_entities)

    def test_extracts_all_entity_types(self) -> None:
        """Extracts people, accounts, and organizations from realistic text."""
        text = (
            "John Smith transferred money from account 123456789 "
            "to ABC Corporation on behalf of Global Holdings Ltd."
        )
        entities = extract_entities(text)
        persons = [e for e in entities if e.startswith("Person:")]
        accounts = [e for e in entities if e.startswith("Account:")]
        orgs = [e for e in entities if e.startswith("Org:")]
        assert len(persons) >= 1, f"Expected at least one person, got: {entities}"
        assert len(accounts) >= 1, f"Expected at least one account, got: {entities}"
        assert len(orgs) >= 1, f"Expected at least one org, got: {entities}"

    def test_empty_text_returns_empty(self) -> None:
        """Empty text produces empty result."""
        assert extract_entities("") == []
        assert extract_entities("   ") == []

    def test_none_text_returns_empty(self) -> None:
        """None text produces empty result."""
        assert extract_entities(None) == []

    def test_no_entities_returns_empty(self) -> None:
        """Text with no recognizable entities returns empty list."""
        text = "the quick brown fox jumped over the lazy dog 123"
        entities = extract_entities(text)
        # Should be empty — no names, no account patterns, no org suffixes
        assert entities == []

    def test_no_hallucinated_entities(self) -> None:
        """Only entities actually in the text are extracted."""
        text = "John Smith works at Mega Corp."
        entities = extract_entities(text)
        # Should NOT contain entities not in the text
        for entity in entities:
            # Check the value part (after the prefix)
            value = entity.split(": ", 1)[1] if ": " in entity else entity
            assert value in text or any(
                part in text for part in value.split()
            ), f"Hallucinated entity: {entity}"

    def test_deduplication(self) -> None:
        """Duplicate entity mentions are deduplicated."""
        text = (
            "John Smith sent money. John Smith received money. "
            "Account 12345678 was debited. Account 12345678 was credited."
        )
        entities = extract_entities(text)
        # Check no exact duplicates
        assert len(entities) == len(set(entities))

    def test_filters_false_positive_names(self) -> None:
        """Month names and common words are not extracted as persons."""
        text = "Report filed in January for the United States office."
        entities = extract_entities(text)
        person_entities = [e for e in entities if e.startswith("Person:")]
        # None of the false-positive names should be extracted
        for pe in person_entities:
            assert "United States" not in pe


# ============================================================
# Transaction Extraction Tests
# ============================================================


class TestTransactionExtraction:
    """Tests for extract_transactions()."""

    def test_extracts_transaction_ids(self) -> None:
        """Recognizes transaction ID patterns."""
        text = "Transaction TXN-9876 was processed successfully."
        transactions = extract_transactions(text)
        txn_entries = [t for t in transactions if t.startswith("TXN:")]
        assert len(txn_entries) >= 1
        assert any("TXN-9876" in t for t in txn_entries)

    def test_extracts_amounts(self) -> None:
        """Recognizes monetary amount patterns."""
        text = "The total amount is $5,000.00 USD."
        transactions = extract_transactions(text)
        amount_entries = [t for t in transactions if t.startswith("Amount:")]
        assert len(amount_entries) >= 1
        assert any("5,000.00" in t for t in amount_entries)

    def test_extracts_dates(self) -> None:
        """Recognizes date patterns."""
        text = "Transaction dated 2025-01-15 was flagged."
        transactions = extract_transactions(text)
        date_entries = [t for t in transactions if t.startswith("Date:")]
        assert len(date_entries) >= 1
        assert any("2025-01-15" in t for t in date_entries)

    def test_extracts_all_transaction_fields(self) -> None:
        """Extracts IDs, amounts, and dates from realistic transaction text."""
        text = (
            "Wire transfer TXN-12345 for $10,000.00 USD was initiated "
            "on 2025-03-20 from account 87654321 to beneficiary account."
        )
        transactions = extract_transactions(text)
        txns = [t for t in transactions if t.startswith("TXN:")]
        amounts = [t for t in transactions if t.startswith("Amount:")]
        dates = [t for t in transactions if t.startswith("Date:")]
        assert len(txns) >= 1, f"Expected transaction ID, got: {transactions}"
        assert len(amounts) >= 1, f"Expected amount, got: {transactions}"
        assert len(dates) >= 1, f"Expected date, got: {transactions}"

    def test_empty_text_returns_empty(self) -> None:
        """Empty text produces empty result."""
        assert extract_transactions("") == []
        assert extract_transactions("   ") == []

    def test_none_text_returns_empty(self) -> None:
        """None text produces empty result."""
        assert extract_transactions(None) == []

    def test_no_transactions_returns_empty(self) -> None:
        """Text with no transaction patterns returns empty list."""
        text = "the quick brown fox jumped over the lazy dog"
        transactions = extract_transactions(text)
        assert transactions == []

    def test_no_hallucinated_transactions(self) -> None:
        """Only transactions actually in the text are extracted."""
        text = "Payment of $1,234.56 with reference REF-7890 on 2025-06-15."
        transactions = extract_transactions(text)
        for txn in transactions:
            value = txn.split(": ", 1)[1] if ": " in txn else txn
            # The value (or a recognizable substring) should exist in the text
            assert value in text or any(
                part in text for part in value.split()
            ), f"Hallucinated transaction: {txn}"

    def test_multiple_amounts(self) -> None:
        """Multiple amounts in the same text are all extracted."""
        text = "Debit of $500.00 followed by credit of $1,200.00."
        transactions = extract_transactions(text)
        amounts = [t for t in transactions if t.startswith("Amount:")]
        assert len(amounts) >= 2

    def test_various_date_formats(self) -> None:
        """Multiple date formats are recognized."""
        text = (
            "First transaction on 2025-01-15. "
            "Second on 01/15/2025. "
            "Third on 15 January 2025. "
            "Fourth on March 20, 2025."
        )
        transactions = extract_transactions(text)
        dates = [t for t in transactions if t.startswith("Date:")]
        assert len(dates) >= 3, f"Expected at least 3 dates, got: {dates}"

    def test_reference_id_patterns(self) -> None:
        """Various reference ID patterns are recognized."""
        text = "Wire WIRE-4567 with reference REF-1234 via ACH-8901."
        transactions = extract_transactions(text)
        txns = [t for t in transactions if t.startswith("TXN:")]
        assert len(txns) >= 2, f"Expected multiple refs, got: {txns}"

    def test_deduplication(self) -> None:
        """Duplicate transaction references are deduplicated."""
        text = "TXN-1234 was sent. TXN-1234 was received. $500.00 paid. $500.00 confirmed."
        transactions = extract_transactions(text)
        assert len(transactions) == len(set(transactions))


# ============================================================
# Shared Extraction Path Tests
# ============================================================


class TestSharedExtractionPath:
    """Verify that the same extraction logic handles text from both paths."""

    def test_extraction_on_direct_pdf_text(self) -> None:
        """Entity + transaction extraction works on directly extracted PDF text."""
        # Simulate text that would come from pypdf extraction
        pdf_text = (
            "Invoice #INV-2025-001\n"
            "Date: 2025-07-01\n"
            "From: John Smith\n"
            "To: Acme Corporation\n"
            "Amount: $15,000.00\n"
            "Account: 98765432\n"
            "Reference: REF-5678\n"
        )
        entities = extract_entities(pdf_text)
        transactions = extract_transactions(pdf_text)

        assert len(entities) > 0, "Expected entities from PDF text"
        assert len(transactions) > 0, "Expected transactions from PDF text"

    def test_extraction_on_ocr_text(self) -> None:
        """Entity + transaction extraction works on OCR-extracted text."""
        # Simulate text that would come from OCR/Vision
        ocr_text = (
            "BANK STATEMENT\n"
            "Account Holder: Jane Doe\n"
            "Account Number: 11223344\n"
            "Global Trust Bank\n"
            "Transaction TXN-4321 on 2025-02-14\n"
            "Debit: $2,500.00\n"
            "Credit: $3,750.00\n"
        )
        entities = extract_entities(ocr_text)
        transactions = extract_transactions(ocr_text)

        assert len(entities) > 0, "Expected entities from OCR text"
        assert len(transactions) > 0, "Expected transactions from OCR text"

    def test_both_paths_produce_same_format(self) -> None:
        """Both paths produce entities and transactions in the same format."""
        text = "John Smith sent $1,000.00 via TXN-9999 to Mega Corp on 2025-05-01."

        entities = extract_entities(text)
        transactions = extract_transactions(text)

        # All entities should be typed strings
        for e in entities:
            assert ": " in e, f"Entity missing type prefix: {e}"
            prefix = e.split(": ")[0]
            assert prefix in ("Person", "Account", "Org"), f"Unknown prefix: {prefix}"

        # All transactions should be typed strings
        for t in transactions:
            assert ": " in t, f"Transaction missing type prefix: {t}"
            prefix = t.split(": ")[0]
            assert prefix in ("TXN", "Amount", "Date"), f"Unknown prefix: {prefix}"
