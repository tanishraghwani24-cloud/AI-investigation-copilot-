import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";
import {
  SUPABASE_ANON_KEY,
  SUPABASE_URL,
  isAuthConfigured,
} from "@/lib/supabaseMiddleware";

/**
 * Sign in with an Officer ID and password.
 *
 * Runs entirely server-side so the internal Supabase email never reaches the
 * browser. The flow is:
 *
 *   Officer ID  ->  (backend lookup, with the shared secret)  ->  email
 *               ->  Supabase signInWithPassword  ->  session cookies
 *
 * Supabase remains the only thing that checks the password; this route stores
 * no credential and makes no authorisation decision of its own. Failures are
 * reported identically whether the Officer ID or the password was wrong, so
 * this cannot be used to enumerate valid officers.
 */

const BACKEND_BASE = (
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000/api"
).replace(/\/$/, "");

const API_SECRET = process.env.API_SHARED_SECRET || "";

const GENERIC_FAILURE = "Invalid Officer ID or password.";

export async function POST(request: NextRequest) {
  if (!isAuthConfigured()) {
    return NextResponse.json(
      { error: "Sign-in is not configured for this deployment." },
      { status: 503 },
    );
  }

  let officerId = "";
  let password = "";
  try {
    const body = await request.json();
    officerId = String(body.officer_id ?? "").trim();
    password = String(body.password ?? "");
  } catch {
    return NextResponse.json({ error: GENERIC_FAILURE }, { status: 400 });
  }

  if (!officerId || !password) {
    return NextResponse.json({ error: GENERIC_FAILURE }, { status: 400 });
  }

  // Resolve the Officer ID to the account Supabase authenticates. The secret is
  // server-only; this call never happens from the browser.
  let email: string;
  try {
    const lookup = await fetch(`${BACKEND_BASE}/officers/lookup`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(API_SECRET ? { "x-api-key": API_SECRET } : {}),
      },
      body: JSON.stringify({ officer_id: officerId }),
      cache: "no-store",
    });
    if (!lookup.ok) {
      // Unknown ID and wrong password are indistinguishable to the caller.
      return NextResponse.json({ error: GENERIC_FAILURE }, { status: 401 });
    }
    email = (await lookup.json()).email;
  } catch {
    return NextResponse.json(
      { error: "The investigation service is unavailable." },
      { status: 503 },
    );
  }

  // Build the response first: Supabase writes its session cookies onto it.
  const response = NextResponse.json({ ok: true });
  const supabase = createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (toSet) =>
        toSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options),
        ),
    },
  });

  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    return NextResponse.json({ error: GENERIC_FAILURE }, { status: 401 });
  }
  return response;
}
