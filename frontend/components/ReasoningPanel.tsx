import { Brain } from "lucide-react";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { AgentStatus } from "@/types";
import type { InvestigationReasoning } from "@/types";

interface ReasoningPanelProps {
  data?: InvestigationReasoning | null;
}

export function ReasoningPanel({ data }: ReasoningPanelProps) {
  const status = data?.status ?? AgentStatus.NOT_STARTED;

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
            <Brain className="h-5 w-5" />
          </div>
          <h3 className="text-base font-semibold text-gray-900">Investigation Reasoning</h3>
        </div>
        <StatusBadge value={status} />
      </div>
      <div className="px-6 py-5">
        {data?.reasoning_summary ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">{data.reasoning_summary}</p>
            {data.hypotheses && data.hypotheses.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Hypotheses
                </h4>
                <div className="space-y-2">
                  {data.hypotheses.map((h) => (
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
                      <p className="mt-1 text-xs text-gray-500">{h.description}</p>

                      {h.supporting_evidence && h.supporting_evidence.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs font-semibold text-gray-500">Supporting Evidence:</span>
                          <ul className="list-inside list-disc text-xs text-emerald-700">
                            {h.supporting_evidence.map((ev, i) => <li key={i}>{ev}</li>)}
                          </ul>
                        </div>
                      )}

                      {h.contradicting_evidence && h.contradicting_evidence.length > 0 && (
                        <div className="mt-1">
                          <span className="text-xs font-semibold text-gray-500">Contradicting Evidence:</span>
                          <ul className="list-inside list-disc text-xs text-amber-700">
                            {h.contradicting_evidence.map((ev, i) => <li key={i}>{ev}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <EmptyState icon={Brain} title="No reasoning available" description="The investigation reasoning and hypotheses have not been generated yet." />
        )}
      </div>
    </div>
  );
}
