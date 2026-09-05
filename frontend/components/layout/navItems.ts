import { 
  LayoutDashboard,
  Search,
  ArrowLeftRight,
  Diamond,
  Hexagon,
  AlignJustify,
  CircleDot
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * Sidebar navigation entries.
 *
 * Shared by the desktop sidebar and the mobile drawer so the two can never
 * drift apart. Presentation only — no routing or data behaviour lives here.
 * Each item carries an icon so Officer Inbox / Investigations / Reports /
 * Settings read as distinct areas of one system, not four separate themes.
 */
export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Investigations", href: "/investigations", icon: Search },
  { label: "Transactions", href: "/officer", icon: ArrowLeftRight },
  { label: "Analytics", href: "#", icon: Diamond },
  { label: "Collaboration", href: "#", icon: Hexagon },
  { label: "Reports", href: "/reports", icon: AlignJustify },
  { label: "Audit Trail", href: "#", icon: CircleDot },
];
