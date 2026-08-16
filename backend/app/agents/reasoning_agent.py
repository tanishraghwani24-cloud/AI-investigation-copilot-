"""Reasoning Agent — Gemini-powered hypothesis generation.

Takes ``case_input`` and ``context_intelligence`` from the current
``InvestigationState``, sends the investigation data to Gemini via
the existing ``GeminiClient``, and produces exactly ONE validated
``Hypothesis``.

Round 2: Single hypothesis generation.  Multiple / competing
hypotheses belong to a later round.

Round 5: When ``evidence_compliance_validation`` is already present in the
state, the agent cross-references compliance findings with each hypothesis.
If a compliance finding directly contradicts a hypothesis (shared evidence
reference + flagged concern), confidence is reduced and the contradiction
is explicitly acknowledged in the hypothesis description.
"""

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
from app.services.gemini_client import GeminiClientError, get_gemini_client

logger = logging.getLogger(__name__)


# ── Response Schema ──────────────────────────────────────────────────


class HypothesesResponse(BaseModel):
    """Schema for Gemini to return multiple hypotheses."""
    hypotheses: list[Hypothesis]


_EVIDENCE_ID_PATTERN = re.compile(r"\b(?:TXN|DOC|CUST|ACC|ANOM)-[A-Z0-9-]+\b")
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


# ── Prompt construction ──────────────────────────────────────────────


def _build_prompt(state: InvestigationState) -> str:
    """Build a Gemini prompt from the investigation state.

    Includes serialised case data and context intelligence so the
    model can reason about the specific case rather than generating
    generic output. Instructs the model to generate at least TWO
    competing hypotheses based on the provided evidence.
    """
    # Serialise case input
    case_json = state.case_input.model_dump_json(indent=2)

    # Serialise context intelligence
    if state.context_intelligence is not None:
        context_json = state.context_intelligence.model_dump_json(indent=2)
    else:
        context_json = "{}"

    prompt = f"""\
You are a senior financial crime investigator.  Analyse the case data
and context intelligence below, then generate at least TWO genuinely competing
investigation hypotheses.

=== CASE DATA ===
{case_json}

=== CONTEXT INTELLIGENCE ===
{context_json}

=== INSTRUCTIONS ===
Respond with a single JSON object (no markdown fences, no extra text)
that conforms to the following schema:

{{
  "hypotheses": [
    {{
      "hypothesis_id": "<string – unique identifier, e.g. HYP-001>",
      "title": "<string – short hypothesis label>",
      "description": "<string – detailed explanation of the hypothesis>",
      "confidence": <float between 0.0 and 1.0>,
      "supporting_evidence": ["<string>", ...],
      "contradicting_evidence": ["<string>", ...]
    }},
    ...
  ]
}}

Rules:
- The hypotheses MUST be specific to the case data and context intelligence provided above.
- You MUST produce at least TWO hypotheses that represent materially different explanations.
- supporting_evidence MUST reference real data points from the case.
- contradicting_evidence MUST list plausible counter-arguments based on the case data.
- Do not invent facts, transactions, documents, names, amounts, or any external facts.
- Distinguish evidence from assumptions and explicitly acknowledge missing evidence if applicable.
- confidence MUST be between 0.0 and 1.0 inclusive, based on evidence strength.
- If documents or context are unavailable, leave evidence lists empty unless a
  case-data reference exists, use conservative confidence, and state that the
  hypothesis is only an investigative possibility.
- Return ONLY the raw JSON object.  No markdown, no commentary.
"""
    return prompt


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

    client = get_gemini_client()

    try:
        response = _get_hypotheses(client, prompt)
    except Exception as exc:
        if not _is_malformed_structured_output(exc):
            logger.exception("Gemini call failed in reasoning_agent")
            raise

        logger.warning("Malformed Gemini reasoning response; retrying once")
        retry_prompt = prompt + """

Your previous response could not be validated. Return only the exact JSON
object matching the requested HypothesesResponse schema. Every hypothesis
must include all required fields with correctly typed values. Do not add
unsupported evidence or certainty when evidence is unavailable.
"""
        try:
            response = _get_hypotheses(client, retry_prompt)
        except Exception as retry_exc:
            if not _is_malformed_structured_output(retry_exc):
                logger.exception("Gemini retry failed in reasoning_agent")
                raise
            logger.warning("Gemini reasoning retry also returned malformed output")
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
