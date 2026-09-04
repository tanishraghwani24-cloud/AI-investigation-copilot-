"""Reasoning Agent Prompts.

Contains the prompt templates and builders for the Gemini-powered
Reasoning Agent. Extracted for quality tuning in Round 7.
"""

def build_reasoning_prompt(case_json: str, context_json: str) -> str:
    """Build the prompt for generating investigation hypotheses.
    
    Instructs the LLM to act as a senior financial crime investigator
    and produce specific, evidence-grounded, coherent hypotheses.
    """
    return f"""\
You are a senior financial crime investigator analysing a potential risk event.
Your task is to review the case data and context intelligence below, and formulate EXACTLY TWO genuinely competing, mutually exclusive investigation hypotheses explaining the activity.

=== CASE DATA ===
{case_json}

=== CONTEXT INTELLIGENCE ===
{context_json}

=== INSTRUCTIONS ===
Produce a rigorous, objective analysis. Respond with a single JSON object (no markdown fences, no extra text) conforming EXACTLY to the schema below.

Answer directly from the facts supplied above — they are already extracted and need no further derivation. Do not deliberate at length before writing; keep each "description" under 80 words and each evidence list to at most 3 short entries.

{{
  "hypotheses": [
    {{
      "hypothesis_id": "<string – unique identifier, e.g. HYP-001>",
      "title": "<string – short, specific hypothesis label>",
      "description": "<string – detailed explanation of the hypothesis>",
      "confidence": <float between 0.0 and 1.0>,
      "supporting_evidence": ["<string>", ...],
      "contradicting_evidence": ["<string>", ...]
    }},
    ...
  ]
}}

=== STRICT GROUNDING AND ANTI-HALLUCINATION RULES ===
CRITICAL: You may ONLY use facts present in the supplied case data and context intelligence.
1. USE PROVIDED FACTS: Every hypothesis must explicitly reference at least one concrete fact from the supplied case, preferably the transaction amount, baseline amount, transaction ID, sender account, or receiver account. Never replace concrete supplied facts with vague phrases such as 'high amount', 'unusual transaction', or 'the account'.
2. DO NOT INVENT FACTS: Only use facts explicitly present in the supplied case. Do not infer, assume, or assert any unavailable information. The supplied data is exhaustive; if a detail is not provided, do not invent one to fill the gap.
3. DO NOT MENTION UNAVAILABLE DATA: When a data type is not supplied, do not mention that data type at all, even to say that it is missing, absent, unavailable, lacking, or not provided. Reason only from supplied facts. Do not mention or reason from any unavailable data category.
4. MISSING DATA IS UNKNOWN: Missing information must be explicitly treated as UNKNOWN or NOT PROVIDED. Do not assume or fabricate details.
5. LABEL HYPOTHESES PROPERLY: A hypothesis may propose a possible explanation, but the explanation must clearly be labelled as a hypothesis (e.g., "It is possible that...") and must NOT present invented facts as evidence.
6. STRICT SUPPORTING EVIDENCE: "supporting_evidence" must contain ONLY evidence identifiers and facts that actually exist in the supplied input.
7. STRICT CONTRADICTING EVIDENCE: "contradicting_evidence" must contain ONLY evidence that actually exists in the supplied input. Do not invent counter-arguments based on fabricated data.
8. INSUFFICIENT EVIDENCE PROTOCOL: If there is insufficient evidence, you MUST explicitly state in the description that evidence is limited and recommend what should be verified next.
9. CONSERVATIVE CONFIDENCE: Confidence scores must remain conservative (e.g., 0.1 to 0.4) when evidence is sparse.
10. COMPETING EXPLANATIONS: You must provide EXACTLY TWO hypotheses representing materially different explanations (e.g., "Account Takeover" vs "Authorized unusual activity").
11. FORMATTING: Return ONLY the raw JSON object. No markdown blocks, no conversational text.
"""

def build_reasoning_retry_prompt(original_prompt: str) -> str:
    """Build the retry prompt for when the original response is malformed."""
    return original_prompt + """

=== RETRY INSTRUCTIONS ===
Your previous response could not be parsed as valid JSON matching the requested schema. 
Return ONLY the exact JSON object matching the requested HypothesesResponse schema. 
Every hypothesis must include all required fields with correctly typed values. 
CRITICAL: Do not invent ANY facts. Use ONLY provided evidence. Do not add unsupported evidence or certainty when evidence is unavailable. 
No markdown fences (```json), no extra text.
"""

def build_grounding_retry_prompt(original_prompt: str, violation_msg: str) -> str:
    """Build the retry prompt for when the original response violates grounding rules."""
    return original_prompt + f"""

=== RETRY INSTRUCTIONS ===
Your previous response violated grounding rules. 
{violation_msg}

Rewrite the hypotheses using ONLY concrete supplied facts and do not mention unavailable data. 
Ensure you still output a valid JSON matching the requested HypothesesResponse schema.
No markdown fences, no extra text.
"""
