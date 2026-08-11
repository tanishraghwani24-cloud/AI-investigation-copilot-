"""Shared Investigation State schema.

Defines the Pydantic models and enums that form the single shared state
object every LangGraph node will later read from and write to.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# Enums
# ============================================================


class AgentStatus(str, Enum):
    """Processing status of an individual agent."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnomalyType(str, Enum):
    """Category of a detected anomaly."""

    POINT = "POINT"
    BEHAVIORAL = "BEHAVIORAL"
    CONTEXTUAL = "CONTEXTUAL"
    NETWORK = "NETWORK"
    MERCHANT = "MERCHANT"
    SEASONAL = "SEASONAL"


class SeverityLevel(str, Enum):
    """Severity rating for anomalies and compliance findings."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DecisionAction(str, Enum):
    """Possible resolution actions for a case."""

    ALLOW = "ALLOW"
    HOLD = "HOLD"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class CurrentStage(str, Enum):
    """Pipeline stage the investigation is currently in."""

    INTAKE = "INTAKE"
    CONTEXT = "CONTEXT"
    REASONING = "REASONING"
    COMPLIANCE = "COMPLIANCE"
    DECISION = "DECISION"
    REPORTING = "REPORTING"
    DONE = "DONE"


class ProcessingStatus(str, Enum):
    """Lifecycle status of a supporting document's processing."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    SUMMARIZED = "SUMMARIZED"
    FAILED = "FAILED"


# ============================================================
# Reusable Domain Models
# ============================================================


class Transaction(BaseModel):
    """A single financial transaction under investigation."""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    timestamp: datetime = Field(..., description="When the transaction occurred")
    sender_account: str = Field(..., description="Source account identifier")
    receiver_account: str = Field(..., description="Destination account identifier")
    transaction_type: str = Field(..., description="e.g. WIRE, ACH, P2P, CARD")
    channel: str = Field(default="ONLINE", description="e.g. ONLINE, ATM, BRANCH")
    description: Optional[str] = Field(default=None, description="Free-text memo")
    location: Optional[str] = Field(default=None, description="Originating location")


class CustomerProfile(BaseModel):
    """Profile of the customer associated with the case."""

    customer_id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., description="Full legal name")
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    date_of_birth: Optional[str] = Field(default=None)
    account_open_date: Optional[str] = Field(default=None)
    risk_rating: Optional[str] = Field(default=None, description="e.g. LOW, MEDIUM, HIGH")
    occupation: Optional[str] = Field(default=None)
    nationality: Optional[str] = Field(default=None)


class MerchantInfo(BaseModel):
    """Details about the merchant involved in the transaction."""

    merchant_id: str = Field(..., description="Unique merchant identifier")
    name: str = Field(..., description="Merchant business name")
    category: str = Field(..., description="MCC or business category")
    country: Optional[str] = Field(default=None)
    risk_level: Optional[SeverityLevel] = Field(default=None)
    registered_date: Optional[str] = Field(default=None)


class DeviceInfo(BaseModel):
    """Device and session metadata captured during the transaction."""

    device_id: Optional[str] = Field(default=None)
    device_type: Optional[str] = Field(default=None, description="e.g. MOBILE, DESKTOP")
    ip_address: Optional[str] = Field(default=None)
    geolocation: Optional[str] = Field(default=None)
    is_known_device: bool = Field(default=False)
    os: Optional[str] = Field(default=None)
    browser: Optional[str] = Field(default=None)


class BeneficiaryInfo(BaseModel):
    """Information about the payment beneficiary."""

    beneficiary_id: str = Field(..., description="Unique beneficiary identifier")
    name: str = Field(..., description="Beneficiary name")
    account_number: str = Field(..., description="Destination account")
    bank_name: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)
    is_new: bool = Field(default=False, description="First-time beneficiary flag")
    relationship: Optional[str] = Field(default=None, description="Stated relationship")


class BehavioralBiometrics(BaseModel):
    """Behavioral biometric signals captured during the session."""

    typing_speed: Optional[float] = Field(default=None, description="Keys per minute")
    mouse_dynamics: Optional[str] = Field(default=None, description="Movement pattern summary")
    session_duration_seconds: Optional[int] = Field(default=None)
    anomaly_score: Optional[float] = Field(
        default=None, description="0.0 – 1.0 deviation score"
    )


class FaceVerificationResult(BaseModel):
    """Outcome of facial verification during the session."""

    is_verified: bool = Field(default=False)
    confidence_score: Optional[float] = Field(
        default=None, description="0.0 – 1.0 match confidence"
    )
    method: Optional[str] = Field(default=None, description="e.g. LIVENESS, PHOTO_MATCH")
    timestamp: Optional[datetime] = Field(default=None)


