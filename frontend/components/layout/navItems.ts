/**
 * Sidebar navigation entries.
 *
 * Shared by the desktop sidebar and the mobile drawer so the two can never
 * drift apart. Presentation only — no routing or data behaviour lives here.
 */
export interface NavItem {
  label: string;
  href: string;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Officer Inbox", href: "/officer" },
  { label: "Investigations", href: "/investigations" },
  { label: "Reports", href: "/reports" },
  { label: "Settings", href: "#" },
];
