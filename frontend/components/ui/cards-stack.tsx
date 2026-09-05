"use client";

import * as React from "react";
import { type HTMLMotionProps, motion } from "motion/react";

import { cn } from "@/lib/utils";

/**
 * Sticky stacking-card scroll interaction: a perspective container whose
 * children pin in place one after another as the page scrolls, each offset a
 * little further down and forward in z so the stack reads as layered case
 * files being reviewed in sequence. Used by the "How ARIA Works" section
 * (components/landing/LandingSections.tsx).
 */

const ContainerScroll = React.forwardRef<HTMLDivElement, React.HTMLProps<HTMLDivElement>>(
  ({ children, className, style, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("relative w-full", className)}
        style={{ perspective: "1200px", ...style }}
        {...props}
      >
        {children}
      </div>
    );
  },
);
ContainerScroll.displayName = "ContainerScroll";

interface CardStickyProps extends HTMLMotionProps<"div"> {
  index: number;
  /** Base sticky offset from the top of the viewport, in px. */
  topOffset?: number;
  /** Extra px of top offset added per index, so later cards sit lower. */
  incrementY?: number;
  /** Extra px of translateZ added per index, for the perspective depth cue. */
  incrementZ?: number;
}

const CardSticky = React.forwardRef<HTMLDivElement, CardStickyProps>(
  (
    { index, topOffset = 112, incrementY = 16, incrementZ = 10, children, className, style, ...props },
    ref,
  ) => {
    const top = topOffset + index * incrementY;
    const z = index * incrementZ;

    return (
      <motion.div
        ref={ref}
        style={{
          top,
          z,
          zIndex: index + 1,
          backfaceVisibility: "hidden",
          ...style,
        }}
        className={cn("sticky", className)}
        {...props}
      >
        {children}
      </motion.div>
    );
  },
);
CardSticky.displayName = "CardSticky";

export { ContainerScroll, CardSticky };
