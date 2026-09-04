import type {
  InvestigationState,
  SupportingDocument,
} from "@/types";

// The backend requires a shared-secret X-API-Key header (P1 hardening).
// That secret must never reach browser JS. Server Components (this code
// running in Node.js) call the backend directly and attach it from a
// non-public env var; the browser instead calls the same-origin Next.js
// proxy route, which attaches the secret server-side. See
// app/api/proxy/[...path]/route.ts.
const isServer = typeof window === "undefined";

const API_BASE = isServer
  ? (
      process.env.BACKEND_INTERNAL_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://127.0.0.1:8000/api"
    ).replace(/\/$/, "")
  : "/api/proxy";

export class ApiError extends Error {
  readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function responseMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail = body.detail;
      if (typeof detail === "string") return detail;
    }
  } catch {
    // The server may return an empty or non-JSON error response.
  }
  return response.statusText || `Request failed with status ${response.status}`;
}

/**
 * Supplies the signed-in investigator's Supabase access token.
 *
 * Registered by InvestigatorProvider so this module never needs to know how
 * sessions are stored. The token identifies *who* is acting; the shared secret
 * below authenticates the deployment. They are separate concerns and both are
 * attached where applicable.
 */
type AccessTokenProvider = () => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;

export function setAccessTokenProvider(provider: AccessTokenProvider | null): void {
  accessTokenProvider = provider;
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
  /** Officer token for Server Components, which have no browser session. */
  accessToken?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
  // Investigator identity travels as a bearer token the backend verifies
  // against Supabase's public keys. A caller cannot name an investigator any
  // other way, so this is the only route by which actions become attributable.
  if (!isServer && accessTokenProvider) {
    try {
      const token = await accessTokenProvider();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    } catch {
      // A missing session must not break unauthenticated reads.
    }
  }
  // Only attach the secret on the server: process.env.API_SHARED_SECRET is
  // never inlined into the client bundle (only NEXT_PUBLIC_* vars are), so
  // this is always undefined in the browser — the header is simply omitted
  // there and the same-origin proxy attaches it instead.
  if (isServer && process.env.API_SHARED_SECRET) {
    headers["X-API-Key"] = process.env.API_SHARED_SECRET;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
    });
  } catch {
    throw new ApiError("The investigation service is unavailable. Check your connection and try again.");
  }

  if (!response.ok) {
    throw new ApiError(await responseMessage(response), response.status);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("The investigation service returned an incomplete response.", response.status);
  }
}

export function listInvestigationsRequest(): Promise<InvestigationState[]> {
  return requestJson<InvestigationState[]>("/investigations", {
    cache: "no-store",
  });
}

export function getInvestigationRequest(
  caseId: string,
  /** Supplied by Server Components, which have no browser session to read. */
  accessToken?: string | null,
): Promise<InvestigationState> {
  return requestJson<InvestigationState>(
    `/investigations/${encodeURIComponent(caseId)}`,
    { cache: "no-store" },
    accessToken,
  );
}

export function createInvestigationRequest(accountId?: string): Promise<InvestigationState> {
  const url = accountId ? `/investigations?account_id=${encodeURIComponent(accountId)}` : "/investigations";
  return requestJson<InvestigationState>(url, {
    method: "POST",
  });
}


export function runInvestigationRequest(caseId: string): Promise<InvestigationState> {
  return requestJson<InvestigationState>(
    `/investigations/${encodeURIComponent(caseId)}/run`,
    { method: "POST" },
  );
}

export async function uploadDocumentRequest(
  caseId: string,
  file: File,
  documentType = "OTHER",
): Promise<SupportingDocument> {
  if (!caseId.trim()) {
    throw new ApiError("A valid investigation ID is required before uploading a document.");
  }

  const body = new FormData();
  body.append("file", file);
  body.append("document_type", documentType);
  return requestJson<SupportingDocument>(
    `/investigations/${encodeURIComponent(caseId)}/documents`,
    { method: "POST", body },
  );
}

export function getMockBankTransactions(accountId: string): Promise<unknown[]> {
  return requestJson<unknown[]>(
    `/mock-bank/accounts/${encodeURIComponent(accountId)}/transactions`,
    { cache: "no-store" }
  );
}

export function getMockBankCustomer(customerId: string): Promise<unknown> {
  return requestJson<unknown>(
    `/mock-bank/customers/${encodeURIComponent(customerId)}`,
    { cache: "no-store" }
  );
}

/** One fraud alert in the Officer Inbox. */
export interface BankAlert {
  alert_id: string;
  transaction_id: string;
  account_id: string;
  customer_id?: string | null;
  customer_name?: string | null;
  reason: string;
  severity: string;
  risk_score: number;
  status: string;
  case_id?: string | null;
  amount?: number | null;
  currency?: string | null;
  transaction_type?: string | null;
  created_at: string;
}

/** The investigation an alert was escalated to. */
export interface InvestigateAlertResult {
  alert_id: string;
  case_id: string;
  created: boolean;
}

export function listAlertsRequest(status: "OPEN" | "INVESTIGATING" | "ALL" = "OPEN"): Promise<BankAlert[]> {
  return requestJson<BankAlert[]>(`/alerts?status=${status}`);
}

/**
 * Escalate one alert into its own investigation.
 *
 * The backend derives the case ID from the alert, so calling this twice for the
 * same alert returns the existing case (`created: false`) instead of creating a
 * second investigation.
 */
export function investigateAlertRequest(alertId: string): Promise<InvestigateAlertResult> {
  return requestJson<InvestigateAlertResult>(
    `/alerts/${encodeURIComponent(alertId)}/investigate`,
    { method: "POST" },
  );
}


/** The investigator identity the UI renders as an avatar. */
export interface Investigator {
  user_id: string;
  full_name: string;
  email?: string | null;
  initial: string;
  officer_id?: string | null;
  role?: string | null;
}

/** Investigators currently working a given case. */
export interface PresenceEntry {
  case_id: string;
  investigators: Investigator[];
}

/** The investigator who handled a case (historical). */
export interface CaseAssignment {
  case_id: string;
  investigator: Investigator | null;
}

export function getMeRequest(): Promise<Investigator> {
  return requestJson<Investigator>("/investigators/me");
}

export function listPresenceRequest(): Promise<PresenceEntry[]> {
  return requestJson<PresenceEntry[]>("/presence");
}

export function heartbeatPresenceRequest(caseId: string): Promise<PresenceEntry> {
  return requestJson<PresenceEntry>(
    `/presence/${encodeURIComponent(caseId)}/heartbeat`,
    { method: "POST" },
  );
}

export function listAssignmentsRequest(): Promise<CaseAssignment[]> {
  return requestJson<CaseAssignment[]>("/investigators/assignments");
}
