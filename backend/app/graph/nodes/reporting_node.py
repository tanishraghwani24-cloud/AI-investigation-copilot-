"""Reporting & Visualization node.

Produces a realistic dummy InvestigationReport with graph
visualizations and a timeline. No AI or external API calls.
"""

from datetime import datetime
from typing import Any

from app.schemas.investigation_state import (
    AgentStatus,
    CurrentStage,
    GraphData,
    GraphEdge,
    GraphNode,
    InvestigationReport,
    ReportGraphs,
    TimelineEvent,
)


def reporting_node(state: Any) -> dict:
    """Execute the Reporting & Visualization step.

    Returns a fully populated InvestigationReport with entity graphs,
    reasoning flow, decision comparison, and timeline, then sets the
    stage to DONE.
    """

    # -- Entity Relationship Graph --
    entity_nodes = [
        GraphNode(
            node_id="N-CUST",
            label="James Whitfield",
            node_type="PERSON",
            metadata={"customer_id": "CUST-90215", "risk_rating": "MEDIUM"},
        ),
        GraphNode(
            node_id="N-MERCH",
            label="CryptoVault Holdings Ltd.",
            node_type="MERCHANT",
            metadata={"merchant_id": "MERCH-KY-7741", "country": "KY"},
        ),
        GraphNode(
            node_id="N-BEN",
            label="CryptoVault Holdings Ltd.",
            node_type="BENEFICIARY",
            metadata={"beneficiary_id": "BEN-KY-3319", "is_new": "true"},
        ),
        GraphNode(
            node_id="N-DEV",
            label="Unknown Mobile Device",
            node_type="DEVICE",
            metadata={"device_id": "DEV-UNKNOWN-8812", "geolocation": "Bucharest, Romania"},
        ),
    ]
    entity_edges = [
        GraphEdge(source="N-CUST", target="N-BEN", relationship="SENT_TO", weight=0.9),
        GraphEdge(source="N-BEN", target="N-MERCH", relationship="OWNED_BY", weight=0.8),
        GraphEdge(source="N-CUST", target="N-DEV", relationship="USED_DEVICE", weight=0.7),
    ]

    # -- Reasoning Graph --
    reasoning_nodes = [
        GraphNode(node_id="R-EVIDENCE", label="Evidence Collected", node_type="STAGE"),
        GraphNode(node_id="R-HYP", label="Hypotheses Generated", node_type="STAGE"),
        GraphNode(node_id="R-VALID", label="Compliance Validated", node_type="STAGE"),
        GraphNode(node_id="R-DECISION", label="Decision Optimised", node_type="STAGE"),
    ]
    reasoning_edges = [
        GraphEdge(source="R-EVIDENCE", target="R-HYP", relationship="FEEDS_INTO"),
        GraphEdge(source="R-HYP", target="R-VALID", relationship="FEEDS_INTO"),
        GraphEdge(source="R-VALID", target="R-DECISION", relationship="FEEDS_INTO"),
    ]

    # -- Decision Comparison Graph --
    decision_nodes = [
        GraphNode(node_id="D-ALLOW", label="ALLOW", node_type="DECISION", metadata={"confidence": "0.15"}),
        GraphNode(node_id="D-HOLD", label="HOLD (Recommended)", node_type="DECISION", metadata={"confidence": "0.70"}),
        GraphNode(node_id="D-BLOCK", label="BLOCK", node_type="DECISION", metadata={"confidence": "0.40"}),
        GraphNode(node_id="D-ESCALATE", label="ESCALATE", node_type="DECISION", metadata={"confidence": "0.55"}),
    ]
    decision_edges = [
        GraphEdge(source="D-HOLD", target="D-ALLOW", relationship="PREFERRED_OVER"),
        GraphEdge(source="D-HOLD", target="D-BLOCK", relationship="PREFERRED_OVER"),
        GraphEdge(source="D-HOLD", target="D-ESCALATE", relationship="PREFERRED_OVER"),
    ]

    # -- Investigation Timeline --
    timeline = [
        TimelineEvent(
            timestamp=datetime(2025, 8, 19, 14, 32, 11),
            event_name="Transaction Flagged",
            stage=CurrentStage.INTAKE,
        ),
        TimelineEvent(
            timestamp=datetime(2025, 8, 19, 14, 33, 0),
            event_name="Evidence Collected and Context Analysed",
            stage=CurrentStage.CONTEXT,
        ),
        TimelineEvent(
            timestamp=datetime(2025, 8, 19, 14, 34, 0),
            event_name="Hypotheses Generated and Reasoning Completed",
            stage=CurrentStage.REASONING,
        ),
        TimelineEvent(
            timestamp=datetime(2025, 8, 19, 14, 35, 0),
            event_name="Decision Generated — HOLD Recommended",
            stage=CurrentStage.DECISION,
        ),
    ]

    graphs = ReportGraphs(
        entity_relationship_graph=GraphData(nodes=entity_nodes, edges=entity_edges),
        reasoning_graph=GraphData(nodes=reasoning_nodes, edges=reasoning_edges),
        decision_comparison_graph=GraphData(nodes=decision_nodes, edges=decision_edges),
        investigation_timeline=timeline,
    )

    report = InvestigationReport(
        status=AgentStatus.COMPLETED,
        executive_summary=(
            "A $48,500 wire transfer to CryptoVault Holdings Ltd. (Cayman Islands) "
            "was flagged due to a first-time beneficiary, device geolocation mismatch, "
            "and high-risk merchant category. Three hypotheses were evaluated; money "
            "laundering via crypto exchange scored highest (75% confidence). Two "
            "compliance violations were identified (AML EDD and KYC beneficiary "
            "screening). Recommendation: HOLD the transaction pending customer "
            "verification and source-of-funds declaration."
        ),
        detailed_narrative=(
            "On 19 August 2025 at 14:32 UTC, customer James Whitfield (CUST-90215) "
            "initiated a $48,500 wire transfer from account ACC-US-8821004 to "
            "ACC-KY-5529183 (CryptoVault Holdings Ltd.), a cryptocurrency exchange "
            "registered in the Cayman Islands. The transaction was submitted from "
            "an unrecognised mobile device (DEV-UNKNOWN-8812) geolocated in "
            "Bucharest, Romania, while the customer's address is in New York.\n\n"
            "Context analysis identified three key risk indicators: first-time "
            "beneficiary in a high-risk jurisdiction, device geolocation mismatch, "
            "and high-risk merchant category. The overall contextual risk score "
            "was assessed at 0.72.\n\n"
            "The reasoning agent generated three hypotheses. Money laundering via "
            "crypto exchange was rated at 75% confidence, supported by the "
            "convergence of risk signals. Account takeover was rated at 55%, "
            "primarily driven by the unknown device. Legitimate investment was "
            "rated at 35%, weakly supported by the customer's occupation as a "
            "portfolio manager.\n\n"
            "Compliance validation flagged two violations: AML enhanced due "
            "diligence (HIGH severity) and KYC beneficiary verification (MEDIUM "
            "severity). Two evidence gaps remain: beneficiary identity verification "
            "and source-of-funds declaration.\n\n"
            "Decision optimisation evaluated four options. HOLD was recommended "
            "(70% confidence) as it balances risk mitigation with customer "
            "experience, allowing time for verification without permanently "
            "blocking a potentially legitimate transaction."
        ),
        graphs=graphs,
        generated_at=datetime.utcnow(),
    )

    return {
        "investigation_report": report,
        "current_stage": CurrentStage.DONE,
    }
