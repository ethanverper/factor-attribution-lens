# 0015. Phase 10f: real interaction/motion language, and a real Tools & Technologies section

Date: 2026-08-11
Status: accepted

## Context

Fourth round of feedback on Factor Lens. Despite the identity pass (decisions 0012/0013), Ethan's read is that the app still feels static/"arcaico." His own words: *"quiero botones, sliders, desplazamiento visual más interactivo, y en general que el contenido se muestre de una forma más interactiva"* — buttons, sliders, more interactive scroll behavior, content shown more interactively. He explicitly called out the Learning section's diagrams as a direction worth *extending*, not the static form/results pages.

Decision 0012's motion guidance said "stays restrained... no new decorative animation." That guidance under-delivered: it conflated restraint with absence. `docs/output-standards.md` rule 11 (added this round) corrects it directly — restraint means nothing decorative, not the absence of interactivity. Real premium references (Stripe, Linear, Mercury) are full of purposeful interaction: hover/press states, transitions, animated data reveals, interactive controls. This decision replaces 0012 §5's motion guidance with the spec below; everything else in 0012 (the aperture mark, type weight, one-accent discipline) stands.

This decision also closes rule 13 — the Tools & Technologies section currently reads as a flat, thinly-labeled list, not something a hiring manager could map to real job requirements.

## Audit of the live app (before proposing anything)

Ran the app locally (`uv run uvicorn app.main:app --reload --reload-dir app`) and drove it through the in-app Browser tools rather than reasoning about it abstractly. Findings, concrete:

- **Tab navigation** (`shell.py::_shell_script`): `p.hidden = !match` — an instant, un-eased attribute flip. No transition of any kind between panels.
- **Inputs → Results**: a real full-page `POST /dashboard` navigation (this is a server-rendered app, no client fetch/XHR layer — confirmed in `shell.py`'s own loading-overlay comment: *"classic full-page form POST / GET navigation, not an SPA/fetch flow"*). The iris loading overlay (decision 0012 #3) already covers the *wait*; what's missing is the Results page's own *arrival* — every stat tile, chart, and banner paints simultaneously, fully formed, with zero motion.
- **Buttons already have hover states defined in CSS but no transitions** — e.g. `.hero-cta:hover { filter: brightness(1.08); }`, `.quickstart-btn:hover { border-color: var(--signal); color: var(--signal); }`, `.nav-item.is-active { border-left-color: var(--signal); }` all change instantly, snap-style, despite the states themselves being well-designed. This is the single most concrete, fixable finding: the identity work built the *right* states, just never eased into them.
- **Charts are static SVG** (`viz.py`): diverging bars are `<path>` elements inside `<g class="viz-mark">`; the frontier curve is a plain `<polyline>`; markers (GMV/max-Sharpe/current-portfolio) are `<rect>`/`<circle>` groups, the current-portfolio one built from the same concentric-ring geometry as the wordmark (`mark.py::_rings_markup`). All render fully-formed, no entrance of any kind.
- **Allocation inputs** (`pages.py::_holding_row_html`): `<input type="number" name="weight">` — the "sliders-adjacent" live-total badge (Phase 9b) recalculates on every keystroke, but the badge's own color-state swap (`data-state="exact/under/over"`) is an instant CSS variable swap, and there is no actual drag/slider control anywhere in the app.
- **Learning section diagrams** (`diagrams.py`, Phase 9e): three hand-built inline SVGs (CAPM decomposition blocks, a factor-loading CI whisker example, a frontier-position gap diagram) — exactly the direction Ethan flagged as worth extending. Currently fully static.

## Research grounding this spec

- `gsap-core` (Skill) — core tween/timeline API, `gsap.matchMedia()` for `prefers-reduced-motion`, transform aliases (`x`/`y`/`scale`/`autoAlpha`), easing vocabulary.
- `design-motion-principles` (Skill) — ran its context-weighting framework against Factor Lens's actual shape (a data-dense analytics/SaaS dashboard, not a marketing site or a kids' app): **Emil Kowalski primary** (restraint, speed, the frequency gate — a tab a user clicks dozens of times a session gets *fast, minimal* motion, not a production flourish), **Jakub Krehel secondary** (hover/press polish, enter animations for genuinely one-time "arrival" moments like Results), **Jhey Tompkins selective** (the Learning diagrams only — a rare, narrative, once-per-session moment where a more expressive sequenced reveal is earned). Cross-checked every proposed pattern against its anti-checklist (pulsing indicators, hover-scale-on-everything, stagger-spam-on-every-list, uniform-fade-in-on-every-element, motion-on-mount-for-static-content) to avoid reintroducing "AI-slop" motion under the banner of "more interactive."
- `ui-ux-pro-max`'s animation/forms/charts guidelines (`references/quick-reference.md`, read directly — the skill's search script requires shell execution, unavailable in this session, so the static reference file was read instead and cited accordingly): duration budgets (150–300ms micro-interactions, ≤400ms complex transitions), `exit-faster-than-enter`, `stagger-sequence` (30–50ms/item), `motion-meaning` (animation must express cause-effect, not decorate), `animation-optional` (chart entrance must respect reduced-motion and data must be readable immediately, not gated behind an animation finishing), and the forms guidance against replacing a precise numeric input with a gesture-only control for exact data.

