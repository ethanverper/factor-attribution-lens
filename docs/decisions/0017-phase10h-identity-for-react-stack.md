# 0017. Phase 10h: identity direction for the React/Tailwind/shadcn rebuild

Date: 2026-08-11
Status: accepted

## Context

Decision 0004 (Cowork OS root) traced Factor Lens's fourth round of frontend feedback to the architecture itself, not the taste applied to it: a hand-rolled server-rendered/inline-SVG/vanilla-JS stack has a lower ceiling than a real component system, no matter how much identity work (decisions 0012, 0015) or QA rigor goes on top of it. The team's new default is React (Vite + TypeScript) + Tailwind CSS + shadcn/ui, backend reduced to a pure JSON API. This decision re-grounds decisions 0012 (identity) and 0015 (motion) in that real stack — it does not redo their research, it translates their conclusions into shadcn primitives and Tailwind tokens `developer` can build directly.

Ethan's verbatim complaint, which sets the bar this spec has to clear: *"plain text app... sin nada interactivo, de mejor diseño, ni nada innovador... no se ve ningún branding... tiene que llamar la atención de headhunters,"* explicitly benchmarked against an **investment-banking-grade pitch/sales deck**. That is a real, high bar: not "less plain," but something that would make a hiring manager stop scrolling.

## Audit of the live app (before proposing anything)

Ran the current server-rendered app locally and drove it through the in-app Browser tools rather than reasoning from memory:

- **Overview** is exactly what Ethan described: a one-paragraph intro over three flat, identical, equal-width text cards (CAPM / Fama-French / Markowitz), no imagery, no chart, no asymmetry. This is the single highest-leverage page to fix — it's the first thing anyone sees.
- **Real World / Corporate Applications** is a wall of paragraph text per card, with tag-pill labels as the only structural device (`Multi-factor risk models`, `Barra / Axioma / MSCI`, `Risk decomposition`) — confirmed live, two full paragraphs per card, no numbers pulled out, no icons.
- **Tools & Technologies** is five flat category groups, each a bold tool name followed by a sentence — confirmed live via `get_page_text`. No icons anywhere in the section, despite it existing specifically to read like "a hiring manager's checklist" (rule 13).
- **Results** (via the sample-portfolio quick-start) is actually the app's best-designed page already — real stat tiles, mono tabular data, the frontier/bar SVG charts, a freshness banner, share/export controls. This should be preserved in spirit, not thrown out — the rebuild's job here is component fidelity (real `Card`/`Chart` primitives, real Recharts) more than a new design.

## Research — real products and systems actually studied for this phase

