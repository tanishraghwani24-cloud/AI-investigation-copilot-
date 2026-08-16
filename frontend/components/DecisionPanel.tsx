import { Scale } from "lucide-react";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import { AgentStatus } from "@/types";
import type { DecisionOption, DecisionOptimization } from "@/types";

interface DecisionPanelProps {
  data?: DecisionOptimization | null;
}

function Percentage({ value }: { value?: number }) {
  return <span>{value === undefined ? "Not provided" : `${(value * 100).toFixed(0)}%`}</span>;
}

function ItemList({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h5 className="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</h5>
      <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-gray-600">
        {items.map((item, index) => <li key={`${label}-${index}`}>{item}</li>)}
      </ul>
    </div>
  );
}

function OptionCard({ option, recommended }: { option: DecisionOption; recommended: boolean }) {
  return (
    <article className={`rounded-lg border p-4 ${recommended ? "border-blue-400 bg-blue-50/50" : "border-gray-100"}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="font-semibold text-gray-900">{option.action}</h4>
        {recommended && <span className="rounded-full bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white">Recommended</span>}
      </div>
      <p className="mt-2 text-sm text-gray-700">{option.rationale}</p>
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500">
        <span>Confidence: <strong className="text-gray-700"><Percentage value={option.confidence} /></strong></span>
        <span>Risk score: <strong className="text-gray-700"><Percentage value={option.risk_score} /></strong></span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <ItemList label="Pros" items={option.pros ?? []} />
        <ItemList label="Cons" items={option.cons ?? []} />
        <ItemList label="Risks" items={option.risks ?? []} />
        <ItemList label="Mitigation" items={option.mitigation ?? []} />
      </div>
    </article>
  );
}

export function DecisionPanel({ data }: DecisionPanelProps) {
  const status = data?.status ?? AgentStatus.NOT_STARTED;
  const options = data?.decision_options ?? [];

  return (
    <section className="rounded-xl border border-gray-200 bg-white shadow-sm" aria-labelledby="decision-panel-title">
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600"><Scale className="h-5 w-5" /></div>
          <h3 id="decision-panel-title" className="text-base font-semibold text-gray-900">Decision Optimization</h3>
        </div>
        <StatusBadge value={status} />
      </div>
      <div className="space-y-4 px-6 py-5">
        {data?.decision_rationale && (
          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">Decision rationale</h4>
            <p className="text-sm text-gray-700">{data.decision_rationale}</p>
          </div>
        )}
        {data?.recommended_decision && (
          <div className="rounded-lg bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-700">
            Recommended action: {data.recommended_decision}
          </div>
        )}
        {options.length > 0 ? (
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Decision options</h4>
            {options.map((option) => (
              <OptionCard key={option.option_id} option={option} recommended={option.action === data?.recommended_decision} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400 italic">Decision options are not available yet.</p>
        )}
      </div>
    </section>
  );
}
