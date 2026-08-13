"""Decision Agent skeleton.

Produces deterministic placeholder DecisionOption objects.
No AI, no Gemini, no external API calls — all values are hardcoded.

TEMPORARY — Round 2 placeholder output.
Real Gemini-based decision generation belongs to Round 3.
"""

from app.schemas.investigation_state import (
    AgentStatus,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    InvestigationState,
)


def decision_agent(state: InvestigationState) -> dict:
    """Execute the Decision Agent on the given investigation state.

    Produces deterministic placeholder decision options and returns a
    dict of state updates (compatible with LangGraph node conventions).

    Args:
        state: The current investigation state.

    Returns:
        A dict containing ``decision_optimization`` with at least 2
        distinct placeholder DecisionOption objects.
    """

    # TEMPORARY — Round 2 placeholder output.
    # Real Gemini-based decision generation belongs to Round 3.
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
            pros=[
                "No customer friction",
                "Preserves relationship with high-value client",
            ],
            cons=[
                "Potential regulatory exposure if illicit",
                "AML enhanced due diligence not completed",
            ],
            risks=[
                "Regulatory sanction if transaction is later found illicit",
                "Reputational damage from compliance failure",
            ],
            mitigation=[
                "Post-transaction monitoring with 30-day review window",
                "Flag account for enhanced ongoing due diligence",
            ],
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
            pros=[
                "Prevents fund movement during investigation",
                "Allows time for beneficiary verification",
                "Allows time for source-of-funds declaration",
            ],
            cons=[
                "Customer inconvenience",
                "48-hour regulatory hold window constraint",
            ],
            risks=[
                "Customer complaint if transaction is legitimate",
                "Operational delay in processing",
            ],
            mitigation=[
                "Proactive customer outreach to expedite verification",
                "Assign to priority queue for faster resolution",
            ],
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
            pros=[
                "Eliminates risk of fund loss entirely",
                "Satisfies strictest compliance interpretation",
            ],
            cons=[
                "High customer friction",
                "Potential reputational damage if legitimate",
                "May trigger formal complaint",
            ],
            risks=[
                "Customer attrition",
                "Reputational damage if transaction is legitimate",
            ],
            mitigation=[
                "Offer alternative transfer channel after full KYC clearance",
                "Document compliance rationale for audit trail",
            ],
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
            pros=[
                "Engages senior fraud analysts and compliance officers",
                "Multi-disciplinary review for complex cases",
                "Appropriate for converging risk signals",
            ],
            cons=[
                "Longer resolution time",
                "Resource-intensive process",
            ],
            risks=[
                "Delayed resolution may cause customer frustration",
                "Senior analyst availability may be limited",
            ],
            mitigation=[
                "Assign to high-priority queue for same-day review",
                "Set escalation SLA with 4-hour response target",
            ],
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
    }
