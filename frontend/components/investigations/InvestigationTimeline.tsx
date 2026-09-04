import { History } from "lucide-react";
import type { TimelineEvent } from "@/types";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatusBadge } from "@/components/investigations/StatusBadge";
import type { CurrentStage } from "@/types";

interface InvestigationTimelineProps {
  events?: TimelineEvent[];
}

export function InvestigationTimeline({ events = [] }: InvestigationTimelineProps) {
  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <History className="h-4 w-4 text-gray-500 dark:text-gray-400" />
        <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Investigation Timeline</h4>
      </div>

      {events.length === 0 ? (
        <EmptyState
          icon={History}
          title="No timeline data"
          description="No timestamped events are available for this investigation."
        />
      ) : (
        <ol className="space-y-3 border-l border-gray-200 pl-4 dark:border-gray-800">
          {events.map((event, index) => (
            <li key={`${event.event_name}-${index}`} className="relative">
              <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-gray-300 ring-2 ring-white" />
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-gray-800 dark:text-gray-100">{event.event_name}</span>
                {event.stage && <StatusBadge value={event.stage as CurrentStage} />}
              </div>
              <span className="text-xs text-gray-400 dark:text-gray-500">
                {new Date(event.timestamp).toLocaleString()}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