class SupportingDocument(BaseModel):
    """A document attached as evidence to the case."""

    document_id: str = Field(..., description="Unique document identifier")
    document_type: str = Field(..., description="e.g. ID_SCAN, BANK_STATEMENT, INVOICE")
    file_name: Optional[str] = Field(default=None)
    file_url: Optional[str] = Field(default=None)
    uploaded_at: Optional[datetime] = Field(default=None)
    summary: Optional[str] = Field(default=None, description="Extracted or AI-generated summary")
    extracted_text: Optional[str] = Field(
        default=None,
        description="Raw text extracted from the document, via direct extraction or OCR",
    )
    extracted_entities: list[str] = Field(
        default_factory=list,
        description="Named entities identified in the document (people, accounts, organizations, etc.)",
    )
    extracted_transactions: list[str] = Field(
        default_factory=list,
        description="References to transactions identified within the document content",
    )
    evidence_references: list[str] = Field(
        default_factory=list,
        description="IDs linking this document's content to specific evidence used elsewhere in the investigation",
    )
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Current stage of this document's processing pipeline",
    )


class ComplianceMapping(BaseModel):
    """A single compliance regulation mapped to the case."""

    regulation_id: str = Field(..., description="e.g. AML-2023-04")
    regulation_name: str = Field(..., description="Human-readable regulation title")
    description: Optional[str] = Field(default=None)
    is_violated: bool = Field(default=False)
    severity: SeverityLevel = Field(default=SeverityLevel.LOW)
    evidence_references: list[str] = Field(
        default_factory=list, description="IDs of supporting evidence"
    )


class Hypothesis(BaseModel):
    """An investigation hypothesis generated by the reasoning agent."""

    hypothesis_id: str = Field(..., description="Unique hypothesis identifier")
    title: str = Field(..., description="Short hypothesis label")
    description: str = Field(..., description="Detailed explanation")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Agent confidence score"
    )
    supporting_evidence: list[str] = Field(
        default_factory=list, description="IDs of supporting evidence"
    )
    contradicting_evidence: list[str] = Field(
        default_factory=list, description="IDs of contradicting evidence"
    )


class DetectedAnomaly(BaseModel):
    """An anomaly detected during analysis."""

    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    anomaly_type: AnomalyType = Field(...)
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    description: str = Field(..., description="What was detected")
    related_transactions: list[str] = Field(
        default_factory=list, description="Transaction IDs involved"
    )


class DecisionOption(BaseModel):
    """A possible resolution option with rationale."""

    option_id: str = Field(..., description="Unique option identifier")
    action: DecisionAction = Field(...)
    rationale: str = Field(..., description="Why this action is recommended")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Agent confidence score"
    )
    risk_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Associated risk level"
    )
    pros: list[str] = Field(
        default_factory=list,
        description="Advantages of choosing this action",
    )
    cons: list[str] = Field(
        default_factory=list,
        description="Drawbacks of choosing this action",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Specific named risks of this action — distinct from risk_score, which is a single 0-1 magnitude",
    )
    mitigation: list[str] = Field(
        default_factory=list,
        description="Steps that reduce the listed risks",
    )


class GraphNode(BaseModel):
    """A node in the investigation relationship graph."""

    node_id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label")
    node_type: str = Field(..., description="e.g. ACCOUNT, PERSON, MERCHANT")
    metadata: dict[str, str] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An edge connecting two nodes in the investigation graph."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relationship: str = Field(..., description="e.g. SENT_TO, OWNED_BY")
    weight: Optional[float] = Field(default=None)


class GraphData(BaseModel):
    """Full graph structure for visualization."""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class AgentError(BaseModel):
    """An error recorded during agent execution."""

    agent_name: str = Field(..., description="Name of the agent that failed")
    error_type: str = Field(..., description="Exception class name")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# Higher-Level Agent Output Models
# ============================================================


class CaseInput(BaseModel):
    """Raw inputs that initiate an investigation case."""

    transactions: list[Transaction] = Field(
        default_factory=list, description="Flagged transactions"
    )
    customer_profile: Optional[CustomerProfile] = Field(default=None)
    merchant_info: Optional[MerchantInfo] = Field(default=None)
    device_info: Optional[DeviceInfo] = Field(default=None)
    beneficiary_info: Optional[BeneficiaryInfo] = Field(default=None)
    behavioral_biometrics: Optional[BehavioralBiometrics] = Field(default=None)
    face_verification: Optional[FaceVerificationResult] = Field(default=None)
    supporting_documents: list[SupportingDocument] = Field(default_factory=list)
    alert_reason: Optional[str] = Field(
        default=None, description="Why this case was flagged"
    )


