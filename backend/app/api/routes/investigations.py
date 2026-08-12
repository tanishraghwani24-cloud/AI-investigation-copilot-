"""Investigation API routes.

Provides the POST /api/investigations endpoint that returns a hardcoded
InvestigationState for Round 1.  No AI, no database, no generation logic.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    BehavioralBiometrics,
    BeneficiaryInfo,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CurrentStage,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    DetectedAnomaly,
    DeviceInfo,
    EvidenceComplianceValidation,
    FaceVerificationResult,
    GraphData,
    GraphEdge,
    GraphNode,
    Hypothesis,
    InvestigationReasoning,
    InvestigationReport,
    InvestigationState,
    MerchantInfo,
    CustomerProfile,
    ProcessingStatus,
    ReportGraphs,
    SeverityLevel,
    SupportingDocument,
    TimelineEvent,
    Transaction,
)

router = APIRouter()

# ── Static timestamps used across the mock data ──────────────────────
_T0 = datetime(2025, 7, 15, 9, 30, 0, tzinfo=timezone.utc)
_T1 = datetime(2025, 7, 15, 10, 0, 0, tzinfo=timezone.utc)
_T2 = datetime(2025, 7, 15, 10, 15, 0, tzinfo=timezone.utc)
_T3 = datetime(2025, 7, 15, 10, 45, 0, tzinfo=timezone.utc)
_T4 = datetime(2025, 7, 15, 11, 0, 0, tzinfo=timezone.utc)
_T5 = datetime(2025, 7, 15, 11, 30, 0, tzinfo=timezone.utc)
_CREATED = datetime(2025, 7, 15, 12, 0, 0, tzinfo=timezone.utc)

# ── Hardcoded InvestigationState ─────────────────────────────────────
_MOCK_STATE = InvestigationState(
    case_id="CASE-2025-00042",
    case_input=CaseInput(
        transactions=[
            Transaction(
                transaction_id="TXN-90001",
                amount=14_500.00,
                currency="USD",
                timestamp=_T0,
                sender_account="ACCT-100200",
                receiver_account="ACCT-300400",
                transaction_type="WIRE",
                channel="ONLINE",
                description="Invoice payment – Oceanic Trading Ltd",
                location="New York, US",
            ),
            Transaction(
                transaction_id="TXN-90002",
                amount=3_200.00,
                currency="USD",
                timestamp=_T1,
                sender_account="ACCT-100200",
                receiver_account="ACCT-500600",
                transaction_type="ACH",
                channel="ONLINE",
                description="Supplier advance – QuickParts Inc",
                location="New York, US",
            ),
        ],
        customer_profile=CustomerProfile(
            customer_id="CUST-7890",
            name="Elena Vasquez",
            email="elena.vasquez@example.com",
            phone="+1-555-012-3456",
            address="742 Evergreen Terrace, New York, NY 10001",
            date_of_birth="1985-03-22",
            account_open_date="2019-06-10",
            risk_rating="MEDIUM",
            occupation="Import/Export Consultant",
            nationality="US",
        ),
        merchant_info=MerchantInfo(
            merchant_id="MERCH-4010",
            name="Oceanic Trading Ltd",
            category="5099 – Durable Goods",
            country="US",
            risk_level=SeverityLevel.MEDIUM,
            registered_date="2017-11-03",
        ),
        device_info=DeviceInfo(
            device_id="DEV-ABC123",
            device_type="DESKTOP",
            ip_address="203.0.113.42",
            geolocation="40.7128,-74.0060",
            is_known_device=True,
            os="Windows 11",
            browser="Chrome 126",
        ),
        beneficiary_info=BeneficiaryInfo(
            beneficiary_id="BEN-5001",
            name="Oceanic Trading Ltd",
            account_number="ACCT-300400",
            bank_name="Global Commerce Bank",
            country="US",
            is_new=False,
            relationship="Supplier",
        ),
        behavioral_biometrics=BehavioralBiometrics(
            typing_speed=72.0,
            mouse_dynamics="NORMAL",
            session_duration_seconds=480,
            anomaly_score=0.15,
        ),
        face_verification=FaceVerificationResult(
            is_verified=True,
            confidence_score=0.97,
            method="LIVENESS",
            timestamp=_T0,
        ),
        supporting_documents=[
            SupportingDocument(
                document_id="DOC-001",
                document_type="INVOICE",
                file_name="oceanic_invoice_2025.pdf",
                file_url="https://docs.example.com/oceanic_invoice_2025.pdf",
                uploaded_at=_T0,
                summary="Commercial invoice from Oceanic Trading Ltd for durable goods shipment.",
                extracted_text="Invoice #INV-2025-1147 dated 2025-07-14 for USD 14,500.00.",
                extracted_entities=["Oceanic Trading Ltd", "Elena Vasquez"],
                extracted_transactions=["TXN-90001"],
                evidence_references=["EVID-001"],
                processing_status=ProcessingStatus.SUMMARIZED,
            ),
        ],
        alert_reason="Wire transfer of USD 14,500 to a medium-risk merchant flagged by rule engine.",
    ),
    # ── Agent outputs (placeholder/static for Round 1) ───────────
    context_intelligence=ContextIntelligence(
        status=AgentStatus.NOT_STARTED,
        context_summary="Placeholder — Context Agent has not run yet.",
        key_indicators=[
            "Two outgoing transfers within 30 minutes",
            "Medium-risk merchant recipient",
        ],
        anomalies=[
            DetectedAnomaly(
                anomaly_id="ANOM-001",
                anomaly_type=AnomalyType.BEHAVIORAL,
                severity=SeverityLevel.MEDIUM,
                description="Two rapid outgoing transfers totalling USD 17,700 within 30 minutes.",
                related_transactions=["TXN-90001", "TXN-90002"],
            ),
        ],
        risk_score=0.55,
    ),
    investigation_reasoning=InvestigationReasoning(
        status=AgentStatus.NOT_STARTED,
        hypotheses=[
            Hypothesis(
                hypothesis_id="HYP-001",
                title="Legitimate trade payments",
                description="Transactions are routine supplier payments consistent with the customer's import/export business.",
                confidence=0.65,
                supporting_evidence=["DOC-001"],
                contradicting_evidence=[],
            ),
            Hypothesis(
                hypothesis_id="HYP-002",
                title="Structuring attempt",
                description="Splitting a larger payment into two transfers to avoid reporting thresholds.",
                confidence=0.30,
                supporting_evidence=["ANOM-001"],
                contradicting_evidence=["DOC-001"],
            ),
        ],
        reasoning_summary="Placeholder — Reasoning Agent has not run yet.",
        recommended_actions=["Review supplier invoices", "Verify beneficiary history"],
    ),
    evidence_compliance_validation=EvidenceComplianceValidation(
        status=AgentStatus.NOT_STARTED,
        compliance_mappings=[
            ComplianceMapping(
                regulation_id="AML-2023-04",
                regulation_name="Anti-Money Laundering – Wire Transfer Rule",
                description="Requires enhanced due diligence for wire transfers exceeding USD 10,000.",
                is_violated=False,
                severity=SeverityLevel.MEDIUM,
                evidence_references=["EVID-001"],
            ),
        ],
        evidence_gaps=["Beneficiary KYC documentation not on file"],
        validation_summary="Placeholder — Compliance Agent has not run yet.",
    ),
    decision_optimization=DecisionOptimization(
        status=AgentStatus.NOT_STARTED,
        decision_options=[
            DecisionOption(
                option_id="OPT-001",
                action=DecisionAction.HOLD,
                rationale="Hold pending additional beneficiary verification.",
                confidence=0.60,
                risk_score=0.45,
                pros=["Prevents potential loss", "Allows time for verification"],
                cons=["May delay legitimate business"],
                risks=["Customer dissatisfaction"],
                mitigation=["Expedite KYC review within 24 hours"],
            ),
            DecisionOption(
                option_id="OPT-002",
                action=DecisionAction.ALLOW,
                rationale="Invoice documentation supports legitimate trade activity.",
                confidence=0.35,
                risk_score=0.30,
                pros=["Maintains customer relationship"],
                cons=["Residual structuring risk"],
                risks=["Regulatory exposure if structuring confirmed"],
                mitigation=["Flag for post-transaction monitoring"],
            ),
        ],
        recommended_decision=DecisionAction.HOLD,
        decision_rationale="Placeholder — Decision Agent has not run yet.",
    ),
    investigation_report=InvestigationReport(
        status=AgentStatus.NOT_STARTED,
        executive_summary="Placeholder — Reporting Agent has not run yet.",
        detailed_narrative="Placeholder — full narrative will be generated by the Reporting Agent.",
        graphs=ReportGraphs(
            entity_relationship_graph=GraphData(
                nodes=[
                    GraphNode(
                        node_id="N1",
                        label="Elena Vasquez",
                        node_type="PERSON",
                        metadata={"customer_id": "CUST-7890"},
                    ),
                    GraphNode(
                        node_id="N2",
                        label="Oceanic Trading Ltd",
                        node_type="MERCHANT",
                        metadata={"merchant_id": "MERCH-4010"},
                    ),
                    GraphNode(
                        node_id="N3",
                        label="ACCT-100200",
                        node_type="ACCOUNT",
                        metadata={"owner": "CUST-7890"},
                    ),
                ],
                edges=[
                    GraphEdge(source="N1", target="N3", relationship="OWNS", weight=1.0),
                    GraphEdge(source="N3", target="N2", relationship="SENT_TO", weight=0.8),
                ],
            ),
            investigation_timeline=[
                TimelineEvent(
                    timestamp=_T0,
                    event_name="Wire transfer initiated",
                    stage=CurrentStage.INTAKE,
                ),
                TimelineEvent(
                    timestamp=_T1,
                    event_name="ACH transfer initiated",
                    stage=CurrentStage.INTAKE,
                ),
                TimelineEvent(
                    timestamp=_CREATED,
                    event_name="Case created",
                    stage=CurrentStage.INTAKE,
                ),
            ],
        ),
        generated_at=_CREATED,
    ),
    current_stage=CurrentStage.INTAKE,
    created_at=_CREATED,
    updated_at=_CREATED,
    errors=[],
)


@router.post("/investigations", response_model=InvestigationState)
async def create_investigation() -> InvestigationState:
    """Create a new investigation case.

    Round 1: returns a hardcoded, fully populated InvestigationState.
    No AI processing, no database, no persistence.
    """
    return _MOCK_STATE
