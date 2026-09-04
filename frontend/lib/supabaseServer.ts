import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { SUPABASE_ANON_KEY, SUPABASE_URL, isAuthConfigured } from "@/lib/supabaseMiddleware";

/**
 * Server-side Supabase clients backed by cookies.
 *
 * Cookies (rather than localStorage) are what let middleware and Server
 * Components see the session at all — a token only the browser knows cannot
 * gate a server-rendered page.
 *
 * Only the public URL and anon key are used here; the service-role key is never
 * referenced anywhere in this project.
 */


/** Client for Server Components and route handlers (reads the request cookies). */
export async function getServerSupabase() {
  const cookieStore = await cookies();
  return createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => cookieStore.getAll(),
      setAll: (toSet) => {
        try {
          toSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options),
          );
        } catch {
          // Server Components cannot set cookies; middleware refreshes them.
        }
      },
    },
  });
}

/** The access token for the current request, or null when signed out. */
export async function getServerAccessToken(): Promise<string | null> {
  if (!isAuthConfigured()) return null;
  const supabase = await getServerSupabase();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}
