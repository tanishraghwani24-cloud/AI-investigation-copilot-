import type { LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  ClipboardList,
  Clock,
  Loader2,
  Search,
  ShieldCheck,
  Scale,
  XCircle,
} from "lucide-react";
import { AgentStatus, CurrentStage } from "@/types";
import type { AgentError, InvestigationState } from "@/types";
import { cn } from "@/lib/utils";

type StageKey = "context" | "reasoning" | "compliance" | "decision" | "reporting";

/** Visual status for a pipeline node. Distinct from AgentStatus: "running"
 * is inferred for stages the backend never marks IN_PROGRESS — see
 * deriveStageResults() below. */
type VisualStatus = "pending" | "running" | "completed" | "failed";

interface StageDef {
  key: StageKey;
  label: string;
  icon: LucideIcon;
}

interface StageResult {
  status: VisualStatus;
  errorMessage?: string;
}

const STAGES: StageDef[] = [
  { key: "context", label: "Context Intelligence", icon: Search },
  { key: "reasoning", label: "Investigation Reasoning", icon: Brain },
  { key: "compliance", label: "Evidence Compliance Validation", icon: ShieldCheck },
  { key: "decision", label: "Decision Optimization", icon: Scale },
  { key: "reporting", label: "Reporting", icon: ClipboardList },
];

const STATUS_CONFIG: Record<
  VisualStatus,
  { label: string; dot: string; ring: string; icon: LucideIcon; iconClass: string }
> = {
  pending: {
    label: "Pending",
    dot: "bg-gray-300",
    ring: "border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900",
    icon: Clock,
    iconClass: "text-gray-400 dark:text-gray-500",
  },
  running: {
    label: "Running",
    dot: "bg-blue-500 animate-pulse",
    ring: "border-blue-300 bg-blue-50 dark:bg-blue-900/30",
    icon: Loader2,
    iconClass: "text-blue-600 animate-spin dark:text-blue-400",
  },
  completed: {
    label: "Completed",
    dot: "bg-emerald-500",
    ring: "border-emerald-300 bg-emerald-50 dark:bg-emerald-900/30",
    icon: CheckCircle2,
    iconClass: "text-emerald-600",
  },
  failed: {
    label: "Failed",
    dot: "bg-red-500",
    ring: "border-red-300 bg-red-50 dark:bg-red-900/30",
    icon: XCircle,
    iconClass: "text-red-600 dark:text-red-400",
  },
};

/**
 * Derive each stage's visual status strictly from data already present on
 * InvestigationState — never fabricated.
 *
 * Rules (see the P1 audit for the backend behavior this mirrors):
 * - A stage with its own `status: FAILED`, or a recorded AgentError whose
 *   `agent_name` matches the stage, is "failed".
 * - A stage with `status: COMPLETED` is "completed".
 * - A stage with `status: IN_PROGRESS` is "running" (backend sets this
 *   explicitly only for Context at kickoff — see
 *   investigation_service.start_investigation).
 * - Otherwise the stage has no output yet. Because this is a fixed linear
 *   pipeline where exactly one stage executes at a time, the stage
 *   immediately after the last *completed* stage is inferred "running"
 *   (only once the run has actually started and hasn't finished/failed).
 *   Every other not-yet-reached stage is "pending".
 */
function deriveStageResults(investigation: InvestigationState): Record<StageKey, StageResult> {
  const dataByKey: Record<StageKey, { status: AgentStatus } | null | undefined> = {
    context: investigation.context_intelligence,
    reasoning: investigation.investigation_reasoning,
    compliance: investigation.evidence_compliance_validation,
    decision: investigation.decision_optimization,
    reporting: investigation.investigation_report,
  };

  // AgentError.agent_name is set from the backend's lowercase node
  // constants ("context", "reasoning", ...) — see
  // backend/app/graph/workflow.py (_identify_failed_node) and
  // backend/app/graph/builder.py (CONTEXT/REASONING/... constants).
  const errorByKey = new Map<StageKey, AgentError>();
  for (const error of investigation.errors ?? []) {
    const key = error.agent_name as StageKey;
    if (!errorByKey.has(key)) errorByKey.set(key, error);
  }

  const pipelineStarted = investigation.current_stage !== CurrentStage.INTAKE;
  const pipelineFinished = investigation.current_stage === CurrentStage.DONE;

  const results = {} as Record<StageKey, StageResult>;
  // Context can only be inferred "running" once a run has actually been
  // triggered — otherwise a freshly created, never-run case would show its
  // first stage as running.
  let previousCompleted = pipelineStarted;

  for (const stage of STAGES) {
    const data = dataByKey[stage.key];
    const error = errorByKey.get(stage.key);

    if (data?.status === AgentStatus.FAILED || error) {
      results[stage.key] = { status: "failed", errorMessage: error?.message };
      previousCompleted = false;
      continue;
    }
    if (data?.status === AgentStatus.COMPLETED) {
      results[stage.key] = { status: "completed" };
      previousCompleted = true;
      continue;
    }
    if (data?.status === AgentStatus.IN_PROGRESS) {
      results[stage.key] = { status: "running" };
      previousCompleted = false;
      continue;
    }
    if (previousCompleted && !pipelineFinished) {
      results[stage.key] = { status: "running" };
      previousCompleted = false;
    } else {
      results[stage.key] = { status: "pending" };
    }
  }

  return results;
}

