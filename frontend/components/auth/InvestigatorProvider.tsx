"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Session } from "@supabase/supabase-js";
import { getSupabaseClient, isAuthConfigured } from "@/services/supabaseClient";
import { getMeRequest, setAccessTokenProvider } from "@/services/api";
import type { Investigator } from "@/types";

/**
 * Holds the signed-in investigator for the whole app.
 *
 * The Supabase session is the only identity source. Its access token is handed
 * to the API layer through a setter rather than being read from storage at call
 * time, so exactly one place knows how to obtain it.
 *
 * `initials` and `fullName` are derived from the authenticated account, never
 * hardcoded, so every officer renders their own avatar.
 */

interface InvestigatorContextValue {
  investigator: Investigator | null;
  loading: boolean;
  authConfigured: boolean;
  signInWithOfficerId: (officerId: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const InvestigatorContext = createContext<InvestigatorContextValue>({
  investigator: null,
  loading: true,
  authConfigured: false,
  signInWithOfficerId: async () => {},
  signOut: async () => {},
});

/** First letter of the display name — derived, never hardcoded. */
export function initialOf(fullName: string | undefined | null): string {
  const trimmed = (fullName ?? "").trim();
  return trimmed ? trimmed[0].toUpperCase() : "?";
}

function fromSession(session: Session | null): Investigator | null {
  if (!session?.user) return null;
  const metadata = (session.user.user_metadata ?? {}) as Record<string, unknown>;
  const name =
    (typeof metadata.full_name === "string" && metadata.full_name.trim()) ||
    (typeof metadata.name === "string" && metadata.name.trim()) ||
    session.user.email?.split("@")[0] ||
    "Unknown investigator";
  return {
    user_id: session.user.id,
    full_name: name,
    email: session.user.email ?? null,
    initial: initialOf(name),
  };
}

export function InvestigatorProvider({ children }: { children: ReactNode }) {
  const [investigator, setInvestigator] = useState<Investigator | null>(null);
  const [loading, setLoading] = useState(true);
  const authConfigured = isAuthConfigured();

  useEffect(() => {
    const supabase = getSupabaseClient();
    if (supabase === null) {
      // Nothing to subscribe to when auth is unconfigured; settle immediately.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoading(false);
      return;
    }

    // The API layer asks for a token per request, so a refreshed session is
    // picked up without re-registering anything.
    setAccessTokenProvider(async () => {
      const { data } = await supabase.auth.getSession();
      return data.session?.access_token ?? null;
    });

    let active = true;

    /**
     * Adopt a session, then enrich it with the officer profile.
     *
     * The Supabase token carries the name but not the Officer ID, which lives
     * in the profile table. Fetching it also creates the profile on an
     * officer's first sign-in. A failure here leaves the session usable with
     * just the name rather than blocking sign-in.
     */
    const adopt = async (session: Session | null) => {
      const base = fromSession(session);
      if (!active) return;
      setInvestigator(base);
      setLoading(false);
      if (!base) return;
      try {
        const profile = await getMeRequest();
        if (active) setInvestigator({ ...base, ...profile });
      } catch {
        // Keep the session; the header simply shows no Officer ID.
      }
    };

    void supabase.auth.getSession().then(({ data }) => void adopt(data.session));

    const { data: subscription } = supabase.auth.onAuthStateChange(
      (_event, session) => void adopt(session),
    );

    return () => {
      active = false;
      subscription.subscription.unsubscribe();
    };
  }, []);

  /**
   * Sign in with an Officer ID.
   *
   * The exchange happens in a server route: it resolves the Officer ID to the
   * account Supabase authenticates and performs the password grant there, so
   * the internal email never reaches browser JavaScript. The route sets the
   * session cookies that middleware and Server Components read.
   */
  const signInWithOfficerId = useCallback(async (officerId: string, password: string) => {
    const response = await fetch("/api/auth/officer-login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ officer_id: officerId, password }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || "Invalid Officer ID or password.");
    }
    // Pick the new cookie session up in this tab straight away.
    const supabase = getSupabaseClient();
    if (supabase !== null) {
      const { data } = await supabase.auth.getSession();
      const base = fromSession(data.session);
      setInvestigator(base);
      if (base) {
        try {
          setInvestigator({ ...base, ...(await getMeRequest()) });
        } catch {
          // Officer ID is cosmetic; never block a successful sign-in.
        }
      }
    }
  }, []);

  const signOut = useCallback(async () => {
    const supabase = getSupabaseClient();
    if (supabase !== null) await supabase.auth.signOut();
    setInvestigator(null);
    // Full navigation, so middleware re-evaluates with the cookies now cleared
    // and every protected route becomes inaccessible again.
    window.location.assign("/login");
  }, []);

  const value = useMemo(
    () => ({ investigator, loading, authConfigured, signInWithOfficerId, signOut }),
    [investigator, loading, authConfigured, signInWithOfficerId, signOut],
  );

  return (
    <InvestigatorContext.Provider value={value}>{children}</InvestigatorContext.Provider>
  );
}

export function useInvestigator(): InvestigatorContextValue {
  return useContext(InvestigatorContext);
}
