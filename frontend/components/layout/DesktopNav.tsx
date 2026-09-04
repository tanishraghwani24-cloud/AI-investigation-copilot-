"use client";

import { NAV_ITEMS } from "@/components/layout/navItems";
import { SidebarNavLink } from "@/components/layout/SidebarNavLink";

/**
 * The desktop sidebar's nav list. Kept as its own Client Component (like
 * MobileNav) so the icon-bearing NAV_ITEMS never cross the server/client
 * boundary as a prop from the Server Component `app/layout.tsx` — React
 * cannot serialize a function (a component reference) passed that way.
 */
export function DesktopNav() {
  return (
    <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
      {NAV_ITEMS.map((item) => (
        <SidebarNavLink key={item.label} item={item} />
      ))}
    </nav>
  );
}
