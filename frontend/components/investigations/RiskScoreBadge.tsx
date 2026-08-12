"use client";

import { cn } from "@/lib/utils";

interface RiskScoreBadgeProps {
  score?: number;
  className?: string;
}

function getRiskConfig(score: number): { label: string; style: string } {
  if (score >= 0.7) {
    return {
      label: "High",
      style: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
    };
  }
  if (score >= 0.4) {
    return {
      label: "Medium",
      style:
        "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
    };
  }
  return {
    label: "Low",
    style:
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  };
}

export function RiskScoreBadge({ score, className }: RiskScoreBadgeProps) {
  if (score === undefined || score === null) {
    return (
      <span
        className={cn(
          "inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-semibold text-gray-500 dark:bg-gray-800 dark:text-gray-400",
          className,
        )}
      >
        N/A
      </span>
    );
  }

  const { label, style } = getRiskConfig(score);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        style,
        className,
      )}
    >
      <span className="tabular-nums">{(score * 100).toFixed(0)}%</span>
      <span className="opacity-70">·</span>
      <span>{label}</span>
    </span>
  );
}
