import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * Browser-side Supabase Auth client.
 *
 * Only the project URL and the anon key are used. Both are public by design —
 * the anon key is meant to ship in browser JS and is protected by RLS, not by
 * secrecy. The service-role key is never referenced here or anywhere in the
 * frontend.
 *
 * Supabase is the sole source of investigator identity: the app holds no
 * password and issues no session of its own.
 */

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

let client: SupabaseClient | null = null;

/** True when the deployment has Supabase Auth configured. */
export function isAuthConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}

/**
 * Return the shared browser client, or null when auth is not configured.
 *
 * Returning null rather than throwing keeps an unconfigured deployment usable
 * in its existing single-user form instead of white-screening.
 */
export function getSupabaseClient(): SupabaseClient | null {
  if (!isAuthConfigured()) return null;
  if (client === null) {
    client = createBrowserClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return client;
}
