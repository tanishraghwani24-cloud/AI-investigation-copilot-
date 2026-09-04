(globalThis["TURBOPACK"] || (globalThis["TURBOPACK"] = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/components/investigations/InvestigationList.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "InvestigationList",
    ()=>InvestigationList
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$investigationService$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/services/investigationService.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/services/api.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$auth$2f$InvestigatorProvider$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/auth/InvestigatorProvider.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$investigators$2f$InvestigatorAvatar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/investigators/InvestigatorAvatar.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$investigations$2f$StatusBadge$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/investigations/StatusBadge.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$investigations$2f$RiskScoreBadge$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/investigations/RiskScoreBadge.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
;
;
;
function InvestigationList() {
    _s();
    const [investigations, setInvestigations] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const [error, setError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    // case_id -> the investigator who handled it. Historical and permanent,
    // deliberately separate from the Officer Box's live presence.
    const [handledBy, setHandledBy] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({});
    const { investigator, authConfigured, loading: authLoading } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$auth$2f$InvestigatorProvider$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useInvestigator"])();
    const loadInvestigations = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "InvestigationList.useCallback[loadInvestigations]": ()=>{
            setLoading(true);
            setError(null);
            (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$investigationService$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["listInvestigations"])().then(setInvestigations).catch({
                "InvestigationList.useCallback[loadInvestigations]": (reason)=>{
                    setError(reason instanceof Error ? reason.message : "Unable to load investigations.");
                }
            }["InvestigationList.useCallback[loadInvestigations]"]).finally({
                "InvestigationList.useCallback[loadInvestigations]": ()=>setLoading(false)
            }["InvestigationList.useCallback[loadInvestigations]"]);
        }
    }["InvestigationList.useCallback[loadInvestigations]"], []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "InvestigationList.useEffect": ()=>{
            // eslint-disable-next-line react-hooks/set-state-in-effect
            void loadInvestigations();
        }
    }["InvestigationList.useEffect"], [
        loadInvestigations
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "InvestigationList.useEffect": ()=>{
            // Attribution is fetched separately so the existing investigation list
            // contract is untouched, and its failure leaves the table fully usable
            // with every case simply shown as unassigned.
            //
            // Waiting for the session matters: this endpoint requires a bearer token,
            // and firing before Supabase has restored the session returned 401 and
            // left every case reading "Unassigned" with no retry. Depending on the
            // resolved investigator makes the fetch run again once sign-in completes.
            if (!authConfigured || authLoading || !investigator) return;
            let active = true;
            void (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["listAssignmentsRequest"])().then({
                "InvestigationList.useEffect": (assignments)=>{
                    if (!active) return;
                    setHandledBy(Object.fromEntries(assignments.map({
                        "InvestigationList.useEffect": (a)=>[
                                a.case_id,
                                a.investigator
                            ]
                    }["InvestigationList.useEffect"])));
                }
            }["InvestigationList.useEffect"]).catch({
                "InvestigationList.useEffect": ()=>{
                    if (active) setHandledBy({});
                }
            }["InvestigationList.useEffect"]);
            return ({
                "InvestigationList.useEffect": ()=>{
                    active = false;
                }
            })["InvestigationList.useEffect"];
        }
    }["InvestigationList.useEffect"], [
        authConfigured,
        authLoading,
        investigator
    ]);
    if (loading) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "animate-pulse",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "mb-6",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "h-8 w-48 rounded bg-gray-200 dark:bg-gray-700"
                        }, void 0, false, {
                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                            lineNumber: 76,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mt-2 h-4 w-32 rounded bg-gray-100 dark:bg-gray-800"
                        }, void 0, false, {
                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                            lineNumber: 77,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                    lineNumber: 75,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                        className: "w-full text-left text-sm",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("thead", {
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                    className: "border-b border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-800/50",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "px-6 py-4",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "h-4 w-24 rounded bg-gray-200 dark:bg-gray-700"
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 85,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 84,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "px-6 py-4",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "h-4 w-24 rounded bg-gray-200 dark:bg-gray-700"
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 88,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 87,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "px-6 py-4",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "h-4 w-16 rounded bg-gray-200 dark:bg-gray-700"
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 91,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 90,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "px-6 py-4",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "h-4 w-16 rounded bg-gray-200 dark:bg-gray-700"
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 94,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 93,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "px-6 py-4",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "h-4 w-20 rounded bg-gray-200 dark:bg-gray-700"
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 97,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 96,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                                    lineNumber: 83,
                                    columnNumber: 15
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                lineNumber: 82,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tbody", {
                                className: "divide-y divide-gray-100 dark:divide-gray-800",
                                children: [
                                    1,
                                    2,
                                    3,
                                    4,
                                    5
                                ].map((i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                className: "px-6 py-4",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "h-4 w-20 rounded bg-gray-100 dark:bg-gray-800"
                                                }, void 0, false, {
                                                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                    lineNumber: 106,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 105,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                className: "px-6 py-4",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "h-4 w-32 rounded bg-gray-100 dark:bg-gray-800"
                                                }, void 0, false, {
                                                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                    lineNumber: 109,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 108,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                className: "px-6 py-4",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "h-6 w-24 rounded-full bg-gray-100 dark:bg-gray-800"
                                                }, void 0, false, {
                                                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                    lineNumber: 112,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 111,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                className: "px-6 py-4",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "h-6 w-16 rounded-full bg-gray-100 dark:bg-gray-800"
                                                }, void 0, false, {
                                                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                    lineNumber: 115,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 114,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                className: "px-6 py-4",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "h-4 w-24 rounded bg-gray-100 dark:bg-gray-800"
                                                }, void 0, false, {
                                                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                    lineNumber: 118,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 117,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, i, true, {
                                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                                        lineNumber: 104,
                                        columnNumber: 17
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                lineNumber: 102,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                        lineNumber: 81,
                        columnNumber: 11
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                    lineNumber: 80,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/investigations/InvestigationList.tsx",
            lineNumber: 74,
            columnNumber: 7
        }, this);
    }
    if (error) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "rounded-xl border border-red-200 bg-red-50 px-4 py-8 text-center sm:px-6 dark:border-red-900 dark:bg-red-950/40",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                    className: "text-lg font-semibold text-red-800 dark:text-red-200",
                    children: "Unable to load investigations"
                }, void 0, false, {
                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                    lineNumber: 132,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                    className: "mt-2 text-sm text-red-700 dark:text-red-300",
                    children: error
                }, void 0, false, {
                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                    lineNumber: 136,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    type: "button",
                    onClick: loadInvestigations,
                    className: "mt-4 rounded-md bg-red-700 px-3 py-2 text-sm font-medium text-white hover:bg-red-800 dark:bg-red-600 dark:hover:bg-red-500",
                    children: "Retry"
                }, void 0, false, {
                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                    lineNumber: 138,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/investigations/InvestigationList.tsx",
            lineNumber: 131,
            columnNumber: 7
        }, this);
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                        className: "text-2xl font-bold text-gray-900 dark:text-white",
                        children: "Investigations"
                    }, void 0, false, {
                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                        lineNumber: 153,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "mt-1 text-sm text-gray-500 dark:text-gray-400",
                        children: [
                            investigations.length,
                            " investigation",
                            investigations.length !== 1 ? "s" : "",
                            " triggered from alerts"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                        lineNumber: 155,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/investigations/InvestigationList.tsx",
                lineNumber: 152,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                    className: "w-full min-w-[44rem] text-left text-sm",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("thead", {
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                className: "border-b border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-800/50",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                        className: "px-6 py-3 font-semibold text-gray-600 dark:text-gray-300",
                                        children: "Investigation ID"
                                    }, void 0, false, {
                                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                                        lineNumber: 166,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                        className: "px-6 py-3 font-semibold text-gray-600 dark:text-gray-300",
                                        children: "Customer Name"
                                    }, void 0, false, {
                                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                                        lineNumber: 170,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                        className: "px-6 py-3 font-semibold text-gray-600 dark:text-gray-300",
                                        children: "Status"
                                    }, void 0, false, {
                                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                                        lineNumber: 174,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                        className: "px-6 py-3 font-semibold text-gray-600 dark:text-gray-300",
                                        children: "Risk Score"
                                    }, void 0, false, {
                                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                                        lineNumber: 178,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                        className: "px-6 py-3 font-semibold text-gray-600 dark:text-gray-300",
                                        children: "Created Date"
                                    }, void 0, false, {
                                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                                        lineNumber: 182,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                        className: "px-6 py-3 font-semibold text-gray-600 dark:text-gray-300",
                                        children: "Investigator"
                                    }, void 0, false, {
                                        fileName: "[project]/components/investigations/InvestigationList.tsx",
                                        lineNumber: 186,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                lineNumber: 165,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                            lineNumber: 164,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tbody", {
                            className: "divide-y divide-gray-100 dark:divide-gray-800",
                            children: investigations.length === 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                    colSpan: 6,
                                    className: "px-6 py-10 text-center text-sm text-gray-500 dark:text-gray-400",
                                    children: "No investigations found."
                                }, void 0, false, {
                                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                                    lineNumber: 195,
                                    columnNumber: 17
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                lineNumber: 194,
                                columnNumber: 15
                            }, this) : investigations.map((inv)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                    className: "cursor-pointer transition-colors hover:bg-blue-50/50 dark:hover:bg-blue-900/20",
                                    onClick: ()=>{
                                        window.location.href = `/investigations/${inv.case_id}`;
                                    },
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                            className: "px-6 py-4 font-medium whitespace-nowrap text-blue-600 dark:text-blue-400",
                                            children: inv.case_id
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 211,
                                            columnNumber: 19
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                            className: "px-6 py-4 text-gray-900 dark:text-gray-100",
                                            children: inv.customer_name
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 215,
                                            columnNumber: 19
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                            className: "px-6 py-4",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$investigations$2f$StatusBadge$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["StatusBadge"], {
                                                value: inv.current_stage
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 220,
                                                columnNumber: 21
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 219,
                                            columnNumber: 19
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                            className: "px-6 py-4",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$investigations$2f$RiskScoreBadge$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["RiskScoreBadge"], {
                                                score: inv.risk_score
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 224,
                                                columnNumber: 21
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 223,
                                            columnNumber: 19
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                            className: "px-6 py-4 whitespace-nowrap text-gray-500 dark:text-gray-400",
                                            children: new Date(inv.created_at).toLocaleDateString("en-US", {
                                                year: "numeric",
                                                month: "short",
                                                day: "numeric"
                                            })
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 227,
                                            columnNumber: 19
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                            className: "px-6 py-4",
                                            children: handledBy[inv.case_id] ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$investigators$2f$InvestigatorAvatar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["InvestigatorAvatar"], {
                                                investigator: handledBy[inv.case_id],
                                                context: "handled this investigation"
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 237,
                                                columnNumber: 23
                                            }, this) : // Cases raised before investigator accounts existed have
                                            // nobody to name; say so rather than inventing one.
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm text-gray-400 dark:text-gray-500",
                                                title: "No investigator recorded for this case",
                                                children: "Unassigned"
                                            }, void 0, false, {
                                                fileName: "[project]/components/investigations/InvestigationList.tsx",
                                                lineNumber: 244,
                                                columnNumber: 23
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                                            lineNumber: 235,
                                            columnNumber: 19
                                        }, this)
                                    ]
                                }, inv.case_id, true, {
                                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                                    lineNumber: 204,
                                    columnNumber: 17
                                }, this))
                        }, void 0, false, {
                            fileName: "[project]/components/investigations/InvestigationList.tsx",
                            lineNumber: 192,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/investigations/InvestigationList.tsx",
                    lineNumber: 163,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/investigations/InvestigationList.tsx",
                lineNumber: 162,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/investigations/InvestigationList.tsx",
        lineNumber: 150,
        columnNumber: 5
    }, this);
}
_s(InvestigationList, "Yeq6vI0j5BpZNh2h3h4dvsHXgDU=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$auth$2f$InvestigatorProvider$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useInvestigator"]
    ];
});
_c = InvestigationList;
var _c;
__turbopack_context__.k.register(_c, "InvestigationList");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/investigations/RiskScoreBadge.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "RiskScoreBadge",
    ()=>RiskScoreBadge
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/utils.ts [app-client] (ecmascript)");
"use client";
;
;
function getRiskConfig(score) {
    if (score >= 0.7) {
        return {
            label: "High",
            style: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
        };
    }
    if (score >= 0.4) {
        return {
            label: "Medium",
            style: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
        };
    }
    return {
        label: "Low",
        style: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
    };
}
function RiskScoreBadge({ score, className }) {
    if (score === undefined || score === null) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
            className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["cn"])("inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-semibold text-gray-500 dark:bg-gray-800 dark:text-gray-400", className),
            children: "N/A"
        }, void 0, false, {
            fileName: "[project]/components/investigations/RiskScoreBadge.tsx",
            lineNumber: 34,
            columnNumber: 7
        }, this);
    }
    const { label, style } = getRiskConfig(score);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["cn"])("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold", style, className),
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "tabular-nums",
                children: [
                    (score * 100).toFixed(0),
                    "%"
                ]
            }, void 0, true, {
                fileName: "[project]/components/investigations/RiskScoreBadge.tsx",
                lineNumber: 55,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "opacity-70",
                children: "·"
            }, void 0, false, {
                fileName: "[project]/components/investigations/RiskScoreBadge.tsx",
                lineNumber: 56,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                children: label
            }, void 0, false, {
                fileName: "[project]/components/investigations/RiskScoreBadge.tsx",
                lineNumber: 57,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/investigations/RiskScoreBadge.tsx",
        lineNumber: 48,
        columnNumber: 5
    }, this);
}
_c = RiskScoreBadge;
var _c;
__turbopack_context__.k.register(_c, "RiskScoreBadge");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/investigations/StatusBadge.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "StatusBadge",
    ()=>StatusBadge
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/utils.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$types$2f$index$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/types/index.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/types/investigation.ts [app-client] (ecmascript)");
"use client";
;
;
;
const statusStyles = {
    // AgentStatus
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AgentStatus"].NOT_STARTED]: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AgentStatus"].IN_PROGRESS]: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AgentStatus"].COMPLETED]: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AgentStatus"].FAILED]: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
    // CurrentStage
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].INTAKE]: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].CONTEXT]: "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].REASONING]: "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].COMPLIANCE]: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].DECISION]: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].REPORTING]: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].DONE]: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
};
const displayLabels = {
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AgentStatus"].NOT_STARTED]: "Not Started",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AgentStatus"].IN_PROGRESS]: "In Progress",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AgentStatus"].COMPLETED]: "Completed",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AgentStatus"].FAILED]: "Failed",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].INTAKE]: "Intake",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].CONTEXT]: "Context",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].REASONING]: "Reasoning",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].COMPLIANCE]: "Compliance",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].DECISION]: "Decision",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].REPORTING]: "Reporting",
    [__TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CurrentStage"].DONE]: "Done"
};
function StatusBadge({ value, className }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["cn"])("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide", statusStyles[value] ?? "bg-gray-100 text-gray-600", className),
        children: displayLabels[value] ?? value
    }, void 0, false, {
        fileName: "[project]/components/investigations/StatusBadge.tsx",
        lineNumber: 56,
        columnNumber: 5
    }, this);
}
_c = StatusBadge;
var _c;
__turbopack_context__.k.register(_c, "StatusBadge");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/services/investigationService.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "createInvestigation",
    ()=>createInvestigation,
    "getInvestigation",
    ()=>getInvestigation,
    "listInvestigations",
    ()=>listInvestigations
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/services/api.ts [app-client] (ecmascript)");
;
/** Maps the full backend state into the fields used by the list table. */ function toListItem(investigation) {
    return {
        case_id: investigation.case_id,
        customer_name: investigation.case_input.customer_profile?.name ?? "Unknown customer",
        current_stage: investigation.current_stage,
        risk_score: investigation.context_intelligence?.risk_score,
        created_at: investigation.created_at,
        alert_reason: investigation.case_input.alert_reason
    };
}
async function listInvestigations() {
    const investigations = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["listInvestigationsRequest"])();
    return investigations.map(toListItem).sort((first, second)=>new Date(second.created_at).getTime() - new Date(first.created_at).getTime());
}
function getInvestigation(id) {
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getInvestigationRequest"])(id);
}
function createInvestigation(accountId) {
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["createInvestigationRequest"])(accountId);
}
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/types/index.ts [app-client] (ecmascript) <locals>", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([]);
var __TURBOPACK__imported__module__$5b$project$5d2f$types$2f$investigation$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/types/investigation.ts [app-client] (ecmascript)");
;
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/types/investigation.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

