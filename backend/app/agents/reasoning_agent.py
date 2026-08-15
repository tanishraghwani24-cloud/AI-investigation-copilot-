"""Reasoning Agent — Gemini-powered hypothesis generation.

Takes ``case_input`` and ``context_intelligence`` from the current
``InvestigationState``, sends the investigation data to Gemini via
the existing ``GeminiClient``, and produces exactly ONE validated
``Hypothesis``.

Round 2: Single hypothesis generation.  Multiple / competing
hypotheses belong to a later round.
"""

import logging

from pydantic import BaseModel

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
        response: HypothesesResponse = client.generate(
            prompt,
            response_schema=HypothesesResponse,
        )
    except GeminiClientError:
        logger.exception("Gemini call failed in reasoning_agent")
        raise

    hypotheses = response.hypotheses

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
