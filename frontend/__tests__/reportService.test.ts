import { AgentStatus, CurrentStage, DecisionAction } from "@/types";
import { listInvestigationsRequest } from "@/services/api";
import { isCompletedReport, listReports } from "@/services/reportService";

jest.mock("@/services/api", () => ({
  listInvestigationsRequest: jest.fn(),
}));

const completedInvestigation = {
  case_id: "CASE-REPORT-001",
  current_stage: CurrentStage.DONE,
  created_at: "2026-09-01T09:00:00.000Z",
  updated_at: "2026-09-02T09:00:00.000Z",
  errors: [],
  case_input: {
    customer_profile: { customer_id: "CUST-001", name: "Ada Lovelace" },
    transactions: [],
    supporting_documents: [],
  },
  context_intelligence: { status: AgentStatus.COMPLETED, risk_score: 0.92, anomalies: [], key_indicators: [] },
  decision_optimization: { status: AgentStatus.COMPLETED, decision_options: [], recommended_decision: DecisionAction.BLOCK },
  investigation_report: { status: AgentStatus.COMPLETED, generated_at: "2026-09-01T10:00:00.000Z" },
};

describe("reportService", () => {
  it("accepts only DONE investigations with a completed investigation report", () => {
    expect(isCompletedReport(completedInvestigation)).toBe(true);
    expect(isCompletedReport({ ...completedInvestigation, current_stage: CurrentStage.REPORTING })).toBe(false);
    expect(isCompletedReport({ ...completedInvestigation, investigation_report: { status: AgentStatus.IN_PROGRESS } })).toBe(false);
    expect(isCompletedReport({ ...completedInvestigation, investigation_report: undefined })).toBe(false);
  });

  it("maps persisted investigation reports from the existing investigations API", async () => {
    (listInvestigationsRequest as jest.Mock).mockResolvedValue([
      { ...completedInvestigation, case_id: "CASE-OLDER", updated_at: "2026-09-01T09:00:00.000Z" },
      completedInvestigation,
      { ...completedInvestigation, case_id: "CASE-INCOMPLETE", current_stage: CurrentStage.DECISION },
    ]);

    await expect(listReports()).resolves.toEqual([
      expect.objectContaining({
        caseId: "CASE-REPORT-001",
        customerName: "Ada Lovelace",
        riskScore: 0.92,
        recommendation: DecisionAction.BLOCK,
        createdAt: "2026-09-01T10:00:00.000Z",
      }),
      expect.objectContaining({ caseId: "CASE-OLDER" }),
    ]);
  });
});
