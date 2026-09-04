"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { NavItem } from "@/components/layout/navItems";

/**
 * "Settings" has no page yet (href is "#"), so it never matches a route —
 * that mirrors current reality rather than inventing a fake destination.
 * Everything else matches its own route and any nested route beneath it
 * (e.g. `/investigations/CASE-104` keeps "Investigations" illuminated).
 */
function isRouteActive(pathname: string | null, href: string): boolean {
  if (!pathname || href === "#") return false;
  return pathname === href || pathname.startsWith(`${href}/`);
}

interface SidebarNavLinkProps {
  item: NavItem;
  onNavigate?: () => void;
}

/**
 * One entry in ARIA's navigation — shared by the desktop sidebar and the
 * mobile drawer so both stay visually and behaviorally identical. The active
 * treatment reuses the same purple/blue-purple glow as the hero's MagicRings
 * background (#a855f7 / #6366f1), rendered as a restrained illuminated
 * border rather than the bright green of the Cult UI reference it was
 * inspired by.
 */
export function SidebarNavLink({ item, onNavigate }: SidebarNavLinkProps) {
  const pathname = usePathname();
  const active = isRouteActive(pathname, item.href);
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-2.5 rounded-lg border px-3.5 py-2.5 text-sm font-medium transition-all duration-300",
        active
          ? "border-purple-400/60 bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-transparent text-gray-900 shadow-[0_0_0_1px_rgba(168,85,247,0.15),0_0_18px_-4px_rgba(139,92,246,0.55)] dark:border-purple-500/50 dark:text-white dark:shadow-[0_0_0_1px_rgba(168,85,247,0.2),0_0_20px_-4px_rgba(139,92,246,0.6)]"
          : "border-transparent text-gray-700 hover:border-gray-200 hover:bg-gray-100 dark:text-gray-300 dark:hover:border-gray-700 dark:hover:bg-gray-800/60",
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0 transition-colors",
          active
            ? "text-purple-600 dark:text-purple-400"
            : "text-gray-400 group-hover:text-gray-600 dark:text-gray-500 dark:group-hover:text-gray-300",
        )}
        strokeWidth={2}
        aria-hidden="true"
      />
      {item.label}
    </Link>
  );
}
