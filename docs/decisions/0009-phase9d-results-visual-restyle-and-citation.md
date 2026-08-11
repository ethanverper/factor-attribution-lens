# 0009. Phase 9d: chart-specific restyle to close the "quant terminal" gap,
plus the formal ticker-universe citation

Date: 2026-08-10
Status: accepted

## Context

Phase 9c (decision 0008) rebuilt the app shell's design tokens (Space
Grotesk + Inter + JetBrains Mono, graphite-navy/cool-gray-blue surfaces, one
amber "signal" accent) and wired them into `app/dashboard/viz.py::CHART_STYLE`
as shared CSS custom properties on `.viz-root`, so the chart layer would
inherit the new palette automatically. It explicitly deferred chart *mark*
and typography-flow polish to this phase, per `docs/project-standards.md`
rule 6 ("Results needs a genuine visual presence, not just inherited color
tokens"). This phase re-assessed the Results section with the `dataviz`
skill loaded fresh, found three concrete places where the charts were still
visually "the old research-memo charts wearing new colors," fixed them, and
added the formal ticker-universe citation to References & Formulas that
decision 0008 flagged as this phase's other half of rule 7.

## Audit: what still read as the old system

Not a vague impression -- specific, traced causes, found by reading
`viz.py`'s actual CSS against `shell.py`'s (`SHELL_STYLE`) token definitions,
not by eyeballing a screenshot:

1. **Chart card headings (`.viz-card h2`) were not using the display font.**
   Every other card type in the app (`ref-card`, `learn-card`, `rw-card`,
   `method-card`) explicitly sets `font-family: var(--font-display)` on its
   `h2`/`h3`. `.viz-card h2` had no such rule, so "CAPM beta vs. ^GSPC,"
   "Your portfolio vs. the modeled efficient frontier," etc. rendered in the
   body font (Inter) while every other section header on the page rendered in
   Space Grotesk -- a real, verifiable typographic inconsistency between
   Results and every other tab.
2. **Every number and label actually drawn inside a chart's SVG (axis ticks,
   bar value labels, category/asset names, the frontier's connector
   annotation) had no `font-family` set at all**, so it fell back to
   whatever font inherited down the DOM -- in practice the body sans, not the
   mono face decision 0008 describes using "aggressively... every stat-tile
   value, legend, table cell, formula, nav mark, and section eyebrow." The
   legend and table-view twin CSS already correctly used
   `var(--font-mono, ...)`; the SVG mark layer itself -- the single most
   "instrument panel" surface in the whole app -- was the one place that
   didn't. This was the single biggest concrete gap between "restyled chrome"
   and "an instrument-panel readout."
3. **`.viz-root`'s own `font-family` declaration in `CHART_STYLE` was
   hardcoded to `system-ui, -apple-system, "Segoe UI", sans-serif`**, a
   leftover from the pre-9c "research memo" system, rather than deferring to
   `var(--font-body, ...)`. In the live page this was masked because
   `SHELL_STYLE`'s own later `.viz-root` rule (same selector, later in the
   concatenated `<style>{viz.CHART_STYLE}{SHELL_STYLE}</style>` block) won
   the cascade -- but it left `viz.py` internally inconsistent with its own
   documented "inherits the new palette automatically" claim, and fragile if
   the two stylesheets are ever reordered or `CHART_STYLE` is reused
   standalone.

None of this was a broken chart -- Phase 9c's claim that color/font *tokens*
flow through was true. What was missing was routing the chart layer's own
type and a couple of mark-level touches through those tokens, which is
exactly rule 6's ask.

## Changes made (`app/dashboard/viz.py`)

- `.viz-card h2` now sets `font-family: var(--font-display, inherit)`,
  matching every other card heading in the app.
- Added `.viz-chart-wrap svg text { font-family: var(--font-mono, ...);
  font-variant-numeric: tabular-nums; }` -- routes every axis tick, bar
  value/category label, and annotation text in all three chart types
  (diverging bar, frontier scatter, risk-split bar) through the same mono
  readout face used everywhere else data appears in the app.
