"""Deterministic Reporting Agent built from the shared investigation state."""

from datetime import datetime, timezone

from app.schemas.investigation_state import (
    AgentStatus,
    CurrentStage,
    GraphData,
    GraphEdge,
    GraphNode,
    InvestigationReport,
    InvestigationState,
    ReportGraphs,
    TimelineEvent,
)


def _value(value: object) -> str:
    """Render optional state values without inventing a replacement value."""
    return str(value) if value is not None and str(value) else "Unavailable"


def _items(values: list[str], empty: str = "None provided") -> str:
    """Render supplied values while making missing upstream data explicit."""
    return "; ".join(str(value) for value in values if value) or empty


def _build_entity_graph(state: InvestigationState) -> GraphData:
    case_input = state.case_input
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    customer = case_input.customer_profile
    if customer:
        nodes.append(GraphNode(
            node_id=customer.customer_id,
            label=customer.name,
            node_type="PERSON",
            metadata={"customer_id": customer.customer_id},
        ))
    merchant = case_input.merchant_info
    if merchant:
        nodes.append(GraphNode(
            node_id=merchant.merchant_id,
            label=merchant.name,
            node_type="MERCHANT",
            metadata={"merchant_id": merchant.merchant_id},
        ))
    beneficiary = case_input.beneficiary_info
    if beneficiary:
        nodes.append(GraphNode(
            node_id=beneficiary.beneficiary_id,
            label=beneficiary.name,
            node_type="BENEFICIARY",
            metadata={"beneficiary_id": beneficiary.beneficiary_id},
        ))
    device = case_input.device_info
    if device and device.device_id:
        nodes.append(GraphNode(
            node_id=device.device_id,
            label=device.device_id,
            node_type="DEVICE",
            metadata={"device_id": device.device_id},
        ))

    if customer and beneficiary:
        edges.append(GraphEdge(
            source=customer.customer_id,
            target=beneficiary.beneficiary_id,
            relationship="ASSOCIATED_WITH",
        ))
    if beneficiary and merchant:
        edges.append(GraphEdge(
            source=beneficiary.beneficiary_id,
            target=merchant.merchant_id,
            relationship="IDENTIFIED_AS",
        ))
    if customer and device and device.device_id:
        edges.append(GraphEdge(
            source=customer.customer_id,
            target=device.device_id,
            relationship="USED_DEVICE",
        ))
    return GraphData(nodes=nodes, edges=edges)


def _build_reasoning_graph(state: InvestigationState) -> GraphData:
    reasoning = state.investigation_reasoning
    compliance = state.evidence_compliance_validation
    decision = state.decision_optimization
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    evidence_ids = {
        reference
        for hypothesis in (reasoning.hypotheses if reasoning else [])
        for reference in (*hypothesis.supporting_evidence, *hypothesis.contradicting_evidence)
        if reference
    }
    for reference in sorted(evidence_ids):
        nodes.append(GraphNode(node_id=reference, label=reference, node_type="EVIDENCE"))

    hypothesis_nodes = []
    for hypothesis in reasoning.hypotheses if reasoning else []:
        nodes.append(GraphNode(
            node_id=hypothesis.hypothesis_id,
            label=hypothesis.title,
            node_type="HYPOTHESIS",
            metadata={"confidence": str(hypothesis.confidence)},
        ))
        hypothesis_nodes.append(hypothesis.hypothesis_id)
        for reference in (*hypothesis.supporting_evidence, *hypothesis.contradicting_evidence):
            if reference:
                edges.append(GraphEdge(source=reference, target=hypothesis.hypothesis_id, relationship="INFORMS"))

    compliance_ids = []
    for mapping in compliance.compliance_mappings if compliance else []:
        nodes.append(GraphNode(
            node_id=mapping.regulation_id,
            label=mapping.regulation_name,
            node_type="COMPLIANCE",
            metadata={"severity": mapping.severity.value},
        ))
        compliance_ids.append(mapping.regulation_id)
        for reference in mapping.evidence_references:
            if reference:
                edges.append(GraphEdge(source=reference, target=mapping.regulation_id, relationship="SUPPORTS"))

    if decision and decision.recommended_decision:
        decision_id = decision.recommended_decision.value
        nodes.append(GraphNode(
            node_id=decision_id,
            label=decision_id,
            node_type="DECISION",
        ))
        for source in (*hypothesis_nodes, *compliance_ids):
            edges.append(GraphEdge(source=source, target=decision_id, relationship="INFORMS"))

    return GraphData(nodes=nodes, edges=edges)


