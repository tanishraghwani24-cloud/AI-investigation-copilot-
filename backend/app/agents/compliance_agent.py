"""Evidence-backed AML/KYC compliance analysis agent.

Round 5: finalize evidence traceability — every ComplianceMapping either
cites real evidence or is explicitly labelled as unsupported.
"""

from __future__ import annotations

import logging
import re

from app.schemas.investigation_state import (
    AgentStatus,
    ComplianceMapping,
    EvidenceComplianceValidation,
    InvestigationState,
    SeverityLevel,
)
from app.services.gemini_client import GeminiClientError, get_gemini_client

logger = logging.getLogger(__name__)

_INSUFFICIENT_EVIDENCE_LABEL = (
    "Insufficient evidence to confirm or deny this compliance "
    "concern: the available case materials do not substantiate the finding."
)


def _available_evidence_ids(state: InvestigationState) -> set[str]:
    """Collect only concrete identifiers genuinely available in the state."""
    case_input = state.case_input
    identifiers = {
        transaction.transaction_id
        for transaction in case_input.transactions
        if transaction.transaction_id.strip()
    }
    for document in case_input.supporting_documents:
        if document.document_id.strip():
            identifiers.add(document.document_id)
        identifiers.update(
            reference for reference in document.evidence_references if reference.strip()
        )
        identifiers.update(
            reference for reference in document.extracted_transactions if reference.strip()
        )
    for value in (
        case_input.customer_profile.customer_id if case_input.customer_profile else None,
        case_input.merchant_info.merchant_id if case_input.merchant_info else None,
        case_input.beneficiary_info.beneficiary_id if case_input.beneficiary_info else None,
        case_input.device_info.device_id if case_input.device_info else None,
    ):
        if value and value.strip():
            identifiers.add(value)
    if state.context_intelligence:
        identifiers.update(
            anomaly.anomaly_id
            for anomaly in state.context_intelligence.anomalies
            if anomaly.anomaly_id.strip()
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


# ── Round 5: evidence derivation from reasoning hypotheses ───────────


def _derive_evidence_from_description(
    description: str,
    available_ids: set[str],
    state: InvestigationState,
) -> list[str]:
    """Attempt to derive real evidence IDs for a mapping that lacks direct references.

    Scans the mapping's description text for structured evidence IDs that
    match ``available_ids``.  Then cross-references reasoning hypotheses:
    if a hypothesis's ``supporting_evidence`` contains an ID present in
    ``available_ids`` *and* that ID appears in the mapping description,
    it is included.

    Returns only IDs that exist in ``available_ids`` — never fabricated.
    """
    if not description:
        return []

    # 1. Match actual state identifiers exactly.  This intentionally avoids
    # treating a string as evidence merely because it looks like an ID.
    mentioned_ids = {
        evidence_id
        for evidence_id in available_ids
        if re.search(
            rf"(?<![A-Za-z0-9_-]){re.escape(evidence_id)}(?![A-Za-z0-9_-])",
            description,
        )
    }
    derived = set(mentioned_ids)

    # 2. Cross-reference reasoning hypotheses for additional real IDs.
    if state.investigation_reasoning:
        for hypothesis in state.investigation_reasoning.hypotheses:
            # Collect real evidence IDs from hypothesis supporting_evidence.
            for evidence_item in hypothesis.supporting_evidence:
                real_ids = {
                    evidence_id
                    for evidence_id in available_ids
                    if re.search(
                        rf"(?<![A-Za-z0-9_-]){re.escape(evidence_id)}(?![A-Za-z0-9_-])",
                        evidence_item,
                    )
                }
                if not real_ids:
                    continue
                # If any of these real IDs are also mentioned in the mapping
                # description, they strengthen traceability.
                for rid in real_ids:
                    if rid in description:
                        derived.add(rid)

    return sorted(derived)


def _normalise_mappings(
    mappings: list[ComplianceMapping],
    available_ids: set[str],
    state: InvestigationState,
) -> list[ComplianceMapping]:
    """Remove fabricated identifiers and qualify findings without evidence.

    Round 5: before labelling a mapping as unsupported, attempts to derive
    real evidence references from the mapping description and reasoning
    hypothesis cross-references.
    """
    normalised: list[ComplianceMapping] = []
    for mapping in mappings:
        # Step 1: keep only evidence references that exist in the state.
        evidence = [reference for reference in mapping.evidence_references if reference in available_ids]

        if evidence:
            normalised.append(mapping.model_copy(update={"evidence_references": evidence}))
            continue

        # Step 2 (Round 5): attempt to derive real evidence from description.
        description = mapping.description or ""
        derived = _derive_evidence_from_description(description, available_ids, state)

        if derived:
            normalised.append(mapping.model_copy(update={"evidence_references": derived}))
            continue

        # Step 3: no real evidence — explicitly label as insufficient.
        if "insufficient evidence" not in description.lower():
            description = f"{description} {_INSUFFICIENT_EVIDENCE_LABEL}".strip()
        normalised.append(mapping.model_copy(update={
            "description": description,
            "is_violated": False,
            "severity": SeverityLevel.LOW,
            "evidence_references": [],
        }))
    return normalised


from app.prompts.compliance_prompts import build_compliance_prompt

def _build_prompt(state: InvestigationState) -> str:
    """Build a prompt that exposes all permitted evidence identifiers."""
    case_json = state.case_input.model_dump_json(indent=2)
    context_json = state.context_intelligence.model_dump_json(indent=2) if state.context_intelligence else "{}"
    reasoning_json = state.investigation_reasoning.model_dump_json(indent=2) if state.investigation_reasoning else "{}"
    valid_ids = sorted(_available_evidence_ids(state))

    return build_compliance_prompt(
        case_json=case_json,
        context_json=context_json,
        reasoning_json=reasoning_json,
        valid_evidence_ids=valid_ids,
    )


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
    available_ids = _available_evidence_ids(state)
    mappings = _normalise_mappings(response.compliance_mappings, available_ids, state)
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
