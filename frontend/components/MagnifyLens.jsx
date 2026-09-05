"use client";

import React, { useRef, useState, useCallback, useEffect } from "react";

// Tune these
const LENS_RADIUS = 50;
const ZOOM_SCALE = 1.28;
const BULGE_AMPLITUDE = 9;
const BULGE_SIGMA = LENS_RADIUS * 0.55;
const HANDLE_ANGLE = 42;
const HANDLE_LENGTH = 35;
const HANDLE_WIDTH = 12;
const RIM_BORDER = 5;

export default function MagnifyLens() {
    const containerRef = useRef(null);
    const [pos, setPos] = useState({ x: 140, y: 40 });
    const [dragging, setDragging] = useState(false);

    const clampToContainer = useCallback((x, y) => {
        const el = containerRef.current;
        if (!el) return { x, y };
        const rect = el.getBoundingClientRect();
        return {
            x: Math.min(Math.max(x, 0), rect.width),
            y: Math.min(Math.max(y, 0), rect.height),
        };
    }, []);

    const updateFromClientPoint = useCallback(
        (clientX, clientY) => {
            const el = containerRef.current;
            if (!el) return;
            const rect = el.getBoundingClientRect();
            const raw = { x: clientX - rect.left, y: clientY - rect.top };
            setPos(clampToContainer(raw.x, raw.y));
        },
        [clampToContainer]
    );

    const onHandleDown = (e) => {
        e.preventDefault();
        setDragging(true);
    };

    useEffect(() => {
        if (!dragging) return;
        const onMove = (e) => {
            const point = e.touches ? e.touches[0] : e;
            updateFromClientPoint(point.clientX, point.clientY);
        };
        const onUp = () => setDragging(false);

        window.addEventListener("mousemove", onMove);
        window.addEventListener("mouseup", onUp);
        window.addEventListener("touchmove", onMove, { passive: false });
        window.addEventListener("touchend", onUp);

        return () => {
            window.removeEventListener("mousemove", onMove);
            window.removeEventListener("mouseup", onUp);
            window.removeEventListener("touchmove", onMove);
            window.removeEventListener("touchend", onUp);
        };
    }, [dragging, updateFromClientPoint]);

    const headline = "Autonomous Risk Investigation Agent";
    const chars = headline.split("");

    const charSpanRefs = useRef([]);
    const [charCenters, setCharCenters] = useState([]);

    const measureChars = useCallback(() => {
        const containerEl = containerRef.current;
        if (!containerEl) return;
        const containerRect = containerEl.getBoundingClientRect();
        const centers = charSpanRefs.current.map((el) => {
            if (!el) return 0;
            const r = el.getBoundingClientRect();
            return r.left + r.width / 2 - containerRect.left;
        });
        setCharCenters(centers);
    }, []);

    useEffect(() => {
        measureChars();
        window.addEventListener("resize", measureChars);
        return () => window.removeEventListener("resize", measureChars);
    }, [measureChars]);

    const bulgeFor = (centerX) => {
        const d = centerX - pos.x;
        return BULGE_AMPLITUDE * Math.exp(-(d * d) / (2 * BULGE_SIGMA * BULGE_SIGMA));
    };

    const textStyle = {
        fontWeight: 800,
        // Fluid so the single-line headline (white-space: pre) shrinks to fit
        // narrow viewports instead of overflowing them.
        fontSize: "clamp(14px, 5.2vw, 40px)",
        lineHeight: 1.15,
        color: "var(--lens-ink)",
        letterSpacing: "-0.01em",
    };

    const shiftX = pos.x * (1 - ZOOM_SCALE);
    const shiftY = pos.y * (1 - ZOOM_SCALE);
    const magnifiedTransform = `translate(${shiftX}px, ${shiftY}px) scale(${ZOOM_SCALE})`;

    const rimMask = `radial-gradient(circle ${LENS_RADIUS}px at ${pos.x}px ${pos.y}px, transparent 0%, transparent 50%, rgba(0,0,0,0.9) 78%, black 100%)`;
    const lensClip = `circle(${LENS_RADIUS}px at ${pos.x}px ${pos.y}px)`;
    // Inverse of lensClip: punches a hole exactly where the lens sits so the
    // base (un-magnified) text is hidden there, leaving only the magnified
    // copy drawn inside the lens visible — everywhere outside the lens the
    // base text stays fully visible.
    const baseTextMask = `radial-gradient(circle ${LENS_RADIUS}px at ${pos.x}px ${pos.y}px, transparent 0%, transparent 99%, black 100%)`;

    const angleRad = (HANDLE_ANGLE * Math.PI) / 180;
    const attachX = LENS_RADIUS + LENS_RADIUS * Math.cos(angleRad);
    const attachY = LENS_RADIUS + LENS_RADIUS * Math.sin(angleRad);

    return (
        <div className="w-full flex items-center justify-center p-4">
            <style>{`
        @keyframes glitchJitterA {
          0%, 100% { transform: translate(0px, 0px); }
          20% { transform: translate(3px, -2px); }
          40% { transform: translate(-2px, 1px); }
          60% { transform: translate(2px, 2px); }
          80% { transform: translate(-3px, -1px); }
        }
        @keyframes glitchJitterB {
          0%, 100% { transform: translate(0px, 0px); }
          25% { transform: translate(-3px, 2px); }
          50% { transform: translate(2px, -3px); }
          75% { transform: translate(3px, 1px); }
        }
      `}</style>
            <div
                ref={containerRef}
                className="relative select-none"
                style={{ width: "100%", maxWidth: "100%", touchAction: "none" }}
            >
                <div
                    style={{
                        WebkitMaskImage: baseTextMask,
                        maskImage: baseTextMask,
                    }}
                >
                    <p style={{ ...textStyle, margin: 0, whiteSpace: "pre" }}>
                        {chars.map((ch, i) => (
                            <span
                                key={i}
                                ref={(el) => (charSpanRefs.current[i] = el)}
                                style={{ display: "inline-block" }}
                            >
                                {ch === " " ? "\u00A0" : ch}
                            </span>
                        ))}
                    </p>
                </div>

                <div
                    aria-hidden="true"
                    style={{
                        position: "absolute",
                        inset: 0,
                        pointerEvents: "none",
                        clipPath: lensClip,
                        WebkitClipPath: lensClip,
                        background: "transparent",
                    }}
                >
                    <div style={{ position: "absolute", inset: 0, transform: magnifiedTransform, transformOrigin: "0 0" }}>
                        <p style={{ ...textStyle, margin: 0, whiteSpace: "pre" }}>
                            {chars.map((ch, i) => (
                                <span
                                    key={i}
                                    style={{
                                        display: "inline-block",
                                        transform: `translateY(-${bulgeFor(charCenters[i] || 0)}px)`,
                                    }}
                                >
                                    {ch === " " ? "\u00A0" : ch}
                                </span>
                            ))}
                        </p>
                    </div>
                </div>

                <div
                    aria-hidden="true"
                    style={{
                        position: "absolute",
                        inset: 0,
                        pointerEvents: "none",
                        clipPath: lensClip,
                        WebkitClipPath: lensClip,
                        WebkitMaskImage: rimMask,
                        maskImage: rimMask,
                        filter: "blur(2.5px)",
                    }}
                >
                    <div style={{ position: "absolute", inset: 0, transform: magnifiedTransform, transformOrigin: "0 0" }}>
                        <p style={{ ...textStyle, color: "#FF3B3B", opacity: 0.6, margin: 0, whiteSpace: "pre" }}>
                            {chars.map((ch, i) => (
                                <span
                                    key={i}
                                    style={{ display: "inline-block", transform: `translateY(-${bulgeFor(charCenters[i] || 0)}px)` }}
                                >
                                    <span style={{ display: "inline-block", animation: "glitchJitterA 1.6s steps(4, end) infinite" }}>
                                        {ch === " " ? "\u00A0" : ch}
                                    </span>
                                </span>
                            ))}
                        </p>
                    </div>
                    <div style={{ position: "absolute", inset: 0, transform: magnifiedTransform, transformOrigin: "0 0" }}>
                        <p style={{ ...textStyle, color: "#2FD3FF", opacity: 0.6, margin: 0, whiteSpace: "pre" }}>
                            {chars.map((ch, i) => (
                                <span
                                    key={i}
                                    style={{ display: "inline-block", transform: `translateY(-${bulgeFor(charCenters[i] || 0)}px)` }}
                                >
                                    <span style={{ display: "inline-block", animation: "glitchJitterB 1.9s steps(4, end) infinite" }}>
                                        {ch === " " ? "\u00A0" : ch}
                                    </span>
                                </span>
                            ))}
                        </p>
                    </div>
                </div>

                <div
                    onMouseDown={onHandleDown}
                    onTouchStart={onHandleDown}
                    style={{
                        position: "absolute",
                        left: pos.x - LENS_RADIUS,
                        top: pos.y - LENS_RADIUS,
                        width: LENS_RADIUS * 2,
                        height: LENS_RADIUS * 2,
                        cursor: dragging ? "grabbing" : "grab",
                        transition: dragging ? "none" : "transform 0.15s ease-out",
                    }}
                >
                    <div
                        style={{
                            position: "absolute",
                            left: attachX - HANDLE_WIDTH / 2,
                            top: attachY - 2,
                            width: HANDLE_WIDTH,
                            height: HANDLE_LENGTH,
                            background:
                                "linear-gradient(180deg, var(--lens-handle-from) 0%, var(--lens-handle-to) 100%)",
                            borderRadius: HANDLE_WIDTH / 2,
                            transform: `rotate(${HANDLE_ANGLE - 90}deg)`,
                            transformOrigin: "50% 0%",
                            boxShadow: "0 3px 6px rgba(0,0,0,0.3)",
                            zIndex: 0,
                        }}
                    />
                    <div
                        style={{
                            position: "absolute",
                            inset: 0,
                            boxSizing: "border-box",
                            borderRadius: "50%",
                            background:
                                "radial-gradient(circle at 35% 30%, rgba(255,255,255,0.55), rgba(200,225,235,0.15) 45%, rgba(10,10,10,0.05) 70%)",
                            border: `${RIM_BORDER}px solid var(--lens-rim)`,
                            boxShadow:
                                "0 8px 20px rgba(0,0,0,0.22), inset 0 0 12px rgba(255,255,255,0.35)",
                            zIndex: 1,
                        }}
                    />
                    <div
                        style={{
                            position: "absolute",
                            width: "32%",
                            height: "18%",
                            top: "18%",
                            left: "22%",
                            borderRadius: "50%",
                            background:
                                "linear-gradient(135deg, rgba(255,255,255,0.75), rgba(255,255,255,0))",
                            transform: "rotate(-20deg)",
                            pointerEvents: "none",
                            zIndex: 2,
                        }}
                    />
                </div>
            </div>
        </div>
    );
}