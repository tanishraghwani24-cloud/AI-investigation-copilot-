import type { LucideIcon } from "lucide-react";
import { Waypoints } from "lucide-react";
import type { GraphData } from "@/types";
import { EmptyState } from "@/components/ui/EmptyState";

const VIEW_SIZE = 320;
const CENTER = VIEW_SIZE / 2;
const RADIUS = 108;
const NODE_RADIUS = 26;

const NODE_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  PERSON: { fill: "#eff6ff", stroke: "#3b82f6", text: "#1d4ed8" },
  MERCHANT: { fill: "#fff7ed", stroke: "#f97316", text: "#c2410c" },
  BENEFICIARY: { fill: "#fdf4ff", stroke: "#a855f7", text: "#7e22ce" },
  DEVICE: { fill: "#f0fdf4", stroke: "#22c55e", text: "#15803d" },
  EVIDENCE: { fill: "#f8fafc", stroke: "#64748b", text: "#334155" },
  HYPOTHESIS: { fill: "#eef2ff", stroke: "#6366f1", text: "#4338ca" },
  COMPLIANCE: { fill: "#fefce8", stroke: "#eab308", text: "#a16207" },
  DECISION: { fill: "#fef2f2", stroke: "#ef4444", text: "#b91c1c" },
};
const DEFAULT_COLOR = { fill: "#f9fafb", stroke: "#9ca3af", text: "#4b5563" };

function colorFor(nodeType: string) {
  return NODE_COLORS[nodeType.toUpperCase()] ?? DEFAULT_COLOR;
}

/** Deterministic circular layout — no fabricated positions, just placement. */
function layoutNodes(nodes: GraphData["nodes"]) {
  const n = nodes.length;
  return nodes.map((node, index) => {
    const angle = (2 * Math.PI * index) / n - Math.PI / 2;
    return {
      ...node,
      x: n === 1 ? CENTER : CENTER + RADIUS * Math.cos(angle),
      y: n === 1 ? CENTER : CENTER + RADIUS * Math.sin(angle),
    };
  });
}

function trimToEdge(x1: number, y1: number, x2: number, y2: number, r: number) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  return { x: x1 + (dx / dist) * r, y: y1 + (dy / dist) * r };
}

function truncateLabel(label: string, max = 14): string {
  return label.length > max ? `${label.slice(0, max - 1)}…` : label;
}

interface RelationshipGraphProps {
  title: string;
  icon?: LucideIcon;
  data?: GraphData | null;
  emptyMessage?: string;
}

export function RelationshipGraph({
  title,
  icon: Icon = Waypoints,
  data,
  emptyMessage = "No relationship data available for this investigation.",
}: RelationshipGraphProps) {
  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4 text-gray-500 dark:text-gray-400" />
        <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-100">{title}</h4>
      </div>

      {nodes.length === 0 ? (
        <EmptyState icon={Icon} title="No graph data" description={emptyMessage} />
      ) : (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
          <svg
            viewBox={`0 0 ${VIEW_SIZE} ${VIEW_SIZE}`}
            className="mx-auto h-auto w-full max-w-sm shrink-0"
            role="img"
            aria-label={`${title} diagram`}
          >
            <defs>
              <marker
                id={`arrow-${title.replace(/\s+/g, "-")}`}
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M0,0 L10,5 L0,10 z" fill="#9ca3af" />
              </marker>
            </defs>

            {(() => {
              const positioned = layoutNodes(nodes);
              const byId = new Map(positioned.map((node) => [node.node_id, node]));

              return (
                <>
                  {edges.map((edge, index) => {
                    const source = byId.get(edge.source);
                    const target = byId.get(edge.target);
                    if (!source || !target) return null;
                    const start = trimToEdge(source.x, source.y, target.x, target.y, NODE_RADIUS + 2);
                    const end = trimToEdge(target.x, target.y, source.x, source.y, NODE_RADIUS + 8);
                    const midX = (start.x + end.x) / 2;
                    const midY = (start.y + end.y) / 2;
                    return (
                      <g key={`${edge.source}-${edge.target}-${index}`}>
                        <line
                          x1={start.x}
                          y1={start.y}
                          x2={end.x}
                          y2={end.y}
                          stroke="#9ca3af"
                          strokeWidth={1.5}
                          markerEnd={`url(#arrow-${title.replace(/\s+/g, "-")})`}
                        />
                        {edge.relationship && (
                          <>
                            <rect
                              x={midX - edge.relationship.length * 2.6}
                              y={midY - 7}
                              width={edge.relationship.length * 5.2}
                              height={12}
                              fill="white"
                              opacity={0.9}
                            />
                            <text
                              x={midX}
                              y={midY + 2}
                              textAnchor="middle"
                              fontSize={8}
                              fill="#6b7280"
                            >
                              {edge.relationship}
                            </text>
                          </>
                        )}
                      </g>
                    );
                  })}

                  {positioned.map((node) => {
                    const color = colorFor(node.node_type);
                    return (
                      <g key={node.node_id}>
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={NODE_RADIUS}
                          fill={color.fill}
                          stroke={color.stroke}
                          strokeWidth={1.5}
                        />
                        <text
                          x={node.x}
                          y={node.y - 2}
                          textAnchor="middle"
                          fontSize={8.5}
                          fontWeight={600}
                          fill={color.text}
                        >
                          {truncateLabel(node.label)}
                        </text>
                        <text
                          x={node.x}
                          y={node.y + 10}
                          textAnchor="middle"
                          fontSize={7}
                          fill={color.text}
                          opacity={0.75}
                        >
                          {node.node_type}
                        </text>
                      </g>
                    );
                  })}
                </>
              );
            })()}
          </svg>

          <div className="flex-1 space-y-2">
            <div>
              <h5 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Nodes ({nodes.length})
              </h5>
              <ul className="mt-1 space-y-1">
                {nodes.map((node) => (
                  <li key={node.node_id} className="flex items-center gap-1.5 text-xs text-gray-600">
                    <span
                      className="inline-block h-2 w-2 rounded-full"
                      style={{ backgroundColor: colorFor(node.node_type).stroke }}
                    />
                    <span className="font-medium text-gray-800">{node.label}</span>
                    <span className="text-gray-400">({node.node_type})</span>
                  </li>
                ))}
              </ul>
            </div>
            {edges.length > 0 && (
              <div>
                <h5 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Relationships ({edges.length})
                </h5>
                <ul className="mt-1 space-y-1">
                  {edges.map((edge, index) => (
                    <li key={`${edge.source}-${edge.target}-${index}`} className="text-xs text-gray-600 dark:text-gray-300">
                      <span className="font-medium text-gray-800 dark:text-gray-100">{edge.source}</span>
                      {" → "}
                      <span className="font-medium text-gray-800 dark:text-gray-100">{edge.target}</span>
                      {edge.relationship && <span className="text-gray-400 dark:text-gray-500"> ({edge.relationship})</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
