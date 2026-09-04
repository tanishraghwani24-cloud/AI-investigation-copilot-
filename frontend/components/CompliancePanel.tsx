import { ShieldCheck } from "lucide-react";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { AgentStatus } from "@/types";
import type { EvidenceComplianceValidation } from "@/types";

interface CompliancePanelProps {
  data?: EvidenceComplianceValidation | null;
}

export function CompliancePanel({ data }: CompliancePanelProps) {
  const status = data?.status ?? AgentStatus.NOT_STARTED;

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">Evidence & Compliance Validation</h3>
        </div>
        <StatusBadge value={status} />
      </div>
      <div className="px-6 py-5">
        {data?.validation_summary ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-700 dark:text-gray-300">{data.validation_summary}</p>
            {data.compliance_mappings && data.compliance_mappings.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                  Compliance Mappings
                </h4>
                <div className="space-y-1.5">
                  {data.compliance_mappings.map((cm) => (
                    <div
                      key={cm.regulation_id}
                      className="flex flex-col gap-1 rounded-lg border border-gray-100 px-3 py-2 text-sm dark:border-gray-800"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700 font-medium dark:text-gray-300">{cm.regulation_name}</span>
                        <span
                          className={
                            cm.is_violated ? "font-semibold text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                          }
                        >
                          {cm.is_violated ? "Violated" : "Compliant"}
                        </span>
                      </div>

                      {cm.evidence_references && cm.evidence_references.length > 0 && (
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          <span className="font-semibold">Evidence:</span> {cm.evidence_references.join(", ")}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {data.evidence_gaps && data.evidence_gaps.length > 0 && (
              <div className="mt-4">
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                  Evidence Gaps
                </h4>
                <div className="text-xs text-red-500">
                  <span className="font-semibold">Gaps:</span> {data.evidence_gaps.join(", ")}
                </div>
              </div>
            )}
          </div>
        ) : (
          <EmptyState icon={ShieldCheck} title="No compliance findings" description="Compliance validation has not been performed for this investigation." />
        )}
      </div>
    </div>
  );
}
