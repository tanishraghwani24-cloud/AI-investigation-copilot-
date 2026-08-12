"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listInvestigations } from "@/services/investigationService";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { RiskScoreBadge } from "@/components/investigations/RiskScoreBadge";
import type { InvestigationListItem } from "@/types";

export function InvestigationList() {
  const [investigations, setInvestigations] = useState<InvestigationListItem[]>(
    [],
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listInvestigations()
      .then(setInvestigations)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
      </div>
    );
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Investigations</h1>
          <p className="mt-1 text-sm text-gray-500">
            {investigations.length} active investigation
            {investigations.length !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50/80">
              <th className="px-6 py-3 font-semibold text-gray-600">
                Investigation ID
              </th>
              <th className="px-6 py-3 font-semibold text-gray-600">
                Customer Name
              </th>
              <th className="px-6 py-3 font-semibold text-gray-600">Status</th>
              <th className="px-6 py-3 font-semibold text-gray-600">
                Risk Score
              </th>
              <th className="px-6 py-3 font-semibold text-gray-600">
                Created Date
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {investigations.map((inv) => (
              <Link
                key={inv.case_id}
                href={`/investigations/${inv.case_id}`}
                className="contents"
              >
                <tr className="cursor-pointer transition-colors hover:bg-blue-50/50">
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
              </Link>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
