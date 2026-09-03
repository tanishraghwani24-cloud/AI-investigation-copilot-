"""Reasoning Agent — Gemini-powered hypothesis generation.

Uses compact JSON summaries of case data and context intelligence
to reduce prompt size while preserving all investigation-relevant
facts needed for evidence-grounded hypothesis generation.

Round 2: Single hypothesis generation.  Multiple / competing
hypotheses belong to a later round.

Round 5: When ``evidence_compliance_validation`` is already present in the
state, the agent cross-references compliance findings with each hypothesis.
If a compliance finding directly contradicts a hypothesis (shared evidence
reference + flagged concern), confidence is reduced and the contradiction
is explicitly acknowledged in the hypothesis description.
"""

import json as _json
import logging
import re
from json import JSONDecodeError

from pydantic import BaseModel, ValidationError

from app.schemas.investigation_state import (
    AgentStatus,
    ComplianceMapping,
    Hypothesis,
    InvestigationReasoning,
    InvestigationState,
    SeverityLevel,
)
from app.services.gemini_client import GeminiClientError, get_reasoning_client


logger = logging.getLogger(__name__)


# ── Response Schema ──────────────────────────────────────────────────


class HypothesesResponse(BaseModel):
    """Schema for Gemini to return multiple hypotheses."""
    hypotheses: list[Hypothesis]


class GroundingViolationError(Exception):
    """Raised when the model output mentions unavailable data categories."""
    pass


# These are the stable, case-scoped identifiers that can appear in evidence
# citations.  Keep device IDs here as well: the compact reasoning prompt
# exposes them and therefore an invented DEV-* identifier must not slip
# through normalisation merely because "device" is descriptive language.
_EVIDENCE_ID_PATTERN = re.compile(r"\b(?:TXN|DOC|CUST|ACC|ANOM|DEV)-[A-Z0-9-]+\b")
_SPARSE_CONFIDENCE_CAP = 0.5


def _is_sparse_evidence(state: InvestigationState) -> bool:
    """Return whether the case lacks documentary or contextual corroboration."""
    documents = state.case_input.supporting_documents or []
    context = state.context_intelligence
    has_context = bool(
        context
        and (
            context.context_summary
            or context.key_indicators
            or context.anomalies
        )
    )
    return not documents or (not state.case_input.transactions and not has_context)


def _available_evidence_values(state: InvestigationState) -> set[str]:
    """Collect concrete identifiers and text already present in the state."""
    values: set[str] = set()
    case_input = state.case_input

    for transaction in case_input.transactions:
        values.update(
            value for value in (
                transaction.transaction_id,
                transaction.sender_account,
                transaction.receiver_account,
                transaction.description,
            ) if value
        )
    for document in case_input.supporting_documents or []:
        values.update(
            value for value in (
                document.document_id,
                document.file_name,
                document.document_type,
                document.summary,
                document.extracted_text,
            ) if value
        )
    if case_input.customer_profile is not None:
        values.update(
            str(value) for value in case_input.customer_profile.model_dump().values()
            if value is not None
        )
    if case_input.device_info is not None and case_input.device_info.device_id:
        values.add(case_input.device_info.device_id)
    if case_input.alert_reason:
        values.add(case_input.alert_reason)
    if state.context_intelligence is not None:
        context = state.context_intelligence
        values.update(value for value in context.key_indicators if value)
        values.update(
            value for value in (context.context_summary,) if value
        )
        for anomaly in context.anomalies:
            values.update([anomaly.anomaly_id, anomaly.description])
            values.update(anomaly.related_transactions)
    return values


def _evidence_is_available(item: str, available_values: set[str]) -> bool:
    """Accept evidence only when it refers to data already in the state."""
    referenced_ids = set(_EVIDENCE_ID_PATTERN.findall(item.upper()))
    available_ids = {
        identifier.upper()
        for value in available_values
        for identifier in _EVIDENCE_ID_PATTERN.findall(value.upper())
    }
    if referenced_ids and not referenced_ids.issubset(available_ids):
        return False

    item_lower = item.lower()
    # Existing reasoning outputs commonly reference an alert generically;
    # that remains grounded when the case includes an alert reason.
    if "alert triggered" in item_lower and any(
        "alert" in value.lower() or "suspicious" in value.lower()
        for value in available_values
    ):
        return True
    return any(
        len(value.strip()) >= 4 and value.lower() in item_lower
        for value in available_values
    )


