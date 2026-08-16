import Link from "next/link";
import { ArrowLeft, FileText, Scale, ClipboardList, AlertTriangle } from "lucide-react";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { RiskScoreBadge } from "@/components/investigations/RiskScoreBadge";
import { AgentStatus } from "@/types";
import type { InvestigationState } from "@/types";

// The new panels
import { ContextPanel } from "@/components/ContextPanel";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { CompliancePanel } from "@/components/CompliancePanel";

interface PageProps {
  params: Promise<{ id: string }>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export default async function InvestigationDetailPage({ params }: PageProps) {
  const { id } = await params;
  const decodedId = decodeURIComponent(id);

  let investigation: InvestigationState | null = null;
  let errorMsg = null;

  try {
    const res = await fetch(`${API_BASE}/investigations/${decodedId}`, { cache: 'no-store' });
    if (!res.ok) {
      if (res.status === 404) {
        errorMsg = `No investigation found with ID: ${decodedId}`;
      } else {
        errorMsg = `Failed to fetch investigation: ${res.status} ${res.statusText}`;
      }
    } else {
      investigation = await res.json();
    }
  } catch (err: any) {
    errorMsg = err.message || "An unexpected error occurred while fetching the investigation.";
  }

  if (errorMsg || !investigation) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-4 h-12 w-12 text-amber-500" />
        <h2 className="text-lg font-semibold text-gray-900">Investigation Error</h2>
        <p className="mt-1 text-sm text-gray-500">{errorMsg}</p>
        <Link href="/investigations" className="mt-6 text-sm font-medium text-blue-600 hover:text-blue-700">
          ← Back to Investigations
        </Link>
      </div>
    );
  }

  const { case_input } = investigation;

  return (
    <div className="space-y-6">
      {/* Back link + header */}
      <div>
        <Link
          href="/investigations"
          className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-gray-500 transition-colors hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Investigations
        </Link>

        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{investigation.case_id}</h1>
            <p className="mt-1 text-sm text-gray-500">
              {case_input.customer_profile?.name ?? "Unknown Customer"}
              {case_input.alert_reason && (
                <span className="ml-2 text-gray-400">· {case_input.alert_reason}</span>
              )}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge value={investigation.current_stage} />
            <RiskScoreBadge score={investigation.context_intelligence?.risk_score} />
          </div>
        </div>

        {/* Meta strip */}
        <div className="mt-4 flex flex-wrap gap-6 text-xs text-gray-400">
          <span>
            Created{" "}
            {new Date(investigation.created_at).toLocaleDateString("en-US", {
              year: "numeric",
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          <span>
            Updated{" "}
            {new Date(investigation.updated_at).toLocaleDateString("en-US", {
              year: "numeric",
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          {investigation.errors.length > 0 && (
            <span className="text-red-500">
              {investigation.errors.length} error{investigation.errors.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {/* ── 1. Case Input ────────────────────────────────── */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
              <FileText className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-gray-900">Case Input</h3>
          </div>
        </div>
        <div className="px-6 py-5">
          <div className="space-y-4">
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-700">
                Transactions ({case_input.transactions?.length || 0})
              </h4>
              {case_input.transactions && case_input.transactions.length > 0 ? (
                <div className="overflow-x-auto rounded-lg border border-gray-100">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-gray-100 bg-gray-50/60">
                        <th className="px-3 py-2 font-medium text-gray-500">ID</th>
                        <th className="px-3 py-2 font-medium text-gray-500">Amount</th>
                        <th className="px-3 py-2 font-medium text-gray-500">Type</th>
                        <th className="px-3 py-2 font-medium text-gray-500">Channel</th>
                        <th className="px-3 py-2 font-medium text-gray-500">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {case_input.transactions.map((txn) => (
                        <tr key={txn.transaction_id}>
                          <td className="px-3 py-2 font-mono text-gray-600">{txn.transaction_id}</td>
                          <td className="px-3 py-2 font-semibold text-gray-900">
                            {txn.currency}{" "}
                            {txn.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </td>
                          <td className="px-3 py-2 text-gray-600">{txn.transaction_type}</td>
                          <td className="px-3 py-2 text-gray-600">{txn.channel}</td>
                          <td className="px-3 py-2 text-gray-500">
                            {new Date(txn.timestamp).toLocaleString("en-US", {
                              dateStyle: "short",
                              timeStyle: "short",
                            })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-gray-400 italic">No transactions attached.</p>
              )}
            </div>
            {case_input.customer_profile && (
              <div>
                <h4 className="mb-2 text-sm font-medium text-gray-700">Customer Profile</h4>
                <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm sm:grid-cols-3">
                  <Detail label="Name" value={case_input.customer_profile.name} />
                  <Detail label="ID" value={case_input.customer_profile.customer_id} />
                  <Detail label="Risk Rating" value={case_input.customer_profile.risk_rating} />
                  <Detail label="Email" value={case_input.customer_profile.email} />
                  <Detail label="Occupation" value={case_input.customer_profile.occupation} />
                  <Detail label="Nationality" value={case_input.customer_profile.nationality} />
                </div>
              </div>
            )}
            {case_input.alert_reason && (
              <div>
                <h4 className="mb-1 text-sm font-medium text-gray-700">Alert Reason</h4>
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  {case_input.alert_reason}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── 2. Context Intelligence ──────────────────────── */}
      <ContextPanel data={investigation.context_intelligence} />

      {/* ── 3. Investigation Reasoning ───────────────────── */}
      <ReasoningPanel data={investigation.investigation_reasoning} />

      {/* ── 4. Evidence & Compliance Validation ──────────── */}
      <CompliancePanel data={investigation.evidence_compliance_validation} />

      {/* ── 5. Decision Optimization ─────────────────────── */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
              <Scale className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-gray-900">Decision Optimization</h3>
          </div>
          <StatusBadge value={investigation.decision_optimization?.status ?? AgentStatus.NOT_STARTED} />
        </div>
        <div className="px-6 py-5">
          {investigation.decision_optimization?.decision_rationale ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-700">{investigation.decision_optimization.decision_rationale}</p>
              {investigation.decision_optimization.recommended_decision && (
                <div className="inline-flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-semibold text-blue-700">
                  Recommended: {investigation.decision_optimization.recommended_decision}
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400 italic">Decision analysis will appear here once the Decision Agent has run.</p>
          )}
        </div>
      </div>

      {/* ── 6. Investigation Report ──────────────────────── */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
              <ClipboardList className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-gray-900">Investigation Report</h3>
          </div>
          <StatusBadge value={investigation.investigation_report?.status ?? AgentStatus.NOT_STARTED} />
        </div>
        <div className="px-6 py-5">
          {investigation.investigation_report?.executive_summary ? (
            <div className="space-y-3">
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">Executive Summary</h4>
                <p className="text-sm text-gray-700">{investigation.investigation_report.executive_summary}</p>
              </div>
              {investigation.investigation_report.detailed_narrative && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">Detailed Narrative</h4>
                  <p className="text-sm text-gray-600">{investigation.investigation_report.detailed_narrative}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400 italic">The investigation report will appear here once the Reporting Agent has run.</p>
          )}
        </div>
      </div>

      {/* Errors section */}
      {investigation.errors && investigation.errors.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-4">
          <h3 className="mb-2 text-sm font-semibold text-red-800">Errors ({investigation.errors.length})</h3>
          <div className="space-y-2">
            {investigation.errors.map((err, idx) => (
              <div key={`${err.agent_name}-${idx}`} className="rounded-lg bg-white px-3 py-2 text-sm">
                <span className="font-medium text-red-700">{err.agent_name}</span>
                <span className="mx-1.5 text-gray-300">·</span>
                <span className="text-gray-600">{err.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Detail({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="py-1">
      <span className="text-gray-400">{label}: </span>
      <span className="text-gray-700">{value ?? "—"}</span>
    </div>
  );
}
