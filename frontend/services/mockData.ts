import {
  AgentStatus,
  AnomalyType,
  CurrentStage,
  DecisionAction,
  ProcessingStatus,
  SeverityLevel,
} from "@/types";
import type { InvestigationState } from "@/types";

/**
 * Mock investigation data for Round 1 development.
 * Each investigation represents a different pipeline stage to demonstrate
 * all possible UI states.
 */
export const mockInvestigations: InvestigationState[] = [
  // ── Case 1: Fully completed investigation ───────────────────
  {
    case_id: "INV-2025-001",
    case_input: {
      transactions: [
        {
          transaction_id: "TXN-90001",
          amount: 24500.0,
          currency: "USD",
          timestamp: "2025-07-10T14:32:00Z",
          sender_account: "ACC-112233",
          receiver_account: "ACC-445566",
          transaction_type: "WIRE",
          channel: "ONLINE",
          description: "International wire transfer",
          location: "New York, US",
        },
        {
          transaction_id: "TXN-90002",
          amount: 15200.0,
          currency: "USD",
          timestamp: "2025-07-10T16:45:00Z",
          sender_account: "ACC-112233",
          receiver_account: "ACC-778899",
          transaction_type: "WIRE",
          channel: "ONLINE",
          description: "Follow-up transfer",
          location: "New York, US",
        },
      ],
      customer_profile: {
        customer_id: "CUST-1001",
        name: "Marcus Chen",
        email: "marcus.chen@email.com",
        phone: "+1-555-0142",
        address: "142 Broadway, New York, NY 10001",
        date_of_birth: "1985-03-15",
        account_open_date: "2019-06-20",
        risk_rating: "MEDIUM",
        occupation: "Financial Consultant",
        nationality: "US",
      },
      merchant_info: {
        merchant_id: "MERCH-5001",
        name: "Global Trade Solutions Ltd",
        category: "Financial Services",
        country: "UK",
        risk_level: SeverityLevel.MEDIUM,
        registered_date: "2018-01-10",
      },
      device_info: {
        device_id: "DEV-A1B2C3",
        device_type: "DESKTOP",
        ip_address: "198.51.100.42",
        geolocation: "40.7128,-74.0060",
        is_known_device: true,
        os: "Windows 11",
        browser: "Chrome 126",
      },
      beneficiary_info: {
        beneficiary_id: "BEN-3001",
        name: "Oceanic Imports LLC",
        account_number: "ACC-778899",
        bank_name: "HSBC London",
        country: "UK",
        is_new: true,
        relationship: "Business Partner",
      },
      supporting_documents: [
        {
          document_id: "DOC-001",
          document_type: "INVOICE",
          file_name: "invoice_july_2025.pdf",
          uploaded_at: "2025-07-10T15:00:00Z",
          summary: "Commercial invoice for consulting services",
          extracted_entities: ["Global Trade Solutions", "Marcus Chen"],
          extracted_transactions: ["TXN-90001"],
          evidence_references: ["EVD-001"],
          processing_status: ProcessingStatus.SUMMARIZED,
        },
      ],
      alert_reason: "Multiple high-value wire transfers to new beneficiary in single day",
    },
    context_intelligence: {
      status: AgentStatus.COMPLETED,
      context_summary:
        "Customer initiated two large wire transfers totaling $39,700 to a newly added UK-based beneficiary within 2 hours. The beneficiary entity has limited public records. Transaction pattern deviates from the customer's historical behavior.",
      key_indicators: [
        "New beneficiary added same day as transfers",
        "Transaction amount exceeds 90th percentile for customer",
        "Recipient entity registered < 2 years ago",
        "Two rapid-succession transfers within 2h window",
      ],
      anomalies: [
        {
          anomaly_id: "ANM-001",
          anomaly_type: AnomalyType.BEHAVIORAL,
          severity: SeverityLevel.HIGH,
          description: "Transaction velocity 3x above customer baseline",
          related_transactions: ["TXN-90001", "TXN-90002"],
        },
        {
          anomaly_id: "ANM-002",
          anomaly_type: AnomalyType.CONTEXTUAL,
          severity: SeverityLevel.MEDIUM,
          description: "New beneficiary with limited business history",
          related_transactions: ["TXN-90001"],
        },
      ],
      risk_score: 0.78,
    },
    investigation_reasoning: {
      status: AgentStatus.COMPLETED,
      hypotheses: [
        {
          hypothesis_id: "HYP-001",
          title: "Legitimate Business Transaction",
          description:
            "Customer is a financial consultant making payments for business services. The invoice and business relationship support this.",
          confidence: 0.35,
          supporting_evidence: ["DOC-001", "EVD-001"],
          contradicting_evidence: ["ANM-001", "ANM-002"],
        },
        {
          hypothesis_id: "HYP-002",
          title: "Potential Layering Activity",
          description:
            "Rapid successive transfers to a new beneficiary with limited history may indicate layering in a money laundering scheme.",
          confidence: 0.65,
          supporting_evidence: ["ANM-001", "ANM-002"],
          contradicting_evidence: ["DOC-001"],
        },
      ],
      reasoning_summary:
        "Weight of evidence leans toward suspicious activity. While legitimate business documentation exists, the behavioral anomalies and beneficiary risk factors warrant further investigation.",
      recommended_actions: [
        "Request additional documentation for business relationship",
        "Verify beneficiary entity registration details",
        "Review customer's transaction history for similar patterns",
      ],
    },
    evidence_compliance_validation: {
      status: AgentStatus.COMPLETED,
      compliance_mappings: [
        {
          regulation_id: "AML-2023-04",
          regulation_name: "Anti-Money Laundering Directive",
          description: "Wire transfers exceeding $10,000 require enhanced due diligence",
          is_violated: true,
          severity: SeverityLevel.HIGH,
          evidence_references: ["TXN-90001", "TXN-90002"],
        },
        {
          regulation_id: "KYC-2024-01",
          regulation_name: "Know Your Customer Requirements",
          description: "New beneficiary verification within 24 hours",
          is_violated: false,
          severity: SeverityLevel.MEDIUM,
          evidence_references: ["BEN-3001"],
        },
      ],
      evidence_gaps: [
        "Missing proof of business relationship duration",
        "No secondary verification of beneficiary identity",
      ],
      validation_summary:
        "AML compliance violation detected due to insufficient enhanced due diligence on high-value transfers. KYC requirements met but recommend additional beneficiary verification.",
    },
    decision_optimization: {
      status: AgentStatus.COMPLETED,
      decision_options: [
        {
          option_id: "DEC-001",
          action: DecisionAction.HOLD,
          rationale:
            "Place a temporary hold on the transfers pending additional documentation and beneficiary verification.",
          confidence: 0.72,
          risk_score: 0.45,
          pros: [
            "Prevents potential loss while investigation continues",
            "Compliant with AML requirements",
          ],
          cons: [
            "May impact legitimate business operations",
            "Customer relationship friction",
          ],
          risks: ["Customer complaint", "Regulatory scrutiny if hold is prolonged"],
          mitigation: [
            "Set 48-hour review deadline",
            "Notify customer of documentation requirements",
          ],
        },
        {
          option_id: "DEC-002",
          action: DecisionAction.ESCALATE,
          rationale:
            "Escalate to senior compliance team for manual review given the AML violation.",
          confidence: 0.68,
          risk_score: 0.6,
          pros: [
            "Human expertise on complex case",
            "Proper compliance escalation path",
          ],
          cons: ["Longer resolution time", "Higher operational cost"],
          risks: ["Delayed resolution"],
          mitigation: ["Priority queue for escalated cases"],
        },
      ],
      recommended_decision: DecisionAction.HOLD,
      decision_rationale:
        "Recommend HOLD action: The combination of behavioral anomalies, new beneficiary risk, and AML compliance gap justifies a temporary hold. This balances risk mitigation with customer impact.",
    },
    investigation_report: {
      status: AgentStatus.COMPLETED,
      executive_summary:
        "Investigation INV-2025-001 identified suspicious wire transfer activity involving $39,700 in transfers to a newly added UK-based beneficiary. Behavioral anomalies and an AML compliance violation were detected. Recommended action: HOLD pending additional documentation.",
      detailed_narrative:
        "Marcus Chen (CUST-1001) initiated two wire transfers totaling $39,700 to Oceanic Imports LLC, a UK-based entity registered less than 2 years ago. The transfers occurred within a 2-hour window, representing a 3x increase over the customer's baseline transaction velocity. While a commercial invoice was provided, the evidence is insufficient to fully validate the business relationship. An AML compliance violation was flagged for inadequate enhanced due diligence on transfers exceeding $10,000.",
      generated_at: "2025-07-11T09:00:00Z",
    },
    current_stage: CurrentStage.DONE,
    created_at: "2025-07-10T14:30:00Z",
    updated_at: "2025-07-11T09:00:00Z",
    errors: [],
  },

  // ── Case 2: In-progress at reasoning stage ──────────────────
  {
    case_id: "INV-2025-002",
    case_input: {
      transactions: [
        {
          transaction_id: "TXN-90010",
          amount: 8750.0,
          currency: "EUR",
          timestamp: "2025-08-01T09:15:00Z",
          sender_account: "ACC-223344",
          receiver_account: "ACC-556677",
          transaction_type: "P2P",
          channel: "MOBILE",
          description: "Personal transfer",
          location: "Berlin, DE",
        },
      ],
      customer_profile: {
        customer_id: "CUST-2002",
        name: "Sophia Martinez",
        email: "sophia.m@email.com",
        phone: "+49-30-555-0198",
        address: "45 Friedrichstraße, Berlin, Germany",
        risk_rating: "LOW",
        occupation: "Software Engineer",
        nationality: "DE",
      },
      supporting_documents: [],
      alert_reason: "P2P transfer to high-risk jurisdiction account",
    },
    context_intelligence: {
      status: AgentStatus.COMPLETED,
      context_summary:
        "Single P2P transfer of €8,750 from a low-risk customer to an account in a jurisdiction flagged for elevated financial crime risk.",
      key_indicators: [
        "Destination account in high-risk jurisdiction",
        "Customer has low historical risk rating",
        "Amount just below €10,000 reporting threshold",
      ],
      anomalies: [
        {
          anomaly_id: "ANM-010",
          anomaly_type: AnomalyType.CONTEXTUAL,
          severity: SeverityLevel.MEDIUM,
          description: "Transfer just below regulatory reporting threshold",
          related_transactions: ["TXN-90010"],
        },
      ],
      risk_score: 0.52,
    },
    investigation_reasoning: {
      status: AgentStatus.IN_PROGRESS,
      hypotheses: [],
      recommended_actions: [],
    },
    current_stage: CurrentStage.REASONING,
    created_at: "2025-08-01T09:20:00Z",
    updated_at: "2025-08-01T10:45:00Z",
    errors: [],
  },

  // ── Case 3: Early stage — just intake ───────────────────────
  {
    case_id: "INV-2025-003",
    case_input: {
      transactions: [
        {
          transaction_id: "TXN-90020",
          amount: 125000.0,
          currency: "USD",
          timestamp: "2025-08-05T11:00:00Z",
          sender_account: "ACC-334455",
          receiver_account: "ACC-667788",
          transaction_type: "WIRE",
          channel: "BRANCH",
          description: "Real estate deposit",
          location: "Miami, FL",
        },
      ],
      customer_profile: {
        customer_id: "CUST-3003",
        name: "James Rodriguez",
        email: "j.rodriguez@email.com",
        risk_rating: "HIGH",
        occupation: "Real Estate Developer",
        nationality: "US",
      },
      supporting_documents: [
        {
          document_id: "DOC-020",
          document_type: "BANK_STATEMENT",
          file_name: "statement_q2_2025.pdf",
          uploaded_at: "2025-08-05T11:30:00Z",
          extracted_entities: [],
          extracted_transactions: [],
          evidence_references: [],
          processing_status: ProcessingStatus.PENDING,
        },
      ],
      alert_reason: "High-value branch wire transfer from high-risk rated customer",
    },
    current_stage: CurrentStage.INTAKE,
    created_at: "2025-08-05T11:05:00Z",
    updated_at: "2025-08-05T11:05:00Z",
    errors: [],
  },

  // ── Case 4: Failed during compliance check ──────────────────
  {
    case_id: "INV-2025-004",
    case_input: {
      transactions: [
        {
          transaction_id: "TXN-90030",
          amount: 3200.0,
          currency: "GBP",
          timestamp: "2025-08-08T16:20:00Z",
          sender_account: "ACC-445500",
          receiver_account: "ACC-889900",
          transaction_type: "CARD",
          channel: "ONLINE",
          description: "Online purchase — electronics",
          location: "London, UK",
        },
        {
          transaction_id: "TXN-90031",
          amount: 2800.0,
          currency: "GBP",
          timestamp: "2025-08-08T16:22:00Z",
          sender_account: "ACC-445500",
          receiver_account: "ACC-889901",
          transaction_type: "CARD",
          channel: "ONLINE",
          description: "Online purchase — electronics",
          location: "London, UK",
        },
        {
          transaction_id: "TXN-90032",
          amount: 4100.0,
          currency: "GBP",
          timestamp: "2025-08-08T16:25:00Z",
          sender_account: "ACC-445500",
          receiver_account: "ACC-889902",
          transaction_type: "CARD",
          channel: "ONLINE",
          description: "Online purchase — luxury goods",
          location: "London, UK",
        },
      ],
      customer_profile: {
        customer_id: "CUST-4004",
        name: "Elena Volkov",
        email: "elena.v@email.com",
        phone: "+44-20-555-0176",
        risk_rating: "MEDIUM",
        occupation: "Import/Export Manager",
        nationality: "GB",
      },
      device_info: {
        device_id: "DEV-X9Y8Z7",
        device_type: "MOBILE",
        ip_address: "203.0.113.55",
        is_known_device: false,
        os: "iOS 18",
        browser: "Safari 18",
      },
      supporting_documents: [],
      alert_reason: "Rapid-fire card transactions from unrecognized device",
    },
    context_intelligence: {
      status: AgentStatus.COMPLETED,
      context_summary:
        "Three card-not-present transactions totaling £10,100 within 5 minutes from an unrecognized mobile device. Pattern consistent with potential card fraud or account takeover.",
      key_indicators: [
        "3 transactions in 5 minutes",
        "Unrecognized device",
        "All purchases are high-value electronics/luxury",
        "Different merchant accounts for each transaction",
      ],
      anomalies: [
        {
          anomaly_id: "ANM-030",
          anomaly_type: AnomalyType.POINT,
          severity: SeverityLevel.HIGH,
          description: "Burst of 3 high-value transactions in 5-minute window",
          related_transactions: ["TXN-90030", "TXN-90031", "TXN-90032"],
        },
        {
          anomaly_id: "ANM-031",
          anomaly_type: AnomalyType.BEHAVIORAL,
          severity: SeverityLevel.HIGH,
          description: "Login from previously unseen device and IP address",
          related_transactions: ["TXN-90030"],
        },
      ],
      risk_score: 0.91,
    },
    investigation_reasoning: {
      status: AgentStatus.COMPLETED,
      hypotheses: [
        {
          hypothesis_id: "HYP-010",
          title: "Account Takeover",
          description:
            "Unrecognized device and rapid high-value purchases strongly suggest unauthorized account access.",
          confidence: 0.82,
          supporting_evidence: ["ANM-030", "ANM-031"],
          contradicting_evidence: [],
        },
      ],
      reasoning_summary:
        "High confidence of account takeover based on device anomaly and transaction velocity.",
      recommended_actions: [
        "Block card immediately",
        "Contact customer for verification",
        "Initiate chargeback process",
      ],
    },
    evidence_compliance_validation: {
      status: AgentStatus.FAILED,
      compliance_mappings: [],
      evidence_gaps: ["Compliance check could not complete due to service timeout"],
      validation_summary: "Agent failed during regulatory database lookup.",
    },
    current_stage: CurrentStage.COMPLIANCE,
    created_at: "2025-08-08T16:30:00Z",
    updated_at: "2025-08-08T17:15:00Z",
    errors: [
      {
        agent_name: "ComplianceAgent",
        error_type: "TimeoutError",
        message: "Regulatory database lookup timed out after 30s",
        timestamp: "2025-08-08T17:15:00Z",
      },
    ],
  },
];