def _build_decision_graph(state: InvestigationState) -> GraphData:
    decision = state.decision_optimization
    if not decision:
        return GraphData()
    recommended = decision.recommended_decision
    nodes = [
        GraphNode(
            node_id=option.action.value,
            label=option.action.value,
            node_type="DECISION",
            metadata={
                "confidence": str(option.confidence),
                "risk_score": _value(option.risk_score),
                "recommended": str(option.action == recommended).lower(),
            },
        )
        for option in decision.decision_options
    ]
    edges = [
        GraphEdge(
            source=recommended.value,
            target=option.action.value,
            relationship="PREFERRED_OVER",
        )
        for option in decision.decision_options
        if recommended and option.action != recommended
    ]
    return GraphData(nodes=nodes, edges=edges)


def _build_timeline(state: InvestigationState) -> list[TimelineEvent]:
    events = [
        TimelineEvent(
            timestamp=transaction.timestamp,
            event_name=f"Transaction {transaction.transaction_id} included in investigation",
            stage=CurrentStage.INTAKE,
        )
        for transaction in state.case_input.transactions
    ]
    events.extend(
        TimelineEvent(
            timestamp=document.uploaded_at,
            event_name=f"Document {document.document_id} available as supporting evidence",
            stage=CurrentStage.CONTEXT,
        )
        for document in state.case_input.supporting_documents
        if document.uploaded_at is not None
    )
    return sorted(events, key=lambda event: event.timestamp)


