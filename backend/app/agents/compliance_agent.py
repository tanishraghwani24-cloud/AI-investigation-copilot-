"""Evidence & Compliance Validation agent.

Implements the ComplianceAgent class that validates evidence,
maps transactions to compliance regulations, and identifies
evidence gaps.  Uses the centralized GeminiClient for AI-powered
analysis with graceful fallback on errors.

Round 1: complete skeleton with prompt engineering, structured
parsing, and error handling.  No retries or hardening — those
belong to future rounds.
"""

import logging
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ComplianceMapping,
    EvidenceComplianceValidation,
    InvestigationState,
    SeverityLevel,
    SupportingDocument,
)
from app.services.gemini_client import GeminiClient, GeminiClientError

logger = logging.getLogger(__name__)


# ============================================================
# Gemini Response Schemas
# ============================================================


class _ComplianceMappingResponse(BaseModel):
    """Schema for a single compliance mapping in the Gemini response."""

    regulation_id: str = Field(..., description="e.g. AML-2023-04")
    regulation_name: str = Field(..., description="Human-readable regulation title")
    description: Optional[str] = Field(default=None)
    is_violated: bool = Field(default=False)
    severity: str = Field(default="LOW", description="LOW, MEDIUM, or HIGH")
    evidence_references: list[str] = Field(default_factory=list)


class _ComplianceAnalysisResponse(BaseModel):
    """Expected structure of Gemini's compliance analysis output."""

    compliance_mappings: list[_ComplianceMappingResponse] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    validation_summary: str = Field(
        default="", description="Narrative summary of the compliance analysis"
    )


# ============================================================
# Compliance Agent
# ============================================================


