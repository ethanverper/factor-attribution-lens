# 0018. Phase 10i: React/Tailwind/shadcn frontend rebuild — implementation decisions

Date: 2026-08-11
Status: accepted

## Context

Decision 0017 (`brand-creative`) specified the full rebuild — Tailwind/shadcn token mapping, component-to-primitive mapping, the Overview hero, the mark/motion plan, and a per-section visual-density table. This decision logs the real implementation choices `developer` made building against that spec, and the places where the spec's own flagged uncertainties (KaTeX, GSAP vs. Framer Motion, exact `Empty` sub-API) resolved into concrete answers, plus one deliberate deviation.

## Decision

### 1. Backend: `app/dashboard/` removed, `app/api/` added

`app/dashboard/`'s HTML/SVG/vanilla-JS rendering modules (`routes.py`, `pages.py`, `shell.py`, `viz.py`, `motion.py`, `mark.py`, `diagrams.py`) are deleted outright — fully superseded by the React frontend, nothing left half-migrated. Two modules that were pure data/computation, not rendering, moved into a new `app/api/` package instead of being deleted:

- `tickers.py` (the curated S&P 500/benchmark universe) — unchanged content, docstring updated to describe the new JSON consumer.
- `attribution.py` (return/risk attribution derived from Phase 2 output) — unchanged logic.

New `app/api/routes.py` exposes three endpoints:

