(globalThis["TURBOPACK"] || (globalThis["TURBOPACK"] = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/components/auth/InvestigatorBadge.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "InvestigatorBadge",
    ()=>InvestigatorBadge
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$log$2d$out$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__LogOut$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/log-out.mjs [app-client] (ecmascript) <export default as LogOut>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/client/app-dir/link.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$auth$2f$InvestigatorProvider$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/auth/InvestigatorProvider.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$investigators$2f$InvestigatorAvatar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/investigators/InvestigatorAvatar.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
function InvestigatorBadge() {
    _s();
    const { investigator, loading, authConfigured, signOut } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$auth$2f$InvestigatorProvider$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useInvestigator"])();
    if (!authConfigured || loading) return null;
    if (!investigator) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
            href: "/login",
            className: "rounded-lg border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:text-gray-300 dark:hover:bg-gray-800/60",
            children: "Sign in"
        }, void 0, false, {
            fileName: "[project]/components/auth/InvestigatorBadge.tsx",
            lineNumber: 21,
            columnNumber: 7
        }, this);
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex items-center gap-2",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$investigators$2f$InvestigatorAvatar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["InvestigatorAvatar"], {
                investigator: investigator,
                size: "md"
            }, void 0, false, {
                fileName: "[project]/components/auth/InvestigatorBadge.tsx",
                lineNumber: 32,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "hidden leading-tight sm:block",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "block text-sm font-medium text-gray-700 dark:text-gray-300",
                        children: investigator.full_name
                    }, void 0, false, {
                        fileName: "[project]/components/auth/InvestigatorBadge.tsx",
                        lineNumber: 34,
                        columnNumber: 9
                    }, this),
                    investigator.officer_id && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "block text-xs text-gray-400 dark:text-gray-500",
                        children: investigator.officer_id
                    }, void 0, false, {
                        fileName: "[project]/components/auth/InvestigatorBadge.tsx",
                        lineNumber: 38,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/auth/InvestigatorBadge.tsx",
                lineNumber: 33,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                type: "button",
                onClick: ()=>void signOut(),
                title: "Sign out",
                "aria-label": "Sign out",
                className: "rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-200",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$log$2d$out$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__LogOut$3e$__["LogOut"], {
                    className: "h-4 w-4"
                }, void 0, false, {
                    fileName: "[project]/components/auth/InvestigatorBadge.tsx",
                    lineNumber: 50,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/auth/InvestigatorBadge.tsx",
                lineNumber: 43,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/auth/InvestigatorBadge.tsx",
        lineNumber: 31,
        columnNumber: 5
    }, this);
}
_s(InvestigatorBadge, "1dO916XtBWPldKuM8d353HsQw1E=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$auth$2f$InvestigatorProvider$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useInvestigator"]
    ];
});
_c = InvestigatorBadge;
var _c;
__turbopack_context__.k.register(_c, "InvestigatorBadge");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/auth/InvestigatorProvider.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "InvestigatorProvider",
    ()=>InvestigatorProvider,
    "initialOf",
    ()=>initialOf,
    "useInvestigator",
    ()=>useInvestigator
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$supabaseClient$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/services/supabaseClient.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/services/api.ts [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature();
"use client";
;
;
;
const InvestigatorContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["createContext"])({
    investigator: null,
    loading: true,
    authConfigured: false,
    signInWithOfficerId: async ()=>{},
    signOut: async ()=>{}
});
function initialOf(fullName) {
    const trimmed = (fullName ?? "").trim();
    return trimmed ? trimmed[0].toUpperCase() : "?";
}
function fromSession(session) {
    if (!session?.user) return null;
    const metadata = session.user.user_metadata ?? {};
    const name = typeof metadata.full_name === "string" && metadata.full_name.trim() || typeof metadata.name === "string" && metadata.name.trim() || session.user.email?.split("@")[0] || "Unknown investigator";
    return {
        user_id: session.user.id,
        full_name: name,
        email: session.user.email ?? null,
        initial: initialOf(name)
    };
}
function InvestigatorProvider({ children }) {
    _s();
    const [investigator, setInvestigator] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const authConfigured = (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$supabaseClient$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["isAuthConfigured"])();
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "InvestigatorProvider.useEffect": ()=>{
            const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$supabaseClient$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getSupabaseClient"])();
            if (supabase === null) {
                // Nothing to subscribe to when auth is unconfigured; settle immediately.
                // eslint-disable-next-line react-hooks/set-state-in-effect
                setLoading(false);
                return;
            }
            // The API layer asks for a token per request, so a refreshed session is
            // picked up without re-registering anything.
            (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["setAccessTokenProvider"])({
                "InvestigatorProvider.useEffect": async ()=>{
                    const { data } = await supabase.auth.getSession();
                    return data.session?.access_token ?? null;
                }
            }["InvestigatorProvider.useEffect"]);
            let active = true;
            /**
     * Adopt a session, then enrich it with the officer profile.
     *
     * The Supabase token carries the name but not the Officer ID, which lives
     * in the profile table. Fetching it also creates the profile on an
     * officer's first sign-in. A failure here leaves the session usable with
     * just the name rather than blocking sign-in.
     */ const adopt = {
                "InvestigatorProvider.useEffect.adopt": async (session)=>{
                    const base = fromSession(session);
                    if (!active) return;
                    setInvestigator(base);
                    setLoading(false);
                    if (!base) return;
                    try {
                        const profile = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getMeRequest"])();
                        if (active) setInvestigator({
                            ...base,
                            ...profile
                        });
                    } catch  {
                    // Keep the session; the header simply shows no Officer ID.
                    }
                }
            }["InvestigatorProvider.useEffect.adopt"];
            void supabase.auth.getSession().then({
                "InvestigatorProvider.useEffect": ({ data })=>void adopt(data.session)
            }["InvestigatorProvider.useEffect"]);
            const { data: subscription } = supabase.auth.onAuthStateChange({
                "InvestigatorProvider.useEffect": (_event, session)=>void adopt(session)
            }["InvestigatorProvider.useEffect"]);
            return ({
                "InvestigatorProvider.useEffect": ()=>{
                    active = false;
                    subscription.subscription.unsubscribe();
                }
            })["InvestigatorProvider.useEffect"];
        }
    }["InvestigatorProvider.useEffect"], []);
    /**
   * Sign in with an Officer ID.
   *
   * The exchange happens in a server route: it resolves the Officer ID to the
   * account Supabase authenticates and performs the password grant there, so
   * the internal email never reaches browser JavaScript. The route sets the
   * session cookies that middleware and Server Components read.
   */ const signInWithOfficerId = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "InvestigatorProvider.useCallback[signInWithOfficerId]": async (officerId, password)=>{
            const response = await fetch("/api/auth/officer-login", {
                method: "POST",
                headers: {
                    "content-type": "application/json"
                },
                body: JSON.stringify({
                    officer_id: officerId,
                    password
                })
            });
            if (!response.ok) {
                const body = await response.json().catch({
                    "InvestigatorProvider.useCallback[signInWithOfficerId]": ()=>({})
                }["InvestigatorProvider.useCallback[signInWithOfficerId]"]);
                throw new Error(body.error || "Invalid Officer ID or password.");
            }
            // Pick the new cookie session up in this tab straight away.
            const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$supabaseClient$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getSupabaseClient"])();
            if (supabase !== null) {
                const { data } = await supabase.auth.getSession();
                const base = fromSession(data.session);
                setInvestigator(base);
                if (base) {
                    try {
                        setInvestigator({
                            ...base,
                            ...await (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$api$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getMeRequest"])()
                        });
                    } catch  {
                    // Officer ID is cosmetic; never block a successful sign-in.
                    }
                }
            }
        }
    }["InvestigatorProvider.useCallback[signInWithOfficerId]"], []);
    const signOut = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "InvestigatorProvider.useCallback[signOut]": async ()=>{
            const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$services$2f$supabaseClient$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getSupabaseClient"])();
            if (supabase !== null) await supabase.auth.signOut();
            setInvestigator(null);
            // Full navigation, so middleware re-evaluates with the cookies now cleared
            // and every protected route becomes inaccessible again.
            window.location.assign("/login");
        }
    }["InvestigatorProvider.useCallback[signOut]"], []);
    const value = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "InvestigatorProvider.useMemo[value]": ()=>({
                investigator,
                loading,
                authConfigured,
                signInWithOfficerId,
                signOut
            })
    }["InvestigatorProvider.useMemo[value]"], [
        investigator,
        loading,
        authConfigured,
        signInWithOfficerId,
        signOut
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(InvestigatorContext.Provider, {
        value: value,
        children: children
    }, void 0, false, {
        fileName: "[project]/components/auth/InvestigatorProvider.tsx",
        lineNumber: 172,
        columnNumber: 5
    }, this);
}
_s(InvestigatorProvider, "6yIuF50imnoYlh/85ikYGcDyL38=");
_c = InvestigatorProvider;
function useInvestigator() {
    _s1();
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useContext"])(InvestigatorContext);
}
_s1(useInvestigator, "gDsCjeeItUuvgOWf1v4qoK9RF6k=");
var _c;
__turbopack_context__.k.register(_c, "InvestigatorProvider");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/investigators/InvestigatorAvatar.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "InvestigatorAvatar",
    ()=>InvestigatorAvatar,
    "InvestigatorAvatarGroup",
    ()=>InvestigatorAvatarGroup
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
"use client";
;
/**
 * Circular avatar showing an investigator's initial, with their full name on
 * hover — the Google-Sheets-style presence cue.
 *
 * The letter is whatever the backend derived from the authenticated account, so
 * nothing here is hardcoded to a particular officer.
 *
 * `InvestigatorAvatarGroup` takes a list so the same component covers both the
 * single-investigator case used today and several investigators later, without
 * adding UI that is not needed yet.
 */ const SIZES = {
    sm: "h-6 w-6 text-[11px]",
    md: "h-7 w-7 text-xs"
};
// Stable per-person colour: the same investigator always gets the same tint,
// derived from their id so no palette assignment has to be stored.
const PALETTE = [
    "bg-blue-600",
    "bg-emerald-600",
    "bg-violet-600",
    "bg-amber-600",
    "bg-rose-600",
    "bg-cyan-700"
];
function colourFor(userId) {
    let hash = 0;
    for(let i = 0; i < userId.length; i += 1){
        hash = (hash + userId.charCodeAt(i)) % PALETTE.length;
    }
    return PALETTE[hash];
}
function InvestigatorAvatar({ investigator, size = "sm", context }) {
    const label = context ? `${investigator.full_name} ${context}` : investigator.full_name;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
        className: "group/avatar relative inline-flex",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: `inline-flex items-center justify-center rounded-full font-semibold text-white ring-2 ring-white dark:ring-gray-900 ${SIZES[size]} ${colourFor(investigator.user_id)}`,
                // title gives native hover text plus a screen-reader-friendly fallback
                // everywhere the styled tooltip cannot reach (e.g. touch devices).
                title: label,
                "aria-label": label,
                role: "img",
                children: investigator.initial
            }, void 0, false, {
                fileName: "[project]/components/investigators/InvestigatorAvatar.tsx",
                lineNumber: 59,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                role: "tooltip",
                className: "pointer-events-none absolute left-1/2 top-full z-20 mt-1.5 -translate-x-1/2 whitespace-nowrap rounded-md bg-gray-900 px-2 py-1 text-xs font-medium text-white opacity-0 shadow-lg transition-opacity duration-100 group-hover/avatar:opacity-100 dark:bg-gray-700",
                children: label
            }, void 0, false, {
                fileName: "[project]/components/investigators/InvestigatorAvatar.tsx",
                lineNumber: 69,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/investigators/InvestigatorAvatar.tsx",
        lineNumber: 58,
        columnNumber: 5
    }, this);
}
_c = InvestigatorAvatar;
function InvestigatorAvatarGroup({ investigators, size = "sm", context, fallback = null, max = 3 }) {
    if (investigators.length === 0) return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
        children: fallback
    }, void 0, false, {
        fileName: "[project]/components/investigators/InvestigatorAvatar.tsx",
        lineNumber: 95,
        columnNumber: 42
    }, this);
    const shown = investigators.slice(0, max);
    const overflow = investigators.length - shown.length;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
        className: "inline-flex items-center -space-x-1.5",
        children: [
            shown.map((investigator)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(InvestigatorAvatar, {
                    investigator: investigator,
                    size: size,
                    context: context
                }, investigator.user_id, false, {
                    fileName: "[project]/components/investigators/InvestigatorAvatar.tsx",
                    lineNumber: 103,
                    columnNumber: 9
                }, this)),
            overflow > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: `inline-flex items-center justify-center rounded-full bg-gray-500 font-semibold text-white ring-2 ring-white dark:ring-gray-900 ${SIZES[size]}`,
                title: investigators.slice(max).map((i)=>i.full_name).join(", "),
                children: [
                    "+",
                    overflow
                ]
            }, void 0, true, {
                fileName: "[project]/components/investigators/InvestigatorAvatar.tsx",
                lineNumber: 111,
                columnNumber: 9
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/investigators/InvestigatorAvatar.tsx",
        lineNumber: 101,
        columnNumber: 5
    }, this);
}
_c1 = InvestigatorAvatarGroup;
var _c, _c1;
__turbopack_context__.k.register(_c, "InvestigatorAvatar");
__turbopack_context__.k.register(_c1, "InvestigatorAvatarGroup");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/layout/navItems.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "NAV_ITEMS",
    ()=>NAV_ITEMS
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$file$2d$chart$2d$column$2d$increasing$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__FileBarChart$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/file-chart-column-increasing.mjs [app-client] (ecmascript) <export default as FileBarChart>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$folder$2d$search$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__FolderSearch$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/folder-search.mjs [app-client] (ecmascript) <export default as FolderSearch>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$inbox$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Inbox$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/inbox.mjs [app-client] (ecmascript) <export default as Inbox>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$settings$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Settings$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/settings.mjs [app-client] (ecmascript) <export default as Settings>");
;
const NAV_ITEMS = [
    {
        label: "Officer Inbox",
        href: "/officer",
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$inbox$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Inbox$3e$__["Inbox"]
    },
    {
        label: "Investigations",
        href: "/investigations",
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$folder$2d$search$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__FolderSearch$3e$__["FolderSearch"]
    },
    {
        label: "Reports",
        href: "/reports",
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$file$2d$chart$2d$column$2d$increasing$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__FileBarChart$3e$__["FileBarChart"]
    },
    {
        label: "Settings",
        href: "#",
        icon: __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$settings$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Settings$3e$__["Settings"]
    }
];
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/ui/GradientButtonGroup.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>GradientButtonGroup
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/client/app-dir/link.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/navigation.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$animation$2f$animate$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/framer-motion/dist/es/animation/animate/index.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$motion$2d$value$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/framer-motion/dist/es/value/use-motion-value.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$elements$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__MotionSpan__as__span$3e$__ = __turbopack_context__.i("[project]/node_modules/framer-motion/dist/es/render/components/motion/elements.mjs [app-client] (ecmascript) <export MotionSpan as span>");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/utils.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$ui$2f$ThemeToggle$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/ui/ThemeToggle.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$layout$2f$navItems$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/layout/navItems.ts [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature(), _s2 = __turbopack_context__.k.signature();
"use client";
;
;
;
;
;
;
;
;
const themes = {
    dark: {
        textActive: "text-white",
        textInactive: "text-[#6b6b6d] hover:text-zinc-400",
        iconColor: "text-white hover:text-zinc-300"
    },
    light: {
        textActive: "text-zinc-900",
        textInactive: "text-zinc-400 hover:text-zinc-600",
        iconColor: "text-zinc-700 hover:text-zinc-900"
    }
};
/**
 * This project keeps its own dark-mode system (a `dark` class on <html> plus
 * a localStorage flag — see ThemeToggle) rather than next-themes, so this
 * mirrors that mechanism instead of pulling in a second, disconnected
 * theme provider that wouldn't actually track the site's real theme.
 */ function useSiteTheme() {
    _s();
    const [isDarkMode, setIsDarkMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "useSiteTheme.useEffect": ()=>{
            const root = document.documentElement;
            setIsDarkMode(root.classList.contains("dark"));
            const observer = new MutationObserver({
                "useSiteTheme.useEffect": ()=>setIsDarkMode(root.classList.contains("dark"))
            }["useSiteTheme.useEffect"]);
            observer.observe(root, {
                attributes: true,
                attributeFilter: [
                    "class"
                ]
            });
            return ({
                "useSiteTheme.useEffect": ()=>observer.disconnect()
            })["useSiteTheme.useEffect"];
        }
    }["useSiteTheme.useEffect"], []);
    const toggleTheme = ()=>{
        const isDark = document.documentElement.classList.toggle("dark");
        try {
            window.localStorage.setItem(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$ui$2f$ThemeToggle$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["THEME_STORAGE_KEY"], isDark ? "dark" : "light");
        } catch  {
        // Storage can be unavailable (private browsing, blocked cookies).
        }
    };
    return {
        isDarkMode,
        toggleTheme
    };
}
_s(useSiteTheme, "wcg0iE8CdipV533flP6RCfuqOPI=");
function isRouteActive(pathname, href) {
    if (!pathname || href === "#") return false;
    return pathname === href || pathname.startsWith(`${href}/`);
}
function InnerButtonOverlay({ isOverlayActive, isDarkMode }) {
    _s1();
    const overlayProgress = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$motion$2d$value$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMotionValue"])(isOverlayActive ? 1 : 0);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "InnerButtonOverlay.useEffect": ()=>{
            const controls = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$animation$2f$animate$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["animate"])(overlayProgress, isOverlayActive ? 1 : 0, {
                delay: isOverlayActive ? 0.02 : 0,
                duration: isOverlayActive ? 0.18 : 0.14,
                ease: "easeOut"
            });
            return ({
                "InnerButtonOverlay.useEffect": ()=>controls.stop()
            })["InnerButtonOverlay.useEffect"];
        }
    }["InnerButtonOverlay.useEffect"], [
        isOverlayActive,
        overlayProgress
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$elements$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__MotionSpan__as__span$3e$__["span"], {
        initial: false,
        className: "absolute inset-0 rounded-[10px]",
        animate: isOverlayActive ? {
            borderWidth: 1,
            borderColor: isDarkMode ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)"
        } : {
            borderWidth: 0,
            borderColor: "transparent",
            boxShadow: "none"
        },
        transition: {
            borderColor: {
                duration: 0.16,
                ease: "easeOut"
            }
        },
        style: {
            borderStyle: "solid"
        }
    }, void 0, false, {
        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
        lineNumber: 65,
        columnNumber: 5
    }, this);
}
_s1(InnerButtonOverlay, "RPYgqk9+MM9OOF0nfEb0JmqTyI4=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$motion$2d$value$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMotionValue"]
    ];
});
_c = InnerButtonOverlay;
function GradientButtonGroup() {
    _s2();
    const pathname = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["usePathname"])();
    const { isDarkMode, toggleTheme } = useSiteTheme();
    const theme = isDarkMode ? themes.dark : themes.light;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "pointer-events-none fixed inset-x-0 bottom-4 z-50 flex w-full justify-center py-1 sm:bottom-6",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "inline-flex min-w-max origin-center scale-[0.72] items-center sm:scale-[0.82] md:scale-[0.9] lg:scale-100",
            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "relative inline-flex items-center",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "absolute inset-0 z-0 rounded-[28px] transition-colors duration-300",
                        style: {
                            background: isDarkMode ? "linear-gradient(180deg, #141416 0%, #111113 50%, #0e0e10 100%)" : "linear-gradient(180deg, #d1d1d6 0%, #cacad0 50%, #c3c3c9 100%)",
                            boxShadow: isDarkMode ? "inset 0 2px 8px rgba(0,0,0,0.6), inset 0 1px 2px rgba(0,0,0,0.4), 0 1px 0 rgba(255,255,255,0.04)" : "inset 0 2px 6px rgba(0,0,0,0.1), inset 0 0 0 1px rgba(0,0,0,0.08), 0 1px 0 rgba(255,255,255,0.55)"
                        }
                    }, void 0, false, {
                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                        lineNumber: 83,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "relative flex z-10",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "absolute -inset-[4px] rounded-[28px] border-[1px] bg-muted dark:bg-background transition-colors duration-300",
                                style: {
                                    borderColor: isDarkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.08)"
                                }
                            }, void 0, false, {
                                fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                lineNumber: 91,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("nav", {
                                "aria-label": "Primary navigation",
                                className: "pointer-events-auto relative inline-flex items-center gap-3 rounded-[24px] p-1.5 transition-colors duration-300",
                                style: {
                                    background: isDarkMode ? "linear-gradient(180deg, #1c1c1f 0%, #17171a 52%, #131316 100%)" : "linear-gradient(180deg, #ffffff 0%, #fefeff 52%, #fcfcfe 100%)",
                                    borderTop: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid rgba(255,255,255,1)",
                                    boxShadow: isDarkMode ? "none" : "0 1px 2px rgba(0,0,0,0.04), 0 1px 0 rgba(255,255,255,1)"
                                },
                                children: __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$layout$2f$navItems$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["NAV_ITEMS"].map((item)=>{
                                    const isActive = isRouteActive(pathname, item.href);
                                    const Icon = item.icon;
                                    const isOverlayActive = isActive;
                                    const wellStyle = isDarkMode ? {
                                        background: "linear-gradient(180deg, #0a0a0c 0%, #0e0e10 50%, #0c0c0e 100%)",
                                        boxShadow: "inset 0 2px 6px rgba(0,0,0,0.9), inset 0 0 4px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.05)"
                                    } : {
                                        boxShadow: "inset 0 2px 6px rgba(0,0,0,0.12), inset 0 0 4px rgba(0,0,0,0.06), 0 1px 0 rgba(255,255,255,0.9)"
                                    };
                                    const innerGapStyle = isDarkMode ? {
                                        background: "#0a0a0d",
                                        boxShadow: "inset 0 1px 3px rgba(0,0,0,0.9), inset 0 0 2px rgba(0,0,0,0.6)"
                                    } : {
                                        boxShadow: "inset 0 1px 3px rgba(0,0,0,0.18), inset 0 0 2px rgba(0,0,0,0.1)"
                                    };
                                    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                        href: item.href,
                                        "aria-label": item.label,
                                        "aria-current": isActive ? "page" : undefined,
                                        title: item.label,
                                        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["cn"])("group/nav relative flex h-[76px] w-[76px] items-center justify-center rounded-[18px] transition-all duration-300", isActive ? theme.textActive : theme.textInactive),
                                        children: [
                                            isActive && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$elements$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__MotionSpan__as__span$3e$__["span"], {
                                                        layoutId: "active-well",
                                                        className: "absolute inset-0 bg-muted rounded-[18px] transition-colors duration-300",
                                                        style: wellStyle,
                                                        transition: {
                                                            type: "spring",
                                                            stiffness: 400,
                                                            damping: 30
                                                        }
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                        lineNumber: 118,
                                                        columnNumber: 25
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$elements$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__MotionSpan__as__span$3e$__["span"], {
                                                        layoutId: "active-purple-ring",
                                                        className: "absolute inset-[3px] overflow-hidden rounded-[15px]",
                                                        transition: {
                                                            type: "spring",
                                                            stiffness: 400,
                                                            damping: 30
                                                        },
                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "absolute inset-[-60%] origin-center will-change-transform animate-gold-spin",
                                                            style: {
                                                                background: "conic-gradient(from 220deg, #a855f7 0%, #7c3aed 18%, #6366f1 36%, #c084fc 52%, #8b5cf6 70%, #a855f7 86%, #a855f7 100%)"
                                                            }
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                            lineNumber: 120,
                                                            columnNumber: 27
                                                        }, this)
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                        lineNumber: 119,
                                                        columnNumber: 25
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$elements$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__MotionSpan__as__span$3e$__["span"], {
                                                        layoutId: "active-inner-ring",
                                                        className: "absolute inset-[6px] bg-muted rounded-[12px] transition-colors duration-300",
                                                        style: innerGapStyle,
                                                        transition: {
                                                            type: "spring",
                                                            stiffness: 400,
                                                            damping: 30
                                                        }
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                        lineNumber: 122,
                                                        columnNumber: 25
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                lineNumber: 117,
                                                columnNumber: 23
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$elements$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__MotionSpan__as__span$3e$__["span"], {
                                                initial: false,
                                                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["cn"])("relative z-10 flex items-center justify-center rounded-[10px]", isActive ? "h-[calc(100%-18px)] w-[calc(100%-18px)]" : "h-full w-full"),
                                                animate: isActive ? {
                                                    scale: 1,
                                                    opacity: 1
                                                } : {
                                                    scale: 0.985,
                                                    opacity: 0.96
                                                },
                                                transition: {
                                                    type: "spring",
                                                    stiffness: 380,
                                                    damping: 30,
                                                    delay: isActive ? 0.12 : 0
                                                },
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(InnerButtonOverlay, {
                                                        isOverlayActive: isOverlayActive,
                                                        isDarkMode: isDarkMode
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                        lineNumber: 126,
                                                        columnNumber: 23
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Icon, {
                                                        className: "relative z-10 h-6 w-6",
                                                        strokeWidth: 1.7,
                                                        "aria-hidden": "true"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                        lineNumber: 127,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                lineNumber: 125,
                                                columnNumber: 21
                                            }, this)
                                        ]
                                    }, item.label, true, {
                                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                        lineNumber: 108,
                                        columnNumber: 19
                                    }, this);
                                })
                            }, void 0, false, {
                                fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                lineNumber: 92,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "pointer-events-auto relative z-[1] flex items-center px-4",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    type: "button",
                                    onClick: toggleTheme,
                                    "aria-label": "Toggle dark mode",
                                    title: "Toggle dark mode",
                                    className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$utils$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["cn"])("relative flex h-[60px] w-[60px] items-center justify-center rounded-[16px] transition-colors", theme.iconColor),
                                    children: isDarkMode ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                        width: "28",
                                        height: "28",
                                        viewBox: "0 0 24 24",
                                        fill: "none",
                                        stroke: "currentColor",
                                        strokeWidth: "1.5",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                                                cx: "12",
                                                cy: "12",
                                                r: "4"
                                            }, void 0, false, {
                                                fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                lineNumber: 136,
                                                columnNumber: 119
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                d: "M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"
                                            }, void 0, false, {
                                                fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                                lineNumber: 136,
                                                columnNumber: 151
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                        lineNumber: 136,
                                        columnNumber: 19
                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                        width: "26",
                                        height: "26",
                                        viewBox: "0 0 24 24",
                                        fill: "none",
                                        stroke: "currentColor",
                                        strokeWidth: "1.5",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                            d: "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
                                        }, void 0, false, {
                                            fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                            lineNumber: 138,
                                            columnNumber: 119
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                        lineNumber: 138,
                                        columnNumber: 19
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                    lineNumber: 134,
                                    columnNumber: 15
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                                lineNumber: 133,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                        lineNumber: 90,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/ui/GradientButtonGroup.tsx",
                lineNumber: 82,
                columnNumber: 9
            }, this)
        }, void 0, false, {
            fileName: "[project]/components/ui/GradientButtonGroup.tsx",
            lineNumber: 81,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/components/ui/GradientButtonGroup.tsx",
        lineNumber: 80,
        columnNumber: 5
    }, this);
}
_s2(GradientButtonGroup, "5SDNXDNimRhB/S5cElOGi3c3n8c=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["usePathname"],
        useSiteTheme
    ];
});
_c1 = GradientButtonGroup;
var _c, _c1;
__turbopack_context__.k.register(_c, "InnerButtonOverlay");
__turbopack_context__.k.register(_c1, "GradientButtonGroup");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/ui/ThemeToggle.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "THEME_STORAGE_KEY",
    ()=>THEME_STORAGE_KEY,
    "ThemeToggle",
    ()=>ThemeToggle
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$moon$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Moon$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/moon.mjs [app-client] (ecmascript) <export default as Moon>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$sun$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Sun$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/sun.mjs [app-client] (ecmascript) <export default as Sun>");
"use client";
;
;
const THEME_STORAGE_KEY = "aria-theme";
function ThemeToggle() {
    const toggleTheme = ()=>{
        const isDark = document.documentElement.classList.toggle("dark");
        try {
            window.localStorage.setItem(THEME_STORAGE_KEY, isDark ? "dark" : "light");
        } catch  {
        // Storage can be unavailable (private browsing, blocked cookies). The
        // toggle still works for this session; only persistence is lost.
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
        type: "button",
        onClick: toggleTheme,
        "aria-label": "Toggle dark mode",
        title: "Toggle dark mode",
        className: "inline-flex h-11 w-11 items-center justify-center rounded-xl border border-transparent text-slate-400 transition-all duration-200 hover:border-purple-300/35 hover:bg-purple-500/15 hover:text-purple-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-300 sm:h-12 sm:w-12",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$sun$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Sun$3e$__["Sun"], {
                className: "hidden h-5 w-5 dark:block",
                "aria-hidden": "true"
            }, void 0, false, {
                fileName: "[project]/components/ui/ThemeToggle.tsx",
                lineNumber: 37,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$moon$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Moon$3e$__["Moon"], {
                className: "h-5 w-5 dark:hidden",
                "aria-hidden": "true"
            }, void 0, false, {
                fileName: "[project]/components/ui/ThemeToggle.tsx",
                lineNumber: 38,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/ui/ThemeToggle.tsx",
        lineNumber: 30,
        columnNumber: 5
    }, this);
}
_c = ThemeToggle;
var _c;
__turbopack_context__.k.register(_c, "ThemeToggle");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/lib/utils.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "cn",
    ()=>cn
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$clsx$2f$dist$2f$clsx$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/clsx/dist/clsx.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/tailwind-merge/dist/bundle-mjs.mjs [app-client] (ecmascript)");
;
;
function cn(...inputs) {
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["twMerge"])((0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$clsx$2f$dist$2f$clsx$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["clsx"])(inputs));
}
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/services/api.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ApiError",
    ()=>ApiError,
    "createInvestigationRequest",
    ()=>createInvestigationRequest,
    "getInvestigationRequest",
    ()=>getInvestigationRequest,
    "getMeRequest",
    ()=>getMeRequest,
    "getMockBankCustomer",
    ()=>getMockBankCustomer,
    "getMockBankTransactions",
    ()=>getMockBankTransactions,
    "heartbeatPresenceRequest",
    ()=>heartbeatPresenceRequest,
    "investigateAlertRequest",
    ()=>investigateAlertRequest,
    "listAlertsRequest",
    ()=>listAlertsRequest,
    "listAssignmentsRequest",
    ()=>listAssignmentsRequest,
    "listInvestigationsRequest",
    ()=>listInvestigationsRequest,
    "listPresenceRequest",
    ()=>listPresenceRequest,
    "runInvestigationRequest",
    ()=>runInvestigationRequest,
    "setAccessTokenProvider",
    ()=>setAccessTokenProvider,
    "uploadDocumentRequest",
    ()=>uploadDocumentRequest
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
// The backend requires a shared-secret X-API-Key header (P1 hardening).
// That secret must never reach browser JS. Server Components (this code
// running in Node.js) call the backend directly and attach it from a
// non-public env var; the browser instead calls the same-origin Next.js
// proxy route, which attaches the secret server-side. See
// app/api/proxy/[...path]/route.ts.
const isServer = ("TURBOPACK compile-time value", "object") === "undefined";
const API_BASE = ("TURBOPACK compile-time falsy", 0) ? "TURBOPACK unreachable" : "/api/proxy";
class ApiError extends Error {
    status;
    constructor(message, status){
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}
async function responseMessage(response) {
    try {
        const body = await response.json();
        if (typeof body === "object" && body !== null && "detail" in body) {
            const detail = body.detail;
            if (typeof detail === "string") return detail;
        }
    } catch  {
    // The server may return an empty or non-JSON error response.
    }
    return response.statusText || `Request failed with status ${response.status}`;
}
let accessTokenProvider = null;
function setAccessTokenProvider(provider) {
    accessTokenProvider = provider;
}
async function requestJson(path, init, /** Officer token for Server Components, which have no browser session. */ accessToken) {
    const headers = {
        Accept: "application/json",
        ...init?.headers
    };
    if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
    // Investigator identity travels as a bearer token the backend verifies
    // against Supabase's public keys. A caller cannot name an investigator any
    // other way, so this is the only route by which actions become attributable.
    if (!isServer && accessTokenProvider) {
        try {
            const token = await accessTokenProvider();
            if (token) headers["Authorization"] = `Bearer ${token}`;
        } catch  {
        // A missing session must not break unauthenticated reads.
        }
    }
    // Only attach the secret on the server: process.env.API_SHARED_SECRET is
    // never inlined into the client bundle (only NEXT_PUBLIC_* vars are), so
    // this is always undefined in the browser — the header is simply omitted
    // there and the same-origin proxy attaches it instead.
    if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
    ;
    let response;
    try {
        response = await fetch(`${API_BASE}${path}`, {
            ...init,
            headers
        });
    } catch  {
        throw new ApiError("The investigation service is unavailable. Check your connection and try again.");
    }
    if (!response.ok) {
        throw new ApiError(await responseMessage(response), response.status);
    }
    try {
        return await response.json();
    } catch  {
        throw new ApiError("The investigation service returned an incomplete response.", response.status);
    }
}
function listInvestigationsRequest() {
    return requestJson("/investigations", {
        cache: "no-store"
    });
}
function getInvestigationRequest(caseId, /** Supplied by Server Components, which have no browser session to read. */ accessToken) {
    return requestJson(`/investigations/${encodeURIComponent(caseId)}`, {
        cache: "no-store"
    }, accessToken);
}
function createInvestigationRequest(accountId) {
    const url = accountId ? `/investigations?account_id=${encodeURIComponent(accountId)}` : "/investigations";
    return requestJson(url, {
        method: "POST"
    });
}
function runInvestigationRequest(caseId) {
    return requestJson(`/investigations/${encodeURIComponent(caseId)}/run`, {
        method: "POST"
    });
}
async function uploadDocumentRequest(caseId, file, documentType = "OTHER") {
    if (!caseId.trim()) {
        throw new ApiError("A valid investigation ID is required before uploading a document.");
    }
    const body = new FormData();
    body.append("file", file);
    body.append("document_type", documentType);
    return requestJson(`/investigations/${encodeURIComponent(caseId)}/documents`, {
        method: "POST",
        body
    });
}
function getMockBankTransactions(accountId) {
    return requestJson(`/mock-bank/accounts/${encodeURIComponent(accountId)}/transactions`, {
        cache: "no-store"
    });
}
function getMockBankCustomer(customerId) {
    return requestJson(`/mock-bank/customers/${encodeURIComponent(customerId)}`, {
        cache: "no-store"
    });
}
function listAlertsRequest(status = "OPEN") {
    return requestJson(`/alerts?status=${status}`);
}
function investigateAlertRequest(alertId) {
    return requestJson(`/alerts/${encodeURIComponent(alertId)}/investigate`, {
        method: "POST"
    });
}
function getMeRequest() {
    return requestJson("/investigators/me");
}
function listPresenceRequest() {
    return requestJson("/presence");
}
function heartbeatPresenceRequest(caseId) {
    return requestJson(`/presence/${encodeURIComponent(caseId)}/heartbeat`, {
        method: "POST"
    });
}
function listAssignmentsRequest() {
    return requestJson("/investigators/assignments");
}
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/services/supabaseClient.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "getSupabaseClient",
    ()=>getSupabaseClient,
    "isAuthConfigured",
    ()=>isAuthConfigured
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$supabase$2f$ssr$2f$dist$2f$module$2f$createBrowserClient$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@supabase/ssr/dist/module/createBrowserClient.js [app-client] (ecmascript)");
;
/**
 * Browser-side Supabase Auth client.
 *
 * Only the project URL and the anon key are used. Both are public by design —
 * the anon key is meant to ship in browser JS and is protected by RLS, not by
 * secrecy. The service-role key is never referenced here or anywhere in the
 * frontend.
 *
 * Supabase is the sole source of investigator identity: the app holds no
 * password and issues no session of its own.
 */ const SUPABASE_URL = ("TURBOPACK compile-time value", "https://rwrgjcujhmvdboggmctf.supabase.co") ?? "";
const SUPABASE_ANON_KEY = ("TURBOPACK compile-time value", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3cmdqY3VqaG12ZGJvZ2dtY3RmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY4NTczOTEsImV4cCI6MjEwMjQzMzM5MX0.eZQM5Pa7skwfUnN5c8bRzRSqlpLOPlhK5IzAOnHCoNs") ?? "";
let client = null;
function isAuthConfigured() {
    return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}
function getSupabaseClient() {
    if (!isAuthConfigured()) return null;
    if (client === null) {
        client = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$supabase$2f$ssr$2f$dist$2f$module$2f$createBrowserClient$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["createBrowserClient"])(SUPABASE_URL, SUPABASE_ANON_KEY);
    }
    return client;
}
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=_1wgohkx._.js.map