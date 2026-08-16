"""Reasoning Agent — Gemini-powered hypothesis generation.

Takes ``case_input`` and ``context_intelligence`` from the current
``InvestigationState``, sends the investigation data to Gemini via
the existing ``GeminiClient``, and produces exactly ONE validated
``Hypothesis``.

Round 2: Single hypothesis generation.  Multiple / competing
hypotheses belong to a later round.
"""

import logging
import re
from json import JSONDecodeError

from pydantic import BaseModel, ValidationError

from app.schemas.investigation_state import (
    AgentStatus,
    Hypothesis,
    InvestigationReasoning,
    InvestigationState,
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
