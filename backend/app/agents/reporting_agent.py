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
    return str(value) if value is not None else "Unavailable"


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
    """Assemble a report from upstream outputs without recomputing them."""
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
        f"Recommended decision: {_value(recommendation)}."
    )
    detailed_narrative = "\n".join([
        f"Case identity: {state.case_id}.",
        f"Alert reason: {_value(case_input.alert_reason)}.",
        f"Customer: {_value(customer.name if customer else None)} ({_value(customer.customer_id if customer else None)}).",
        f"Transactions: {', '.join(transaction.transaction_id for transaction in transactions) or 'Unavailable'}.",
        f"Context indicators: {', '.join(context.key_indicators) if context and context.key_indicators else 'Unavailable'}.",
        f"Hypotheses: {'; '.join(f'{item.title} ({item.confidence:g})' for item in hypotheses) or 'Unavailable'}.",
        f"Compliance findings: {'; '.join(item.regulation_name for item in mappings) or 'Unavailable'}.",
        f"Evidence references: {', '.join(evidence_references) or 'Unavailable'}.",
        f"Recommended decision: {_value(recommendation)}.",
        f"Decision rationale: {_value(rationale)}.",
    ])

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
