"""Mock Bank data models.

Pure data shapes for the simulated banking environment.
No generation logic, factories, or seed functions — those
belong to a later round.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Customer(BaseModel):
    """A bank customer in the Mock Bank system."""

    customer_id: str = Field(..., description="Unique customer identifier")
    first_name: str = Field(..., description="Customer first name")
    last_name: str = Field(..., description="Customer last name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    date_of_birth: Optional[str] = Field(default=None, description="ISO 8601 date string")
    address: Optional[str] = Field(default=None, description="Mailing address")
    nationality: Optional[str] = Field(default=None, description="Country code")
    occupation: Optional[str] = Field(default=None, description="Stated occupation")
    risk_rating: Optional[str] = Field(
        default=None, description="e.g. LOW, MEDIUM, HIGH"
    )
    created_at: Optional[datetime] = Field(
        default=None, description="When the customer record was created"
    )


class Account(BaseModel):
    """A bank account in the Mock Bank system."""

    account_id: str = Field(..., description="Unique account identifier")
    customer_id: str = Field(..., description="Owning customer identifier")
    account_type: str = Field(
        ..., description="e.g. CHECKING, SAVINGS, BUSINESS"
    )
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    balance: float = Field(default=0.0, description="Current account balance")
    opened_at: Optional[datetime] = Field(
        default=None, description="Account opening date"
    )
    status: str = Field(
        default="ACTIVE", description="e.g. ACTIVE, FROZEN, CLOSED"
    )


class Transaction(BaseModel):
    """A financial transaction in the Mock Bank system."""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    sender_account_id: str = Field(..., description="Source account identifier")
    receiver_account_id: str = Field(..., description="Destination account identifier")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    transaction_type: str = Field(
        ..., description="e.g. WIRE, ACH, P2P, CARD"
    )
    channel: str = Field(default="ONLINE", description="e.g. ONLINE, ATM, BRANCH")
    timestamp: Optional[datetime] = Field(
        default=None, description="When the transaction occurred"
    )
    description: Optional[str] = Field(default=None, description="Free-text memo")
    location: Optional[str] = Field(default=None, description="Originating location")
    status: str = Field(
        default="COMPLETED", description="e.g. PENDING, COMPLETED, FAILED, REVERSED"
    )