def reporting_agent(state: InvestigationState) -> dict:
    """Assemble a polished, evidence-aware report without recomputing agents."""
    case_input = state.case_input
    customer = case_input.customer_profile
    context = state.context_intelligence
    reasoning = state.investigation_reasoning
    compliance = state.evidence_compliance_validation
    decision = state.decision_optimization

    transactions = case_input.transactions
    total_amount = sum(transaction.amount for transaction in transactions)
    recommendation = decision.recommended_decision.value if decision and decision.recommended_decision else None
    rationale = decision.decision_rationale if decision else None
    hypotheses = reasoning.hypotheses if reasoning else []
    mappings = compliance.compliance_mappings if compliance else []
    evidence_references = sorted({
        reference
        for document in case_input.supporting_documents
        for reference in (*[document.document_id], *document.evidence_references)
        if reference
    })
    evidence_references.extend(transaction.transaction_id for transaction in transactions)
    evidence_references.extend(
        reference
        for hypothesis in hypotheses
        for reference in (*hypothesis.supporting_evidence, *hypothesis.contradicting_evidence)
        if reference
    )
    evidence_references.extend(
        reference
        for mapping in mappings
        for reference in mapping.evidence_references
        if reference
    )
    evidence_references = sorted(set(evidence_references))

    executive_summary = (
        f"Investigation {state.case_id} covers {len(transactions)} transaction(s) "
        f"totalling {total_amount:g}. Customer: {_value(customer.name if customer else None)}. "
        f"Context summary: {_value(context.context_summary if context else None)} "
        f"Recommended decision: {_value(recommendation)}. "
        f"Evidence gaps identified: {len(compliance.evidence_gaps) if compliance else 0}."
    )
    narrative = [
        "## Final synthesis",
        f"This report consolidates the available case material and upstream findings for case {state.case_id}.",
        f"The current recommendation is {_value(recommendation)}; its stated rationale is {_value(rationale)}.",
        (
            f"The conclusion remains subject to {len(compliance.evidence_gaps)} documented evidence gap(s), listed below."
            if compliance and compliance.evidence_gaps
            else "No evidence gaps were identified by the available compliance output."
        ),
        "",
        "## Case information",
        f"- Case ID: {state.case_id}",
        f"- Alert reason: {_value(case_input.alert_reason)}",
        f"- Customer: {_value(customer.name if customer else None)} ({_value(customer.customer_id if customer else None)})",
        "- Transactions:",
    ]
    narrative.extend(
        f"  - {transaction.transaction_id}: {transaction.amount:g} {transaction.currency}; "
        f"{transaction.transaction_type}; {transaction.sender_account} → {transaction.receiver_account}; "
        f"{transaction.timestamp.isoformat()}"
        for transaction in transactions
    )
    if not transactions:
        narrative.append("  - None provided")
    if case_input.merchant_info:
        merchant = case_input.merchant_info
        narrative.append(f"- Merchant: {merchant.name} ({merchant.merchant_id}); category={merchant.category}; country={_value(merchant.country)}")
    if case_input.beneficiary_info:
        beneficiary = case_input.beneficiary_info
        narrative.append(f"- Beneficiary: {beneficiary.name} ({beneficiary.beneficiary_id}); country={_value(beneficiary.country)}; new={beneficiary.is_new}")
    if case_input.device_info:
        device = case_input.device_info
        narrative.append(f"- Device: {_value(device.device_id)}; type={_value(device.device_type)}; known={device.is_known_device}")
    narrative.append("- Supporting documents:")
    narrative.extend(
        f"  - {document.document_id}: {document.document_type}; file={_value(document.file_name)}; "
        f"references={_items(document.evidence_references)}"
        for document in case_input.supporting_documents
    )
    if not case_input.supporting_documents:
        narrative.append("  - None provided")

    narrative.extend(["", "## Context and reasoning findings", f"- Context summary: {_value(context.context_summary if context else None)}", f"- Context risk score: {_value(context.risk_score if context else None)}", f"- Key indicators: {_items(context.key_indicators if context else [])}"])
    if context and context.anomalies:
        narrative.append("- Anomalies:")
        narrative.extend(f"  - {item.anomaly_id} ({item.anomaly_type.value}, {item.severity.value}): {item.description}; related transactions={_items(item.related_transactions)}" for item in context.anomalies)
    else:
        narrative.append("- Anomalies: None provided")
    narrative.extend([f"- Reasoning summary: {_value(reasoning.reasoning_summary if reasoning else None)}", "- Hypotheses:"])
    if hypotheses:
        for item in hypotheses:
            narrative.extend([f"  - {item.hypothesis_id}: {item.title} (confidence {item.confidence:g})", f"    - Finding: {item.description}", f"    - Supporting evidence: {_items(item.supporting_evidence)}", f"    - Contradicting evidence: {_items(item.contradicting_evidence)}"])
    else:
        narrative.append("  - None provided")
    if reasoning:
        narrative.append(f"- Recommended actions from reasoning: {_items(reasoning.recommended_actions)}")

    narrative.extend(["", "## Compliance and evidence traceability", f"- Compliance validation summary: {_value(compliance.validation_summary if compliance else None)}", "- Compliance mappings:"])
    if mappings:
        for item in mappings:
            narrative.extend([f"  - {item.regulation_id} — {item.regulation_name}", f"    - Description: {_value(item.description)}", f"    - Violation status: {'VIOLATED' if item.is_violated else 'NOT ESTABLISHED'}", f"    - Severity: {item.severity.value}"])
            narrative.append(f"    - Evidence references: {_items(item.evidence_references)}" if item.evidence_references else "    - Evidence status: Insufficient evidence — no evidence references were supplied for this compliance mapping.")
    else:
        narrative.append("  - None provided")
    narrative.append(f"- Evidence gaps: {_items(compliance.evidence_gaps if compliance else [], 'None identified by the compliance stage')}")

    narrative.extend(["", "## Decision assessment", f"- Recommended decision: {_value(recommendation)}", f"- Decision rationale: {_value(rationale)}", "- Available decision options:"])
    if decision and decision.decision_options:
        for item in decision.decision_options:
            narrative.extend([f"  - {item.action.value} (confidence {item.confidence:g}; risk score {_value(item.risk_score)})", f"    - Rationale: {item.rationale}", f"    - Pros: {_items(item.pros)}", f"    - Cons: {_items(item.cons)}", f"    - Risks: {_items(item.risks)}", f"    - Mitigations: {_items(item.mitigation)}"])
    else:
        narrative.append("  - None provided")

    narrative.extend(["", "## Evidence and provenance", f"- Evidence references available across case input and upstream findings: {_items(evidence_references)}", "- Evidence references are reproduced from upstream inputs; this report does not infer additional evidence."])
    detailed_narrative = "\n".join(narrative)

    return {
        "investigation_report": InvestigationReport(
            status=AgentStatus.COMPLETED,
            executive_summary=executive_summary,
            detailed_narrative=detailed_narrative,
            graphs=ReportGraphs(
                entity_relationship_graph=_build_entity_graph(state),
                reasoning_graph=_build_reasoning_graph(state),
                decision_comparison_graph=_build_decision_graph(state),
                investigation_timeline=_build_timeline(state),
            ),
            generated_at=datetime.now(timezone.utc),
        )
    }
