"""Mock Bank package.

Contains data models for Customer, Account, and Transaction
used by the Mock Bank simulation layer, and the deterministic
generator for producing synthetic banking data.
"""

from app.mock_bank.generator import (
    MockBankData,
    generate_account,
    generate_alert,
    generate_customer,
    generate_investigation_data,
    generate_transactions,
)

__all__ = [
    "MockBankData",
    "generate_account",
    "generate_alert",
    "generate_customer",
    "generate_investigation_data",
    "generate_transactions",
]