def _normalise_hypotheses(
    hypotheses: list[Hypothesis],
    state: InvestigationState,
) -> list[Hypothesis]:
    """Remove unsupported evidence and calibrate sparse-case hypotheses."""
    available_values = _available_evidence_values(state)
    sparse = _is_sparse_evidence(state)
    normalised: list[Hypothesis] = []

    for hypothesis in hypotheses:
        supporting = [
            item for item in hypothesis.supporting_evidence
            if _evidence_is_available(item, available_values)
        ]
        contradicting = [
            item for item in hypothesis.contradicting_evidence
            if _evidence_is_available(item, available_values)
        ]
        description = hypothesis.description
        confidence = hypothesis.confidence
        if sparse:
            confidence = min(confidence, _SPARSE_CONFIDENCE_CAP)
            uncertainty = (
                " Available evidence is limited; this is an investigative "
                "possibility rather than an established finding."
            )
            if "evidence is limited" not in description.lower():
                description += uncertainty

        normalised.append(hypothesis.model_copy(update={
            "description": description,
            "confidence": confidence,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
        }))
    return normalised


def _check_grounding_violation(hypotheses: list[Hypothesis], state: InvestigationState) -> str | None:
    """Return an error message if the response violates grounding rules, else None.

    This check rejects hypotheses that reference **data categories the
    pipeline never supplies** (e.g. biometric scans, KYC documents,
    passport data).  Generic descriptive words like "device", "channel",
    "mobile", "document", and "alert" are NOT forbidden because they are
    natural language the LLM uses when describing facts present in the
    prompt.  Concrete invented identifiers (TXN-999, DEV-XYZ, ACC-ABC)
    are separately caught by ``_evidence_is_available`` in
    ``_normalise_hypotheses``.
    """
    # Only categories the pipeline genuinely never provides.
    # Generic descriptive words (device, channel, mobile, document, alert,
    # profile, web, history) were removed because they caused false
    # rejections when Gemini referenced facts actually present in the
    # prompt.  Concrete ID protection is handled by _evidence_is_available.
    forbidden_terms = [
        "biometric", "face", "facial",
        "past behavior", "previous transaction",
        "demographic", "kyc",
        "passport", "id card", "invoice",
    ]

    available_text = " ".join([v.lower() for v in _available_evidence_values(state)])

    for hyp in hypotheses:
        # Check title, evidence, and factual part of description
        desc_factual = hyp.description.lower().split("recommend")[0]
        text_to_check = (
            hyp.title.lower() + " " +
            desc_factual + " " +
            " ".join(hyp.supporting_evidence).lower() + " " +
            " ".join(hyp.contradicting_evidence).lower()
        )

        for term in forbidden_terms:
            if term in text_to_check and term not in available_text:
                return f"Used unavailable data category '{term}'."

    return None


# ── Round 5: Compliance alignment ────────────────────────────────────

# Compliance severity levels considered significant enough to constitute a
# contradiction when they reference evidence shared with a hypothesis.
_CONTRADICTION_SEVERITIES = {SeverityLevel.MEDIUM, SeverityLevel.HIGH}

# Multiplier applied to hypothesis confidence when a compliance contradiction
# is detected.  0.8 means a 20 % reduction.
_COMPLIANCE_CONFIDENCE_PENALTY = 0.8


def _extract_evidence_ids(evidence_items: list[str]) -> set[str]:
    """Extract all structured evidence IDs from a list of evidence strings."""
    ids: set[str] = set()
    for item in evidence_items:
        ids.update(_EVIDENCE_ID_PATTERN.findall(item.upper()))
    return ids


def _find_contradicting_mappings(
    hypothesis: Hypothesis,
    compliance_mappings: list[ComplianceMapping],
) -> list[ComplianceMapping]:
    """Return compliance mappings that directly contradict *hypothesis*.

    A mapping is considered contradictory when:
    1. At least one of its ``evidence_references`` matches an evidence ID
       referenced in the hypothesis's ``supporting_evidence``.
    2. The mapping is flagged — either ``is_violated`` is True or its
       ``severity`` is MEDIUM or higher.

    This ensures that only meaningfully related and flagged compliance
    findings are treated as contradictions.
    """
    hypothesis_ids = _extract_evidence_ids(hypothesis.supporting_evidence)
    if not hypothesis_ids:
        return []

    contradicting: list[ComplianceMapping] = []
    for mapping in compliance_mappings:
        # Only consider flagged findings
        is_flagged = mapping.is_violated or mapping.severity in _CONTRADICTION_SEVERITIES
        if not is_flagged:
            continue

        mapping_ids = {ref.upper() for ref in mapping.evidence_references}
        if hypothesis_ids & mapping_ids:
            contradicting.append(mapping)

    return contradicting


