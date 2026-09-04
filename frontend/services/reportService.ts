import { AgentStatus, CurrentStage } from "@/types";
import type { InvestigationState } from "@/types";
import { listInvestigationsRequest } from "@/services/api";

export interface ReportListItem {
  caseId: string;
  customerName: string;
  riskScore?: number;
  recommendation?: string;
  createdAt: string;
  updatedAt: string;
}

/** A report is available only after both the case and reporting agent finish. */
export function isCompletedReport(
  investigation: InvestigationState,
): boolean {
  return (
    investigation.current_stage === CurrentStage.DONE &&
    investigation.investigation_report?.status === AgentStatus.COMPLETED
  );
}

function toReportListItem(investigation: InvestigationState): ReportListItem {
  return {
    caseId: investigation.case_id,
    customerName: investigation.case_input.customer_profile?.name ?? "Unknown customer",
    riskScore: investigation.context_intelligence?.risk_score,
    recommendation: investigation.decision_optimization?.recommended_decision,
    createdAt: investigation.investigation_report?.generated_at ?? investigation.created_at,
    updatedAt: investigation.updated_at,
  };
}

/** Reuses the authenticated investigations API, which contains persisted reports. */
export async function listReports(): Promise<ReportListItem[]> {
  const investigations = await listInvestigationsRequest();
  return investigations
    .filter(isCompletedReport)
    .map(toReportListItem)
    .sort((first, second) =>
      new Date(second.createdAt).getTime() - new Date(first.createdAt).getTime(),
    );
}
