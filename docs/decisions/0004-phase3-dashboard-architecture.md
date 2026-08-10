# 0004. Phase 3 dashboard architecture: server-rendered HTML/SVG inside the
existing FastAPI app, no client charting library, no Jinja2, presentation-
layer return/risk attribution

Date: 2026-08-10
Status: accepted

## Context

Phase 3's mandate is to turn Phase 2's `PortfolioAnalysis` (CAPM,
Fama-French, efficient frontier) into visual, explainable attribution: a
factor exposure breakdown, an efficient-frontier chart with the current
portfolio plotted on it, and a return/risk attribution view — reached by a
user after submitting holdings, as *part of the running FastAPI app*, not a
disconnected static artifact. Several genuinely contestable choices had to
be made building this; recorded here for Phase 4/5 per this role's standing
mandate.

## Decisions

**1. Server-rendered HTML with hand-built inline SVG charts, no client-side
charting library (Chart.js/Plotly/D3), no new heavyweight dependency.**
`app/dashboard/viz.py` builds every chart (diverging bar, frontier
scatter/line, part-to-whole split bar) as inline SVG strings assembled in
Python, styled and interactive per the `dataviz` skill's method (fixed
mark specs, the documented default categorical palette, hover tooltips via
a small shared vanilla-JS layer, a `<details>` table-view twin on every
chart). This keeps the dashboard a genuine part of the FastAPI app (a
route returns HTML, full stop) rather than introducing a JS build step,
bundler, or a second runtime the `uv`-managed Python stack would otherwise
be free of. The tradeoff: chart code is more verbose than
`plotly.express.bar(...)` would be, and there's no pan/zoom. Judged worth
it for a project whose whole differentiator is a small, curated,
explainable set of views (3 chart types) rather than a general-purpose
exploration tool — see roadmap's "smallest dashboard that answers the
question" standard.

**2. No Jinja2 (or any templating engine) — pages are assembled with plain
Python f-string functions in `app/dashboard/pages.py`.**
`fastapi`/`starlette` don't pull in Jinja2 by default (confirmed absent
from `uv.lock` before this phase), and the page-assembly need here is
modest: two pages, a handful of reusable section functions. Adding a
templating dependency for that is not proportionate. All user-originated
strings (tickers, benchmark name, error messages) are passed through
`html.escape` (`app/dashboard/viz.py`'s `esc()`) before interpolation —
this is the one place a hand-rolled approach needs explicit discipline
that a templating engine would give by default, and it's applied
consistently at every interpolation site. If Phase 4's narrative layer or
later phases need real template inheritance, multi-page navigation, or
non-trivial control flow in markup, revisit — Jinja2 is a reasonable
addition at that point, not a rejected option forever.

**3. The dashboard is reached via a real form: `GET /` (holdings-entry
form) -> `POST /dashboard` (results page), built on Phase 1's own
`PortfolioRequest`/`build_portfolio_return_data`, not a parallel input
model.** `POST /dashboard` constructs the exact same `PortfolioRequest`
Phase 1's `POST /portfolio/returns` uses, calls the same
`build_portfolio_return_data`, then `analyze_portfolio` — this is
deliberate: the dashboard must show live model output, and reusing Phase
1/2's real functions (not reimplementing or mocking a subset) is what
makes that true rather than aspirational. Repeated `symbol`/`weight` form
fields (rather than a fixed number of named fields, or a JSON textarea) let
the form support an arbitrary number of holdings via FastAPI's native
`list[str] = Form(...)` support, with a small vanilla-JS "add holding"
button cloning a `<template>` row — no separate holdings-count negotiation
between client and server.

**4. Return/risk attribution (the dashboard's 3rd required view) is
presentation-layer logic in `app/dashboard/attribution.py`, not a new
Phase 2 model output.** It deliberately does not touch
`app/models/schemas.py`'s stable Phase 2/3/4 contract. Two derivations:
   - **Risk attribution** is exactly `FactorModelResult.r_squared` (factor-
     explained share of return variance) vs. `1 - r_squared`
     (idiosyncratic/residual share) — no new computation needed.
   - **Return attribution** decomposes the portfolio's realized mean
     periodic excess return into alpha plus each factor's own contribution
     (`loading_i * factor_i`'s own mean return over the same aligned
     window). This is an **exact OLS identity**, not an approximation or a
     new model: the Fama-French regression is fit by OLS with an
     intercept, which guarantees the fitted residual has zero mean over
     the regression sample, so `mean(excess_portfolio) = alpha +
     sum(loading_i * mean(factor_i))` holds by construction. The
     contributions are reported **per-period (not annualized)** —
     deliberately, because decision 0003 already establishes that alpha's
     annualization (compounding) and the frontier's annualization (linear
     scaling) are different, non-interchangeable conventions; summing
     already-annualized, differently-convention'd pieces back into a whole
     would not reconcile the way the per-period identity above does
     exactly. Phase 4 should present these as per-day/per-month
     contributions and should not re-annualize them piecewise — if a
     narrative wants an annualized headline number, annualize the *total*
     (via the alpha compounding convention, since it's a return, not a
     covariance object), not each factor's slice individually.

**5. Statistical diagnostics are visible in the chart itself, not only in a
hover tooltip or a linked table.** Per the assignment's explicit
requirement ("diagnostics visible, not hidden"), every Fama-French loading
bar renders a 95% CI whisker directly under the bar (not just in the
tooltip/table), and CAPM beta/alpha stat tiles show their CI, t-stat, and
p-value as visible sub-text, not a hover-only affordance. The tooltip and
the `<details>` table-view twin are additive (per `interaction.md`:
"tooltips enhance, never gate"), not the only way to reach these numbers.

**6. `EfficientFrontierResult.covariance_regularized` is surfaced as a
visible warning banner on the frontier chart when true**, per decision
0003's own flagged consequence ("this should never happen silently") —
not buried in the table view.

**7. No investment-advice framing.** Section copy throughout explicitly
frames the frontier/gap numbers as descriptive positioning ("where your
portfolio sits", "not a rebalancing recommendation"), matching decision
0003's hard limit and the project's roadmap-level scope exclusion. The
disclaimer is a persistent banner at the top of the dashboard, not a
footnote.

## Consequences

- Phase 4 (`educator`) narrating this dashboard's numbers should read
  return-attribution contributions as per-period, not annualized, and
  should know the decomposition is an exact identity (sums to the realized
  mean excess return) rather than an approximate one worth hedging in
  prose.
- Phase 5 (`qa-tester`) verifying this dashboard should check the return-
  attribution identity holds numerically (sum of contributions ≈ realized
  mean portfolio excess return over the aligned window) as a strong
  correctness signal, in addition to the existing Phase 2 reference-value
  checks.
- Adding a client-side charting library or Jinja2 later is not blocked by
  anything here — this decision documents why they weren't needed *yet*,
  not a prohibition.
- `app/dashboard/` is new surface area with no dedicated unit tests for
  individual SVG-building functions (covered instead by an end-to-end
  live test through `POST /dashboard`, matching this project's existing
  convention of live-data tests over mocked ones for the data/API layer —
  see `tests/test_dashboard.py`). Phase 5 may want to add narrower
  synthetic-data tests for `attribution.py`'s numeric identity if tighter
  regression coverage is wanted before sign-off.