def _apply_compliance_alignment(
    hypotheses: list[Hypothesis],
    state: InvestigationState,
) -> list[Hypothesis]:
    """Adjust hypotheses that are directly contradicted by compliance findings.

    When ``evidence_compliance_validation`` is present in *state* and contains
    compliance mappings, each hypothesis is checked for overlapping evidence
    references.  If a flagged compliance finding shares evidence with a
    hypothesis, the hypothesis's confidence is reduced and its description is
    updated to explicitly acknowledge the compliance concern.

    When compliance data is absent, None, or empty, hypotheses are returned
    unchanged — preserving full backward compatibility.
    """
    compliance = state.evidence_compliance_validation
    if compliance is None:
        return hypotheses
    if not compliance.compliance_mappings:
        return hypotheses

    aligned: list[Hypothesis] = []
    for hypothesis in hypotheses:
        contradictions = _find_contradicting_mappings(
            hypothesis, compliance.compliance_mappings,
        )
        if not contradictions:
            aligned.append(hypothesis)
            continue

        # Build acknowledgment language citing each contradicting regulation.
        concerns = []
        for mapping in contradictions:
            label = mapping.regulation_name or mapping.regulation_id
            detail = mapping.description or "compliance concern identified"
            concerns.append(f"{label}: {detail}")

        acknowledgment = (
            " [Compliance alignment] Confidence reduced — compliance "
            "findings raise concern(s) related to the same evidence: "
            + "; ".join(concerns)
            + "."
        )

        adjusted_confidence = round(
            max(0.0, min(1.0, hypothesis.confidence * _COMPLIANCE_CONFIDENCE_PENALTY)),
            4,
        )

        # Add compliance concern references to contradicting_evidence so
        # downstream consumers can see the provenance.
        extra_contradicting = [
            f"Compliance finding ({m.regulation_id}): {m.description or m.regulation_name}"
            for m in contradictions
        ]

        aligned.append(hypothesis.model_copy(update={
            "description": hypothesis.description + acknowledgment,
            "confidence": adjusted_confidence,
            "contradicting_evidence": hypothesis.contradicting_evidence + extra_contradicting,
        }))

    return aligned

def _is_malformed_structured_output(error: Exception) -> bool:
    """Identify parsing or Pydantic validation failures eligible for one retry."""
    if isinstance(error, (ValidationError, JSONDecodeError, TypeError, AttributeError)):
        return True
    return (
        isinstance(error, GeminiClientError)
        and isinstance(error.original_error, (ValidationError, JSONDecodeError, TypeError))
    )


def _get_hypotheses(client: object, prompt: str) -> HypothesesResponse:
    """Request and validate the Gemini structured response defensively."""
    response = client.generate(prompt, response_schema=HypothesesResponse)  # type: ignore[attr-defined]
    return HypothesesResponse.model_validate(response)


# ── Compact prompt builders ──────────────────────────────────────────


def _build_compact_case(state: InvestigationState) -> str:
    """Build a compact JSON summary of case data for the Reasoning prompt.

    Preserves all investigation-relevant facts:
    - alert_reason
    - Transaction: ID, amount, currency, timestamp, sender/receiver, type,
      channel, description, location
    - Customer: ID, name, risk_rating
    - Merchant: ID, name, category, country, risk_level
    - Beneficiary: ID, name, country, is_new
    - Device: ID, type, geolocation, is_known_device
    - Documents: ID, type, summary, evidence_references

    Excluded (PII / metadata not needed for hypothesis generation):
    - Customer: email, phone, address, date_of_birth, account_open_date,
      occupation, nationality
    - Device: ip_address, os, browser
    - Documents: file_url, file_name, extracted_text, extracted_entities,
      extracted_transactions, processing_status, uploaded_at
    - behavioral_biometrics (entire object)
    - face_verification (entire object)

    Note: grounding checks (_available_evidence_values, _check_grounding_violation)
    read from the state object directly — NOT from the prompt text — so removing
    fields from the prompt does not affect post-processing.
    """
    case_input = state.case_input
    compact: dict = {"alert_reason": case_input.alert_reason}

    # Transactions: keep all fact fields for hypothesis reasoning
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
            **({"location": t.location} if t.location else {}),
        }
        for t in case_input.transactions
    ]

    # Customer: identity + risk rating only
    customer = case_input.customer_profile
    if customer:
        compact["customer"] = {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "risk_rating": customer.risk_rating,
        }

    # Merchant: identity + risk indicators
    merchant = case_input.merchant_info
    if merchant:
        compact["merchant"] = {
            "merchant_id": merchant.merchant_id,
            "name": merchant.name,
            "category": merchant.category,
            "country": merchant.country,
            "risk_level": merchant.risk_level.value if merchant.risk_level else None,
        }

    # Beneficiary: identity + risk indicators
    beneficiary = case_input.beneficiary_info
    if beneficiary:
        compact["beneficiary"] = {
            "beneficiary_id": beneficiary.beneficiary_id,
            "name": beneficiary.name,
            "country": beneficiary.country,
            "is_new": beneficiary.is_new,
        }

    # Device: investigative facts only (no browser/OS/IP)
    device = case_input.device_info
    if device:
        compact["device"] = {
            "device_id": device.device_id,
            "device_type": device.device_type,
            "geolocation": device.geolocation,
            "is_known_device": device.is_known_device,
        }

    # Documents: IDs and evidence references for traceability
    if case_input.supporting_documents:
        compact["supporting_documents"] = [
            {
                "document_id": d.document_id,
                "document_type": d.document_type,
                **({"summary": d.summary} if d.summary else {}),
                **({"evidence_references": d.evidence_references} if d.evidence_references else {}),
            }
            for d in case_input.supporting_documents
        ]

    return _json.dumps(compact, indent=2, default=str)


