"use client";

import { Moon, Sun } from "lucide-react";

/**
 * Light/dark theme switch.
 *
 * The theme is just a `dark` class on <html> (Tailwind's class strategy) plus a
 * localStorage entry, which the inline script in the root layout replays before
 * paint so a reload keeps the chosen theme without a flash.
 *
 * The icons are swapped by CSS (`dark:` variants) rather than React state, so
 * the button renders identically on the server and the client and there is no
 * hydration mismatch to work around.
 */
export const THEME_STORAGE_KEY = "aria-theme";

export function ThemeToggle() {
  const toggleTheme = () => {
    const isDark = document.documentElement.classList.toggle("dark");
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, isDark ? "dark" : "light");
    } catch {
      // Storage can be unavailable (private browsing, blocked cookies). The
      // toggle still works for this session; only persistence is lost.
    }
  };

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label="Toggle dark mode"
      title="Toggle dark mode"
      className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-transparent text-slate-400 transition-all duration-200 hover:border-purple-300/35 hover:bg-purple-500/15 hover:text-purple-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-300 sm:h-12 sm:w-12"
    >
      <Sun className="hidden h-5 w-5 dark:block" aria-hidden="true" />
      <Moon className="h-5 w-5 dark:hidden" aria-hidden="true" />
    </button>
  );
}