- **shadcn/ui itself** (`ui.shadcn.com`, browsed live, not from training memory): the `dashboard-01` block (`npx shadcn add dashboard-01`) is the team's own reference implementation of exactly this app's shape — a collapsible `Sidebar`, stat `Card`s with trend badges, an interactive area `Chart`, a `Data Table` below. Confirmed the `Chart` component's real API (`ChartContainer`, `ChartTooltip`, `ChartTooltipContent`, built directly on Recharts v3, themed via `--chart-1`…`--chart-5` CSS tokens — "we do not wrap Recharts, the components are yours"). Confirmed the `Sidebar` composition (`SidebarProvider > Sidebar > SidebarHeader/SidebarContent/SidebarGroup/SidebarMenu/SidebarMenuItem/SidebarMenuButton`) and the full component list, including `Combobox`, `Empty`, `Skeleton`, `Slider`, `Accordion`, `Table` — all named below are real, currently-shipping shadcn components, not generic descriptions.
- **stripe.com/payments** (browsed live): the hero is a genuine split layout — left, a tight headline/subtext/CTA stack; right, a **real, live-feeling embedded product UI** (an actual checkout flow screenshot: shipping address, payment method tabs, order summary, running total), not an illustration or a div-drawn fake. This is the concrete pattern this decision borrows for Factor Lens's own hero (see below) — a real preview of the actual product, not decoration.
- **Decisions 0012's Stripe/Linear/Mercury research stands** — restrained 480–510 headline weight, one functional accent used only on the single most important element per view, real specific numbers used as a branding device, near-black/off-white (not pure) dark mode. Not re-derived here; carried forward.
- **ycharts.com** (browsed live, a real, directly-comparable competitor already cited in this project's own Real World section) was checked and explicitly **rejected** as a reference: generic corporate-blue gradient hero, no embedded product visual, dated component styling. Noted so it's clear this was checked, not skipped — Factor Lens should not aspire to this bar, it should clear it.

## Decision

### 1. Tailwind / shadcn token mapping

Carry the existing graphite-navy/amber system forward by value, not by re-deriving new colors — these hex values are already live, tested in both themes, and validated against the `dataviz` palette (decision 0004, original). Source: `app/dashboard/viz.py::CHART_STYLE`.

Write these as CSS custom properties (shadcn's current CLI scaffolds Tailwind v4's CSS-first `@theme inline` convention; if `developer` scaffolds against Tailwind v3 instead, the same values go in `tailwind.config.ts`'s `theme.extend.colors` as `hsl(var(--x))`/`var(--x))` references — pick whichever `shadcn@latest init` actually generates and don't fight it):

```css
/* src/index.css — light (default) */
:root {
  --background:            #eef1f6;  /* page-plane */
  --foreground:             #0d1117;  /* text-primary */
  --card:                   #ffffff;  /* surface-1 */
  --card-foreground:        #0d1117;
  --popover:                #ffffff;  /* combobox/select menus */
  --popover-foreground:     #0d1117;
  --primary:                #a64d09;  /* signal amber — the ONE functional accent */
  --primary-foreground:     #ffffff;
  --secondary:              #e7ebf2;  /* surface-2 */
  --secondary-foreground:   #0d1117;
  --muted:                  #e7ebf2;
  --muted-foreground:       #4b5468;  /* text-secondary */
  --accent:                 #e7ebf2;  /* hover/active surfaces (nav items, menu items) */
  --accent-foreground:      #0d1117;
  --destructive:            #dc2626;  /* diverging-neg */
  --destructive-foreground: #ffffff;
  --border:                 rgba(13,17,23,0.10);
  --input:                  rgba(13,17,23,0.10);
  --ring:                   #a64d09;  /* focus rings pick up the signal color */
  --radius:                 0.625rem; /* 10px — matches the existing .viz-card radius */

  /* extended, not in shadcn's default set — used for badges/status, not decoration */
  --success:                #15803d;  /* status-good */
  --warning:                #b45309;  /* status-warning */

  /* chart tokens — feed shadcn's Chart component and Recharts <Bar>/<Line> fill/stroke directly */
  --chart-1: #2461ea;  /* series-1 — frontier line, factor-explained, positive loadings */
  --chart-2: #a64d09;  /* series-2/signal — current-portfolio emphasis */
  --chart-3: #15803d;  /* status-good — used sparingly for a positive-delta callout */
  --chart-4: #b45309;  /* status-warning */
  --chart-5: #dc2626;  /* diverging-neg — negative loadings/contributions */

  /* sidebar-specific tokens (shadcn's Sidebar ships its own token set) */
  --sidebar:                  #eef1f6;  /* page-plane, same as background — sidebar sits flush */
  --sidebar-foreground:       #0d1117;
  --sidebar-primary:          #a64d09;
  --sidebar-primary-foreground: #ffffff;
  --sidebar-accent:           #ffffff;  /* nav-item hover/active = surface-1, per current CSS */
  --sidebar-accent-foreground: #0d1117;
  --sidebar-border:           rgba(13,17,23,0.10);
  --sidebar-ring:              #a64d09;
}

.dark {
  --background:            #0a0d13;
  --foreground:             #eef1f6;
  --card:                   #12161f;
  --card-foreground:        #eef1f6;
  --popover:                #12161f;
  --popover-foreground:     #eef1f6;
  --primary:                #f0a63e;  /* amber lightens in dark mode, already validated live */
  --primary-foreground:     #0a0d13;  /* dark text on the lighter dark-mode amber, not white */
  --secondary:              #171c27;
  --secondary-foreground:   #eef1f6;
  --muted:                  #171c27;
  --muted-foreground:       #9aa3b5;
  --accent:                 #171c27;
  --accent-foreground:      #eef1f6;
  --destructive:            #ef6b6b;
  --destructive-foreground: #0a0d13;
  --border:                 rgba(255,255,255,0.08);
  --input:                  rgba(255,255,255,0.08);
  --ring:                   #f0a63e;

  --success:                #22c55e;
  --warning:                #e6b23c;

  --chart-1: #4c93f0;
  --chart-2: #f0a63e;
  --chart-3: #22c55e;
  --chart-4: #e6b23c;
  --chart-5: #ef6b6b;

  --sidebar:                  #0a0d13;
  --sidebar-foreground:       #eef1f6;
  --sidebar-primary:          #f0a63e;
  --sidebar-primary-foreground: #0a0d13;
  --sidebar-accent:           #12161f;
  --sidebar-accent-foreground: #eef1f6;
  --sidebar-border:           rgba(255,255,255,0.08);
  --sidebar-ring:              #f0a63e;
}
```

```css
/* font tokens — same three faces, same rationale as decision 0012/0013 */
@theme inline {
  --font-display: "Space Grotesk", ui-sans-serif, system-ui, sans-serif;
  --font-sans:    "Inter", ui-sans-serif, system-ui, sans-serif;   /* Tailwind's default body font slot */
  --font-mono:    "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}
```

**Non-negotiable carryover from decision 0012's single highest-leverage finding**: no shadcn/Tailwind default component may set `font-display`/heading text to `font-bold`. Every `h1`/`h2`/`CardTitle`/section heading uses `font-display font-medium` (weight 500) — shadcn's default `CardTitle` ships `font-semibold` (600), which must be overridden project-wide (a one-line Tailwind component override or a `className` convention `developer` applies consistently, not a per-instance fix). Reserve 600+ only for genuinely load-bearing single-stat values (the stat-tile number itself, the allocation total badge) — both already mono, not display-font "poster" text, exactly as decision 0012 specified.

**One-accent discipline carries over exactly**: `--primary`/`--chart-2`/`--sidebar-primary` are the *same* amber value everywhere on purpose. Audit before shipping (as decision 0013 had to do retroactively) that `--primary` is used only on the one primary CTA per view and the frontier's current-portfolio marker/legend — not on every card border, every active nav item glow, every badge. `--chart-1` through `--chart-5` exist so charts can use the full validated palette without reaching for `--primary` decoratively.

### 2. shadcn/ui primitive mapping — which component handles what

| App surface | shadcn primitive(s) | Notes |
|---|---|---|
| Primary 8-section navigation | `Sidebar` (`SidebarProvider`/`Sidebar`/`SidebarHeader`/`SidebarContent`/`SidebarGroup`/`SidebarMenu`/`SidebarMenuButton`), driving real React Router routes (`/`, `/inputs`, `/results`, `/learning`, `/glossary`, `/tools`, `/references`, `/real-world`) | **Change from the current app**: the 8 sections become real deep-linkable routes, not in-page tab panels — closes a real gap (`ui-ux-pro-max`'s `deep-linking` rule: every key screen must be reachable by URL). `SidebarTrigger` collapses to a `Sheet` on mobile, replacing the current horizontal scroll-strip. |
| Sidebar mobile collapse | `Sheet` (shadcn's built-in sidebar-mobile behavior) | Comes free with the `Sidebar` component, no separate build. |
| Ticker/benchmark selection (Inputs) | `Combobox` (Command + Popover composition) for holdings tickers (search over the curated ~496-symbol universe); `Select` for benchmark (6-item fixed list, no search needed) | Replaces the hand-built accessible combobox from Phase 7 with the real primitive. Citation of the curated universe's source/limitation (rule 7) stays inline next to the `Combobox`, not just in References & Formulas. |
| Allocation % input | Paired `Input` (type number, value of record) + `Slider` (Radix-based, decision 0015's dual-control spec carries over unchanged in concept) | `Slider`'s track fill uses `--primary`; thumb is a plain themed dot, not the aperture glyph (decision 0015's own guidance — don't compete with the real mark). |
| Allocation total state (exact/under/over) | `Badge` with `variant` swapped between a `success`/`default`/`destructive`-mapped custom variant | shadcn ships `default`/`secondary`/`destructive`/`outline` — add one `success` variant (maps to `--success`) since "exact" needs a real positive state distinct from the primary amber. |
| "Split evenly" / "Normalize to 100%" | `Button variant="outline" size="sm"` | Secondary actions, visually subordinate to the primary `Run analysis` button per the one-CTA-per-view rule. |
| Date range | `Popover` + `Calendar` (shadcn's documented Date Picker pattern) | Replaces whatever native date inputs exist today. |
| Run analysis submit | `Button` (default variant, `--primary`) with a `Spinner`-in-button loading state while the request is in flight | Disabled until allocation is within tolerance, exactly as today — `Button`'s built-in `disabled` styling. |
| Stat tiles (CAPM beta, alpha, R², etc.) | `Card`/`CardHeader`/`CardTitle`/`CardDescription`/`CardContent`, mono tabular-num values | Direct port of the current `.viz-stat-tile` — this part of the app already reads well, don't redesign it, just rebuild it as a real `Card`. |
| Diverging-bar charts (Fama-French loadings, return/risk attribution) | Recharts `BarChart` (horizontal, negative-aware) wrapped in shadcn's `ChartContainer`, `ChartTooltip`/`ChartTooltipContent` | CI whiskers as Recharts `ErrorBar` or a custom `<Bar>` shape — the geometry logic from `viz.py::_hbar_path` ports directly, only the rendering layer changes. |
| Efficient frontier chart | Recharts `ComposedChart` (`Line` for the curve, `Scatter` for GMV/max-Sharpe/current-portfolio markers) in `ChartContainer` | The current-portfolio marker uses a custom Recharts `shape` render prop drawing the **aperture-ring glyph** (see §4) instead of a default dot — this is the mark's one functional, non-decorative use, carried over exactly per decision 0012. |
| "View as table" twin under each chart | `Collapsible` (or `Accordion` with a single item) wrapping a shadcn `Table` | Replaces the native `<details>` twin — same behavior (manual, rare disclosure, opens instantly, no animation per decision 0015 §4's "what does NOT get animated"). |
| Chart/data loading state | `Skeleton` (in-place, per chart) for the Results page's data fetch; the full-page aperture/iris overlay (decision 0012 #3) stays for the Inputs→Results *navigation* moment specifically, not every fetch | Two different loading moments, two different treatments — don't collapse them into one. |
| "No analysis yet" empty state | shadcn's `Empty` component (`EmptyHeader`/`EmptyTitle`/`EmptyDescription`/`EmptyContent` — confirm exact subcomponent names against `npx shadcn add empty`'s generated source at build time, the API may have shifted) | This is a literal, exact-match upgrade — the current hand-built "No analysis yet" card becomes a real, purpose-built component instead of a bespoke `Card`. |
| Glossary (27 terms, 3 concept groups) | `Accordion` (`type="multiple"`), one `AccordionItem` per concept group (Factor models & regression / Portfolio theory & optimization / Attribution), each containing the dual-register term list | Per `ui-ux-pro-max`'s "long lists need a different UI, not a longer list" (>5 items): grouped `Accordion`, not one flat scroll. |
| Tools & Technologies | `Card` grid (2–3 columns, `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`), one `Card` per category, `lucide-react` icon in each `CardHeader` | Icon-per-category (5 icons total), not icon-per-tool-line — see §5. |
| Real World / Corporate Applications | `Card` grid retained, but each card gets a large display-weight stat pulled to the top (`CardTitle`-adjacent, mono, `--chart-2`/primary-colored) before the supporting paragraph | Turns "paragraph wall + tag pills" into a real pull-quote/stat-callout pattern — see §5. |
| References & Formulas | `Card` grid retained; **recommend upgrading the hand-rolled `<sub>/<sup>` HTML notation to real KaTeX** (`react-katex` or `better-react-mathjax`) now that a real build step exists (decision 0004 superseded the "no client library" constraint that originally forced the HTML-notation workaround in decision 0006) | Flagged as recommended, not mandatory — a genuine visual-quality lever `developer` should take if scope allows, since real rendered math reads meaningfully more "investment-banking-grade" than manual sub/sup HTML. |
| Share/export controls | `Button` group (`variant="outline"`) unchanged in behavior, restyled as real components | No functional change — shareable link and print-to-PDF logic are unaffected by the frontend rebuild. |
| Theme toggle | `Button variant="ghost" size="icon"` in `SidebarFooter` | Same placement as today. |

### 3. The Overview hero — the single biggest lever

The current Overview is three identical text cards under a paragraph — the exact "plain text app" Ethan is describing, and the first thing anyone sees. Replace it with a real split hero, grounded directly in the stripe.com/payments pattern studied above (a real embedded product preview, not an illustration):

**Layout**: asymmetric two-column hero (roughly 55/45 on desktop, stacks to one column under 768px). NOT centered — Factor Lens is a real analytical product, not a manifesto page.

- **Left column** (max 4 text elements, per hero discipline):
  - No eyebrow — the sidebar's own `[01] OVERVIEW` mark already does that job; a second eyebrow in the hero body is redundant.
  - Headline, ≤2 lines: keep the existing "Factor Lens explains why a portfolio behaves the way it does" — it's already tight and specific, don't touch it.
  - Subtext, trimmed to ≤20 words: the current paragraph runs 80+ words and needs to move below the fold as a "How it works" strip, not live in the hero itself. Something like: *"CAPM beta, Fama-French loadings, and Markowitz positioning — computed live, with statistical diagnostics shown alongside every estimate."*
  - CTAs: one primary (`Enter your holdings →`), one secondary (`Run a live example`) — unchanged from today, both already correctly single-intent.
- **Right column — the actual hero moment**: a real, live, **non-decorative** miniature of the Results page's own frontier chart, rendered with the sample portfolio's real numbers (AAPL/MSFT/GOOGL/AMZN), inside a `Card` styled like a genuine app window (not a fake browser chrome, just the same `Card`/border/shadow language used everywhere else in the app — honesty over skeuomorphism). On mount, it draws in with the same `stroke-dashoffset` technique used on the real Results page (§4/decision 0015) — this is a genuine preview of what the tool produces, reusing the actual chart component, not a bespoke hero graphic. This is the direct answer to "no chart in the hero" and to Stripe's pattern: show the real product, not an icon of it.
  - Below/beside the mini chart, one **precision-stat callout** in the Stripe "1.696%"-device sense: a real, live-computed number from that same sample run (e.g. `CAPM β 0.34 · R² 50.3%`), mono, large, `--primary`-colored — not invented, sourced from an actual `/portfolio/returns` call against the sample portfolio. This single device does more for "looks engineered, not templated" than any additional card would.
- **Below the hero, un-competing with it**: the existing three CAPM/Fama-French/Markowitz method cards can stay, but demoted to a plain 3-column feature row *under* the hero (not inside it) — per hero-stack discipline, feature bullets don't belong inside the hero itself.

### 4. The mark and motion language, carried into React

**Mark**: port `app/dashboard/mark.py::_rings_markup`'s exact construction (outer ring `r = size × 0.40`, mid ring `r = size × 0.255`, solid core `r = size × 0.105`, mid-ring stroke at 0.72× the outer stroke) into a single `<ApertureMark />` React component taking `size`/`className` props, using `currentColor` so it themes for free exactly as it does today. One component feeds every use:

- the sidebar masthead, next to the wordmark;
- the favicon (build as a real static SVG asset in `public/`, not a data-URI this time — a Vite app has a real static-asset pipeline, no reason to hand-encode a data URI anymore);
- the frontier chart's current-portfolio marker, as a Recharts `Scatter` custom `shape` prop rendering `<ApertureMark>` at the marker's pixel position — this is still the one functional, non-decorative use of the motif, unchanged from decision 0012's rationale;
- the hero's mini-chart marker (§3), for visual continuity between the hero preview and the real Results page;
- a loading-state variant (opening/closing rings) for the Inputs→Results route transition specifically — a real `<AnimatePresence>`/GSAP-driven sequence now, not a CSS-only `<animate>` SVG.

**Motion**: keep GSAP, don't re-derive the motion language with Framer Motion. Decision 0015 already produced a complete, validated, per-surface spec (exact durations, easings, what does/doesn't animate) and decision 0016 implemented it — re-running that research against a different library would discard validated work for no functional gain. GSAP works identically well inside React: isolate each animated surface in its own component, wire tweens in `useEffect`, clean up with `gsap.context(...).revert()` in the effect's return function (the standard, idiomatic React+GSAP pattern). Concretely, decision 0015's spec ports as:

- §1 (hover/press transitions) → Tailwind `transition-*` utilities directly on shadcn components — no JS needed, this was CSS-only from the start.
- §2 (tab fade) → superseded by real routes (§2 above); route transitions get a `220ms` opacity/`y` fade via GSAP on route change (React Router's `useLocation` + a wrapping transition component), same duration budget as the old tab fade.
- §3 (Inputs→Results arrival choreography) → unchanged in spec, now triggered by the route-mount `useEffect` instead of a full-page-load listener.
- §4 (stat-tile count-up, bar `scaleX` reveal, frontier `stroke-dashoffset` draw-in) → unchanged in spec; the count-up now animates a `useState` proxy number instead of writing into `.textContent` directly, everything else is the same technique against different DOM nodes.
- §5 (paired slider+number control) → the native `<input type=range>` becomes shadcn's `Slider`; the 120ms `:active` scale carries over as a Tailwind `active:scale-*` utility.
- §6 (scroll-triggered Learning diagram reveals) → unchanged, `IntersectionObserver` via a small `useInView` hook feeding the same GSAP timelines, no ScrollTrigger plugin needed (still true — nothing here scroll-scrubs).

**No new architecture required beyond what decision 0004 already committed to.** GSAP self-hosted, no ScrollTrigger, no ambient/looping motion beyond the iris loading state (unchanged exception).

### 5. Visual density per section — the direct answer to "puro texto"

| Section | Current state (confirmed live) | Target density/treatment |
|---|---|---|
| Overview | 3 flat text cards | Hero moment (§3) + demoted 3-col feature row below. Highest density fix in this spec. |
| Inputs | Form-dense already, reasonably good | Keep as a real dense form (shadcn `Input`/`Combobox`/`Slider`/`Select`/`Calendar`) — this section's job is data entry, not persuasion; don't add decoration here. |
| Results | Already the best-designed page | Preserve structure, upgrade components (§2) — Card/Chart/Table fidelity, not a redesign. |
| Learning | Diagram-forward, already good (decision 0009e) | Keep hand-built SVG diagrams (rule: hand-drawn SVG stays right for conceptual illustration, not data), rebuild motion in React per §4. |
| Glossary | Flat 27-term list | Grouped `Accordion` by concept area (§2), not a longer flat list. |
| Tools & Technologies | Flat category text, zero icons — confirmed live | `Card` grid, **one `lucide-react` icon per category header** (5 total: a code-bracket icon for Languages, a package/box icon for Frameworks & libraries, a function/sigma-adjacent icon for Data & quant methods, a layout icon for Presentation & rendering, a server icon for Infrastructure). Icon-per-category, not icon-per-line — the fix for "puro texto" here is the grid structure and the one anchor icon per group, not decorating all ~20 individual tool entries. |
| References & Formulas | Card grid + manual sub/sup HTML | Keep the `Card` grid; upgrade math rendering to real KaTeX (§2, recommended). |
| Real World / Corporate Applications | Paragraph walls + tag pills, zero numbers pulled out — confirmed live | Pull the one real number per card into a large mono stat callout at the top of the `Card` (e.g. "62 → 3 packages," the Barra/Axioma price-point gap, "14% → 30%" platform-consolidation stat already in the source research) — pull-quote/stat-callout treatment, paragraph shortened to supporting context below it. |

## Consequences / flags for `developer` and `pm`

- **Recharts is a new real dependency**, per decision 0004's own preference for a real charting library over hand-drawn SVG for data (not diagrams). The chart *logic* (frontier position math, diverging-bar geometry, CI whiskers) is unchanged — only the rendering layer moves from hand-built `<path>`/`<polyline>` to Recharts components wrapped in shadcn's `Chart` primitives.
- **The 8 sections become real routes**, not in-page tab panels — a genuine improvement (deep-linking) but a real architectural change from the current single-page-with-hidden-panels model. `developer` needs React Router (or equivalent) in the Vite scaffold; this was implicitly assumed by "Vite + TypeScript + Tailwind + shadcn/ui" in the roadmap but is being made explicit here since it changes how the shareable-link feature (Phase 9c) is implemented — it becomes actual URL state (holdings/benchmark/date-range as query params on `/results`), which is arguably a cleaner mechanism than the current server-side replay, not a regression.
- **GSAP stays, Framer Motion is not introduced** — a deliberate choice to preserve decision 0015's validated spec rather than re-derive it against `design-taste-frontend`'s own stack default (which prefers `motion/react` for React UI). This is flagged explicitly per the mandate to surface tradeoffs: if `developer` finds GSAP's React ergonomics genuinely worse in practice once building starts, that's a real reason to revisit, but it shouldn't be swapped by default just because it's the more commonly recommended React motion library.
- **KaTeX for References & Formulas is recommended, not required** — real scope/time tradeoff for `developer` to weigh; flagged because it's a concrete, high-visibility upgrade opportunity the old architecture explicitly couldn't take (decision 0006's "no client library" constraint no longer applies post-0004).
- **What must be preserved, not rebuilt from scratch**: the Results page's existing information architecture (stat tiles → factor charts → frontier → attribution, in that order), the freshness banner, the share-link/PDF-export/OG-meta trio (Phase 9c, rule 8), the sample-portfolio quick-start, and every existing validated number/methodology in `app/models/`/`app/data/` — none of that changes. This is a presentation-layer rebuild, not a product rebuild.

## Handoff to `developer` (Phase 10i)

Build per §§1–5 above against the Vite + TypeScript + Tailwind + shadcn/ui scaffold, wired to the existing `/portfolio/returns` JSON API. The Tailwind tokens in §1 and the component mapping in §2 are meant to be dropped in directly, not reinterpreted — if a specific shadcn component's exact sub-API has shifted since this spec was written (the `Empty` component in particular, flagged above), check `npx shadcn@latest add <component>`'s generated source at build time rather than guessing. A style-tile/mockup Artifact accompanies this decision (colors, type samples, hero mockup, stat-tile/card mockups) as a visual reference alongside this prose.
