import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Supabase client for middleware.
 *
 * Kept apart from `supabaseServer` because that module imports `next/headers`,
 * which is only valid inside Server Components — pulling it in here would drag
 * it into bundles that cannot use it.
 */

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export function isAuthConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}

/**
 * Reads request cookies and writes refreshed ones onto both the request and
 * the response.
 *
 * `getUser()` can rotate the session (refresh the access token) as part of
 * validating it. Writing the refreshed cookies only onto the response updates
 * the browser for the *next* request but leaves the request object that
 * continues on to the route handler / Server Component still carrying the
 * stale, already-rotated-out session — so `next/headers` `cookies()`
 * downstream reads an invalid token even though this same request just
 * validated successfully. Mirroring the cookies onto `request` and rebuilding
 * the response from that mutated request (the pattern Supabase's own Next.js
 * SSR guide documents) keeps the rest of this request in sync with the
 * refresh.
 */
export function getMiddlewareSupabase(request: NextRequest) {
  let response = NextResponse.next({ request });
  const supabase = createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (toSet) => {
        toSet.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        toSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options),
        );
      },
    },
  });
  return { supabase, getResponse: () => response };
}
