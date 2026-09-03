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

async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
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

export function getInvestigationRequest(caseId: string): Promise<InvestigationState> {
  return requestJson<InvestigationState>(
    `/investigations/${encodeURIComponent(caseId)}`,
    { cache: "no-store" },
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
