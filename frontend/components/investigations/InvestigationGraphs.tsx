import { ChevronDown, Network, Scale, Waypoints } from "lucide-react";
import type { ReportGraphs } from "@/types";
import { RelationshipGraph } from "@/components/investigations/RelationshipGraph";
import { InvestigationTimeline } from "@/components/investigations/InvestigationTimeline";

interface InvestigationGraphsProps {
  graphs?: ReportGraphs | null;
}

/**
 * Report-level graph visualizations: entity/relationship graph and
 * timeline are the primary, always-visible views; the reasoning and
 * decision-comparison graphs share the same GraphData shape but are
 * secondary, so they live behind a collapsible <details> section to keep
 * this part of the page from crowding out the case findings above it.
 */
export function InvestigationGraphs({ graphs }: InvestigationGraphsProps) {
  const hasSecondaryGraphs = Boolean(
    graphs?.reasoning_graph?.nodes.length || graphs?.decision_comparison_graph?.nodes.length,
  );

  return (
    <section
      className="rounded-xl border border-gray-200 bg-white shadow-sm"
      aria-labelledby="investigation-graphs-title"
    >
      <div className="flex items-center gap-3 border-b border-gray-100 px-6 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
          <Network className="h-5 w-5" />
        </div>
        <h3 id="investigation-graphs-title" className="text-base font-semibold text-gray-900">
          Investigation Graphs
        </h3>
      </div>

      <div className="space-y-8 px-6 py-5">
        <RelationshipGraph
          title="Entity Relationship Graph"
          icon={Waypoints}
          data={graphs?.entity_relationship_graph}
          emptyMessage="No relationship data available for this investigation."
        />

        <div className="border-t border-gray-100 pt-6">
          <InvestigationTimeline events={graphs?.investigation_timeline} />
        </div>

        {hasSecondaryGraphs && (
          <details className="group border-t border-gray-100 pt-6">
            <summary className="flex cursor-pointer list-none items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900">
              <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
              Reasoning &amp; decision graphs
            </summary>
            <div className="mt-4 space-y-8">
              <RelationshipGraph
                title="Reasoning Graph"
                icon={Waypoints}
                data={graphs?.reasoning_graph}
                emptyMessage="No reasoning graph data available for this investigation."
              />
              <RelationshipGraph
                title="Decision Comparison Graph"
                icon={Scale}
                data={graphs?.decision_comparison_graph}
                emptyMessage="No decision comparison graph data available for this investigation."
              />
            </div>
          </details>
        )}
      </div>
    </section>
  );
}
