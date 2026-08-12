import { CurrentStage } from "@/types";
import type { InvestigationListItem, InvestigationState } from "@/types";
import { mockInvestigations } from "./mockData";

/**
 * Mock API service for investigations.
 *
 * All functions return Promises resolved with static data.
 * No HTTP requests are made — backend integration happens in later rounds.
 */

/** Simulated network delay in milliseconds. */
const MOCK_DELAY_MS = 300;

/** Helper to simulate async network latency. */
function delay<T>(data: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(data), MOCK_DELAY_MS));
}

/**
 * Returns a lightweight list of all investigations.
 * Maps the full InvestigationState into InvestigationListItem summaries.
 */
export async function listInvestigations(): Promise<InvestigationListItem[]> {
  const items: InvestigationListItem[] = mockInvestigations.map((inv) => ({
    case_id: inv.case_id,
    customer_name: inv.case_input.customer_profile?.name ?? "Unknown",
    current_stage: inv.current_stage,
    risk_score: inv.context_intelligence?.risk_score,
    created_at: inv.created_at,
    alert_reason: inv.case_input.alert_reason,
  }));

  return delay(items);
}

/**
 * Returns a single investigation by case ID.
 * Throws if the ID is not found.
 */
export async function getInvestigation(id: string): Promise<InvestigationState> {
  const investigation = mockInvestigations.find((inv) => inv.case_id === id);

  if (!investigation) {
    throw new Error(`Investigation not found: ${id}`);
  }

  return delay(investigation);
}

/**
 * Creates a new investigation and returns it.
 * Returns a stub InvestigationState at INTAKE stage.
 */
export async function createInvestigation(): Promise<InvestigationState> {
  const newInvestigation: InvestigationState = {
    case_id: `INV-2025-${String(Date.now()).slice(-4)}`,
    case_input: {
      transactions: [],
      supporting_documents: [],
      alert_reason: "Manually created investigation",
    },
    current_stage: CurrentStage.INTAKE,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    errors: [],
  };

  return delay(newInvestigation);
}
