
"use client";

import { useCallback, useEffect, useState } from "react";
import { listInvestigations } from "@/services/investigationService";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { RiskScoreBadge } from "@/components/investigations/RiskScoreBadge";
import type { InvestigationListItem } from "@/types";

export function InvestigationList() {
  const [investigations, setInvestigations] = useState<
    InvestigationListItem[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="mb-6">
          <div className="h-8 w-48 rounded bg-gray-200" />
          <div className="mt-2 h-4 w-32 rounded bg-gray-100" />
        </div>

        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50/80">
                <th className="px-6 py-4">
                  <div className="h-4 w-24 rounded bg-gray-200" />
                </th>
                <th className="px-6 py-4">
                  <div className="h-4 w-24 rounded bg-gray-200" />
                </th>
                <th className="px-6 py-4">
                  <div className="h-4 w-16 rounded bg-gray-200" />
                </th>
                <th className="px-6 py-4">
                  <div className="h-4 w-16 rounded bg-gray-200" />
                </th>
                <th className="px-6 py-4">
                  <div className="h-4 w-20 rounded bg-gray-200" />
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-100">
              {[1, 2, 3, 4, 5].map((i) => (
                <tr key={i}>
                  <td className="px-6 py-4">
                    <div className="h-4 w-20 rounded bg-gray-100" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 w-32 rounded bg-gray-100" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-6 w-24 rounded-full bg-gray-100" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-6 w-16 rounded-full bg-gray-100" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 w-24 rounded bg-gray-100" />
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
      <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-8 text-center">
        <h1 className="text-lg font-semibold text-red-800">
          Unable to load investigations
        </h1>

        <p className="mt-2 text-sm text-red-700">{error}</p>

        <button
          type="button"
          onClick={loadInvestigations}
          className="mt-4 rounded-md bg-red-700 px-3 py-2 text-sm font-medium text-white hover:bg-red-800"
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
        <h1 className="text-2xl font-bold text-gray-900">Investigations</h1>

        <p className="mt-1 text-sm text-gray-500">
          {investigations.length} investigation
          {investigations.length !== 1 ? "s" : ""} triggered from alerts
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50/80">
              <th className="px-6 py-3 font-semibold text-gray-600">
                Investigation ID
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600">
                Customer Name
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600">
                Status
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600">
                Risk Score
              </th>

              <th className="px-6 py-3 font-semibold text-gray-600">
                Created Date
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-100">
            {investigations.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className="px-6 py-10 text-center text-sm text-gray-500"
                >
                  No investigations found.
                </td>
              </tr>
            ) : (
              investigations.map((inv) => (
                <tr
                  key={inv.case_id}
                  className="cursor-pointer transition-colors hover:bg-blue-50/50"
                  onClick={() => {
                    window.location.href = `/investigations/${inv.case_id}`;
                  }}
                >
                  <td className="px-6 py-4 font-medium text-blue-600">
                    {inv.case_id}
                  </td>

                  <td className="px-6 py-4 text-gray-900">
                    {inv.customer_name}
                  </td>

                  <td className="px-6 py-4">
                    <StatusBadge value={inv.current_stage} />
                  </td>

                  <td className="px-6 py-4">
                    <RiskScoreBadge score={inv.risk_score} />
                  </td>

                  <td className="px-6 py-4 text-gray-500">
                    {new Date(inv.created_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
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

