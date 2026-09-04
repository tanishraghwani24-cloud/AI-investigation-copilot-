"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { animate, useMotionValue } from "motion/react"
import * as motion from "motion/react-client"
import { cn } from "@/lib/utils"
import { THEME_STORAGE_KEY } from "@/components/ui/ThemeToggle"
import { NAV_ITEMS } from "@/components/layout/navItems"

const themes = {
  dark: {
    textActive: "text-white", textInactive: "text-[#6b6b6d] hover:text-zinc-400",
    iconColor: "text-white hover:text-zinc-300",
  },
  light: {
    textActive: "text-zinc-900", textInactive: "text-zinc-400 hover:text-zinc-600",
    iconColor: "text-zinc-700 hover:text-zinc-900",
  },
}

/**
 * This project keeps its own dark-mode system (a `dark` class on <html> plus
 * a localStorage flag — see ThemeToggle) rather than next-themes, so this
 * mirrors that mechanism instead of pulling in a second, disconnected
 * theme provider that wouldn't actually track the site's real theme.
 */
function useSiteTheme() {
  const [isDarkMode, setIsDarkMode] = useState(true)

  useEffect(() => {
    const root = document.documentElement
    setIsDarkMode(root.classList.contains("dark"))
    const observer = new MutationObserver(() => setIsDarkMode(root.classList.contains("dark")))
    observer.observe(root, { attributes: true, attributeFilter: ["class"] })
    return () => observer.disconnect()
  }, [])

  const toggleTheme = () => {
    const isDark = document.documentElement.classList.toggle("dark")
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, isDark ? "dark" : "light")
    } catch {
      // Storage can be unavailable (private browsing, blocked cookies).
    }
  }

  return { isDarkMode, toggleTheme }
}

function isRouteActive(pathname: string | null, href: string): boolean {
  if (!pathname || href === "#") return false
  return pathname === href || pathname.startsWith(`${href}/`)
}