def _build_compact_context(state: InvestigationState) -> str:
    """Build a compact JSON summary of context intelligence for the Reasoning prompt.

    Preserves:
    - context_summary
    - key_indicators
    - risk_score
    - Anomalies: anomaly_id, anomaly_type, severity, description,
      related_transactions

    Excluded:
    - status (agent lifecycle, not prompt-relevant)
    - historical_baseline (already consumed by Context Agent to generate
      anomalies/indicators; raw baseline numbers add tokens without aiding
      hypothesis generation)
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


# ── Prompt construction ──────────────────────────────────────────────


from app.prompts.reasoning_prompts import build_reasoning_prompt

def _build_prompt(state: InvestigationState) -> str:
    """Build a Gemini prompt from the investigation state.

    Uses compact JSON summaries of case data and context intelligence
    to reduce prompt size while preserving all transaction IDs, evidence
    references, and risk indicators needed for grounded hypothesis
    generation.
    """
    case_json = _build_compact_case(state)
    context_json = _build_compact_context(state)

    return build_reasoning_prompt(case_json, context_json)


# ── Public API ────────────────────────────────────────────────────────


def reasoning_agent(state: InvestigationState) -> dict:
    """Execute the Reasoning Agent.

    Reads case data and context intelligence from *state*, constructs
    a prompt, calls Gemini via ``GeminiClient.generate()``, and wraps
    the validated ``Hypothesis`` in an ``InvestigationReasoning``.

    Args:
        state: The current investigation state (must contain
            ``case_input``; ``context_intelligence`` is strongly
            expected but handled defensively if absent).

    Returns:
        A dict containing ``investigation_reasoning`` — compatible
        with LangGraph node update conventions.
    """
    prompt = _build_prompt(state)

    client = get_reasoning_client()

    try:
        response = _get_hypotheses(client, prompt)
        violation = _check_grounding_violation(response.hypotheses, state)
        if violation:
            raise GroundingViolationError(violation)
    except Exception as exc:
        if not (_is_malformed_structured_output(exc) or isinstance(exc, GroundingViolationError)):
            logger.exception("Gemini call failed in reasoning_agent")
            raise

        logger.warning("Malformed or ungrounded Gemini reasoning response; retrying once")
        from app.prompts.reasoning_prompts import build_reasoning_retry_prompt, build_grounding_retry_prompt
        
        if isinstance(exc, GroundingViolationError):
            retry_prompt = build_grounding_retry_prompt(prompt, str(exc))
        else:
            retry_prompt = build_reasoning_retry_prompt(prompt)
            
        try:
            response = _get_hypotheses(client, retry_prompt)
            violation = _check_grounding_violation(response.hypotheses, state)
            if violation:
                raise GroundingViolationError(violation)
        except Exception as retry_exc:
            if not (_is_malformed_structured_output(retry_exc) or isinstance(retry_exc, GroundingViolationError)):
                logger.exception("Gemini retry failed in reasoning_agent")
                raise
            logger.warning("Gemini reasoning retry also returned malformed or ungrounded output")
            return {
                "investigation_reasoning": InvestigationReasoning(
                    status=AgentStatus.FAILED,
                    hypotheses=[],
                    reasoning_summary=(
                        "Unable to validate structured reasoning output after one retry; "
                        "no hypotheses were accepted."
                    ),
                    recommended_actions=[
                        "Request a structured reasoning response again",
                        "Review the available case evidence manually",
                    ],
                ),
            }

    hypotheses = _normalise_hypotheses(response.hypotheses, state)
    # Round 5: cross-reference existing compliance findings (if available).
    hypotheses = _apply_compliance_alignment(hypotheses, state)

    reasoning = InvestigationReasoning(
        status=AgentStatus.COMPLETED,
        hypotheses=hypotheses,
        reasoning_summary=(
            f"Generated {len(hypotheses)} competing hypotheses based on case data "
            f"and context intelligence analysis."
        ),
        recommended_actions=[
            "Review the competing hypotheses against available evidence",
            "Verify flagged transactions and entities",
        ],
    )

    return {
        "investigation_reasoning": reasoning,
    }
