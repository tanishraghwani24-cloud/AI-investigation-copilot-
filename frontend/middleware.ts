import { NextRequest, NextResponse } from "next/server";
import { getMiddlewareSupabase, isAuthConfigured } from "@/lib/supabaseMiddleware";

/**
 * Route gate: no protected page or data proxy without a signed-in officer.
 *
 * This runs before the page or route handler, so it protects Server Components
 * too — the investigation detail page fetches its case server-side, and hiding
 * a nav link would not have stopped that HTML being rendered for a logged-out
 * visitor.
 *
 * It is one of two layers, not the only one: the backend independently requires
 * a verified officer token, so bypassing middleware still yields 401s.
 */

// Everything that is *not* gated. Anything else under the matcher requires a
// session, so a new protected page is covered by default rather than by
// remembering to add it.
const PUBLIC_PATHS = ["/login"];
const PUBLIC_API = ["/api/auth/officer-login", "/api/proxy/health"];

function isPublic(pathname: string): boolean {
  return (
    PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`)) ||
    PUBLIC_API.some((p) => pathname === p)
  );
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // With auth unconfigured the app stays usable in its previous single-user
  // form rather than locking everyone out of a misconfigured deployment.
  if (!isAuthConfigured() || isPublic(pathname)) {
    return NextResponse.next();
  }

  // getMiddlewareSupabase mirrors any refreshed cookies onto `request` as well
  // as the response, so getResponse() reflects the rebuilt request and the
  // route handler downstream sees the same (possibly just-refreshed) session
  // this call validates.
  const { supabase, getResponse } = getMiddlewareSupabase(request);

  // getUser() revalidates against Supabase rather than trusting the cookie's
  // contents, so a forged or expired cookie cannot pass this gate.
  const { data, error } = await supabase.auth.getUser();

  if (error || !data.user) {
    // Data requests get a status they can handle; page requests get sent to
    // the login screen with a return path.
    if (pathname.startsWith("/api/")) {
      return NextResponse.json(
        { error: { code: "unauthorized", message: "Sign in to continue." } },
        { status: 401 },
      );
    }
    const login = request.nextUrl.clone();
    login.pathname = "/login";
    login.search = `?next=${encodeURIComponent(pathname + request.nextUrl.search)}`;
    return NextResponse.redirect(login);
  }

  return getResponse();
}

export const config = {
  // Everything except Next's own assets and the favicon. Listing exclusions
  // rather than inclusions means a newly added page is protected by default.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|svg|gif|webp|ico)$).*)"],
};
