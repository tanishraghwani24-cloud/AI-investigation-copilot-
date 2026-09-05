import { ClipboardList, FileWarning, Download } from "lucide-react";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { StructuredNarrative } from "@/components/reports/StructuredNarrative";
import { EmptyState } from "@/components/ui/EmptyState";
import { AgentStatus } from "@/types";
import type { InvestigationReport } from "@/types";

// Always browser-initiated (plain <a> navigation), so this must go through
// the same-origin proxy — the backend's shared-secret header can't be
// attached to a direct anchor navigation. See services/api.ts.
const API_BASE = "/api/proxy";

interface ReportViewerProps {
  caseId: string;
  report?: InvestigationReport | null;
}

export function ReportViewer({ caseId, report }: ReportViewerProps) {
  const status = report?.status ?? AgentStatus.NOT_STARTED;

  return (
    <section className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-surface-dark" aria-labelledby="report-viewer-title">
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300"><ClipboardList className="h-5 w-5" /></div>
          <h3 id="report-viewer-title" className="text-base font-semibold text-gray-900 dark:text-white">Investigation Report</h3>
        </div>
        <StatusBadge value={status} />
      </div>
      <div className="space-y-6 px-6 py-5">
        {report?.executive_summary ? (
          <>
            <div>
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Executive summary</h4>
              <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-300">{report.executive_summary}</p>
            </div>
            {report.detailed_narrative && (
              <div>
                <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Detailed narrative</h4>
                <StructuredNarrative narrative={report.detailed_narrative} />
              </div>
            )}
            {report.generated_at && <p className="text-xs text-gray-400 dark:text-gray-500">Generated {new Date(report.generated_at).toLocaleString()}</p>}
            <div className="pt-2">
              <a
                href={`${API_BASE}/investigations/${encodeURIComponent(caseId)}/report/download`}
                download
                className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors shadow-sm dark:border-gray-800 dark:bg-surface-dark dark:text-gray-300 dark:hover:bg-gray-800/60"
              >
                <Download className="h-4 w-4" />
                Download Report
              </a>
            </div>
          </>
        ) : (
          <EmptyState
            icon={status === AgentStatus.FAILED ? FileWarning : ClipboardList}
            title={status === AgentStatus.FAILED ? "Report generation failed" : "No report available"}
            description={status === AgentStatus.FAILED ? "The report could not be generated due to an error." : "The investigation report has not been generated yet."}
          />
        )}
      </div>
    </section>
  );
}
