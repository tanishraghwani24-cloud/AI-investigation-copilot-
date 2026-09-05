"use client";

import { Fragment, type ReactNode } from "react";
import { motion } from "motion/react";

/**
 * Scroll-triggered reveal primitives for the landing page.
 *
 * These are prop factories rather than wrapper components so a heading can
 * *become* the animated element (`<motion.h2 {...blurIn()} />`) instead of
 * gaining an extra wrapper div — no added DOM, no margin-collapsing surprises,
 * and no layout shift, since every effect animates only opacity / transform /
 * filter / clip-path.
 *
 * Reduced motion is handled in CSS rather than with `useReducedMotion()`: that
 * hook reads the media query during render, so it returns null on the server
 * and true on the client, which both mismatches hydration and leaves the SSR'd
 * text at opacity 0 until hydration. The `data-reveal` marker below pairs with
 * a `prefers-reduced-motion` block in globals.css that pins these elements to
 * their finished state, before any JS runs.
 */

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];
const VIEWPORT = { once: true, amount: 0.3 } as const;

/**
 * `data-reveal` is the hook for the two globals.css rules that back these
 * effects: the reduced-motion override, and the `.reveal-ready` pre-hide that
 * stops revealed text flashing visible before hydration.
 *
 * `suppressHydrationWarning` covers a deliberate mismatch: Next's prerender
 * does not emit Motion's `initial` styles into the static HTML (plain
 * `renderToString` does, so this is specific to the prerender path), but the
 * client applies them on mount. React would flag the resulting style-attribute
 * difference; it is expected here, and the `.reveal-ready` rule means the
 * painted result is identical either way.
 */
const MARKER = { "data-reveal": "", suppressHydrationWarning: true };

/** Fade + slide up. The workhorse: headings, cards, list rows. */
export function revealUp(delay = 0) {
  return {
    ...MARKER,
    initial: { opacity: 0, y: 24 },
    whileInView: { opacity: 1, y: 0 },
    viewport: VIEWPORT,
    transition: { duration: 0.82, ease: EASE, delay },
  };
}

/** Fade + slide in from the side, for two-column / paired content. */
export function revealFrom(direction: "left" | "right", delay = 0) {
  return {
    ...MARKER,
    initial: { opacity: 0, x: direction === "left" ? -28 : 28 },
    whileInView: { opacity: 1, x: 0 },
    viewport: VIEWPORT,
    transition: { duration: 0.82, ease: EASE, delay },
  };
}

/** Blur-in to sharp focus, for section titles. */
export function blurIn(delay = 0) {
  return {
    ...MARKER,
    initial: { opacity: 0, filter: "blur(10px)", y: 10 },
    whileInView: { opacity: 1, filter: "blur(0px)", y: 0 },
    viewport: VIEWPORT,
    transition: { duration: 0.95, ease: EASE, delay },
  };
}

/** Subtle scale-in, for standalone callout / stat text. */
export function scaleIn(delay = 0) {
  return {
    ...MARKER,
    initial: { opacity: 0, scale: 0.94 },
    whileInView: { opacity: 1, scale: 1 },
    viewport: VIEWPORT,
    transition: { duration: 0.78, ease: EASE, delay },
  };
}

/** Clip-path wipe (left to right), for eyebrow labels and short tags. */
export function wipeIn(delay = 0) {
  return {
    ...MARKER,
    initial: { opacity: 0, clipPath: "inset(0 100% 0 0)" },
    whileInView: { opacity: 1, clipPath: "inset(0 0% 0 0)" },
    viewport: VIEWPORT,
    transition: { duration: 0.88, ease: EASE, delay },
  };
}

/** Stagger offset for a list index, capped so late items never feel laggy. */
export function stagger(index: number) {
  return Math.min(index * 0.09, 0.54);
}

/**
 * Word-by-word reveal for longer paragraph copy. Spaces are real text nodes
 * *between* the inline-block words, so the paragraph still wraps naturally at
 * every breakpoint and reads as one uninterrupted sentence to a screen reader.
 */
export function WordsReveal({
  text,
  className,
  delay = 0,
}: {
  text: string;
  className?: string;
  delay?: number;
}) {
  const words = text.split(" ");

  return (
    <p className={className}>
      {words.map((word, index) => (
        <Fragment key={`${word}-${index}`}>
          <motion.span
            {...MARKER}
            className="inline-block"
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={VIEWPORT}
            transition={{
              duration: 0.68,
              ease: EASE,
              delay: delay + index * 0.028,
            }}
          >
            {word}
          </motion.span>
          {index < words.length - 1 ? " " : null}
        </Fragment>
      ))}
    </p>
  );
}

/**
 * Wrapper form of the same effects, for the few places that need to animate
 * content coming from a Server Component (which cannot spread motion props
 * itself).
 */
export function Reveal({
  children,
  className,
  variant = "up",
  delay = 0,
  as = "div",
}: {
  children: ReactNode;
  className?: string;
  variant?: "up" | "scale" | "blur";
  delay?: number;
  as?: "div" | "p";
}) {
  const props =
    variant === "scale" ? scaleIn(delay) : variant === "blur" ? blurIn(delay) : revealUp(delay);
  const Tag = as === "p" ? motion.p : motion.div;

  return (
    <Tag className={className} {...props}>
      {children}
    </Tag>
  );
}
