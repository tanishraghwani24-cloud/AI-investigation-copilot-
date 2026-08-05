"""Evidence & Compliance Validation node.

Produces a realistic dummy EvidenceComplianceValidation object.
No AI or external API calls — all values are hardcoded.
"""

from typing import Any

from app.schemas.investigation_state import (
    AgentStatus,
    ComplianceMapping,
    CurrentStage,
    EvidenceComplianceValidation,
    SeverityLevel,
)


def compliance_node(state: Any) -> dict:
    """Execute the Evidence & Compliance Validation step.

    Returns a fully populated EvidenceComplianceValidation with realistic
    dummy compliance mappings and advances the stage to COMPLIANCE.
    """
    compliance_mappings = [
        ComplianceMapping(
            regulation_id="AML-2023-04",
            regulation_name="AML Enhanced Due Diligence",
            description=(
                "Transactions exceeding $10,000 involving high-risk jurisdictions "
                "require enhanced due diligence, including verification of the "
                "source of funds and the purpose of the transaction."
            ),
            is_violated=True,
            severity=SeverityLevel.HIGH,
            evidence_references=[
                "TXN-2025-0819-00347",
                "MERCH-KY-7741",
                "BEN-KY-3319",
            ],
        ),
        ComplianceMapping(
            regulation_id="KYC-2022-11",
            regulation_name="KYC Beneficiary Verification",
            description=(
                "First-time beneficiaries receiving transfers above the reporting "
                "threshold must be verified against sanctions lists and adverse "
                "media databases before the transaction is released."
            ),
            is_violated=True,
            severity=SeverityLevel.MEDIUM,
            evidence_references=[
                "BEN-KY-3319",
            ],
        ),
    ]

    validation = EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=compliance_mappings,
        evidence_gaps=[
            "Beneficiary identity verification pending — no KYC documents on file",
            "Source-of-funds declaration not yet obtained from the customer",
        ],
        validation_summary=(
            "Two compliance violations identified. AML enhanced due diligence has "
            "not been performed for this high-value cross-border transfer to a "
            "high-risk jurisdiction. The first-time beneficiary has not been "
            "screened against sanctions and adverse-media databases. Evidence gaps "
            "remain in beneficiary verification and source-of-funds documentation."
        ),
    )

    return {
        "evidence_compliance_validation": validation,
        "current_stage": CurrentStage.COMPLIANCE,
    }
