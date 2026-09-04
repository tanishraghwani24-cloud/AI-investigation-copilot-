"use client";

import { LogOut } from "lucide-react";
import Link from "next/link";
import { useInvestigator } from "@/components/auth/InvestigatorProvider";
import { InvestigatorAvatar } from "@/components/investigators/InvestigatorAvatar";

/**
 * Header chip showing who is signed in, with a sign-out control.
 *
 * Renders nothing when Supabase Auth is not configured, so a deployment
 * without it keeps exactly the header it has today.
 */
export function InvestigatorBadge() {
  const { investigator, loading, authConfigured, signOut } = useInvestigator();

  if (!authConfigured || loading) return null;

  if (!investigator) {
    return (
      <Link
        href="/login"
        className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:text-gray-300 dark:hover:bg-gray-800/60"
      >
        Sign in
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <InvestigatorAvatar investigator={investigator} size="md" />
      <span className="hidden leading-tight sm:block">
        <span className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {investigator.full_name}
        </span>
        {investigator.officer_id && (
          <span className="block text-xs text-gray-400 dark:text-gray-500">
            {investigator.officer_id}
          </span>
        )}
      </span>
      <button
        type="button"
        onClick={() => void signOut()}
        title="Sign out"
        aria-label="Sign out"
        className="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-200"
      >
        <LogOut className="h-4 w-4" />
      </button>
    </div>
  );
}
