import { ClipboardList, FileWarning } from "lucide-react";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { AgentStatus } from "@/types";
import type { InvestigationReport } from "@/types";

interface ReportViewerProps {
  report?: InvestigationReport | null;
}

export function ReportViewer({ report }: ReportViewerProps) {
  const status = report?.status ?? AgentStatus.NOT_STARTED;

  return (
    <section className="rounded-xl border border-gray-200 bg-white shadow-sm" aria-labelledby="report-viewer-title">
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600"><ClipboardList className="h-5 w-5" /></div>
          <h3 id="report-viewer-title" className="text-base font-semibold text-gray-900">Investigation Report</h3>
        </div>
        <StatusBadge value={status} />
      </div>
      <div className="space-y-4 px-6 py-5">
        {report?.executive_summary ? (
          <>
            <div>
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">Executive summary</h4>
              <p className="text-sm text-gray-700">{report.executive_summary}</p>
            </div>
            {report.detailed_narrative && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">Detailed narrative</h4>
                <p className="text-sm text-gray-600">{report.detailed_narrative}</p>
              </div>
            )}
            {report.generated_at && <p className="text-xs text-gray-400">Generated {new Date(report.generated_at).toLocaleString()}</p>}
            <p className="text-sm text-gray-500">The backend has not supplied a downloadable report reference.</p>
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
