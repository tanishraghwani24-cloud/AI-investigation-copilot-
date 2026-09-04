/**
 * Same-origin proxy for browser-initiated requests to the FastAPI backend.
 *
 * The backend now requires a shared-secret X-API-Key header (P1 hardening).
 * That secret must never reach browser JS, so client components call this
 * route instead of the backend directly; this route runs server-side in
 * Next.js, attaches the secret from a non-public env var, and forwards the
 * request. Server Components that already run server-side (e.g. the
 * investigation detail page) skip this hop and call the backend directly —
 * see services/api.ts.
 */
import { NextRequest, NextResponse } from "next/server";
import { getServerAccessToken } from "@/lib/supabaseServer";

const BACKEND_BASE = (
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000/api"
).replace(/\/$/, "");

const API_SECRET = process.env.API_SHARED_SECRET || "";

async function forward(
  request: NextRequest,
  path: string[],
): Promise<Response> {
  const targetUrl = `${BACKEND_BASE}/${path.join("/")}${request.nextUrl.search}`;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  headers.set("accept", "application/json");
  if (API_SECRET) headers.set("x-api-key", API_SECRET);
  // Forward the officer's Supabase access token so the backend can verify *who*
  // is acting. The shared secret above authenticates the deployment; this header
  // authenticates the person, and the backend now requires both.
  //
  // The token is read from the session cookie rather than from a client-supplied
  // header, so the browser cannot hand this route an identity it does not hold.
  const sessionToken = await getServerAccessToken();
  if (sessionToken) headers.set("authorization", `Bearer ${sessionToken}`);

  const hasBody = request.method !== "GET" && request.method !== "HEAD";

  const backendResponse = await fetch(targetUrl, {
    method: request.method,
    headers,
    body: hasBody ? request.body : undefined,
    // Required by Node's fetch when streaming a request body.
    // @ts-expect-error - `duplex` isn't in the standard RequestInit type yet.
    duplex: hasBody ? "half" : undefined,
    cache: "no-store",
  });

  const responseHeaders = new Headers(backendResponse.headers);
  // Let the runtime recompute these for the (unmodified, streamed) body.
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

interface RouteContext {
  params: Promise<{ path: string[] }>;
}

export async function GET(request: NextRequest, { params }: RouteContext) {
  const { path } = await params;
  return forward(request, path);
}

export async function POST(request: NextRequest, { params }: RouteContext) {
  const { path } = await params;
  return forward(request, path);
}