function InnerButtonOverlay({ isOverlayActive, isDarkMode }: { isOverlayActive: boolean; isDarkMode: boolean }) {
  const overlayProgress = useMotionValue(isOverlayActive ? 1 : 0)
  useEffect(() => {
    const controls = animate(overlayProgress, isOverlayActive ? 1 : 0, { delay: isOverlayActive ? 0.02 : 0, duration: isOverlayActive ? 0.18 : 0.14, ease: "easeOut" })
    return () => controls.stop()
  }, [isOverlayActive, overlayProgress])

  return (
    <motion.span
      initial={false} className="absolute inset-0 rounded-[10px]"
      animate={isOverlayActive ? { borderWidth: 1, borderColor: isDarkMode ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)" } : { borderWidth: 0, borderColor: "transparent", boxShadow: "none" }}
      transition={{ borderColor: { duration: 0.16, ease: "easeOut" } }}
      style={{ borderStyle: "solid" }}
    />
  )
}

export default function GradientButtonGroup() {
  const pathname = usePathname()
  const { isDarkMode, toggleTheme } = useSiteTheme()
  const theme = isDarkMode ? themes.dark : themes.light

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex w-full justify-center py-1 sm:bottom-6">
      <div className="inline-flex min-w-max origin-center scale-[0.72] items-center sm:scale-[0.82] md:scale-[0.9] lg:scale-100">
        <div className="relative inline-flex items-center">
          <div
            className="absolute inset-0 z-0 rounded-[28px] transition-colors duration-300"
            style={{
              background: isDarkMode ? "linear-gradient(180deg, #141416 0%, #111113 50%, #0e0e10 100%)" : "linear-gradient(180deg, #d1d1d6 0%, #cacad0 50%, #c3c3c9 100%)",
              boxShadow: isDarkMode ? "inset 0 2px 8px rgba(0,0,0,0.6), inset 0 1px 2px rgba(0,0,0,0.4), 0 1px 0 rgba(255,255,255,0.04)" : "inset 0 2px 6px rgba(0,0,0,0.1), inset 0 0 0 1px rgba(0,0,0,0.08), 0 1px 0 rgba(255,255,255,0.55)",
            }}
          />
          <div className="relative flex z-10">
            <div className="absolute -inset-[4px] rounded-[28px] border-[1px] bg-muted dark:bg-background transition-colors duration-300" style={{ borderColor: isDarkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.08)" }} />
            <nav aria-label="Primary navigation"
              className="pointer-events-auto relative inline-flex items-center gap-3 rounded-[24px] p-1.5 transition-colors duration-300"
              style={{
                background: isDarkMode ? "linear-gradient(180deg, #1c1c1f 0%, #17171a 52%, #131316 100%)" : "linear-gradient(180deg, #ffffff 0%, #fefeff 52%, #fcfcfe 100%)",
                borderTop: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid rgba(255,255,255,1)",
                boxShadow: isDarkMode ? "none" : "0 1px 2px rgba(0,0,0,0.04), 0 1px 0 rgba(255,255,255,1)",
              }}
            >
              {NAV_ITEMS.map((item) => {
                const isActive = isRouteActive(pathname, item.href)
                const Icon = item.icon
                const isOverlayActive = isActive
                const wellStyle = isDarkMode ? { background: "linear-gradient(180deg, #0a0a0c 0%, #0e0e10 50%, #0c0c0e 100%)", boxShadow: "inset 0 2px 6px rgba(0,0,0,0.9), inset 0 0 4px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.05)" } : { boxShadow: "inset 0 2px 6px rgba(0,0,0,0.12), inset 0 0 4px rgba(0,0,0,0.06), 0 1px 0 rgba(255,255,255,0.9)" }
                const innerGapStyle = isDarkMode ? { background: "#0a0a0d", boxShadow: "inset 0 1px 3px rgba(0,0,0,0.9), inset 0 0 2px rgba(0,0,0,0.6)" } : { boxShadow: "inset 0 1px 3px rgba(0,0,0,0.18), inset 0 0 2px rgba(0,0,0,0.1)" }

                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    aria-label={item.label}
                    aria-current={isActive ? "page" : undefined}
                    title={item.label}
                    className={cn("group/nav relative flex h-[76px] w-[76px] items-center justify-center rounded-[18px] transition-all duration-300", isActive ? theme.textActive : theme.textInactive)}
                  >
                    {isActive && (
                      <>
                        <motion.span layoutId="active-well" className="absolute inset-0 bg-muted rounded-[18px] transition-colors duration-300" style={wellStyle} transition={{ type: "spring", stiffness: 400, damping: 30 }} />
                        <motion.span layoutId="active-purple-ring" className="absolute inset-[3px] overflow-hidden rounded-[15px]" transition={{ type: "spring", stiffness: 400, damping: 30 }}>
                          <span className="absolute inset-[-60%] origin-center will-change-transform animate-gold-spin" style={{ background: "conic-gradient(from 220deg, #a855f7 0%, #7c3aed 18%, #6366f1 36%, #c084fc 52%, #8b5cf6 70%, #a855f7 86%, #a855f7 100%)" }} />
                        </motion.span>
                        <motion.span layoutId="active-inner-ring" className="absolute inset-[6px] bg-muted rounded-[12px] transition-colors duration-300" style={innerGapStyle} transition={{ type: "spring", stiffness: 400, damping: 30 }} />
                      </>
                    )}
                    <motion.span initial={false} className={cn("relative z-10 flex items-center justify-center rounded-[10px]", isActive ? "h-[calc(100%-18px)] w-[calc(100%-18px)]" : "h-full w-full")} animate={isActive ? { scale: 1, opacity: 1 } : { scale: 0.985, opacity: 0.96 }} transition={{ type: "spring", stiffness: 380, damping: 30, delay: isActive ? 0.12 : 0 }}>
                      <InnerButtonOverlay isOverlayActive={isOverlayActive} isDarkMode={isDarkMode} />
                      <Icon className="relative z-10 h-6 w-6" strokeWidth={1.7} aria-hidden="true" />
                    </motion.span>
                  </Link>
                )
              })}
            </nav>
            <div className="pointer-events-auto relative z-[1] flex items-center px-4">
              <button type="button" onClick={toggleTheme} aria-label="Toggle dark mode" title="Toggle dark mode" className={cn("relative flex h-[60px] w-[60px] items-center justify-center rounded-[16px] transition-colors", theme.iconColor)}>
                {isDarkMode ? (
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" /></svg>
                ) : (
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
