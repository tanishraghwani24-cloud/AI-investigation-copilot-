"""Decision Agent — Gemini-powered decision option generation.

Takes ``case_input``, ``context_intelligence``, and
``investigation_reasoning`` from the current ``InvestigationState``,
sends the investigation data to Gemini via the existing
``GeminiClient``, and produces exactly FOUR validated
``DecisionOption`` objects — one for each ``DecisionAction``.

Round 3: Option generation only.
Recommendation selection (recommended_decision) belongs to Round 4.
"""

import logging

from pydantic import BaseModel

from app.schemas.investigation_state import (
    AgentStatus,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    InvestigationState,
)
from app.services.gemini_client import GeminiClientError, get_gemini_client

logger = logging.getLogger(__name__)


# ── Private response container ───────────────────────────────────────


class _DecisionOptionsResponse(BaseModel):
    """Container for Gemini structured output.

    This is a module-local helper used exclusively as the
    ``response_schema`` for ``GeminiClient.generate()``.  It is NOT
    part of the shared investigation schema.
    """

    options: list[DecisionOption]


# ── Prompt construction ──────────────────────────────────────────────


def _build_prompt(state: InvestigationState) -> str:
    """Build a Gemini prompt from the investigation state.

    Includes serialised case data, context intelligence, and
    investigation reasoning so the model can produce case-specific
    decision options.
    """
    case_json = state.case_input.model_dump_json(indent=2)

    if state.context_intelligence is not None:
        context_json = state.context_intelligence.model_dump_json(indent=2)
    else:
        context_json = "{}"

    if state.investigation_reasoning is not None:
        reasoning_json = state.investigation_reasoning.model_dump_json(indent=2)
    else:
        reasoning_json = "{}"

    prompt = f"""\
You are a senior financial crime decision analyst.  Given the
investigation data below, generate exactly FOUR decision options —
one for each possible action.

=== CASE DATA ===
{case_json}

=== CONTEXT INTELLIGENCE ===
{context_json}

=== INVESTIGATION REASONING ===
{reasoning_json}

=== INSTRUCTIONS ===
Respond with a single JSON object (no markdown fences, no extra text)
that conforms to the following schema:

{{
  "options": [
    {{
      "option_id": "<string – e.g. OPT-ALLOW>",
      "action": "<one of: ALLOW, HOLD, BLOCK, ESCALATE>",
      "rationale": "<string – case-specific explanation of why this action could be appropriate>",
      "confidence": <float between 0.0 and 1.0>,
      "risk_score": <float between 0.0 and 1.0>,
      "pros": ["<at least one advantage>"],
      "cons": ["<at least one disadvantage>"],
      "risks": ["<at least one named risk>"],
      "mitigation": ["<at least one mitigation step>"]
    }}
  ]
}}

Rules:
- You MUST produce exactly 4 options, one for each action: ALLOW, HOLD, BLOCK, ESCALATE.
- Each action value MUST appear exactly once.
- All rationales MUST reference specific data from the case, context, or reasoning above.
- pros, cons, risks, and mitigation MUST each have at least one entry.
- confidence and risk_score MUST be between 0.0 and 1.0 inclusive.
- Use option_id values: OPT-ALLOW, OPT-HOLD, OPT-BLOCK, OPT-ESCALATE.
- Return ONLY the raw JSON object.  No markdown, no commentary.
"""
    return prompt


# ── Validation ───────────────────────────────────────────────────────


_REQUIRED_ACTIONS = frozenset(DecisionAction)


def _validate_options(options: list[DecisionOption]) -> None:
    """Validate that Gemini returned exactly 4 distinct action options.

    Raises:
        GeminiClientError: If the count is wrong or actions are
            missing / duplicated.
    """
    if len(options) != 4:
        raise GeminiClientError(
            f"Expected exactly 4 decision options, got {len(options)}"
        )

    found_actions = {opt.action for opt in options}
    if found_actions != _REQUIRED_ACTIONS:
        missing = _REQUIRED_ACTIONS - found_actions
        extra = found_actions - _REQUIRED_ACTIONS
        raise GeminiClientError(
            f"Decision options have wrong actions. "
            f"Missing: {missing}, Extra/Duplicate: {extra}"
        )


# ── Public API ────────────────────────────────────────────────────────


def decision_agent(state: InvestigationState) -> dict:
    """Execute the Decision Agent.

    Reads case data, context intelligence, and investigation
    reasoning from *state*, constructs a prompt, calls Gemini via
    ``GeminiClient.generate()``, and wraps the validated
    ``DecisionOption`` objects in a ``DecisionOptimization``.

    Round 3 produces the four options only.
    ``recommended_decision`` and ``decision_rationale`` are not
    set — recommendation selection belongs to Round 4.

    Args:
        state: The current investigation state.

    Returns:
        A dict containing ``decision_optimization`` — compatible
        with LangGraph node update conventions.
    """
    prompt = _build_prompt(state)

    client = get_gemini_client()

    try:
        response: _DecisionOptionsResponse = client.generate(
            prompt,
            response_schema=_DecisionOptionsResponse,
        )
    except GeminiClientError:
        logger.exception("Gemini call failed in decision_agent")
        raise

    _validate_options(response.options)

    decision = DecisionOptimization(
        status=AgentStatus.COMPLETED,
        decision_options=response.options,
        # Round 3: option generation only.
        # recommended_decision and decision_rationale are NOT set.
        # Recommendation selection belongs to Round 4.
    )

    return {
        "decision_optimization": decision,
    }