- **`POST /api/analysis`** — the headline change. `analyze_portfolio()` (Phase 2) was previously only ever reachable from inside the old server-rendered `POST /dashboard` route; it had no JSON contract of its own. This endpoint runs the exact same `build_portfolio_return_data` → `analyze_portfolio` pipeline, adds the same server-side ticker/benchmark validation the old dashboard route had (400 on an invalid symbol, defense in depth against a request that bypasses the frontend's own constrained `Combobox`), and returns `{meta, analysis, return_attribution, risk_attribution}` as one bundle (`app/api/schemas.py::AnalysisResponse`).
- **`GET /api/tickers`** — the curated universe as JSON (`{tickers: [...], benchmarks: [...], source_note}`), replacing the old server-embedded `window.__FL_TICKERS__` script tag.
- **`GET /api/sample`** — the fixed sample-portfolio default (AAPL 40/MSFT 30/GOOGL 20/AMZN 10 vs. `^GSPC`), so the Overview hero and the Inputs/quick-start button don't each hardcode it separately.

`POST /portfolio/returns` (Phase 1) is untouched — it remains the lower-level "aligned returns, no modeling" endpoint `POST /api/analysis` is built on top of, not replaced by it.

The shareable-link feature is now genuinely URL-native rather than a server-side replay route: `/results?symbol=...&weight=...&benchmark=...&start_date=...&end_date=...&factor_model=...&frequency=...` is parsed client-side (`frontend/src/lib/query.ts`) into a request body and posted to `/api/analysis` on mount. `GET /dashboard/view` is gone; there's no server-side equivalent needed. This was flagged as a likely improvement in decision 0017 and confirmed one in practice — no server code owns the shareable-link mechanism at all now.

### 2. Deployment shape: one service, not two

FastAPI serves the frontend's built static assets directly (`app/main.py`): `StaticFiles` mounted at `/assets` for the Vite build's hashed JS/CSS, plus a catch-all route serving `index.html` for any other non-API path (the SPA fallback React Router's client-side routes need on a hard refresh or deep link). The catch-all is registered *after* `/health`, `/portfolio/returns`, and the `/api/*` router in the file so it can never shadow a real route — FastAPI/Starlette matches routes in registration order.

This means: `uv run uvicorn app.main:app` alone serves nothing at `/` until `frontend/dist/` exists (`npm run build` first); the mount is conditional (`if _FRONTEND_DIST.is_dir()`) so the API remains fully usable standalone in local development without ever building the frontend. Chosen over a two-service split (API + a static host/CDN for the frontend) because it's simpler for `devops`'s Phase 11 handoff — one Railway service, one Dockerfile that runs `npm run build` then starts uvicorn, no CORS configuration needed since the frontend and API share an origin in production. The tradeoff: a frontend-only change still requires a full backend redeploy to ship, and the backend process now needs Node available at build time (not at runtime) — acceptable for this project's scale.

### 3. GSAP, not Framer Motion — confirmed, not re-litigated

Decision 0017 §4 already made this call and flagged it as worth revisiting only if GSAP's React ergonomics proved genuinely worse in practice. They didn't: `gsap.context(...).revert()` in a `useEffect` cleanup is a clean, idiomatic pattern for React (no fighting React's render cycle, no stale closures), and every motion surface in this rebuild (`RouteFade`, `RevealSection`, `StatTile`'s count-up, the three Learning diagrams' reveal timelines) follows the same three-line shape: build the timeline in an effect gated on `useReducedMotion()`/`useInView()`, return `ctx.revert()`. GSAP stays self-hosted via the npm package (not vendored as a static file the way the old app did, since a real bundler is now in play — Vite tree-shakes and bundles it like any other dependency). No ScrollTrigger plugin — nothing here scroll-scrubs, `IntersectionObserver` via `useInView` is sufficient for the one-shot reveal triggers, exactly as decision 0017 predicted.

### 4. Frontier and diverging-bar charts: Recharts, with real custom-geometry deviations

Decision 0017 recommended Recharts wrapped in shadcn's `Chart` primitive for both the diverging-bar (factor loadings/return attribution) and frontier charts. Both are built that way — but two pieces of genuinely custom geometry from the old hand-drawn SVG charts don't map onto Recharts' out-of-the-box marks, and were implemented as documented deviations rather than silently dropped:

- **CI whiskers on diverging bars** (`DivergingBarChart.tsx`) use Recharts' "floating bar" pattern — a second, thin `Bar` whose `dataKey` resolves to a `[ciLower, ciUpper]` tuple, positioned by the same numeric x-scale as the value bar. This is a real, documented Recharts technique (not a hack), and keeps the whisker a first-class chart element rather than an SVG overlay.
- **Frontier marker label merging** (`FrontierChart.tsx`) ports decision 0011's behavior (coincident/near-identical markers get one merged label instead of stacking illegibly) via a **domain-normalized** distance threshold (two markers "coincide" if within 3% of the plotted volatility/return span on both axes) rather than the original's **pixel**-based union-find clustering. Recharts' `Scatter` `shape` render prop does hand back the correct pixel `cx`/`cy` per point, but computing pairwise pixel distance would require querying Recharts' internal scale from outside the render pass; the domain-normalized version needs no such access, is computed once before render, and produces materially the same behavior (near-identical points merge, distinct points don't) — verified live in the browser against a real degenerate-portfolio case ("Global min-variance = Your portfolio" merged correctly, "Max Sharpe (tangency)" stayed separate). Documented here as a real, deliberate tradeoff, not a silent simplification.

### 5. KaTeX: not adopted

Decision 0017 flagged upgrading the hand-rolled `<sub>/<sup>` HTML notation to real KaTeX as recommended-not-required, now that a real build step removes the constraint that originally forced the HTML-entity workaround. Given the scope of this rebuild (eight full sections, all-new component architecture, a new charting library, a new motion system), it was deprioritized — the References & Formulas content ported with the same `<sub>/<sup>`/HTML-entity notation as before (rendered via `dangerouslySetInnerHTML` on static, hand-authored, non-user-input strings — the same trust model the old Python code used). This is real, cited scope left on the table: a genuine visual-quality lever, not taken, flagged here rather than silently skipped.

### 6. shadcn CLI base library: Radix, not the new default (Base UI)

The current `shadcn` CLI (v4.17) defaults new inits to a "Nova" preset built on Base UI (`@base-ui/react`) rather than Radix primitives. This produced components (`Button`, `Popover`, `Command`, etc.) with a different polymorphic-rendering API (a `render` prop instead of Radix's documented `asChild`/`Slot` pattern) that decision 0017's component mapping implicitly assumed away (every shadcn doc, and this decision's own prior research, was written against the Radix-based API). Re-initialized explicitly against `-b radix` (the `vega` preset) instead — this is what every other Cowork OS reference (decision 0017's own research, the `shadcn-ui` skill) assumes, and keeps the component set behaviorally identical to standard, widely-documented shadcn/ui. Logged here since it's a real, non-obvious tooling gotcha future phases on this stack should know about.

### 7. What shipped vs. what's flagged for follow-up

**Shipped, verified live**: all eight sections as real routes; the sample-portfolio quick-start and manual holdings entry (Combobox + paired number/slider allocation controls with live total/split-evenly/normalize) end to end against live data; the Overview hero's live mini-frontier-chart preview with a real precision-stat callout; all three Results charts (factor-loading bars with CI whiskers, frontier with marker-label merging, return/risk attribution); the Learning section's three GSAP-revealed diagrams; the 27-term grouped Glossary accordion; the Tools & Technologies icon-per-category grid; the References & Formulas card set with the full citation list; the Real World pull-quote/stat-callout cards; light/dark mode; mobile (Sheet-collapsed sidebar); the shareable-link URL mechanism (deep-link tested with a hard navigation, not just in-app routing); server-side error states (invalid ticker/benchmark, degenerate single-asset frontier) rendering through shadcn's `Empty` component.

**Not independently re-verified in this pass**: `prefers-reduced-motion` is implemented (every GSAP effect checks `useReducedMotion()` and sets the final state instantly instead of animating; a blanket CSS `@media (prefers-reduced-motion: reduce)` rule in `index.css` disables all CSS transitions/animations as a backstop) but this sandboxed browser environment doesn't expose a way to emulate that media feature live, so it was verified by code review rather than a driven browser test — flagged explicitly per the "say so if you couldn't verify something end to end" standard.

**Known, deliberately deferred**: the production JS bundle is a single ~1MB chunk (Vite's own build warns on this) — no code-splitting was added given time constraints; a reasonable Phase 11-adjacent follow-up (route-based `React.lazy` splitting) but not a functional defect. KaTeX (§5) and pixel-exact (vs. domain-normalized) frontier-label clustering (§4) are the other two named, deliberate scope decisions above.
