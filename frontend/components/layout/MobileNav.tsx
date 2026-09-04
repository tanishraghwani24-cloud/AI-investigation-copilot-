"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { NAV_ITEMS } from "@/components/layout/navItems";
import { SidebarNavLink } from "@/components/layout/SidebarNavLink";

/**
 * The sidebar, collapsed for narrow viewports.
 *
 * Below the `md` breakpoint the desktop sidebar is hidden and this hamburger
 * takes its place, opening the same links in a slide-over drawer. Navigation
 * targets are unchanged — this is purely how they are presented on small
 * screens.
 */
export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <div className="md:hidden">
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open navigation menu"
        aria-expanded={open}
        className="inline-flex h-9 w-9 items-center justify-center rounded-md text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
      >
        <Menu className="h-5 w-5" aria-hidden="true" />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Close navigation menu"
            onClick={() => setOpen(false)}
            className="absolute inset-0 h-full w-full bg-gray-900/50 backdrop-blur-[1px]"
          />

          <div className="absolute inset-y-0 left-0 flex w-64 max-w-[80%] flex-col border-r border-gray-200 bg-white shadow-xl dark:border-gray-800 dark:bg-gray-900">
            <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4 dark:border-gray-800">
              <Link
                href="/"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
              >
                <img src="/aria-logo2.png" alt="ARIA logo" className="h-8 w-auto" />
                ARIA
              </Link>

              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close navigation menu"
                className="inline-flex h-8 w-8 items-center justify-center rounded-md text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>

            <nav className="flex-1 space-y-1.5 overflow-y-auto p-4">
              {NAV_ITEMS.map((item) => (
                <SidebarNavLink key={item.label} item={item} onNavigate={() => setOpen(false)} />
              ))}
            </nav>
          </div>
        </div>
      )}
    </div>
  );
}