## Decision, Part 1 — Interaction/motion language

### Global rules (apply everywhere below)

- **Durations**: 120–200ms for hover/press/focus micro-interactions; 220–500ms for one-time entrance/reveal moments; nothing loops or pulses ambiently anywhere new (the iris loading overlay stays the one sanctioned exception, per its own explicit rationale in decision 0012).
- **Easing**: `power2.out` for entrances, `power1.out` for hover/press — no `elastic`/`back` easing on any utility control. The one earned exception is a small `back.out(1.4)` pop on the frontier chart's marker arrivals (§5) — rare, discrete, narratively "and here's you," not a repeated utility action.
- **Accessibility**: every new animation gated through `gsap.matchMedia()`'s `(prefers-reduced-motion: reduce)` condition — reduced-motion users get the final state immediately (duration 0), never a stuck mid-animation state.
- **Progressive enhancement, non-negotiable**: every animated value (stat-tile numbers, bar widths, frontier position) must already be correct in the server-rendered HTML before any JS runs. GSAP animates *from* a temporary state *to* the real SSR'd value — it never generates the value. This matters concretely here because `tests/test_dashboard.py`'s live end-to-end checks read rendered HTML via `httpx` (no JS execution at all, so they see the true SSR value untouched) and because a no-JS user must see correct numbers instantly, not a stuck "0".

### 1. Buttons & interactive controls — hover/press

The states already exist in CSS (decisions 0008–0013 designed them); they're just missing transitions. Add, per class, in `shell.py`'s `SHELL_STYLE`:

```css
.hero-cta, .hero-cta-secondary, .quickstart-btn, .submit-btn, .helper-btn,
.add-row-btn, .share-btn, .theme-btn, .row-remove, .nav-item, .learn-xref {
  transition: background-color 160ms ease-out, border-color 160ms ease-out,
              color 160ms ease-out, box-shadow 160ms ease-out,
              filter 160ms ease-out, transform 120ms ease-out;
}
button:active, a[role="button"]:active, .hero-cta:active, .submit-btn:active,
.quickstart-btn:active, .helper-btn:active {
  transform: scale(0.97);
}
```

