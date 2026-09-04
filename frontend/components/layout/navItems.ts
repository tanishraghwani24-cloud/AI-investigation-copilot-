import { FileBarChart, FolderSearch, Inbox, Settings as SettingsIcon } from "lucide-react";
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
  { label: "Officer Inbox", href: "/officer", icon: Inbox },
  { label: "Investigations", href: "/investigations", icon: FolderSearch },
  { label: "Reports", href: "/reports", icon: FileBarChart },
  { label: "Settings", href: "#", icon: SettingsIcon },
];
