"""Evidence-backed AML/KYC compliance analysis agent.

Round 5: finalize evidence traceability — every ComplianceMapping either
cites real evidence or is explicitly labelled as unsupported.
"""

from __future__ import annotations

import json as _json
import logging
import re

from app.schemas.investigation_state import (
    AgentStatus,
    ComplianceMapping,
    EvidenceComplianceValidation,
    InvestigationState,
    SeverityLevel,
)
from app.services.gemini_client import GeminiClientError, get_reasoning_client

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


# ── Compact prompt builders ──────────────────────────────────────────


def _build_compact_case(state: InvestigationState) -> str:
    """Build a compact JSON summary of case data for the Compliance prompt.

    Preserves all fields needed for compliance analysis:
    - alert_reason
    - Transaction: ID, amount, currency, timestamp, sender/receiver, type,
      channel, description
    - Customer: ID, name, risk_rating
    - Merchant: ID, name, category, country, risk_level
    - Beneficiary: ID, name, country, is_new
    - Device: ID, type, geolocation, is_known_device
    - Documents: ID, type, summary, evidence_references, extracted_transactions

    Excluded (PII / metadata not needed for compliance evaluation):
    - Customer: email, phone, address, date_of_birth, account_open_date,
      occupation, nationality
    - Device: ip_address, os, browser
    - Documents: file_url, file_name, extracted_text, extracted_entities,
      processing_status, uploaded_at
    - behavioral_biometrics (entire object)
    - face_verification (entire object)
    """
    case_input = state.case_input
    compact: dict = {"alert_reason": case_input.alert_reason}

    compact["transactions"] = [
        {
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "currency": t.currency,
            "transaction_type": t.transaction_type,
            "sender_account": t.sender_account,
            "receiver_account": t.receiver_account,
            "timestamp": t.timestamp.isoformat(),
            "channel": t.channel,
            **({"description": t.description} if t.description else {}),
        }
        for t in case_input.transactions
    ]

    customer = case_input.customer_profile
    if customer:
        compact["customer"] = {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "risk_rating": customer.risk_rating,
        }

    merchant = case_input.merchant_info
    if merchant:
        compact["merchant"] = {
            "merchant_id": merchant.merchant_id,
            "name": merchant.name,
            "category": merchant.category,
            "country": merchant.country,
            "risk_level": merchant.risk_level.value if merchant.risk_level else None,
        }

    beneficiary = case_input.beneficiary_info
    if beneficiary:
        compact["beneficiary"] = {
            "beneficiary_id": beneficiary.beneficiary_id,
            "name": beneficiary.name,
            "country": beneficiary.country,
            "is_new": beneficiary.is_new,
        }

    device = case_input.device_info
    if device:
        compact["device"] = {
            "device_id": device.device_id,
            "device_type": device.device_type,
            "geolocation": device.geolocation,
            "is_known_device": device.is_known_device,
        }

    if case_input.supporting_documents:
        compact["supporting_documents"] = [
            {
                "document_id": d.document_id,
                "document_type": d.document_type,
                **({"summary": d.summary} if d.summary else {}),
                **({"evidence_references": d.evidence_references} if d.evidence_references else {}),
                **({"extracted_transactions": d.extracted_transactions} if d.extracted_transactions else {}),
            }
            for d in case_input.supporting_documents
        ]

    return _json.dumps(compact, indent=2, default=str)


def _build_compact_context(state: InvestigationState) -> str:
    """Build a compact JSON summary of context intelligence for the Compliance prompt.

    Preserves: context_summary, key_indicators, risk_score, anomalies.
    Excluded: status, historical_baseline.
    """
    context = state.context_intelligence
    if context is None:
        return "{}"

    compact: dict = {}
    if context.context_summary:
        compact["context_summary"] = context.context_summary
    if context.key_indicators:
        compact["key_indicators"] = context.key_indicators
    if context.risk_score is not None:
        compact["risk_score"] = context.risk_score
    if context.anomalies:
        compact["anomalies"] = [
            {
                "anomaly_id": a.anomaly_id,
                "anomaly_type": a.anomaly_type.value,
                "severity": a.severity.value,
                "description": a.description,
                "related_transactions": a.related_transactions,
            }
            for a in context.anomalies
        ]
    return _json.dumps(compact, indent=2, default=str)


def _build_compact_reasoning(state: InvestigationState) -> str:
    """Build a compact JSON summary of investigation reasoning for the Compliance prompt.

    Preserves:
    - Hypotheses: hypothesis_id, title, description, confidence,
      supporting_evidence, contradicting_evidence
    - recommended_actions

    Excluded:
    - status (agent lifecycle, not compliance-relevant)
    - reasoning_summary (compliance doesn't need the narrative summary;
      the hypotheses themselves contain the relevant analysis)
    """
    reasoning = state.investigation_reasoning
    if reasoning is None:
        return "{}"

    compact: dict = {}
    compact["hypotheses"] = [
        {
            "hypothesis_id": h.hypothesis_id,
            "title": h.title,
            "description": h.description,
            "confidence": h.confidence,
            "supporting_evidence": h.supporting_evidence,
            "contradicting_evidence": h.contradicting_evidence,
        }
        for h in reasoning.hypotheses
    ]
    if reasoning.recommended_actions:
        compact["recommended_actions"] = reasoning.recommended_actions

    return _json.dumps(compact, indent=2, default=str)


def _build_prompt(state: InvestigationState) -> str:
    """Build a prompt that exposes all permitted evidence identifiers.

    Uses compact JSON summaries instead of full model_dump_json() to
    reduce prompt size while preserving all evidence IDs, transaction
    facts, and risk indicators needed for compliance analysis.
    """
    case_json = _build_compact_case(state)
    context_json = _build_compact_context(state)
    reasoning_json = _build_compact_reasoning(state)
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
        response = get_reasoning_client().generate(
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
