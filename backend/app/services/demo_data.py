"""Demo-mode case enrichment (``DEMO_MODE=true``).

The Mock Bank generator produces a customer, an account and transactions, but
no counterparty, merchant or device — so the report's entity-relationship graph
resolves to a single isolated customer node with no edges. That is correct
behaviour for a case that genuinely lacks those entities, and the production
graph builder is deliberately left alone.

For a demo we need the graph to show a real relationship structure, so this
module derives the missing counterparties *from the case that already exists*:
the beneficiary comes from the receiver account of the largest transaction, the
merchant from that transaction's stated description and location, and the device
from the customer. Nothing is invented at random — the same seeded Mock Bank
case always yields the same entities — and the graph the frontend renders is
still built by the production reporting agent from real state.

Only ``create_investigation`` calls this, and only when demo mode is enabled.
"""

from __future__ import annotations

from app.schemas.investigation_state import (
    BeneficiaryInfo,
    CaseInput,
    DeviceInfo,
    MerchantInfo,
    SeverityLevel,
    Transaction,
)

# Jurisdictions used for demo counterparties, chosen deterministically from the
# transaction id so a case is stable across runs without being uniform.
_DEMO_JURISDICTIONS = (
    ("KY", "Cayman National Bank"),
    ("AE", "Gulf Commercial Bank"),
    ("CY", "Mediterranean Trust Bank"),
    ("PA", "Banco Istmo"),
)


def _largest_transaction(case_input: CaseInput) -> Transaction | None:
    """Return the transaction the alert most plausibly centres on."""
    if not case_input.transactions:
        return None
    return max(case_input.transactions, key=lambda txn: txn.amount)


def _stable_index(token: str, modulus: int) -> int:
    """Map *token* onto a stable index without depending on PYTHONHASHSEED."""
    return sum(ord(character) for character in token) % modulus


def enrich_case_for_demo(case_input: CaseInput) -> CaseInput:
    """Return *case_input* with demo counterparties filled in.

    Fields the case already supplies are never overwritten, so a case that
    genuinely carries a merchant, beneficiary or device is left untouched.
    """
    transaction = _largest_transaction(case_input)
    if transaction is None:
        return case_input

    updates: dict[str, object] = {}
    country, bank_name = _DEMO_JURISDICTIONS[
        _stable_index(transaction.transaction_id, len(_DEMO_JURISDICTIONS))
    ]
    high_value = transaction.amount >= 10_000

    if case_input.beneficiary_info is None:
        receiver = transaction.receiver_account or "UNKNOWN"
        updates["beneficiary_info"] = BeneficiaryInfo(
            beneficiary_id=f"BEN-{receiver.split('-')[-1]}",
            name="Meridian Holdings Ltd.",
            account_number=receiver,
            bank_name=bank_name,
            country=country,
            is_new=True,
            relationship="Stated investment counterparty",
        )

    if case_input.merchant_info is None:
        updates["merchant_info"] = MerchantInfo(
            merchant_id=f"MERCH-{transaction.transaction_id.split('-')[-1]}",
            name="Meridian Settlement Services",
            category=transaction.description or "Cross-border settlement",
            country=country,
            risk_level=SeverityLevel.HIGH if high_value else SeverityLevel.MEDIUM,
            registered_date="2023-02-14",
        )

    if case_input.device_info is None or not case_input.device_info.device_id:
        customer = case_input.customer_profile
        suffix = customer.customer_id.split("-")[-1] if customer else "0001"
        updates["device_info"] = DeviceInfo(
            device_id=f"DEV-{suffix}",
            device_type="MOBILE",
            geolocation=transaction.location or "Unrecognised location",
            is_known_device=False,
        )

    if not updates:
        return case_input
    return case_input.model_copy(update=updates)