function StageNode({
  stage,
  result,
  isLast,
}: {
  stage: { label: string; icon: LucideIcon };
  result: StageResult;
  isLast: boolean;
}) {
  const config = STATUS_CONFIG[result.status];
  const StatusIcon = config.icon;
  const StageIcon = stage.icon;

  return (
    <div className="flex flex-1 flex-col items-stretch md:flex-row md:items-center">
      <div
        className={cn(
          "flex flex-1 items-center gap-3 rounded-lg border px-3 py-2.5 transition-colors duration-300",
          config.ring,
        )}
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-gray-500 shadow-sm dark:bg-gray-900 dark:text-gray-400">
          <StageIcon className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-gray-900 dark:text-white">{stage.label}</p>
          <div className="mt-0.5 flex items-center gap-1.5">
            <StatusIcon className={cn("h-3.5 w-3.5", config.iconClass)} />
            <span className="text-xs font-medium text-gray-600 dark:text-gray-300">{config.label}</span>
          </div>
          {result.status === "failed" && result.errorMessage && (
            <p className="mt-1 text-xs text-red-700 dark:text-red-300" title={result.errorMessage}>
              {result.errorMessage}
            </p>
          )}
        </div>
      </div>

      {!isLast && (
        <>
          {/* Vertical connector (stacked layout) */}
          <div className="flex h-5 items-center justify-center md:hidden">
            <div
              className={cn(
                "h-full w-px transition-colors duration-300",
                result.status === "failed" ? "bg-red-200" : result.status === "completed" ? "bg-emerald-300" : "bg-gray-200 dark:bg-gray-700",
              )}
            />
          </div>
          {/* Horizontal connector (row layout) */}
          <div className="hidden shrink-0 items-center px-1 md:flex">
            <div
              className={cn(
                "h-px w-4 transition-colors duration-300 lg:w-6",
                result.status === "completed" ? "bg-emerald-300" : "bg-gray-200 dark:bg-gray-700",
              )}
            />
          </div>
        </>
      )}
    </div>
  );
}

interface InvestigationPipelineProps {
  investigation: InvestigationState;
}

export function InvestigationPipeline({ investigation }: InvestigationPipelineProps) {
  const stageResults = deriveStageResults(investigation);

  return (
    <section
      className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900"
      aria-labelledby="investigation-pipeline-title"
    >
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <h3 id="investigation-pipeline-title" className="text-base font-semibold text-gray-900 dark:text-white">
            Investigation Execution
          </h3>
        </div>
        <div className="hidden items-center gap-3 sm:flex">
          {(Object.keys(STATUS_CONFIG) as VisualStatus[]).map((key) => (
            <div key={key} className="flex items-center gap-1.5">
              <span className={cn("h-2 w-2 rounded-full", STATUS_CONFIG[key].dot)} />
              <span className="text-xs text-gray-500 dark:text-gray-400">{STATUS_CONFIG[key].label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="px-6 py-5">
        <div className="flex flex-col md:flex-row md:items-center">
          {/* Alert / Intake — always satisfied once a case exists (case_input
              is a required field on a persisted InvestigationState). */}
          <StageNode
            stage={{ label: "Alert / Intake", icon: AlertTriangle }}
            result={{ status: "completed" }}
            isLast={false}
          />
          {STAGES.map((stage, index) => (
            <StageNode
              key={stage.key}
              stage={stage}
              result={stageResults[stage.key]}
              isLast={index === STAGES.length - 1}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
