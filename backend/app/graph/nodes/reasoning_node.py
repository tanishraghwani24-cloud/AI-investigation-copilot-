"""Investigation Reasoning node.

Produces a realistic dummy InvestigationReasoning object with
multiple hypotheses. No AI or external API calls.
"""

from typing import Any

from app.schemas.investigation_state import (
    AgentStatus,
    CurrentStage,
    Hypothesis,
    InvestigationReasoning,
)


def reasoning_node(state: Any) -> dict:
    """Execute the Investigation Reasoning step.

    Returns a fully populated InvestigationReasoning with realistic
    dummy hypotheses and advances the stage to REASONING.
    """
    hypotheses = [
        Hypothesis(
            hypothesis_id="HYP-001",
            title="Money Laundering via Crypto Exchange",
            description=(
                "The customer may be layering illicit funds through a cryptocurrency "
                "exchange in a high-risk jurisdiction. The use of an unknown device "
                "from a different country, combined with a first-time beneficiary "
                "and a large round-figure transfer, is consistent with known "
                "money-laundering typologies."
            ),
            confidence=0.75,
            supporting_evidence=[
                "TXN-2025-0819-00347: large wire to first-time beneficiary",
                "DEV-UNKNOWN-8812: unrecognised device in Romania",
                "MERCH-KY-7741: high-risk crypto exchange in Cayman Islands",
            ],
            contradicting_evidence=[
                "Customer occupation is Portfolio Manager — crypto investments may be legitimate",
            ],
        ),
        Hypothesis(
            hypothesis_id="HYP-002",
            title="Legitimate Investment Deposit",
            description=(
                "The customer, a portfolio manager, may be making a legitimate "
                "investment deposit into a licensed cryptocurrency platform. "
                "The device anomaly could be explained by travel or use of a VPN."
            ),
            confidence=0.35,
            supporting_evidence=[
                "Customer occupation: Portfolio Manager",
                "Transaction description references investment deposit",
            ],
            contradicting_evidence=[
                "Device geolocated in Romania — no travel history on file",
                "Beneficiary has no prior transaction history with customer",
                "Merchant registered only 2 years ago",
            ],
        ),
        Hypothesis(
            hypothesis_id="HYP-003",
            title="Account Takeover",
            description=(
                "A threat actor may have compromised the customer's account and "
                "is initiating an unauthorised transfer. The unknown device and "
                "foreign geolocation are strong indicators of credential theft."
            ),
            confidence=0.55,
            supporting_evidence=[
                "DEV-UNKNOWN-8812: device never seen on this account",
                "Geolocation mismatch: Romania vs. customer address in New York",
            ],
            contradicting_evidence=[
                "No recent password-reset or MFA-change events on record",
            ],
        ),
    ]

    reasoning = InvestigationReasoning(
        status=AgentStatus.COMPLETED,
        hypotheses=hypotheses,
        reasoning_summary=(
            "Three hypotheses have been generated. Money laundering via a crypto "
            "exchange ranks highest (75% confidence) due to converging risk "
            "signals: first-time high-risk-jurisdiction beneficiary, unknown "
            "device in a different country, and a large round-figure transfer. "
            "Account takeover is a secondary concern (55%). Legitimate investment "
            "is plausible but weakly supported (35%)."
        ),
        recommended_actions=[
            "Place a temporary hold on the transaction pending further review",
            "Contact the customer to verify the transaction and device usage",
        ],
    )

    return {
        "investigation_reasoning": reasoning,
        "current_stage": CurrentStage.REASONING,
    }
