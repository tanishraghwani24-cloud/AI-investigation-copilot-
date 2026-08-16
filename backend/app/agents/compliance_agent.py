"""Evidence-backed AML/KYC compliance analysis agent."""

from __future__ import annotations

import logging

from app.schemas.investigation_state import (
    AgentStatus,
    ComplianceMapping,
    EvidenceComplianceValidation,
    InvestigationState,
    SeverityLevel,
)
from app.services.gemini_client import GeminiClientError, get_gemini_client

logger = logging.getLogger(__name__)


def _available_evidence_ids(state: InvestigationState) -> set[str]:
    """Collect only concrete identifiers genuinely available in the state."""
    case_input = state.case_input
    identifiers = {transaction.transaction_id for transaction in case_input.transactions}
    for document in case_input.supporting_documents:
        identifiers.add(document.document_id)
        identifiers.update(reference for reference in document.evidence_references if reference)
        identifiers.update(reference for reference in document.extracted_transactions if reference)
    for value in (
        case_input.customer_profile.customer_id if case_input.customer_profile else None,
        case_input.merchant_info.merchant_id if case_input.merchant_info else None,
        case_input.beneficiary_info.beneficiary_id if case_input.beneficiary_info else None,
        case_input.device_info.device_id if case_input.device_info else None,
    ):
        if value:
            identifiers.add(value)
    if state.context_intelligence:
        identifiers.update(anomaly.anomaly_id for anomaly in state.context_intelligence.anomalies)
        for anomaly in state.context_intelligence.anomalies:
            identifiers.update(anomaly.related_transactions)
    if state.investigation_reasoning:
        identifiers.update(
            hypothesis.hypothesis_id
            for hypothesis in state.investigation_reasoning.hypotheses
        )
    return identifiers


def _missing_evidence_gaps(state: InvestigationState) -> list[str]:
    """Identify missing evidence without representing absence as a breach."""
    documents = state.case_input.supporting_documents
    if not documents:
        return [
            "No supporting documents are available to corroborate the transaction or customer information.",
            "Insufficient evidence to confirm KYC completeness: no identity verification document is available.",
        ]
    combined = " ".join(
        " ".join(filter(None, (doc.document_type, doc.summary, doc.extracted_text))).lower()
        for doc in documents
    )
    gaps: list[str] = []
    if not any(token in combined for token in ("passport", "identity", "id_scan", "driver", "national id")):
        gaps.append("Insufficient evidence to confirm KYC completeness: no identity verification document is available.")
    if not any(token in combined for token in ("source of funds", "source-of-funds", "payslip", "income", "bank statement")):
        gaps.append("Insufficient evidence to assess source of funds: no source-of-funds documentation is available.")
    if state.case_input.beneficiary_info and not any(
        token in combined for token in ("beneficial owner", "beneficiary", "ownership")
    ):
        gaps.append("Insufficient evidence to verify beneficiary information: no beneficiary or beneficial-owner documentation is available.")
    return gaps


def _normalise_mappings(mappings: list[ComplianceMapping], available_ids: set[str]) -> list[ComplianceMapping]:
    """Remove fabricated identifiers and qualify findings without evidence."""
    normalised: list[ComplianceMapping] = []
    for mapping in mappings:
        evidence = [reference for reference in mapping.evidence_references if reference in available_ids]
        if evidence:
            normalised.append(mapping.model_copy(update={"evidence_references": evidence}))
            continue
        description = mapping.description or ""
        if "insufficient evidence" not in description.lower():
            description = (
                f"{description} Insufficient evidence to confirm or deny this compliance "
                "concern: the available case materials do not substantiate the finding."
            ).strip()
        normalised.append(mapping.model_copy(update={
            "description": description,
            "is_violated": False,
            "severity": SeverityLevel.LOW,
            "evidence_references": [],
        }))
    return normalised


def _build_prompt(state: InvestigationState) -> str:
    """Build a prompt that exposes all permitted evidence identifiers."""
    context_json = state.context_intelligence.model_dump_json(indent=2) if state.context_intelligence else "{}"
    reasoning_json = state.investigation_reasoning.model_dump_json(indent=2) if state.investigation_reasoning else "{}"
    return f"""\
You are an AML/KYC investigation assistant. Analyse only the supplied materials.
Do not claim a regulatory breach, sanctions hit, KYC failure, or fact that the
case materials do not establish.

=== CASE INPUT ===
{state.case_input.model_dump_json(indent=2)}
=== CONTEXT INTELLIGENCE ===
{context_json}
=== INVESTIGATION REASONING ===
{reasoning_json}
=== VALID EVIDENCE IDENTIFIERS ===
{sorted(_available_evidence_ids(state))}

Return only a JSON object with compliance_mappings, evidence_gaps, and
validation_summary. A compliance_mappings item has regulation_id,
regulation_name, description, is_violated, severity (LOW, MEDIUM, or HIGH),
and evidence_references. Assess suspicious activity, patterns, transaction
size, jurisdiction, beneficiary, and KYC concerns only when the case supports
them. Every evidence_references value must be one of VALID EVIDENCE IDENTIFIERS.
If a concern cannot be confirmed, explicitly state that evidence is insufficient,
use no evidence references, and do not call it a violation. Identify relevant
missing identity, source-of-funds, transaction, or beneficial-owner evidence,
but do not say supplied evidence is missing. Never invent identifiers.
"""


def compliance_agent(state: InvestigationState) -> dict:
    """Produce evidence-backed ``EvidenceComplianceValidation`` for *state*."""
    prompt = _build_prompt(state)
    try:
        response = get_gemini_client().generate(
            prompt, response_schema=EvidenceComplianceValidation
        )
        response = EvidenceComplianceValidation.model_validate(response)
    except GeminiClientError:
        logger.exception("Gemini call failed in compliance_agent")
        raise
    mappings = _normalise_mappings(response.compliance_mappings, _available_evidence_ids(state))
    gaps = list(dict.fromkeys([*response.evidence_gaps, *_missing_evidence_gaps(state)]))
    summary = response.validation_summary or (
        f"Compliance review produced {len(mappings)} evidence-constrained finding(s) and identified {len(gaps)} evidence gap(s)."
    )
    return {"evidence_compliance_validation": EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=mappings,
        evidence_gaps=gaps,
        validation_summary=summary,
    )}
