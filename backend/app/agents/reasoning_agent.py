"""Reasoning Agent — Gemini-powered hypothesis generation.

Takes ``case_input`` and ``context_intelligence`` from the current
``InvestigationState``, sends the investigation data to Gemini via
the existing ``GeminiClient``, and produces exactly ONE validated
``Hypothesis``.

Round 2: Single hypothesis generation.  Multiple / competing
hypotheses belong to a later round.
"""

import logging

from app.schemas.investigation_state import (
    AgentStatus,
    Hypothesis,
    InvestigationReasoning,
    InvestigationState,
)
from app.services.gemini_client import GeminiClientError, get_gemini_client

logger = logging.getLogger(__name__)


# ── Prompt construction ──────────────────────────────────────────────


def _build_prompt(state: InvestigationState) -> str:
    """Build a Gemini prompt from the investigation state.

    Includes serialised case data and context intelligence so the
    model can reason about the specific case rather than generating
    generic output.
    """
    # Serialise case input
    case_json = state.case_input.model_dump_json(indent=2)

    # Serialise context intelligence (may be None if context agent
    # has not run yet — unlikely in the normal pipeline, but we
    # handle it defensively)
    if state.context_intelligence is not None:
        context_json = state.context_intelligence.model_dump_json(indent=2)
    else:
        context_json = "{}"

    prompt = f"""\
You are a senior financial crime investigator.  Analyse the case data
and context intelligence below, then generate exactly ONE investigation
hypothesis.

=== CASE DATA ===
{case_json}

=== CONTEXT INTELLIGENCE ===
{context_json}

=== INSTRUCTIONS ===
Respond with a single JSON object (no markdown fences, no extra text)
that conforms to the following schema:

{{
  "hypothesis_id": "<string – unique identifier, e.g. HYP-001>",
  "title": "<string – short hypothesis label>",
  "description": "<string – detailed explanation of the hypothesis>",
  "confidence": <float between 0.0 and 1.0>,
  "supporting_evidence": ["<string>", ...],
  "contradicting_evidence": ["<string>", ...]
}}

Rules:
- The hypothesis MUST be specific to the case data provided above.
- supporting_evidence MUST reference real data points from the case.
- contradicting_evidence MUST list plausible counter-arguments.
- confidence MUST be between 0.0 and 1.0 inclusive.
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
        hypothesis: Hypothesis = client.generate(
            prompt,
            response_schema=Hypothesis,
        )
    except GeminiClientError:
        logger.exception("Gemini call failed in reasoning_agent")
        raise

    reasoning = InvestigationReasoning(
        status=AgentStatus.COMPLETED,
        hypotheses=[hypothesis],
        reasoning_summary=(
            f"Generated hypothesis '{hypothesis.title}' with "
            f"{hypothesis.confidence:.0%} confidence based on case data "
            f"and context intelligence analysis."
        ),
        recommended_actions=[
            "Review the hypothesis against available evidence",
            "Verify flagged transactions and entities",
        ],
    )

    return {
        "investigation_reasoning": reasoning,
    }
