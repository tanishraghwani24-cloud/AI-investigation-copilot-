(globalThis["TURBOPACK"] || (globalThis["TURBOPACK"] = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/components/MagnifyLens.jsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>MagnifyLens
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
// Tune these
const LENS_RADIUS = 50;
const ZOOM_SCALE = 1.28;
const BULGE_AMPLITUDE = 9;
const BULGE_SIGMA = LENS_RADIUS * 0.55;
const HANDLE_ANGLE = 42;
const HANDLE_LENGTH = 35;
const HANDLE_WIDTH = 12;
const RIM_BORDER = 5;
function MagnifyLens() {
    _s();
    const containerRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const [pos, setPos] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({
        x: 140,
        y: 40
    });
    const [dragging, setDragging] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const clampToContainer = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "MagnifyLens.useCallback[clampToContainer]": (x, y)=>{
            const el = containerRef.current;
            if (!el) return {
                x,
                y
            };
            const rect = el.getBoundingClientRect();
            return {
                x: Math.min(Math.max(x, 0), rect.width),
                y: Math.min(Math.max(y, 0), rect.height)
            };
        }
    }["MagnifyLens.useCallback[clampToContainer]"], []);
    const updateFromClientPoint = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "MagnifyLens.useCallback[updateFromClientPoint]": (clientX, clientY)=>{
            const el = containerRef.current;
            if (!el) return;
            const rect = el.getBoundingClientRect();
            const raw = {
                x: clientX - rect.left,
                y: clientY - rect.top
            };
            setPos(clampToContainer(raw.x, raw.y));
        }
    }["MagnifyLens.useCallback[updateFromClientPoint]"], [
        clampToContainer
    ]);
    const onHandleDown = (e)=>{
        e.preventDefault();
        setDragging(true);
    };
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "MagnifyLens.useEffect": ()=>{
            if (!dragging) return;
            const onMove = {
                "MagnifyLens.useEffect.onMove": (e)=>{
                    const point = e.touches ? e.touches[0] : e;
                    updateFromClientPoint(point.clientX, point.clientY);
                }
            }["MagnifyLens.useEffect.onMove"];
            const onUp = {
                "MagnifyLens.useEffect.onUp": ()=>setDragging(false)
            }["MagnifyLens.useEffect.onUp"];
            window.addEventListener("mousemove", onMove);
            window.addEventListener("mouseup", onUp);
            window.addEventListener("touchmove", onMove, {
                passive: false
            });
            window.addEventListener("touchend", onUp);
            return ({
                "MagnifyLens.useEffect": ()=>{
                    window.removeEventListener("mousemove", onMove);
                    window.removeEventListener("mouseup", onUp);
                    window.removeEventListener("touchmove", onMove);
                    window.removeEventListener("touchend", onUp);
                }
            })["MagnifyLens.useEffect"];
        }
    }["MagnifyLens.useEffect"], [
        dragging,
        updateFromClientPoint
    ]);
    const headline = "Autonomous Risk Investigation Agent";
    const chars = headline.split("");
    const charSpanRefs = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])([]);
    const [charCenters, setCharCenters] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const measureChars = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "MagnifyLens.useCallback[measureChars]": ()=>{
            const containerEl = containerRef.current;
            if (!containerEl) return;
            const containerRect = containerEl.getBoundingClientRect();
            const centers = charSpanRefs.current.map({
                "MagnifyLens.useCallback[measureChars].centers": (el)=>{
                    if (!el) return 0;
                    const r = el.getBoundingClientRect();
                    return r.left + r.width / 2 - containerRect.left;
                }
            }["MagnifyLens.useCallback[measureChars].centers"]);
            setCharCenters(centers);
        }
    }["MagnifyLens.useCallback[measureChars]"], []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "MagnifyLens.useEffect": ()=>{
            measureChars();
            window.addEventListener("resize", measureChars);
            return ({
                "MagnifyLens.useEffect": ()=>window.removeEventListener("resize", measureChars)
            })["MagnifyLens.useEffect"];
        }
    }["MagnifyLens.useEffect"], [
        measureChars
    ]);
    const bulgeFor = (centerX)=>{
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
        letterSpacing: "-0.01em"
    };
    const shiftX = pos.x * (1 - ZOOM_SCALE);
    const shiftY = pos.y * (1 - ZOOM_SCALE);
    const magnifiedTransform = `translate(${shiftX}px, ${shiftY}px) scale(${ZOOM_SCALE})`;
    const rimMask = `radial-gradient(circle ${LENS_RADIUS}px at ${pos.x}px ${pos.y}px, transparent 0%, transparent 50%, rgba(0,0,0,0.9) 78%, black 100%)`;
    const lensClip = `circle(${LENS_RADIUS}px at ${pos.x}px ${pos.y}px)`;
    const angleRad = HANDLE_ANGLE * Math.PI / 180;
    const attachX = LENS_RADIUS + LENS_RADIUS * Math.cos(angleRad);
    const attachY = LENS_RADIUS + LENS_RADIUS * Math.sin(angleRad);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "w-full flex items-center justify-center p-4",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("style", {
                children: `
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
      `
            }, void 0, false, {
                fileName: "[project]/components/MagnifyLens.jsx",
                lineNumber: 119,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                ref: containerRef,
                className: "relative select-none",
                style: {
                    width: "100%",
                    maxWidth: "100%",
                    touchAction: "none"
                },
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        style: {
                            ...textStyle,
                            margin: 0,
                            whiteSpace: "pre"
                        },
                        children: chars.map((ch, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                ref: (el)=>charSpanRefs.current[i] = el,
                                style: {
                                    display: "inline-block"
                                },
                                children: ch === " " ? "\u00A0" : ch
                            }, i, false, {
                                fileName: "[project]/components/MagnifyLens.jsx",
                                lineNumber: 141,
                                columnNumber: 25
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/components/MagnifyLens.jsx",
                        lineNumber: 139,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        "aria-hidden": "true",
                        style: {
                            position: "absolute",
                            inset: 0,
                            pointerEvents: "none",
                            clipPath: lensClip,
                            WebkitClipPath: lensClip,
                            background: "var(--lens-surface)"
                        },
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            style: {
                                position: "absolute",
                                inset: 0,
                                transform: magnifiedTransform,
                                transformOrigin: "0 0"
                            },
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                style: {
                                    ...textStyle,
                                    margin: 0,
                                    whiteSpace: "pre"
                                },
                                children: chars.map((ch, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        style: {
                                            display: "inline-block",
                                            transform: `translateY(-${bulgeFor(charCenters[i] || 0)}px)`
                                        },
                                        children: ch === " " ? "\u00A0" : ch
                                    }, i, false, {
                                        fileName: "[project]/components/MagnifyLens.jsx",
                                        lineNumber: 165,
                                        columnNumber: 33
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/components/MagnifyLens.jsx",
                                lineNumber: 163,
                                columnNumber: 25
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/components/MagnifyLens.jsx",
                            lineNumber: 162,
                            columnNumber: 21
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/components/MagnifyLens.jsx",
                        lineNumber: 151,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        "aria-hidden": "true",
                        style: {
                            position: "absolute",
                            inset: 0,
                            pointerEvents: "none",
                            clipPath: lensClip,
                            WebkitClipPath: lensClip,
                            WebkitMaskImage: rimMask,
                            maskImage: rimMask,
                            filter: "blur(2.5px)"
                        },
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    position: "absolute",
                                    inset: 0,
                                    transform: magnifiedTransform,
                                    transformOrigin: "0 0"
                                },
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                    style: {
                                        ...textStyle,
                                        color: "#FF3B3B",
                                        opacity: 0.6,
                                        margin: 0,
                                        whiteSpace: "pre"
                                    },
                                    children: chars.map((ch, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            style: {
                                                display: "inline-block",
                                                transform: `translateY(-${bulgeFor(charCenters[i] || 0)}px)`
                                            },
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                style: {
                                                    display: "inline-block",
                                                    animation: "glitchJitterA 1.6s steps(4, end) infinite"
                                                },
                                                children: ch === " " ? "\u00A0" : ch
                                            }, void 0, false, {
                                                fileName: "[project]/components/MagnifyLens.jsx",
                                                lineNumber: 199,
                                                columnNumber: 37
                                            }, this)
                                        }, i, false, {
                                            fileName: "[project]/components/MagnifyLens.jsx",
                                            lineNumber: 195,
                                            columnNumber: 33
                                        }, this))
                                }, void 0, false, {
                                    fileName: "[project]/components/MagnifyLens.jsx",
                                    lineNumber: 193,
                                    columnNumber: 25
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/MagnifyLens.jsx",
                                lineNumber: 192,
                                columnNumber: 21
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    position: "absolute",
                                    inset: 0,
                                    transform: magnifiedTransform,
                                    transformOrigin: "0 0"
                                },
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                    style: {
                                        ...textStyle,
                                        color: "#2FD3FF",
                                        opacity: 0.6,
                                        margin: 0,
                                        whiteSpace: "pre"
                                    },
                                    children: chars.map((ch, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            style: {
                                                display: "inline-block",
                                                transform: `translateY(-${bulgeFor(charCenters[i] || 0)}px)`
                                            },
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                style: {
                                                    display: "inline-block",
                                                    animation: "glitchJitterB 1.9s steps(4, end) infinite"
                                                },
                                                children: ch === " " ? "\u00A0" : ch
                                            }, void 0, false, {
                                                fileName: "[project]/components/MagnifyLens.jsx",
                                                lineNumber: 213,
                                                columnNumber: 37
                                            }, this)
                                        }, i, false, {
                                            fileName: "[project]/components/MagnifyLens.jsx",
                                            lineNumber: 209,
                                            columnNumber: 33
                                        }, this))
                                }, void 0, false, {
                                    fileName: "[project]/components/MagnifyLens.jsx",
                                    lineNumber: 207,
                                    columnNumber: 25
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/MagnifyLens.jsx",
                                lineNumber: 206,
                                columnNumber: 21
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/MagnifyLens.jsx",
                        lineNumber: 179,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        onMouseDown: onHandleDown,
                        onTouchStart: onHandleDown,
                        style: {
                            position: "absolute",
                            left: pos.x - LENS_RADIUS,
                            top: pos.y - LENS_RADIUS,
                            width: LENS_RADIUS * 2,
                            height: LENS_RADIUS * 2,
                            cursor: dragging ? "grabbing" : "grab",
                            transition: dragging ? "none" : "transform 0.15s ease-out"
                        },
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    position: "absolute",
                                    left: attachX - HANDLE_WIDTH / 2,
                                    top: attachY - 2,
                                    width: HANDLE_WIDTH,
                                    height: HANDLE_LENGTH,
                                    background: "linear-gradient(180deg, var(--lens-handle-from) 0%, var(--lens-handle-to) 100%)",
                                    borderRadius: HANDLE_WIDTH / 2,
                                    transform: `rotate(${HANDLE_ANGLE - 90}deg)`,
                                    transformOrigin: "50% 0%",
                                    boxShadow: "0 3px 6px rgba(0,0,0,0.3)",
                                    zIndex: 0
                                }
                            }, void 0, false, {
                                fileName: "[project]/components/MagnifyLens.jsx",
                                lineNumber: 235,
                                columnNumber: 21
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    position: "absolute",
                                    inset: 0,
                                    boxSizing: "border-box",
                                    borderRadius: "50%",
                                    background: "radial-gradient(circle at 35% 30%, rgba(255,255,255,0.55), rgba(200,225,235,0.15) 45%, rgba(10,10,10,0.05) 70%)",
                                    border: `${RIM_BORDER}px solid var(--lens-rim)`,
                                    boxShadow: "0 8px 20px rgba(0,0,0,0.22), inset 0 0 12px rgba(255,255,255,0.35)",
                                    zIndex: 1
                                }
                            }, void 0, false, {
                                fileName: "[project]/components/MagnifyLens.jsx",
                                lineNumber: 251,
                                columnNumber: 21
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    position: "absolute",
                                    width: "32%",
                                    height: "18%",
                                    top: "18%",
                                    left: "22%",
                                    borderRadius: "50%",
                                    background: "linear-gradient(135deg, rgba(255,255,255,0.75), rgba(255,255,255,0))",
                                    transform: "rotate(-20deg)",
                                    pointerEvents: "none",
                                    zIndex: 2
                                }
                            }, void 0, false, {
                                fileName: "[project]/components/MagnifyLens.jsx",
                                lineNumber: 265,
                                columnNumber: 21
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/MagnifyLens.jsx",
                        lineNumber: 222,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/MagnifyLens.jsx",
                lineNumber: 134,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/MagnifyLens.jsx",
        lineNumber: 118,
        columnNumber: 9
    }, this);
}
_s(MagnifyLens, "FZL4Sgwgi6mLWugIsdceHAsmk7o=");
_c = MagnifyLens;
var _c;
__turbopack_context__.k.register(_c, "MagnifyLens");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/ui/MagicRings.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>MagicRings
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
/**
 * "Magic Rings" — animated WebGL ring background.
 *
 * Source: React Bits (ts-tailwind variant), used verbatim as the hero's
 * decorative background layer:
 * https://reactbits.dev/animations/magic-rings
 *
 * Renders into its own mount div sized by the parent (`w-full h-full`), so
 * the caller controls positioning/sizing — here that's an absolutely
 * positioned layer behind the hero text. No project logic lives in this
 * file; it is the upstream component unmodified.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$module$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/three/build/three.module.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/three/build/three.core.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
const vertexShader = `
void main() {
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;
const fragmentShader = `
precision highp float;

uniform float uTime, uAttenuation, uLineThickness;
uniform float uBaseRadius, uRadiusStep, uScaleRate;
uniform float uOpacity, uNoiseAmount, uRotation, uRingGap;
uniform float uFadeIn, uFadeOut;
uniform float uMouseInfluence, uHoverAmount, uHoverScale, uParallax, uBurst;
uniform float uCoverageAlpha;
uniform vec2 uResolution, uMouse;
uniform vec3 uColor, uColorTwo;
uniform int uRingCount;

const float HP = 1.5707963;
const float CYCLE = 3.45;

float fade(float t) {
  return t < uFadeIn ? smoothstep(0.0, uFadeIn, t) : 1.0 - smoothstep(uFadeOut, CYCLE - 0.2, t);
}

float ring(vec2 p, float ri, float cut, float t0, float px) {
  float t = mod(uTime + t0, CYCLE);
  float r = ri + t / CYCLE * uScaleRate;
  float d = abs(length(p) - r);
  float a = atan(abs(p.y), abs(p.x)) / HP;
  float th = max(1.0 - a, 0.5) * px * uLineThickness;
  float h = (1.0 - smoothstep(th, th * 1.5, d)) + 1.0;
  d += pow(cut * a, 3.0) * r;
  return h * exp(-uAttenuation * d) * fade(t);
}

void main() {
  float px = 1.0 / min(uResolution.x, uResolution.y);
  vec2 p = (gl_FragCoord.xy - 0.5 * uResolution.xy) * px;
  float cr = cos(uRotation), sr = sin(uRotation);
  p = mat2(cr, -sr, sr, cr) * p;
  p -= uMouse * uMouseInfluence;
  float sc = mix(1.0, uHoverScale, uHoverAmount) + uBurst * 0.3;
  p /= sc;
  vec3 c = vec3(0.0);
  float coverage = 0.0;
  float rcf = max(float(uRingCount) - 1.0, 1.0);
  for (int i = 0; i < 10; i++) {
    if (i >= uRingCount) break;
    float fi = float(i);
    vec2 pr = p - fi * uParallax * uMouse;
    vec3 rc = mix(uColor, uColorTwo, fi / rcf);
    float ringAmount = ring(pr, uBaseRadius + fi * uRadiusStep, pow(uRingGap, fi), i == 0 ? 0.0 : 2.95 * fi, px);
    c = mix(c, rc, vec3(ringAmount));
    coverage = max(coverage, ringAmount);
  }
  c *= 1.0 + uBurst * 2.0;
  float n = fract(sin(dot(gl_FragCoord.xy + uTime * 100.0, vec2(12.9898, 78.233))) * 43758.5453);
  c += (n - 0.5) * uNoiseAmount;
  float intensity = max(c.r, max(c.g, c.b));
  vec3 emissiveColor = intensity > 0.0001 ? clamp(c / intensity, 0.0, 1.0) : vec3(0.0);
  vec3 outputColor = mix(emissiveColor, clamp(c, 0.0, 1.0), uCoverageAlpha);
  float outputAlpha = mix(intensity, coverage, uCoverageAlpha);
  gl_FragColor = vec4(outputColor, clamp(outputAlpha * uOpacity, 0.0, 1.0));
}
`;
function MagicRings({ color = '#fc42ff', colorTwo = '#42fcff', speed = 1, ringCount = 6, attenuation = 10, lineThickness = 2, baseRadius = 0.35, radiusStep = 0.1, scaleRate = 0.1, opacity = 1, blur = 0, noiseAmount = 0.1, rotation = 0, ringGap = 1.5, fadeIn = 0.7, fadeOut = 0.5, followMouse = false, mouseInfluence = 0.2, hoverScale = 1.2, parallax = 0.05, clickBurst = false, alphaMode = 'luminance' }) {
    _s();
    const mountRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const propsRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const mouseRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])([
        0,
        0
    ]);
    const smoothMouseRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])([
        0,
        0
    ]);
    const hoverAmountRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(0);
    const isHoveredRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(false);
    const burstRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(0);
    // Kept in a ref (rather than state) so the rAF loop below always reads the
    // latest prop values via closure without needing to restart the effect on
    // every prop change. Assigning in an effect (not during render) keeps this
    // pure for React's rules while still being ready before the animation loop
    // starts, since effects run in declaration order.
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "MagicRings.useEffect": ()=>{
            propsRef.current = {
                color,
                colorTwo,
                speed,
                ringCount,
                attenuation,
                lineThickness,
                baseRadius,
                radiusStep,
                scaleRate,
                opacity,
                blur,
                noiseAmount,
                rotation,
                ringGap,
                fadeIn,
                fadeOut,
                followMouse,
                mouseInfluence,
                hoverScale,
                parallax,
                clickBurst,
                alphaMode
            };
        }
    }["MagicRings.useEffect"]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "MagicRings.useEffect": ()=>{
            const mount = mountRef.current;
            if (!mount) return;
            let renderer;
            try {
                renderer = new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$module$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["WebGLRenderer"]({
                    alpha: true
                });
            } catch  {
                return;
            }
            if (!renderer.capabilities.isWebGL2) {
                renderer.dispose();
                return;
            }
            renderer.setClearColor(0x000000, 0);
            mount.appendChild(renderer.domElement);
            const scene = new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Scene"]();
            const camera = new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["OrthographicCamera"](-0.5, 0.5, 0.5, -0.5, 0.1, 10);
            camera.position.z = 1;
            const uniforms = {
                uTime: {
                    value: 0
                },
                uAttenuation: {
                    value: 0
                },
                uResolution: {
                    value: new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Vector2"]()
                },
                uColor: {
                    value: new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Color"]()
                },
                uColorTwo: {
                    value: new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Color"]()
                },
                uLineThickness: {
                    value: 0
                },
                uBaseRadius: {
                    value: 0
                },
                uRadiusStep: {
                    value: 0
                },
                uScaleRate: {
                    value: 0
                },
                uRingCount: {
                    value: 0
                },
                uOpacity: {
                    value: 1
                },
                uNoiseAmount: {
                    value: 0
                },
                uRotation: {
                    value: 0
                },
                uRingGap: {
                    value: 1.6
                },
                uFadeIn: {
                    value: 0.5
                },
                uFadeOut: {
                    value: 0.75
                },
                uMouse: {
                    value: new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Vector2"]()
                },
                uMouseInfluence: {
                    value: 0
                },
                uHoverAmount: {
                    value: 0
                },
                uHoverScale: {
                    value: 1
                },
                uParallax: {
                    value: 0
                },
                uBurst: {
                    value: 0
                },
                uCoverageAlpha: {
                    value: 0
                }
            };
            const material = new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ShaderMaterial"]({
                vertexShader,
                fragmentShader,
                uniforms,
                transparent: true
            });
            const quad = new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Mesh"](new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$three$2f$build$2f$three$2e$core$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["PlaneGeometry"](1, 1), material);
            scene.add(quad);
            const resize = {
                "MagicRings.useEffect.resize": ()=>{
                    const w = mount.clientWidth;
                    const h = mount.clientHeight;
                    const dpr = Math.min(window.devicePixelRatio, 2);
                    renderer.setSize(w, h);
                    renderer.setPixelRatio(dpr);
                    uniforms.uResolution.value.set(w * dpr, h * dpr);
                }
            }["MagicRings.useEffect.resize"];
            resize();
            window.addEventListener('resize', resize);
            const ro = new ResizeObserver(resize);
            ro.observe(mount);
            const onMouseMove = {
                "MagicRings.useEffect.onMouseMove": (e)=>{
                    const rect = mount.getBoundingClientRect();
                    mouseRef.current[0] = (e.clientX - rect.left) / rect.width - 0.5;
                    mouseRef.current[1] = -((e.clientY - rect.top) / rect.height - 0.5);
                }
            }["MagicRings.useEffect.onMouseMove"];
            const onMouseEnter = {
                "MagicRings.useEffect.onMouseEnter": ()=>{
                    isHoveredRef.current = true;
                }
            }["MagicRings.useEffect.onMouseEnter"];
            const onMouseLeave = {
                "MagicRings.useEffect.onMouseLeave": ()=>{
                    isHoveredRef.current = false;
                    mouseRef.current[0] = 0;
                    mouseRef.current[1] = 0;
                }
            }["MagicRings.useEffect.onMouseLeave"];
            const onClick = {
                "MagicRings.useEffect.onClick": ()=>{
                    burstRef.current = 1;
                }
            }["MagicRings.useEffect.onClick"];
            mount.addEventListener('mousemove', onMouseMove);
            mount.addEventListener('mouseenter', onMouseEnter);
            mount.addEventListener('mouseleave', onMouseLeave);
            mount.addEventListener('click', onClick);
            let frameId = 0;
            let isVisible = false;
            let isPageVisible = !document.hidden;
            let elapsed = 0;
            let lastT = 0;
            const animate = {
                "MagicRings.useEffect.animate": (t)=>{
                    frameId = requestAnimationFrame(animate);
                    const p = propsRef.current;
                    const dt = lastT === 0 ? 0 : Math.min(t - lastT, 100);
                    lastT = t;
                    elapsed += dt * 0.001 * p.speed;
                    smoothMouseRef.current[0] += (mouseRef.current[0] - smoothMouseRef.current[0]) * 0.08;
                    smoothMouseRef.current[1] += (mouseRef.current[1] - smoothMouseRef.current[1]) * 0.08;
                    hoverAmountRef.current += ((isHoveredRef.current ? 1 : 0) - hoverAmountRef.current) * 0.08;
                    burstRef.current *= 0.95;
                    if (burstRef.current < 0.001) burstRef.current = 0;
                    uniforms.uTime.value = elapsed;
                    uniforms.uAttenuation.value = p.attenuation;
                    uniforms.uColor.value.set(p.color);
                    uniforms.uColorTwo.value.set(p.colorTwo);
                    uniforms.uLineThickness.value = p.lineThickness;
                    uniforms.uBaseRadius.value = p.baseRadius;
                    uniforms.uRadiusStep.value = p.radiusStep;
                    uniforms.uScaleRate.value = p.scaleRate;
                    uniforms.uRingCount.value = p.ringCount;
                    uniforms.uOpacity.value = p.opacity;
                    uniforms.uNoiseAmount.value = p.noiseAmount;
                    uniforms.uRotation.value = p.rotation * Math.PI / 180;
                    uniforms.uRingGap.value = p.ringGap;
                    uniforms.uFadeIn.value = p.fadeIn;
                    uniforms.uFadeOut.value = p.fadeOut;
                    uniforms.uMouse.value.set(smoothMouseRef.current[0], smoothMouseRef.current[1]);
                    uniforms.uMouseInfluence.value = p.followMouse ? p.mouseInfluence : 0;
                    uniforms.uHoverAmount.value = hoverAmountRef.current;
                    uniforms.uHoverScale.value = p.hoverScale;
                    uniforms.uParallax.value = p.parallax;
                    uniforms.uBurst.value = p.clickBurst ? burstRef.current : 0;
                    uniforms.uCoverageAlpha.value = p.alphaMode === 'coverage' ? 1 : 0;
                    renderer.render(scene, camera);
                }
            }["MagicRings.useEffect.animate"];
            frameId = 0;
            const tryStart = {
                "MagicRings.useEffect.tryStart": ()=>{
                    if (isVisible && isPageVisible && frameId === 0) {
                        lastT = 0;
                        frameId = requestAnimationFrame(animate);
                    }
                }
            }["MagicRings.useEffect.tryStart"];
            const tryStop = {
                "MagicRings.useEffect.tryStop": ()=>{
                    if (frameId !== 0) {
                        cancelAnimationFrame(frameId);
                        frameId = 0;
                    }
                }
            }["MagicRings.useEffect.tryStop"];
            const io = new IntersectionObserver({
                "MagicRings.useEffect": ([entry])=>{
                    isVisible = entry.isIntersecting;
                    if (isVisible) tryStart();
                    else tryStop();
                }
            }["MagicRings.useEffect"], {
                threshold: 0
            });
            io.observe(mount);
            const onVisibility = {
                "MagicRings.useEffect.onVisibility": ()=>{
                    isPageVisible = !document.hidden;
                    if (isPageVisible) tryStart();
                    else tryStop();
                }
            }["MagicRings.useEffect.onVisibility"];
            document.addEventListener('visibilitychange', onVisibility);
            tryStart();
            return ({
                "MagicRings.useEffect": ()=>{
                    tryStop();
                    io.disconnect();
                    document.removeEventListener('visibilitychange', onVisibility);
                    window.removeEventListener('resize', resize);
                    ro.disconnect();
                    mount.removeEventListener('mousemove', onMouseMove);
                    mount.removeEventListener('mouseenter', onMouseEnter);
                    mount.removeEventListener('mouseleave', onMouseLeave);
                    mount.removeEventListener('click', onClick);
                    mount.removeChild(renderer.domElement);
                    renderer.dispose();
                    material.dispose();
                }
            })["MagicRings.useEffect"];
        }
    }["MagicRings.useEffect"], []);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ref: mountRef,
        className: "w-full h-full",
        style: blur > 0 ? {
            filter: `blur(${blur}px)`
        } : undefined
    }, void 0, false, {
        fileName: "[project]/components/ui/MagicRings.tsx",
        lineNumber: 335,
        columnNumber: 10
    }, this);
}
_s(MagicRings, "cmqpdL7UL2ebPfWdJr4fvTzfrtg=");
_c = MagicRings;
var _c;
__turbopack_context__.k.register(_c, "MagicRings");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=components_0qeyfsl._.js.map