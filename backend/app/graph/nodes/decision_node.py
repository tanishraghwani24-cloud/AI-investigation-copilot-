"""Decision Optimization node.

Produces a realistic dummy DecisionOptimization object with
one option per DecisionAction. No AI or external API calls.
"""

from typing import Any

from app.schemas.investigation_state import (
    AgentStatus,
    CurrentStage,
    DecisionAction,
    DecisionOption,
    DecisionOptimization,
)


def decision_node(state: Any) -> dict:
    """Execute the Decision Optimization step.

    Returns a fully populated DecisionOptimization with exactly 4
    decision options and advances the stage to DECISION.
    """
    decision_options = [
        DecisionOption(
            option_id="OPT-ALLOW",
            action=DecisionAction.ALLOW,
            rationale=(
                "Pros: No customer friction; preserves relationship with a "
                "high-value portfolio manager. Cons: Potential regulatory exposure "
                "if the transaction is illicit; AML EDD has not been completed. "
                "Mitigation: Post-transaction monitoring with a 30-day review window."
            ),
            confidence=0.15,
            risk_score=0.82,
        ),
        DecisionOption(
            option_id="OPT-HOLD",
            action=DecisionAction.HOLD,
            rationale=(
                "Pros: Prevents fund movement while investigation continues; "
                "allows time to verify beneficiary identity and obtain source-of-funds "
                "declaration. Cons: May cause customer inconvenience; 48-hour "
                "regulatory hold window. Mitigation: Proactive customer outreach "
                "to expedite verification."
            ),
            confidence=0.70,
            risk_score=0.45,
        ),
        DecisionOption(
            option_id="OPT-BLOCK",
            action=DecisionAction.BLOCK,
            rationale=(
                "Pros: Eliminates risk of fund loss entirely; satisfies strictest "
                "compliance interpretation. Cons: High customer friction; potential "
                "reputational damage if the transaction is legitimate; may trigger "
                "a formal complaint. Mitigation: Offer alternative transfer channel "
                "after full KYC clearance."
            ),
            confidence=0.40,
            risk_score=0.20,
        ),
        DecisionOption(
            option_id="OPT-ESCALATE",
            action=DecisionAction.ESCALATE,
            rationale=(
                "Pros: Engages senior fraud analysts and compliance officers for "
                "a multi-disciplinary review; appropriate for cases with converging "
                "risk signals. Cons: Longer resolution time; resource-intensive. "
                "Mitigation: Assign to the high-priority queue for same-day review."
            ),
            confidence=0.55,
            risk_score=0.50,
        ),
    ]

    decision = DecisionOptimization(
        status=AgentStatus.COMPLETED,
        decision_options=decision_options,
        recommended_decision=DecisionAction.HOLD,
        decision_rationale=(
            "HOLD is recommended over the other options because it balances risk "
            "mitigation with customer experience. Unlike BLOCK, it preserves the "
            "possibility of a legitimate transaction completing after verification. "
            "Unlike ALLOW, it prevents fund movement while two open compliance "
            "violations (AML EDD and KYC beneficiary screening) are addressed. "
            "ESCALATE is a viable secondary option but introduces unnecessary delay "
            "given that the required verification steps are well-defined."
        ),
    )

    return {
        "decision_optimization": decision,
        "current_stage": CurrentStage.DECISION,
    }
