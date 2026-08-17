import { Search } from "lucide-react";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { AgentStatus } from "@/types";
import type { ContextIntelligence } from "@/types";

interface ContextPanelProps {
  data?: ContextIntelligence | null;
}

export function ContextPanel({ data }: ContextPanelProps) {
  const status = data?.status ?? AgentStatus.NOT_STARTED;

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
            <Search className="h-5 w-5" />
          </div>
          <h3 className="text-base font-semibold text-gray-900">Context Intelligence</h3>
        </div>
        <StatusBadge value={status} />
      </div>
      <div className="px-6 py-5">
        {data?.context_summary ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">{data.context_summary}</p>
            {data.key_indicators && data.key_indicators.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Key Indicators
                </h4>
                <ul className="list-inside list-disc space-y-0.5 text-sm text-gray-600">
                  {data.key_indicators.map((ind) => (
                    <li key={ind}>{ind}</li>
                  ))}
                </ul>
              </div>
            )}
            {data.anomalies && data.anomalies.length > 0 && (
              <div className="mt-4">
                 <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Anomalies
                </h4>
                <ul className="list-inside list-disc space-y-0.5 text-sm text-gray-600">
                  {data.anomalies.map((anom) => (
                    <li key={anom.anomaly_id}>{anom.description} ({anom.severity})</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <EmptyState icon={Search} title="No context available" description="Context intelligence data has not been generated for this investigation." />
        )}
      </div>
    </div>
  );
}
