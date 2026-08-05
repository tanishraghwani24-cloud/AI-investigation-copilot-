"""Context & Evidence Intelligence node.

Produces a realistic dummy ContextIntelligence object.
No AI or external API calls — all values are hardcoded.
"""

from typing import Any

from app.schemas.investigation_state import (
    AgentStatus,
    ContextIntelligence,
    CurrentStage,
)


def context_node(state: Any) -> dict:
    """Execute the Context & Evidence Intelligence step.

    Returns a fully populated ContextIntelligence with realistic
    dummy data and advances the stage to CONTEXT.
    """
    context = ContextIntelligence(
        status=AgentStatus.COMPLETED,
        context_summary=(
            "A $48,500 wire transfer was initiated to CryptoVault Holdings Ltd., "
            "a cryptocurrency exchange registered in the Cayman Islands. The "
            "transaction originated from an unrecognised mobile device geolocated "
            "in Bucharest, Romania, while the customer is based in New York. "
            "The beneficiary is a first-time payee with no prior relationship history."
        ),
        key_indicators=[
            "First-time beneficiary in a high-risk jurisdiction",
            "Device geolocation mismatch (Romania vs. New York)",
            "High-risk merchant category (Cryptocurrency Exchange)",
        ],
        anomalies=[],
        risk_score=0.72,
    )

    return {
        "context_intelligence": context,
        "current_stage": CurrentStage.CONTEXT,
    }
