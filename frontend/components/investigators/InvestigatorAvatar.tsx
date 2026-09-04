"use client";

import type { Investigator } from "@/types";

/**
 * Circular avatar showing an investigator's initial, with their full name on
 * hover — the Google-Sheets-style presence cue.
 *
 * The letter is whatever the backend derived from the authenticated account, so
 * nothing here is hardcoded to a particular officer.
 *
 * `InvestigatorAvatarGroup` takes a list so the same component covers both the
 * single-investigator case used today and several investigators later, without
 * adding UI that is not needed yet.
 */

const SIZES = {
  sm: "h-6 w-6 text-[11px]",
  md: "h-7 w-7 text-xs",
} as const;

// Stable per-person colour: the same investigator always gets the same tint,
// derived from their id so no palette assignment has to be stored.
const PALETTE = [
  "bg-blue-600",
  "bg-emerald-600",
  "bg-violet-600",
  "bg-amber-600",
  "bg-rose-600",
  "bg-cyan-700",
];

function colourFor(userId: string): string {
  let hash = 0;
  for (let i = 0; i < userId.length; i += 1) {
    hash = (hash + userId.charCodeAt(i)) % PALETTE.length;
  }
  return PALETTE[hash];
}

interface InvestigatorAvatarProps {
  investigator: Investigator;
  size?: keyof typeof SIZES;
  /** Describes why the avatar is shown, e.g. "is working on this case". */
  context?: string;
}

export function InvestigatorAvatar({
  investigator,
  size = "sm",
  context,
}: InvestigatorAvatarProps) {
  const label = context
    ? `${investigator.full_name} ${context}`
    : investigator.full_name;

  return (
    <span className="group/avatar relative inline-flex">
      <span
        className={`inline-flex items-center justify-center rounded-full font-semibold text-white ring-2 ring-white dark:ring-gray-900 ${SIZES[size]} ${colourFor(investigator.user_id)}`}
        // title gives native hover text plus a screen-reader-friendly fallback
        // everywhere the styled tooltip cannot reach (e.g. touch devices).
        title={label}
        aria-label={label}
        role="img"
      >
        {investigator.initial}
      </span>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-20 mt-1.5 -translate-x-1/2 whitespace-nowrap rounded-md bg-gray-900 px-2 py-1 text-xs font-medium text-white opacity-0 shadow-lg transition-opacity duration-100 group-hover/avatar:opacity-100 dark:bg-gray-700"
      >
        {label}
      </span>
    </span>
  );
}

interface InvestigatorAvatarGroupProps {
  investigators: Investigator[];
  size?: keyof typeof SIZES;
  context?: string;
  /** Rendered when nobody is present; omit to render nothing at all. */
  fallback?: React.ReactNode;
  max?: number;
}

export function InvestigatorAvatarGroup({
  investigators,
  size = "sm",
  context,
  fallback = null,
  max = 3,
}: InvestigatorAvatarGroupProps) {
  if (investigators.length === 0) return <>{fallback}</>;

  const shown = investigators.slice(0, max);
  const overflow = investigators.length - shown.length;

  return (
    <span className="inline-flex items-center -space-x-1.5">
      {shown.map((investigator) => (
        <InvestigatorAvatar
          key={investigator.user_id}
          investigator={investigator}
          size={size}
          context={context}
        />
      ))}
      {overflow > 0 && (
        <span
          className={`inline-flex items-center justify-center rounded-full bg-gray-500 font-semibold text-white ring-2 ring-white dark:ring-gray-900 ${SIZES[size]}`}
          title={investigators
            .slice(max)
            .map((i) => i.full_name)
            .join(", ")}
        >
          +{overflow}
        </span>
      )}
    </span>
  );
}
