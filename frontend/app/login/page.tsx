"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, ShieldCheck } from "lucide-react";
import { useInvestigator } from "@/components/auth/InvestigatorProvider";

/**
 * Investigator sign-in, backed entirely by Supabase Auth.
 *
 * No credential is stored or checked by this application: the form hands the
 * email and password straight to Supabase, which issues the session. Uses the
 * existing visual language rather than introducing a new one.
 */
function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { signInWithOfficerId, authConfigured } = useInvestigator();
  const [officerId, setOfficerId] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nextPath = params.get("next") || "/officer";

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await signInWithOfficerId(officerId, password);
      // Refresh so middleware and Server Components observe the new
      // session cookies before the destination renders.
      router.replace(nextPath);
      router.refresh();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Sign-in failed.");
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-md flex-col justify-center py-12">
      <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              Investigator sign in
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Use your bank investigator account.
            </p>
          </div>
        </div>

        {!authConfigured ? (
          <p
            role="alert"
            className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200"
          >
            Investigator sign-in is not configured for this deployment.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="officer-id"
                className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Officer ID
              </label>
              <input
                id="officer-id"
                type="text"
                required
                autoComplete="username"
                placeholder="OFF-001"
                value={officerId}
                onChange={(event) => setOfficerId(event.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-950 dark:text-white"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-gray-800 dark:bg-gray-950 dark:text-white"
              />
            </div>

            {error && (
              <p
                role="alert"
                className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

/**
 * `useSearchParams` opts a route into client-side rendering, which Next
 * requires be wrapped in a Suspense boundary so the rest of the page can still
 * be prerendered.
 */
export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