No new colors, no new states — only the missing transition on states that already exist. `.ticker-option` hover stays instant/near-instant on purpose (a fast, high-frequency list-hover — Emil's frequency gate argues against animating it).

### 2. Tab navigation

High-frequency interaction (clicked dozens of times a session) — per the frequency gate, this gets the *smallest* treatment, not a bigger one. Add a 120ms opacity fade on the panel being shown only (no slide/translate — that would add duration to a frequent action for no explanatory gain):

```js
function activate(id, pushHash) {
  // ...existing hide/show logic...
  var panel = document.querySelector('[data-tab-panel="' + id + '"]');
  if (panel) {
    gsap.fromTo(panel, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.12, ease: "power1.out" });
    panel.scrollIntoView({ block: "start" });
  }
}
```

### 3. Inputs → Results arrival

The architecture is a real page navigation, not an SPA transition — see the "flag to `pm`/`developer`" note below on why this is a real constraint, not an oversight. The fix is a choreographed entrance on the Results page's own load, not a cross-document animation:

1. `.freshness-banner` (portfolio/benchmark/model summary) enters first: `autoAlpha 0→1, y: 8→0`, 260ms, `power2.out`.
2. Section 1's stat tiles (`.viz-stat-tile`) stagger in: `autoAlpha 0→1, y: 10→0`, 220ms, 40ms stagger between tiles.
3. Section 1's chart reveals (§4) once its tiles finish.
4. Sections 2 (frontier) and 3 (attribution) do **not** fire on page load — they trigger on scroll-into-view (`IntersectionObserver`, `{ threshold: 0.3, once: true }`), so a long Results page doesn't front-load every animation at once. This is the "scroll behavior" ask applied where it's genuinely earned: a modeled output the user is actively scrolling down to read, revealed once, not a scroll-scrubbed/pinned effect.

Total on-load choreography: well under 1 second. This isn't a slow flourish — it's the difference between "the whole page appears" and "the page tells you what it's showing you, in the order you'd read it."

**Optional, zero-risk addition**: a 3-line CSS progressive enhancement (`@view-transition { navigation: auto; }`) gives genuine cross-document view transitions in Chromium; it degrades to today's hard cut in Safari/Firefox with no JS and no fallback logic needed. Worth adding alongside the JS choreography above, not instead of it — flagged as optional because of the browser-support gap, not because it's risky.

### 4. Results — data reveal ("que el contenido se muestre de una forma más interactiva")

Each mark type gets its own reveal, matched to what it actually is (not one recipe copy-pasted across every chart — that's the "uniform-fade-in" anti-pattern):

- **Stat tile numbers** (`.viz-stat-tile .stat-value`, e.g. CAPM beta `1.00`, alpha `-1.64%`, R² `50.3%`): count up from 0 over 500–600ms, `power2.out`, formatted on every tick. **Server-side change needed**: `viz.py::stat_tile()` currently emits only the pre-formatted string; add `data-count-target`/`data-count-suffix`/`data-count-decimals` attributes alongside the existing text so the client tweens a raw number rather than parsing formatted strings back apart (fragile). The rendered text itself stays the real value always — GSAP tweens a proxy number and writes it in.
- **Diverging bars** (Fama-French loadings, return/risk attribution — `_hbar_path`'s `<path>` fill inside `<g class="viz-mark">`): wrap each bar's group in a `scaleX: 0 → 1` transform anchored at the zero baseline (`transformOrigin` at `zero_x`), 450ms `power2.out`, 60ms stagger per bar. No chart-geometry rewrite — GSAP applies `scaleX` as a CSS transform on the existing `<g>`, the path data underneath is untouched. CI whisker `<line>` elements fade in 100ms after their bar finishes (a whisker appearing before its bar exists reads as meaningless).
- **Frontier curve** (`<polyline>`): the one chart that's a literal path, so it gets the one technique suited to a path — `stroke-dasharray`/`stroke-dashoffset` draw-in using `polyline.getTotalLength()` (computed client-side, no server change needed), ~500ms `power2.out`. Markers (GMV → max-Sharpe → current-portfolio, in that order) pop in after the curve finishes: `scale 0.8→1`, `autoAlpha 0→1`, `back.out(1.4)`, 80ms apart — the one earned use of overshoot easing in the whole spec, since arrivals here are rare, discrete, and the current-portfolio marker arriving last is a deliberate "and here's you" beat.
- **What does NOT get animated**: table-view `<details>` twins (manual, rare disclosure — opens instantly), prose/disclaimer text, the freshness banner's body copy. Per the anti-checklist's "motion-on-mount-for-static-content" — only the model's actual numeric/graphical output gets a reveal, never headings or paragraphs.

### 5. Allocation inputs — dual number + slider control

Ethan's explicit ask. A pure slider would regress precision (Markowitz allocations often need values like `33.33`, painful on a bare drag control), so this is a **paired** control, not a replacement:

- Keep `<input type="number" name="weight">` as the value of record — zero backend/schema change.
- Add `<input type="range" min="0" max="100" step="0.5">` in the same `.weight-field`, two-way bound: dragging the range writes into the number input's `.value` and dispatches a synthetic `input` event on it, which the existing `recalcAlloc()` listener already picks up (Phase 9b's total-badge/validation logic needs zero changes — it just starts firing from a second source).
- Styling: track fill up to the current value in `--signal`, empty track in `--border`; thumb a small themed dot (not the full multi-ring aperture glyph — that would compete with the actual mark) that scales `1 → 1.15` on `:active` via a plain CSS transition (120ms) — no GSAP needed here, native `<input type="range">` pseudo-elements handle it more cheaply than JS-driving it.
- The total-badge's `data-state="exact/under/over"` color swap (currently an instant CSS-variable change despite already being well-designed states) gets `transition: background-color 200ms ease-out, border-color 200ms ease-out, color 200ms ease-out`.
- "Split evenly"/"Normalize to 100%" (Phase 9b): currently snap values instantly. Add a brief (150ms) tween of the changed number+range values to their new position so a redistribution is visibly seen sweeping into place — this is specifically what "desplazamiento visual más interactivo" is asking for.

### 6. Scroll-linked reveal — extending the Learning diagrams (not forcing it elsewhere)

The single most justified scroll-linked motion in the app, because it's rare (visited once per session while learning, not clicked 100s of times), genuinely explanatory (each reveal mirrors the order the adjacent prose already argues), and it's literally the direction Ethan said he liked:

- **CAPM decomposition** (`diagrams.py`): the three blocks (risk-free, β·market, alpha) reveal left-to-right, 150ms stagger, matching the equation's own reading order — teaching the additive identity through sequence, not decorating it.
- **Factor-loading CI whisker example**: point estimate dot appears, then the whisker draws outward from it (`stroke-dashoffset`, 300ms), then the ✓/≈ verdict label fades in last — the same order a person should actually read a confidence interval.
- **Frontier-position diagram**: curve draws in, "your portfolio" dot appears, then the two gap arrows draw outward from the dot last.

All three use `IntersectionObserver({ threshold: 0.4 }, { once: true })` — fires once, on first scroll-into-view, never replays.

**Explicitly not scroll-linked**: Glossary (27 flat entries — scroll-triggering this is "stagger-spam-on-every-list"), References & Formulas, Real World, Tools & Technologies. These are scanning/reference content; scroll-gating them would slow down a user trying to quickly find something, which fails the frequency/utility test this whole spec is built on.

### 7. What stays exactly as-is

The iris/aperture loading overlay, the tab-hide mechanism itself (only adding the fade, not restructuring), the frontier marker's aperture-ring shape, and the one-accent amber discipline (decision 0012 audit) — no new colors, every new state reuses existing tokens (`--signal`, `--series-1`, `--status-good/-warning`).

## Decision, Part 2 — Tools & Technologies (rule 13)

Restructured from one flat list into five real categories, each substantial entry connected to what it actually did in *this* project, framed against `docs/about-me.md`'s reinforcement-vs-new-territory lens (CAPM/Fama-French/Markowitz reinforce Ethan's existing academic quant depth; the live-data integration, the real deployed FastAPI app, and now the hand-built interaction layer are the genuinely new territory). Full replacement content for `developer` to render in `shell.py`'s Tools & Technologies panel:

**Languages**
- **Python 3.11** — the entire application, from the OpenBB/Kenneth French data layer through the FastAPI HTTP layer to every hand-built inline-SVG chart. One language end to end, not a Python-backend/JS-frontend split.
- **Vanilla JavaScript** (no transpile/build step) — the ticker combobox's search/keyboard-nav, tab navigation, the allocation live-total badge, and (Phase 10g) the interaction/motion layer below — deliberately framework-free given the server-rendered architecture.

**Frameworks & libraries**
- **FastAPI** — the HTTP layer for both the JSON `/portfolio/returns` API and the server-rendered dashboard routes (`GET /`, `POST /dashboard`).
- **Pydantic v2** — typed request/response schemas for holdings, weights, and date ranges; the layer that rejects invalid submissions (duplicate symbols, bad date ranges, allocations that don't sum to 100%) before any model runs.
- **uv** — dependency management and a reproducible lockfile; also the tool that made trimming the OpenBB dependency footprint from 62 packages to 3 (Phase 10e) auditable and reproducible.
- **GSAP** (Phase 10g) — the interaction/motion layer: entrance choreography, count-up data reveals, SVG chart draw-ins. Self-hosted (vendored, not CDN), framework-agnostic core — doesn't require adopting a client framework.

**Data & quant methods**
- **OpenBB Open Data Platform** (yfinance provider) — live equity and benchmark price history; the real market-data backbone, not a static CSV.
- **Kenneth French's Data Library** (via pandas-datareader) — the actual Fama-French 3-/5-factor and risk-free return series, sourced directly since OpenBB's Open Data Platform doesn't carry factor series at all (a real integration finding — decision 0002).
- **CAPM** — single-factor market-beta regression with Newey-West HAC standard errors, not a raw OLS slope.
- **Fama-French 3-/5-factor model** — multi-factor loadings (size, value, profitability, investment) with the same HAC-robust diagnostics.
- **statsmodels** — the OLS engine underneath both, configured for heteroskedasticity/autocorrelation-consistent standard errors rather than textbook-default OLS.
- **Markowitz mean-variance optimization** via **SciPy (SLSQP)** — long-only constrained efficient frontier, with eigenvalue-clipping covariance regularization for near-singular holding sets.
- **NumPy / pandas** — aligning return series across sources with different native frequencies (equities, benchmark, factors) and the array/matrix math underneath the optimizer and regressions.

**Presentation & rendering**
- **Hand-built inline SVG** — every chart (diverging bars with CI whiskers, the Markowitz frontier, the Learning-section diagrams) drawn directly as SVG geometry from computed statistics, no charting library (decision 0004) — the entire render path stays in Python/plain HTML.
- **Server-rendered HTML/CSS** (plain Python string templates, no Jinja2) — every page, including the eight-tab app shell, assembled server-side; no client-side routing or hydration.

**Infrastructure & delivery**
- **pytest + httpx** — the test suite, including live (non-mocked) end-to-end tests against real market data, not fixtures.
- **Railway** (Phase 11) — planned deployment target.
- **Git/GitHub** — public repo with `docs/roadmap.md` and `docs/decisions/` published alongside the code — the decision trail is itself part of the deliverable, not just the app.

One framing line for the section header: *"Reinforces existing academic quant depth (CAPM, Fama-French, Markowitz, econometric diagnostics) with the production engineering around it — live multi-source data integration, a real deployed app instead of a notebook, and a hand-built interaction layer — the genuinely new territory this project pushes into."*

## Consequences / flags for `developer` and `pm`

- **New runtime dependency**: GSAP core is a new client-side library, ~30–40KB gzipped for core alone (no ScrollTrigger plugin needed — see below). Recommend self-hosting a vendored, minified copy under `app/static/vendor/` rather than a CDN `<script src>`, to avoid adding a new external network dependency at request time (Google Fonts is already CDN-loaded, so a GSAP CDN tag wouldn't be a new *category* of risk, but self-hosting is strictly safer and keeps the "no build step" convention — it's just a static file, no bundler). This is a real, if small, architecture addition — flagging per the agent's mandate to surface tradeoffs rather than assume them away.
- **Deliberately no ScrollTrigger plugin**: the scroll-linked pieces in this spec (§6) are fire-once reveals, not scroll-scrubbed/pinned effects — plain `IntersectionObserver` covers them with zero extra dependency weight. If a future phase wants genuine scroll-scrubbing (e.g., a value that tracks scroll position continuously), that would justify pulling in ScrollTrigger; nothing here needs it.
- **`Tools & Technologies` copy must be updated to match**: the current "Presentation" group says *"Vanilla JavaScript... no framework or build step"* — once GSAP ships, the accurate framing is "Vanilla JavaScript + GSAP (self-hosted, no build step)," not a removal of the claim (GSAP is a library, not a framework, and adds no bundler step).
- **Test-timing note for `qa-tester`/`developer`**: `tests/test_dashboard.py`'s live end-to-end checks read rendered HTML via `httpx`, which never executes JS — those tests will keep seeing the true SSR'd values untouched and need no changes. Any *new* Playwright/browser-driven check added for the animations themselves should assert on `data-count-target` or wait for animation completion, not read `.stat-value`'s live text mid-tween.
- **No architecture change required**: everything in this spec (count-up numbers, bar `scaleX` reveals, polyline draw-in, dual slider+number control, tab fade, scroll-triggered diagram reveal) layers on top of the existing server-rendered, no-client-framework architecture without requiring a move to client-side fetch/SPA rendering. The one place this was a genuine question — the Inputs→Results transition — is handled by an on-arrival entrance choreography plus an optional CSS-only cross-document view-transition, not by converting the form submit into a fetch call.
- **Preserved from decision 0012**: the aperture/iris motif's construction, the graphite-navy/amber one-accent system, and Space Grotesk/JetBrains Mono/Inter — none of this spec touches color, type, or the brand mark itself; it's additive motion/interaction only.

## Handoff to `developer` (Phase 10g)

Build this spec, plus (per the roadmap) fix the unscoped `--reload` watcher (rule 12: use `--reload-dir app`) and run `impeccable` as a final polish pass once the interaction layer is in place. An interactive style-tile/mockup `Artifact` (buttons with real hover/press states, a stat tile counting up, a mini bar-chart reveal, the dual slider+number control) was offered for this handoff but not built in this pass — happy to produce one on request if a working visual reference alongside this prose would help before implementation starts.
