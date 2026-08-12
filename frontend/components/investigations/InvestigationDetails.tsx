"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  FileText,
  Brain,
  Search,
  ShieldCheck,
  Scale,
  ClipboardList,
  AlertTriangle,
} from "lucide-react";
import { getInvestigation } from "@/services/investigationService";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { RiskScoreBadge } from "@/components/investigations/RiskScoreBadge";
import { AgentStatus } from "@/types";
import type { InvestigationState } from "@/types";

interface InvestigationDetailsProps {
  id: string;
}

/**
 * Placeholder section card used for each pipeline stage.
 * Displays a title, icon, agent status, and optional content.
 */
function SectionCard({
  title,
  icon: Icon,
  status,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  status?: AgentStatus;
  children?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
            <Icon className="h-5 w-5" />
          </div>
          <h3 className="text-base font-semibold text-gray-900">{title}</h3>
        </div>
        {status && <StatusBadge value={status} />}
      </div>
      <div className="px-6 py-5">{children}</div>
    </div>
  );
}

export function InvestigationDetails({ id }: InvestigationDetailsProps) {
  const [investigation, setInvestigation] =
    useState<InvestigationState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getInvestigation(id)
      .then(setInvestigation)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
      </div>
    );
  }

  if (error || !investigation) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-4 h-12 w-12 text-amber-500" />
        <h2 className="text-lg font-semibold text-gray-900">
          Investigation Not Found
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          {error ?? `No investigation found with ID: ${id}`}
        </p>
        <Link
          href="/investigations"
          className="mt-6 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
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
            <h1 className="text-2xl font-bold text-gray-900">
              {investigation.case_id}
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              {case_input.customer_profile?.name ?? "Unknown Customer"}
              {case_input.alert_reason && (
                <span className="ml-2 text-gray-400">
                  · {case_input.alert_reason}
                </span>
              )}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge value={investigation.current_stage} />
            <RiskScoreBadge
              score={investigation.context_intelligence?.risk_score}
            />
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
              {investigation.errors.length} error
              {investigation.errors.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {/* ── 1. Case Input ────────────────────────────────── */}
      <SectionCard title="Case Input" icon={FileText}>
        <div className="space-y-4">
          {/* Transactions summary */}
          <div>
            <h4 className="mb-2 text-sm font-medium text-gray-700">
              Transactions ({case_input.transactions.length})
            </h4>
            {case_input.transactions.length > 0 ? (
              <div className="overflow-x-auto rounded-lg border border-gray-100">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50/60">
                      <th className="px-3 py-2 font-medium text-gray-500">
                        ID
                      </th>
                      <th className="px-3 py-2 font-medium text-gray-500">
                        Amount
                      </th>
                      <th className="px-3 py-2 font-medium text-gray-500">
                        Type
                      </th>
                      <th className="px-3 py-2 font-medium text-gray-500">
                        Channel
                      </th>
                      <th className="px-3 py-2 font-medium text-gray-500">
                        Timestamp
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {case_input.transactions.map((txn) => (
                      <tr key={txn.transaction_id}>
                        <td className="px-3 py-2 font-mono text-gray-600">
                          {txn.transaction_id}
                        </td>
                        <td className="px-3 py-2 font-semibold text-gray-900">
                          {txn.currency}{" "}
                          {txn.amount.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                        <td className="px-3 py-2 text-gray-600">
                          {txn.transaction_type}
                        </td>
                        <td className="px-3 py-2 text-gray-600">
                          {txn.channel}
                        </td>
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
              <p className="text-sm text-gray-400 italic">
                No transactions attached.
              </p>
            )}
          </div>

          {/* Customer profile */}
          {case_input.customer_profile && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-700">
                Customer Profile
              </h4>
              <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm sm:grid-cols-3">
                <Detail
                  label="Name"
                  value={case_input.customer_profile.name}
                />
                <Detail
                  label="ID"
                  value={case_input.customer_profile.customer_id}
                />
                <Detail
                  label="Risk Rating"
                  value={case_input.customer_profile.risk_rating}
                />
                <Detail
                  label="Email"
                  value={case_input.customer_profile.email}
                />
                <Detail
                  label="Occupation"
                  value={case_input.customer_profile.occupation}
                />
                <Detail
                  label="Nationality"
                  value={case_input.customer_profile.nationality}
                />
              </div>
            </div>
          )}

          {/* Alert reason */}
          {case_input.alert_reason && (
            <div>
              <h4 className="mb-1 text-sm font-medium text-gray-700">
                Alert Reason
              </h4>
              <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
                {case_input.alert_reason}
              </p>
            </div>
          )}
        </div>
      </SectionCard>

      {/* ── 2. Context Intelligence ──────────────────────── */}
      <SectionCard
        title="Context Intelligence"
        icon={Search}
        status={
          investigation.context_intelligence?.status ??
          AgentStatus.NOT_STARTED
        }
      >
        {investigation.context_intelligence?.context_summary ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              {investigation.context_intelligence.context_summary}
            </p>
            {investigation.context_intelligence.key_indicators.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Key Indicators
                </h4>
                <ul className="list-inside list-disc space-y-0.5 text-sm text-gray-600">
                  {investigation.context_intelligence.key_indicators.map(
                    (ind) => (
                      <li key={ind}>{ind}</li>
                    ),
                  )}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <Placeholder text="Context intelligence data will appear here once the Context Agent has run." />
        )}
      </SectionCard>

      {/* ── 3. Investigation Reasoning ───────────────────── */}
      <SectionCard
        title="Investigation Reasoning"
        icon={Brain}
        status={
          investigation.investigation_reasoning?.status ??
          AgentStatus.NOT_STARTED
        }
      >
        {investigation.investigation_reasoning?.reasoning_summary ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              {investigation.investigation_reasoning.reasoning_summary}
            </p>
            {investigation.investigation_reasoning.hypotheses.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Hypotheses
                </h4>
                <div className="space-y-2">
                  {investigation.investigation_reasoning.hypotheses.map((h) => (
                    <div
                      key={h.hypothesis_id}
                      className="rounded-lg border border-gray-100 px-3 py-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-800">
                          {h.title}
                        </span>
                        <span className="text-xs font-semibold tabular-nums text-gray-500">
                          {(h.confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">
                        {h.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <Placeholder text="Reasoning analysis will appear here once the Reasoning Agent has run." />
        )}
      </SectionCard>

      {/* ── 4. Evidence & Compliance Validation ──────────── */}
      <SectionCard
        title="Evidence & Compliance Validation"
        icon={ShieldCheck}
        status={
          investigation.evidence_compliance_validation?.status ??
          AgentStatus.NOT_STARTED
        }
      >
        {investigation.evidence_compliance_validation?.validation_summary ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              {investigation.evidence_compliance_validation.validation_summary}
            </p>
            {investigation.evidence_compliance_validation.compliance_mappings
              .length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Compliance Mappings
                </h4>
                <div className="space-y-1.5">
                  {investigation.evidence_compliance_validation.compliance_mappings.map(
                    (cm) => (
                      <div
                        key={cm.regulation_id}
                        className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 text-sm"
                      >
                        <span className="text-gray-700">
                          {cm.regulation_name}
                        </span>
                        <span
                          className={
                            cm.is_violated
                              ? "font-semibold text-red-600"
                              : "text-emerald-600"
                          }
                        >
                          {cm.is_violated ? "Violated" : "Compliant"}
                        </span>
                      </div>
                    ),
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <Placeholder text="Compliance validation results will appear here once the Compliance Agent has run." />
        )}
      </SectionCard>

      {/* ── 5. Decision Optimization ─────────────────────── */}
      <SectionCard
        title="Decision Optimization"
        icon={Scale}
        status={
          investigation.decision_optimization?.status ??
          AgentStatus.NOT_STARTED
        }
      >
        {investigation.decision_optimization?.decision_rationale ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              {investigation.decision_optimization.decision_rationale}
            </p>
            {investigation.decision_optimization.recommended_decision && (
              <div className="inline-flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-semibold text-blue-700">
                Recommended:{" "}
                {investigation.decision_optimization.recommended_decision}
              </div>
            )}
          </div>
        ) : (
          <Placeholder text="Decision analysis will appear here once the Decision Agent has run." />
        )}
      </SectionCard>

      {/* ── 6. Investigation Report ──────────────────────── */}
      <SectionCard
        title="Investigation Report"
        icon={ClipboardList}
        status={
          investigation.investigation_report?.status ??
          AgentStatus.NOT_STARTED
        }
      >
        {investigation.investigation_report?.executive_summary ? (
          <div className="space-y-3">
            <div>
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Executive Summary
              </h4>
              <p className="text-sm text-gray-700">
                {investigation.investigation_report.executive_summary}
              </p>
            </div>
            {investigation.investigation_report.detailed_narrative && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Detailed Narrative
                </h4>
                <p className="text-sm text-gray-600">
                  {investigation.investigation_report.detailed_narrative}
                </p>
              </div>
            )}
          </div>
        ) : (
          <Placeholder text="The investigation report will appear here once the Reporting Agent has run." />
        )}
      </SectionCard>

      {/* Errors section (only shown if errors exist) */}
      {investigation.errors.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-4">
          <h3 className="mb-2 text-sm font-semibold text-red-800">
            Errors ({investigation.errors.length})
          </h3>
          <div className="space-y-2">
            {investigation.errors.map((err, idx) => (
              <div
                key={`${err.agent_name}-${idx}`}
                className="rounded-lg bg-white px-3 py-2 text-sm"
              >
                <span className="font-medium text-red-700">
                  {err.agent_name}
                </span>
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

/** Simple key-value detail row. */
function Detail({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="py-1">
      <span className="text-gray-400">{label}: </span>
      <span className="text-gray-700">{value ?? "—"}</span>
    </div>
  );
}

/** Placeholder message for sections that haven't been populated yet. */
function Placeholder({ text }: { text: string }) {
  return (
    <p className="text-sm text-gray-400 italic">{text}</p>
  );
}