class ComplianceAgent:
    """Evidence & Compliance Validation agent.

    Validates evidence attached to a case, maps transactions and
    evidence to applicable compliance regulations, identifies
    evidence gaps, and produces an ``EvidenceComplianceValidation``
    output.

    Usage::

        from app.services import get_gemini_client

        agent = ComplianceAgent(gemini_client=get_gemini_client())
        result = agent.analyze(state)

    Args:
        gemini_client: A ``GeminiClient`` instance for AI-powered analysis.
    """

    def __init__(self, gemini_client: GeminiClient) -> None:
        self._gemini_client = gemini_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, state: InvestigationState) -> EvidenceComplianceValidation:
        """Run compliance analysis on the investigation state.

        Builds a structured prompt from the case data, sends it to
        Gemini for analysis, and parses the response into an
        ``EvidenceComplianceValidation``.  Falls back to a
        degraded response if the Gemini call fails.

        Args:
            state: The current investigation state.

        Returns:
            A fully populated ``EvidenceComplianceValidation``.
        """
        prompt = self._build_prompt(state)

        try:
            response = self._gemini_client.generate(
                prompt=prompt,
                response_schema=_ComplianceAnalysisResponse,
            )
            return self._parse_response(response)
        except GeminiClientError as exc:
            logger.warning(
                "Gemini compliance analysis failed, using fallback: %s", exc
            )
            return self._fallback_response(state)

    # ------------------------------------------------------------------
    # Prompt Construction
    # ------------------------------------------------------------------

    def _build_prompt(self, state: InvestigationState) -> str:
        """Construct a structured compliance analysis prompt.

        Assembles transaction details, customer profile, supporting
        documents, and any prior context intelligence into a prompt
        that instructs Gemini to perform compliance mapping and
        evidence gap analysis.
        """
        sections: list[str] = [
            "You are an Evidence & Compliance Validation agent for a financial "
            "investigation system. Analyze the following case data and produce "
            "a compliance assessment.\n",
        ]

        # -- Case metadata --
        sections.append(f"Case ID: {state.case_id}")

        # -- Transactions --
        sections.append(self._format_transactions(state.case_input))

        # -- Customer profile --
        sections.append(self._format_customer(state.case_input))

        # -- Supporting documents --
        sections.append(self._format_documents(state.case_input.supporting_documents))

        # -- Prior context (if available) --
        if state.context_intelligence is not None:
            sections.append(self._format_context(state))

        # -- Instructions --
        sections.append(
            "\n--- Instructions ---\n"
            "1. Identify all applicable compliance regulations.\n"
            "2. For each regulation, assess whether it is violated.\n"
            "3. Assign a severity: LOW, MEDIUM, or HIGH.\n"
            "4. List any evidence gaps (missing documentation or verification).\n"
            "5. Provide a validation summary.\n"
            "\nRespond with valid JSON matching this schema:\n"
            "{\n"
            '  "compliance_mappings": [\n'
            "    {\n"
            '      "regulation_id": "string",\n'
            '      "regulation_name": "string",\n'
            '      "description": "string or null",\n'
            '      "is_violated": true/false,\n'
            '      "severity": "LOW" | "MEDIUM" | "HIGH",\n'
            '      "evidence_references": ["string"]\n'
            "    }\n"
            "  ],\n"
            '  "evidence_gaps": ["string"],\n'
            '  "validation_summary": "string"\n'
            "}"
        )

        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Prompt Helpers
    # ------------------------------------------------------------------

    def _format_transactions(self, case_input: CaseInput) -> str:
        """Format transaction data for the prompt."""
        if not case_input.transactions:
            return "\n--- Transactions ---\nNo transactions provided."

        lines: list[str] = ["\n--- Transactions ---"]
        for txn in case_input.transactions:
            lines.append(
                f"- {txn.transaction_id}: {txn.transaction_type} "
                f"{txn.currency} {txn.amount:,.2f} "
                f"from {txn.sender_account} to {txn.receiver_account} "
                f"at {txn.timestamp.isoformat()}"
            )
            if txn.description:
                lines.append(f"  Description: {txn.description}")
            if txn.location:
                lines.append(f"  Location: {txn.location}")
        return "\n".join(lines)

    def _format_customer(self, case_input: CaseInput) -> str:
        """Format customer profile data for the prompt."""
        profile = case_input.customer_profile
        if profile is None:
            return "\n--- Customer Profile ---\nNo customer profile available."

        lines: list[str] = [
            "\n--- Customer Profile ---",
            f"Customer ID: {profile.customer_id}",
            f"Name: {profile.name}",
        ]
        if profile.risk_rating:
            lines.append(f"Risk Rating: {profile.risk_rating}")
        if profile.occupation:
            lines.append(f"Occupation: {profile.occupation}")
        if profile.nationality:
            lines.append(f"Nationality: {profile.nationality}")
        if profile.account_open_date:
            lines.append(f"Account Opened: {profile.account_open_date}")
        return "\n".join(lines)

    def _format_documents(self, documents: list[SupportingDocument]) -> str:
        """Format supporting document data for the prompt."""
        if not documents:
            return "\n--- Supporting Documents ---\nNo supporting documents attached."

        lines: list[str] = ["\n--- Supporting Documents ---"]
        for doc in documents:
            lines.append(
                f"- {doc.document_id} ({doc.document_type}): "
                f"{doc.file_name or 'unnamed'}"
            )
            if doc.summary:
                lines.append(f"  Summary: {doc.summary}")
            if doc.extracted_text:
                # Include a truncated preview to keep the prompt manageable
                preview = doc.extracted_text[:500]
                lines.append(f"  Extracted Text: {preview}")
            if doc.extracted_entities:
                lines.append(f"  Entities: {', '.join(doc.extracted_entities)}")
            lines.append(f"  Processing Status: {doc.processing_status.value}")
        return "\n".join(lines)

    def _format_context(self, state: InvestigationState) -> str:
        """Format prior context intelligence for the prompt."""
        ctx = state.context_intelligence
        if ctx is None:
            return ""

        lines: list[str] = ["\n--- Prior Context Intelligence ---"]
        if ctx.context_summary:
            lines.append(f"Summary: {ctx.context_summary}")
        if ctx.key_indicators:
            lines.append("Key Indicators:")
            for indicator in ctx.key_indicators:
                lines.append(f"  - {indicator}")
        if ctx.risk_score is not None:
            lines.append(f"Risk Score: {ctx.risk_score}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Response Parsing
    # ------------------------------------------------------------------

    def _parse_response(
        self, response: _ComplianceAnalysisResponse
    ) -> EvidenceComplianceValidation:
        """Convert the Gemini response into an EvidenceComplianceValidation."""
        compliance_mappings: list[ComplianceMapping] = []

        for mapping in response.compliance_mappings:
            severity = self._parse_severity(mapping.severity)
            compliance_mappings.append(
                ComplianceMapping(
                    regulation_id=mapping.regulation_id,
                    regulation_name=mapping.regulation_name,
                    description=mapping.description,
                    is_violated=mapping.is_violated,
                    severity=severity,
                    evidence_references=mapping.evidence_references,
                )
            )

        return EvidenceComplianceValidation(
            status=AgentStatus.COMPLETED,
            compliance_mappings=compliance_mappings,
            evidence_gaps=response.evidence_gaps,
            validation_summary=response.validation_summary or None,
        )

    def _parse_severity(self, severity_str: str) -> SeverityLevel:
        """Safely parse a severity string into a SeverityLevel enum.

        Returns ``SeverityLevel.MEDIUM`` if the string is not a valid
        severity value, to avoid crashing on unexpected Gemini output.
        """
        try:
            return SeverityLevel(severity_str.upper())
        except ValueError:
            logger.warning(
                "Unknown severity '%s', defaulting to MEDIUM", severity_str
            )
            return SeverityLevel.MEDIUM

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _fallback_response(
        self, state: InvestigationState
    ) -> EvidenceComplianceValidation:
        """Produce a degraded response when Gemini is unavailable.

        Performs basic rule-based evidence gap detection so the pipeline
        can continue without AI.  Does not attempt compliance mapping
        without the LLM.
        """
        evidence_gaps = self._detect_evidence_gaps(state.case_input)

        return EvidenceComplianceValidation(
            status=AgentStatus.COMPLETED,
            compliance_mappings=[],
            evidence_gaps=evidence_gaps,
            validation_summary=(
                "Automated compliance analysis was unavailable. "
                "Basic evidence gap detection was performed. "
                "Manual review is recommended."
            ),
        )

    def _detect_evidence_gaps(self, case_input: CaseInput) -> list[str]:
        """Rule-based evidence gap detection.

        Checks for common missing documentation that compliance
        regulations typically require.
        """
        gaps: list[str] = []

        # Check for missing customer profile
        if case_input.customer_profile is None:
            gaps.append("Customer profile not available for KYC verification")

        # Check for missing beneficiary info
        if case_input.beneficiary_info is None:
            gaps.append("Beneficiary information not provided")
        elif case_input.beneficiary_info.is_new:
            gaps.append(
                "First-time beneficiary — KYC verification documents required"
            )

        # Check for missing supporting documents
        if not case_input.supporting_documents:
            gaps.append("No supporting documents attached to the case")

        # Check for unprocessed documents
        for doc in case_input.supporting_documents:
            if doc.processing_status.value in ("PENDING", "FAILED"):
                gaps.append(
                    f"Document {doc.document_id} ({doc.document_type}) "
                    f"has not been successfully processed "
                    f"(status: {doc.processing_status.value})"
                )

        # Check for high-value transactions without source-of-funds
        for txn in case_input.transactions:
            if txn.amount > 10_000:
                has_sof_doc = any(
                    doc.document_type in ("SOURCE_OF_FUNDS", "BANK_STATEMENT")
                    for doc in case_input.supporting_documents
                )
                if not has_sof_doc:
                    gaps.append(
                        f"Transaction {txn.transaction_id} exceeds $10,000 — "
                        f"source-of-funds documentation not on file"
                    )
                break  # Only flag once for the entire case

        return gaps
