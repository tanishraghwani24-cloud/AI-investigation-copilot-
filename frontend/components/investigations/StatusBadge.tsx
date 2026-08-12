"use client";

import { cn } from "@/lib/utils";
import { AgentStatus, CurrentStage } from "@/types";

type BadgeValue = AgentStatus | CurrentStage;

interface StatusBadgeProps {
  value: BadgeValue;
  className?: string;
}

const statusStyles: Record<string, string> = {
  // AgentStatus
  [AgentStatus.NOT_STARTED]:
    "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  [AgentStatus.IN_PROGRESS]:
    "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  [AgentStatus.COMPLETED]:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  [AgentStatus.FAILED]:
    "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  // CurrentStage
  [CurrentStage.INTAKE]:
    "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  [CurrentStage.CONTEXT]:
    "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300",
  [CurrentStage.REASONING]:
    "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300",
  [CurrentStage.COMPLIANCE]:
    "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  [CurrentStage.DECISION]:
    "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  [CurrentStage.REPORTING]:
    "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
  [CurrentStage.DONE]:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
};

const displayLabels: Record<string, string> = {
  [AgentStatus.NOT_STARTED]: "Not Started",
  [AgentStatus.IN_PROGRESS]: "In Progress",
  [AgentStatus.COMPLETED]: "Completed",
  [AgentStatus.FAILED]: "Failed",
  [CurrentStage.INTAKE]: "Intake",
  [CurrentStage.CONTEXT]: "Context",
  [CurrentStage.REASONING]: "Reasoning",
  [CurrentStage.COMPLIANCE]: "Compliance",
  [CurrentStage.DECISION]: "Decision",
  [CurrentStage.REPORTING]: "Reporting",
  [CurrentStage.DONE]: "Done",
};

export function StatusBadge({ value, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide",
        statusStyles[value] ?? "bg-gray-100 text-gray-600",
        className,
      )}
    >
      {displayLabels[value] ?? value}
    </span>
  );
}
