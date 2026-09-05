
"use client";

import { useCallback, useEffect, useState } from "react";
import { listInvestigations } from "@/services/investigationService";
import { listAssignmentsRequest } from "@/services/api";
import { useInvestigator } from "@/components/auth/InvestigatorProvider";
import { InvestigatorAvatar } from "@/components/investigators/InvestigatorAvatar";
import type { Investigator } from "@/types";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { RiskScoreBadge } from "@/components/investigations/RiskScoreBadge";
import type { InvestigationListItem } from "@/types";

export function InvestigationList() {
  const [investigations, setInvestigations] = useState<
    InvestigationListItem[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // case_id -> the investigator who handled it. Historical and permanent,
  // deliberately separate from the Officer Box's live presence.
  const [handledBy, setHandledBy] = useState<Record<string, Investigator | null>>({});
  const { investigator, authConfigured, loading: authLoading } = useInvestigator();

  const loadInvestigations = useCallback(() => {
    setLoading(true);
    setError(null);

    listInvestigations()
      .then(setInvestigations)
      .catch((reason: unknown) => {
        setError(
          reason instanceof Error
            ? reason.message
            : "Unable to load investigations.",
        );
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadInvestigations();
  }, [loadInvestigations]);

  useEffect(() => {
    // Attribution is fetched separately so the existing investigation list
    // contract is untouched, and its failure leaves the table fully usable
    // with every case simply shown as unassigned.
    //
    // Waiting for the session matters: this endpoint requires a bearer token,
    // and firing before Supabase has restored the session returned 401 and
    // left every case reading "Unassigned" with no retry. Depending on the
    // resolved investigator makes the fetch run again once sign-in completes.
    if (!authConfigured || authLoading || !investigator) return;
    let active = true;
    void listAssignmentsRequest()
      .then((assignments) => {
        if (!active) return;
        setHandledBy(
          Object.fromEntries(assignments.map((a) => [a.case_id, a.investigator])),
        );
      })
      .catch(() => {
        if (active) setHandledBy({});
      });
    return () => {
      active = false;
    };
  }, [authConfigured, authLoading, investigator]);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="mb-6">
          <div className="h-8 w-48 rounded bg-gray-200 dark:bg-gray-700" />
          <div className="mt-2 h-4 w-32 rounded bg-gray-100 dark:bg-gray-800" />
        </div>

        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-surface-dark">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-800/50">
                <th className="px-6 py-4">
                  <div className="h-4 w-24 rounded bg-gray-200 dark:bg-gray-700" />
                </th>
                <th className="px-6 py-4">
                  <div className="h-4 w-24 rounded bg-gray-200 dark:bg-gray-700" />
                </th>
                <th className="px-6 py-4">
                  <div className="h-4 w-16 rounded bg-gray-200 dark:bg-gray-700" />
                </th>
                <th className="px-6 py-4">
                  <div className="h-4 w-16 rounded bg-gray-200 dark:bg-gray-700" />
                </th>
                <th className="px-6 py-4">
                  <div className="h-4 w-20 rounded bg-gray-200 dark:bg-gray-700" />
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {[1, 2, 3, 4, 5].map((i) => (
                <tr key={i}>
                  <td className="px-6 py-4">
                    <div className="h-4 w-20 rounded bg-gray-100 dark:bg-gray-800" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 w-32 rounded bg-gray-100 dark:bg-gray-800" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-6 w-24 rounded-full bg-gray-100 dark:bg-gray-800" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-6 w-16 rounded-full bg-gray-100 dark:bg-gray-800" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 w-24 rounded bg-gray-100 dark:bg-gray-800" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-8 text-center sm:px-6 dark:border-red-900 dark:bg-red-950/40">
        <h1 className="text-lg font-semibold text-red-800 dark:text-red-200">
          Unable to load investigations
        </h1>

        <p className="mt-2 text-sm text-red-700 dark:text-red-300">{error}</p>

        <button
          type="button"
          onClick={loadInvestigations}
          className="mt-4 rounded-md bg-red-700 px-3 py-2 text-sm font-medium text-white hover:bg-red-800 dark:bg-red-600 dark:hover:bg-red-500"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Investigations</h1>

        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {investigations.length} investigation
          {investigations.length !== 1 ? "s" : ""} triggered from alerts
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-surface-dark">
        <table className="w-full min-w-[44rem] text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-800/50">
              <th className="px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">
                Investigation ID
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">
                Customer Name
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">
                Status
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">
                Risk Score
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">
                Created Date
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600 dark:text-gray-300">
                Investigator
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {investigations.length === 0 ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-6 py-10 text-center text-sm text-gray-500 dark:text-gray-400"
                >
                  No investigations found.
                </td>
              </tr>
            ) : (
              investigations.map((inv) => (
                <tr
                  key={inv.case_id}
                  className="cursor-pointer transition-colors hover:bg-blue-50/50 dark:hover:bg-blue-900/20"
                  onClick={() => {
                    window.location.href = `/investigations/${inv.case_id}`;
                  }}
                >
                  <td className="px-6 py-4 font-medium whitespace-nowrap text-blue-600 dark:text-blue-400">
                    {inv.case_id}
                  </td>

                  <td className="px-6 py-4 text-gray-900 dark:text-gray-100">
                    {inv.customer_name}
                  </td>

                  <td className="px-6 py-4">
                    <StatusBadge value={inv.current_stage} />
                  </td>

                  <td className="px-6 py-4">
                    <RiskScoreBadge score={inv.risk_score} />
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap text-gray-500 dark:text-gray-400">
                    {new Date(inv.created_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </td>

                  <td className="px-6 py-4">
                    {handledBy[inv.case_id] ? (
                      <InvestigatorAvatar
                        investigator={handledBy[inv.case_id]!}
                        context="handled this investigation"
                      />
                    ) : (
                      // Cases raised before investigator accounts existed have
                      // nobody to name; say so rather than inventing one.
                      <span
                        className="text-sm text-gray-400 dark:text-gray-500"
                        title="No investigator recorded for this case"
                      >
                        Unassigned
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

