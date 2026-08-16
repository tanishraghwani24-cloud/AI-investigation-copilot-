import Link from "next/link";
import { AlertTriangle, ArrowLeft, FileText } from "lucide-react";
import { ApiError, getInvestigationRequest } from "@/services/api";
import { ContextPanel } from "@/components/ContextPanel";
import { DecisionPanel } from "@/components/DecisionPanel";
import { DocumentUpload } from "@/components/DocumentUpload";
import { CompliancePanel } from "@/components/CompliancePanel";
import { ReasoningPanel } from "@/components/ReasoningPanel";
import { ReportViewer } from "@/components/ReportViewer";
import { RiskScoreBadge } from "@/components/investigations/RiskScoreBadge";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { CurrentStage } from "@/types";
import type { InvestigationState } from "@/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function InvestigationDetailPage({ params }: PageProps) {
  const { id } = await params;
  let decodedId = id;
  try {
    decodedId = decodeURIComponent(id);
  } catch {
    // Preserve the route value for a useful error message.
  }

  let investigation: InvestigationState | null = null;
  let errorMessage: string | null = null;
  try {
    investigation = await getInvestigationRequest(decodedId);
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 404) {
      errorMessage = `No investigation found with ID: ${decodedId}`;
    } else if (error instanceof Error) {
      errorMessage = error.message;
    } else {
      errorMessage = "An unexpected error occurred while fetching the investigation.";
    }
  }

  if (!investigation) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-4 h-12 w-12 text-amber-500" />
        <h2 className="text-lg font-semibold text-gray-900">Investigation Error</h2>
        <p className="mt-1 text-sm text-gray-500">{errorMessage ?? "Investigation data was incomplete."}</p>
        <Link href="/investigations" className="mt-6 text-sm font-medium text-blue-600 hover:text-blue-700">
          <ArrowLeft className="mr-1 inline h-4 w-4" /> Back to Investigations
        </Link>
      </div>
    );
  }

  const { case_input: caseInput } = investigation;
  const transactions = caseInput.transactions ?? [];
  const errors = investigation.errors ?? [];
  const hasErrors = errors.length > 0;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/investigations" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4" /> Back to Investigations
        </Link>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{investigation.case_id}</h1>
            <p className="mt-1 text-sm text-gray-500">
              {caseInput.customer_profile?.name ?? "Unknown Customer"}
              {caseInput.alert_reason && <span className="ml-2 text-gray-400">· {caseInput.alert_reason}</span>}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge value={investigation.current_stage} />
            <RiskScoreBadge score={investigation.context_intelligence?.risk_score} />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-6 text-xs text-gray-400">
          <span>Created {new Date(investigation.created_at).toLocaleString()}</span>
          <span>Updated {new Date(investigation.updated_at).toLocaleString()}</span>
          {hasErrors && <span className="text-red-500">{errors.length} error{errors.length === 1 ? "" : "s"}</span>}
        </div>
      </div>

      {hasErrors ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-4" role="alert">
          <h2 className="text-sm font-semibold text-red-800">Investigation processing failed</h2>
          <p className="mt-1 text-sm text-red-700">The results below may be incomplete. Review the recorded agent errors before retrying.</p>
        </div>
      ) : investigation.current_stage !== CurrentStage.DONE ? (
        <div className="rounded-xl border border-blue-200 bg-blue-50 px-6 py-4" role="status">
          <h2 className="text-sm font-semibold text-blue-800">Investigation processing</h2>
          <p className="mt-1 text-sm text-blue-700">The pipeline is currently at the {investigation.current_stage.toLowerCase()} stage. Results below may be incomplete.</p>
        </div>
      ) : null}

      <section className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center gap-3 border-b border-gray-100 px-6 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600"><FileText className="h-5 w-5" /></div>
          <h3 className="text-base font-semibold text-gray-900">Case Input</h3>
        </div>
        <div className="space-y-4 px-6 py-5">
          <div>
            <h4 className="mb-2 text-sm font-medium text-gray-700">Transactions ({transactions.length})</h4>
            {transactions.length > 0 ? (
              <div className="overflow-x-auto rounded-lg border border-gray-100">
                <table className="w-full text-left text-xs">
                  <thead><tr className="border-b border-gray-100 bg-gray-50/60"><th className="px-3 py-2">ID</th><th className="px-3 py-2">Amount</th><th className="px-3 py-2">Type</th><th className="px-3 py-2">Channel</th><th className="px-3 py-2">Timestamp</th></tr></thead>
                  <tbody className="divide-y divide-gray-50">
                    {transactions.map((transaction) => (
                      <tr key={transaction.transaction_id}>
                        <td className="px-3 py-2 font-mono text-gray-600">{transaction.transaction_id}</td>
                        <td className="px-3 py-2 font-semibold text-gray-900">{transaction.currency} {transaction.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}</td>
                        <td className="px-3 py-2 text-gray-600">{transaction.transaction_type}</td>
                        <td className="px-3 py-2 text-gray-600">{transaction.channel}</td>
                        <td className="px-3 py-2 text-gray-500">{new Date(transaction.timestamp).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <p className="text-sm italic text-gray-400">No transactions attached.</p>}
          </div>
          {caseInput.customer_profile && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-700">Customer Profile</h4>
              <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm sm:grid-cols-3">
                <Detail label="Name" value={caseInput.customer_profile.name} /><Detail label="ID" value={caseInput.customer_profile.customer_id} /><Detail label="Risk Rating" value={caseInput.customer_profile.risk_rating} /><Detail label="Email" value={caseInput.customer_profile.email} /><Detail label="Occupation" value={caseInput.customer_profile.occupation} /><Detail label="Nationality" value={caseInput.customer_profile.nationality} />
              </div>
            </div>
          )}
          {caseInput.alert_reason && <div><h4 className="mb-1 text-sm font-medium text-gray-700">Alert Reason</h4><p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">{caseInput.alert_reason}</p></div>}
        </div>
      </section>

      <ContextPanel data={investigation.context_intelligence} />
      <ReasoningPanel data={investigation.investigation_reasoning} />
      <CompliancePanel data={investigation.evidence_compliance_validation} />
      <DecisionPanel data={investigation.decision_optimization} />
      <ReportViewer report={investigation.investigation_report} />
      <DocumentUpload investigationId={investigation.case_id} />

      {hasErrors && (
        <section className="rounded-xl border border-red-200 bg-red-50 px-6 py-4">
          <h3 className="mb-2 text-sm font-semibold text-red-800">Errors ({errors.length})</h3>
          <div className="space-y-2">{errors.map((error, index) => <div key={`${error.agent_name}-${index}`} className="rounded-lg bg-white px-3 py-2 text-sm"><span className="font-medium text-red-700">{error.agent_name}</span><span className="mx-1.5 text-gray-300">·</span><span className="text-gray-600">{error.message}</span></div>)}</div>
        </section>
      )}
    </div>
  );
}

function Detail({ label, value }: { label: string; value?: string | null }) {
  return <div className="py-1"><span className="text-gray-400">{label}: </span><span className="text-gray-700">{value ?? "—"}</span></div>;
}