class ContextIntelligence(BaseModel):
    """Output of the Context & Evidence Intelligence agent."""

    status: AgentStatus = Field(default=AgentStatus.NOT_STARTED)
    context_summary: Optional[str] = Field(
        default=None, description="AI-generated summary of the investigation context"
    )
    key_indicators: list[str] = Field(
        default_factory=list, description="Important signals extracted from evidence"
    )
    anomalies: list[DetectedAnomaly] = Field(default_factory=list)
    risk_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Overall contextual risk"
    )


class InvestigationReasoning(BaseModel):
    """Output of the Investigation Reasoning agent."""

    status: AgentStatus = Field(default=AgentStatus.NOT_STARTED)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    reasoning_summary: Optional[str] = Field(
        default=None, description="Narrative reasoning trace"
    )
    recommended_actions: list[str] = Field(default_factory=list)


class EvidenceComplianceValidation(BaseModel):
    """Output of the Evidence & Compliance Validation agent."""

    status: AgentStatus = Field(default=AgentStatus.NOT_STARTED)
    compliance_mappings: list[ComplianceMapping] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(
        default_factory=list, description="Missing evidence items"
    )
    validation_summary: Optional[str] = Field(default=None)


class DecisionOptimization(BaseModel):
    """Output of the Decision Optimization agent."""

    status: AgentStatus = Field(default=AgentStatus.NOT_STARTED)
    decision_options: list[DecisionOption] = Field(default_factory=list)
    recommended_decision: Optional[DecisionAction] = Field(default=None)
    decision_rationale: Optional[str] = Field(default=None)


class TimelineEvent(BaseModel):
    """A single event in the investigation timeline."""

    timestamp: datetime = Field(
        ...,
        description="When this event occurred",
    )
    event_name: str = Field(
        ...,
        description="Example: Transaction Flagged, Evidence Collected",
    )
    stage: Optional[CurrentStage] = Field(
        default=None,
        description="Pipeline stage this event belongs to",
    )


class ReportGraphs(BaseModel):
    """Graph visualizations included in the investigation report."""

    entity_relationship_graph: Optional[GraphData] = Field(
        default=None,
        description="Customer -> Merchant -> Beneficiary -> Device relationships",
    )
    reasoning_graph: Optional[GraphData] = Field(
        default=None,
        description="Evidence -> Hypotheses -> Validation -> Decision flow",
    )
    decision_comparison_graph: Optional[GraphData] = Field(
        default=None,
        description="Allow/Hold/Block/Escalate comparison with pros/cons/mitigation",
    )
    investigation_timeline: list[TimelineEvent] = Field(
        default_factory=list,
        description="Chronological sequence of investigation events",
    )


class InvestigationReport(BaseModel):
    """Output of the Reporting & Visualization agent."""

    status: AgentStatus = Field(default=AgentStatus.NOT_STARTED)
    executive_summary: Optional[str] = Field(default=None)
    detailed_narrative: Optional[str] = Field(default=None)
    graphs: Optional[ReportGraphs] = Field(default=None)
    generated_at: Optional[datetime] = Field(default=None)


# ============================================================
# Root Investigation State
# ============================================================


class InvestigationState(BaseModel):
    """Single shared state object for the entire investigation pipeline.

    Every LangGraph node reads from and writes to this state.
    """

    case_id: str = Field(..., description="Unique investigation case identifier")
    case_input: CaseInput = Field(...)
    context_intelligence: Optional[ContextIntelligence] = Field(default=None)
    investigation_reasoning: Optional[InvestigationReasoning] = Field(default=None)
    evidence_compliance_validation: Optional[EvidenceComplianceValidation] = Field(
        default=None
    )
    decision_optimization: Optional[DecisionOptimization] = Field(default=None)
    investigation_report: Optional[InvestigationReport] = Field(default=None)
    current_stage: CurrentStage = Field(default=CurrentStage.INTAKE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    errors: list[AgentError] = Field(default_factory=list)


# ============================================================
# Factory Function
# ============================================================


def create_initial_state(case_id: str, case_input: CaseInput) -> InvestigationState:
    """Create a fresh InvestigationState from raw case input.

    All agent outputs default to None, the stage is set to INTAKE,
    and timestamps are initialised to the current time.
    """
    now = datetime.now(timezone.utc)
    return InvestigationState(
        case_id=case_id,
        case_input=case_input,
        current_stage=CurrentStage.INTAKE,
        created_at=now,
        updated_at=now,
    )
