import type { InvestigationListItem, InvestigationState } from "@/types";
import {
  createInvestigationRequest,
  getInvestigationRequest,
  listInvestigationsRequest,
} from "@/services/api";

/** Maps the full backend state into the fields used by the list table. */
function toListItem(investigation: InvestigationState): InvestigationListItem {
  return {
    case_id: investigation.case_id,
    customer_name: investigation.case_input.customer_profile?.name ?? "Unknown customer",
    current_stage: investigation.current_stage,
    risk_score: investigation.context_intelligence?.risk_score,
    created_at: investigation.created_at,
    alert_reason: investigation.case_input.alert_reason,
  };
}

export async function listInvestigations(): Promise<InvestigationListItem[]> {
  const investigations = await listInvestigationsRequest();
  return investigations.map(toListItem);
}

export function getInvestigation(id: string): Promise<InvestigationState> {
  return getInvestigationRequest(id);
}

export function createInvestigation(): Promise<InvestigationState> {
  return createInvestigationRequest();
}