// ============================================================
// Enums — mirror backend app/schemas/investigation_state.py
// ============================================================
/** Processing status of an individual agent. */ __turbopack_context__.s([
    "AgentStatus",
    ()=>AgentStatus,
    "AnomalyType",
    ()=>AnomalyType,
    "CurrentStage",
    ()=>CurrentStage,
    "DecisionAction",
    ()=>DecisionAction,
    "ProcessingStatus",
    ()=>ProcessingStatus,
    "SeverityLevel",
    ()=>SeverityLevel
]);
var AgentStatus = /*#__PURE__*/ function(AgentStatus) {
    AgentStatus["NOT_STARTED"] = "NOT_STARTED";
    AgentStatus["IN_PROGRESS"] = "IN_PROGRESS";
    AgentStatus["COMPLETED"] = "COMPLETED";
    AgentStatus["FAILED"] = "FAILED";
    return AgentStatus;
}({});
var AnomalyType = /*#__PURE__*/ function(AnomalyType) {
    AnomalyType["POINT"] = "POINT";
    AnomalyType["BEHAVIORAL"] = "BEHAVIORAL";
    AnomalyType["CONTEXTUAL"] = "CONTEXTUAL";
    AnomalyType["NETWORK"] = "NETWORK";
    AnomalyType["MERCHANT"] = "MERCHANT";
    AnomalyType["SEASONAL"] = "SEASONAL";
    return AnomalyType;
}({});
var SeverityLevel = /*#__PURE__*/ function(SeverityLevel) {
    SeverityLevel["LOW"] = "LOW";
    SeverityLevel["MEDIUM"] = "MEDIUM";
    SeverityLevel["HIGH"] = "HIGH";
    return SeverityLevel;
}({});
var DecisionAction = /*#__PURE__*/ function(DecisionAction) {
    DecisionAction["ALLOW"] = "ALLOW";
    DecisionAction["HOLD"] = "HOLD";
    DecisionAction["BLOCK"] = "BLOCK";
    DecisionAction["ESCALATE"] = "ESCALATE";
    return DecisionAction;
}({});
var CurrentStage = /*#__PURE__*/ function(CurrentStage) {
    CurrentStage["INTAKE"] = "INTAKE";
    CurrentStage["CONTEXT"] = "CONTEXT";
    CurrentStage["REASONING"] = "REASONING";
    CurrentStage["COMPLIANCE"] = "COMPLIANCE";
    CurrentStage["DECISION"] = "DECISION";
    CurrentStage["REPORTING"] = "REPORTING";
    CurrentStage["DONE"] = "DONE";
    return CurrentStage;
}({});
var ProcessingStatus = /*#__PURE__*/ function(ProcessingStatus) {
    ProcessingStatus["PENDING"] = "PENDING";
    ProcessingStatus["PROCESSING"] = "PROCESSING";
    ProcessingStatus["EXTRACTED"] = "EXTRACTED";
    ProcessingStatus["SUMMARIZED"] = "SUMMARIZED";
    ProcessingStatus["FAILED"] = "FAILED";
    return ProcessingStatus;
}({});
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=_0m3geie._.js.map