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
Your task is to review the case data and context intelligence below, and formulate at least TWO genuinely competing, mutually exclusive investigation hypotheses explaining the activity.

=== CASE DATA ===
{case_json}

=== CONTEXT INTELLIGENCE ===
{context_json}

=== INSTRUCTIONS ===
Produce a rigorous, objective analysis. Respond with a single JSON object (no markdown fences, no extra text) conforming EXACTLY to the schema below.

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

=== QUALITY RULES ===
1. BE SPECIFIC AND EVIDENCE-BASED: Avoid generic boilerplate like "The transaction is suspicious." Instead, explain *why* based on concrete facts (e.g., "The $48,500 wire transfer to CryptoVault Holdings aligns with capital flight typologies because it was initiated from a newly registered device in a high-risk jurisdiction (Romania).").
2. CONNECT THE DOTS: Logically link observed transactions, entities, and documents. Explain the relationship between the customer's profile, the transaction channel, and any detected anomalies.
3. COMPETING EXPLANATIONS: Provide at least TWO hypotheses representing materially different explanations (e.g., "Hypothesis 1: Account Takeover / Unauthorized Access" vs "Hypothesis 2: Authorized Customer engaging in high-risk crypto investment").
4. CITE ACTUAL EVIDENCE: "supporting_evidence" MUST reference concrete data points observed in the provided JSON (e.g., specific transaction IDs, document summaries, or contextual risk indicators).
5. HIGHLIGHT CONTRADICTIONS: "contradicting_evidence" MUST list plausible counter-arguments based on the case data (e.g., "Customer has a history of legitimate large wires to this region" or "Device IP matches the customer's known home address").
6. BE CAUTIOUS WITH INCOMPLETE DATA: If the case lacks documents or contextual corroboration, state explicitly in the description that the hypothesis is an investigative possibility requiring further verification, and assign a conservatively low confidence score.
7. NO HALLUCINATION: Do not invent facts, transactions, documents, names, amounts, or any external facts not present in the provided case data.
8. FORMATTING: Return ONLY the raw JSON object. No markdown blocks, no conversational text.
"""

def build_reasoning_retry_prompt(original_prompt: str) -> str:
    """Build the retry prompt for when the original response is malformed."""
    return original_prompt + """

=== RETRY INSTRUCTIONS ===
Your previous response could not be parsed as valid JSON matching the requested schema. 
Return ONLY the exact JSON object matching the requested HypothesesResponse schema. 
Every hypothesis must include all required fields with correctly typed values. 
Do not add unsupported evidence or certainty when evidence is unavailable. 
No markdown fences (```json), no extra text.
"""