- `.viz-root`'s base `font-family` now reads `var(--font-body, 'Inter',
  system-ui, -apple-system, "Segoe UI", sans-serif)` instead of a hardcoded
  sans stack -- no visible change on the live page (SHELL_STYLE already won
  this in the cascade), but removes the internal inconsistency and makes
  `CHART_STYLE` correct if ever loaded standalone.
- **Frontier chart**: added vertical gridlines at the interior x-ticks
  (same hairline `var(--gridline)` spec as the existing horizontal ones),
  completing a real x/y grid rather than a horizontal-only one -- a scatter
  plot with only horizontal gridlines reads as a bar chart's baseline grid;
  a full grid reads as an instrument/oscilloscope readout, echoing the
  shell's own `.grid-texture` motif (decision 0008: "references the fact
  that every result in this app is a point plotted on a chart").
- **Frontier chart**: added a soft amber halo (a low-opacity `var(--series-2)`
  circle) behind the "Your portfolio" marker only -- not GMV or max-Sharpe,
  which stay neutral/muted by design. This is the one point on the chart the
  site's single signal accent should draw the eye to first; the halo echoes
  the "armed/active" glow decision 0008 already uses on buttons and focus
  rings, rather than leaving the current-portfolio dot at the same visual
  weight as the two reference markers.

**What was checked and left alone, deliberately:** bar thickness (22px,
within the ≤24px mark spec), the 4px rounded-data-end / square-baseline bar
shape, the risk-split-bar's 2px surface gap between segments, gridline
hairline weight/color, the CI-whisker treatment, the diverging color
assignment (blue/red already flow from the shared tokens), and the
tabular-mono stat-tile treatment Phase 9c already built. Re-checked the
stat-tile mono/tabular-nums choice specifically against the `dataviz` skill's
anti-pattern ("tabular-nums on a large standalone number... proportional
figures on hero and stat-tile values") -- that guidance is about proportional
vs. tabular *digit widths within a variable-width sans*; JetBrains Mono has
no proportional-figure variant to begin with (every glyph is fixed-width by
construction), so the anti-pattern doesn't actually apply here, and a
fixed-width numeric readout is a deliberate, coherent choice for a
"quant terminal" identity (the same reasoning a real trading-terminal ticker
tape uses). Judged intentional, not a violation, and left unchanged.

## Rule 7: the formal ticker-universe citation

Added a sixth card to `render_references_section()`
(`app/dashboard/shell.py`), `app/dashboard/tickers.py`, matching the same
card shape and rigor as the CAPM/Fama-French/Newey-West/Markowitz/attribution
cards above it (source, methodology, explicit known limitation) rather than
a lighter-weight note:

- **What it computes / backs**: the Holdings and Benchmark comboboxes'
  constrained-input universe.
- **Coverage / symbol convention**: ~496 S&P 500 constituents + 6 benchmark
  proxies, captured 2026-08-10; share-class dot-to-dash normalization to
  `yfinance` convention at data-entry time.
- **Methodology note**: the two-layer enforcement (client-side combobox +
  server-side `routes.py` re-validation, both from decision 0005).
- **Known limitation, stated explicitly**: static snapshot, not a live
  index-membership feed -- will drift from the real S&P 500 roster over
  time, and a valid-on-`yfinance` ticker outside this list cannot be
  entered.
- **Source**: the public constituents dataset decision 0005 sourced from
  (mirroring the official S&P Dow Jones Indices membership / the same data
  behind Wikipedia's "List of S&P 500 companies"), plus a pointer to decision
  0005 for the full sourcing/refresh policy.

This is the "formal citation in References & Formulas" half of rule 7;
Phase 9c already shipped the "near the input" half (a `.source-note` on the
Inputs tab) -- the two are deliberately not duplicates of each other (one is
a glanceable inline note, the other is the fully-cited record), consistent
with how decision 0008 scoped the split.

**Bug caught and fixed during this card's own verification**: the first
draft reused the existing `.formula-block`/`.fb-eq` component (built for
short, single-line math notation, `white-space: nowrap` by design) for two
prose-length facts ("Coverage," "Symbol convention"), which silently
overflowed the card's fixed width (measured via `scrollWidth`/`clientWidth`:
1494px of content in a 706px box) with no visible scroll affordance --
functionally unreadable past the first ~45 characters. Fixed by rewriting
both entries as genuinely terse, notation-style single lines (e.g.
`BRK.B → BRK-B (dot → yfinance dash, at entry)`) that actually fit the
component's real contract, rather than fighting the component's CSS; moved
the longer explanatory prose into the card's `note` paragraph, which wraps
normally. Re-verified via `scrollWidth === clientWidth` on every
`.formula-block` on the page (all six, including the pre-existing five,
confirmed no overflow) after the fix.

## Regression check

Re-ran Phase 8's own verification portfolio -- AAPL (50%) / MSFT (30%) /
GOOGL (20%) vs. `^GSPC`, Fama-French 3-factor, daily -- computed directly
against `app.models.analysis.analyze_portfolio` (bypassing the HTTP layer
entirely) and cross-checked every one of 10 displayed figures (CAPM beta,
CAPM alpha annualized, CAPM R², Fama-French alpha annualized, Fama-French
R², Fama-French F-statistic, annualized return, annualized volatility,
Sharpe ratio, return gap at matched volatility) against the exact same
formatted strings (`viz.py`'s own `fmt_pct`/`fmt_num`/`fmt_ratio`) rendered
by a live `POST /dashboard` submission through `TestClient`. All 10 matched
exactly -- no regression from Phase 9c's token/structural changes or this
phase's chart-specific changes. Also re-confirmed the Phase 9c sample
quick-start (`GET /dashboard/sample`, AAPL 40% / MSFT 30% / GOOGL 20% / AMZN
10%) still runs end-to-end and renders correctly in both themes.

## Pre-existing bug re-confirmed, not fixed (flagged for Phase 10, `qa-tester`)

The frontier chart's "Your portfolio" / "Global min-variance" marker-label
overlap (first flagged Phase 3, re-confirmed Phase 7 and Phase 8) is still
present and clearly visible on both the AAPL/MSFT/GOOGL portfolio and the
sample-portfolio quick-start -- unresolved across four phases now. This is
`viz.py`'s `marker_group`/label-placement logic (the labels currently only
avoid the plot's right edge, not each other), not a token or mark-style
issue this phase's scope covers. Specifically calling this out to
`qa-tester` for Phase 10 as a real, reproducible, multi-phase-old defect
that should get an actual fix (e.g. a leader-line/small-multiples fallback
per the `dataviz` skill's "when end-labels collide" guidance), not another
deferral.

## Verification

- Full 42-test suite: passing, unchanged from Phase 9c's count (this phase
  added no new tests -- no new user-facing behavior, only visual/citation
  changes to already-tested surfaces; existing tests already assert `<svg>`
  presence and full-page structure).
- `ruff check .`: clean.
- Manual pass in the in-app Browser tools (Playwright): light mode and dark
  mode on the Results tab (sample-portfolio quick-start), References &
  Formulas (new ticker-universe card, both themes, overflow-checked via
  `scrollWidth`/`clientWidth`), Inputs tab (unaffected, confirmed), and a
  375px mobile pass on Inputs (no horizontal overflow, Phase 9c's earlier
  `align-items: stretch` fix still holding).
- Direct model-vs-live-page reconciliation script (AAPL/MSFT/GOOGL) as
  described above -- 10/10 figures matched exactly.

## Consequences / handoff

- **Phase 9e (`educator`)**: no changes to the Learning/Glossary card shapes
  or token usage from this phase -- any new inline SVG diagrams should use
  `var(--font-mono)` for numeric/data text within them now, consistent with
  the chart-layer fix here, not just the ambient body font.
- **Phase 10 (`qa-tester`)**: the frontier-chart label-overlap bug above is
  now a four-phase-old, specifically-reproducible defect -- recommend an
  actual fix this phase, not another flag-and-defer.
