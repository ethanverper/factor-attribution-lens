# 0011. Phase 10b: frontier-chart marker-label collision fix, plain-language
validation errors, and the degenerate-frontier note

Date: 2026-08-11
Status: accepted

## Context

Phase 10 (`qa-tester`) returned verdict **NOT READY**, blocked on one defect
that had been flagged and deferred across Phases 3, 7, 8, and 9d without an
actual fix: `app/dashboard/viz.py::marker_group()` (the frontier chart's
GMV / Max Sharpe / current-portfolio marker labels) had right-edge overflow
avoidance but no awareness of *sibling* labels, so two or three markers
landing close together produced illegible stacked/overlapping text. QA also
reproduced the degenerate case directly: a single-asset portfolio makes GMV,
Max Sharpe, and the current portfolio the exact same point by construction,
stacking all three labels on top of each other. Two non-blocking findings
came with it: raw pydantic validation dumps leaking to users on two error
paths, and a silently-empty frontier chart for degenerate portfolios with no
explanation. This decision covers the fix approach for the blocking defect
(the one with real design tradeoffs) and briefly notes the other two.

## Decision: cluster-and-merge, not just push-apart

Two shapes of fix were on the table:

1. **Pure collision avoidance** — always draw three independent labels,
   nudge overlapping ones apart (vertically stack, or radially offset).
2. **Cluster and merge** — detect when marker *positions* are close enough
   to read as the same point on screen, and give that cluster one combined
   label ("GMV = Your portfolio") instead of stacking two/three separate
   ones; fall back to a lighter collision-avoidance pass only for labels
   that remain close but visually distinct.

Went with (2), layered as two passes, because pure collision avoidance alone
doesn't handle the degenerate case cleanly: pushing three labels for the
*same point* apart in space would draw three separate call-outs pointing at
one dot, which is confusing precision theater, not clarity. QA's own example
fix suggestion ("merge into one combined label... when two+ markers are
within some pixel threshold") is the more honest representation of what's
actually true at that point on the chart — these portfolios *are* the same
(or effectively the same) portfolio, and the label should say so directly.
The lighter collision-avoidance pass still exists as a second layer for the
case QA also called out — two markers close but genuinely distinct (their
own repro: GMV and current portfolio ~0.5px apart, which *does* cross the
merge threshold, but a marginally-larger separation could plausibly not).

## Implementation (`app/dashboard/viz.py::frontier_chart`)

1. **Union-find clustering.** All three markers' pixel positions (`px()`/
   `py()`, already computed for the marks themselves) are pairwise-compared;
   any two within `COINCIDENT_PX = 6.0` screen pixels are unioned into the
   same cluster. 6px was chosen because it's inside the visual footprint of
   the markers themselves (5-6px marker radius, matching stroke widths) —
   below that threshold the dots already visually overlap, so pretending
   their labels refer to distinguishable locations would be misleading.
2. **One label per cluster.** A cluster of size 1 gets its marker's own
   short label ("GMV", "Max Sharpe", "Your portfolio"); a cluster of 2+ gets
   `" = ".join(...)` of its members' short labels, anchored on the cluster's
   shared point. The existing right-edge overflow-avoidance logic (flip left
   instead of clipping) is applied once per cluster label instead of once
   per marker.
3. **Residual collision avoidance.** After cluster labels are placed, any
   remaining pairwise bounding-box overlap (markers close but not within
   `COINCIDENT_PX`) is resolved by sorting labels by y and nudging the lower
   one down until it clears every label already placed above it — a simple,
   bounded (max 10 iterations per label) greedy pass, sufficient for at most
   3 labels on this chart.
4. **Rendering order.** Marks, their (still per-marker, transparent)
   hover/tooltip targets, and labels are now three separate passes instead
   of one bundled `<g>` per marker — labels always render on top of every
   mark, so a label is never partially occluded by a neighboring marker's
   shape. The soft amber "Your portfolio" halo still renders first/lowest,
   now independent of clustering, so it still highlights the shared point
   correctly even when "Your portfolio" is coincident with GMV/Max Sharpe.

Extracted a small `_bbox_overlap()` helper (axis-aligned rectangle overlap)
used by the residual-collision pass; no external layout library — same
"no client-side charting library" convention as the rest of `viz.py`
(decision 0004), and the geometry involved is simple enough not to need one.

## Alternatives considered, not chosen

- **Leader lines / small multiples.** Overkill for at most 3 markers; adds a
  visual element (connector lines) the chart doesn't otherwise use for its
  reference markers, and doesn't solve the degenerate (literally-identical-
  point) case any better than merging does.
- **Always show all three labels with a fixed vertical stack near the
  point** (no clustering test, no merge). Rejected per the "cluster and
  merge" reasoning above — it hides the more useful fact (these points *are*
  the same) behind a plausible-looking layout trick.

## Other two findings (non-blocking), fix approach

- **Raw pydantic error text** (`routes.py`): duplicate-symbol and
  `start_date >= end_date` are now checked explicitly before
  `PortfolioRequest(...)` is ever constructed, with plain-language messages
  matching the existing convention (`"Your allocations add up to..."`).  The
  `except ValidationError` branch around `PortfolioRequest(...)` stays as a
  defense-in-depth backstop for any other schema-level failure (e.g. one
  reached only via a hand-crafted request that bypasses these checks), but
  now goes through a new `_plain_validation_message()` helper that strips
  pydantic's `"Value error, "` prefix and its `errors.pydantic.dev` URL/type
  metadata down to one plain sentence, rather than ever returning `str(exc)`
  directly.
- **Empty/degenerate frontier chart** (`pages.py::_render_frontier_section`):
  detect degeneracy directly from the computed data (`len(ef.frontier) == 0`,
  or — for the "fully-identical-holdings" shape the ticket also named — all
  frontier points collapsing to the same volatility within `1e-6`) and show
  an inline `info_banner()` explaining why, distinct wording for "only one
  holding" vs. "holdings are effectively identical," rather than leaving a
  silently-empty chart. Added a new `viz.info_banner()` (blue/`--series-1`
  tone) alongside the existing amber `warn_banner()` — this isn't a data-
  quality warning, it's expected, correct behavior that needs explaining, so
  it gets its own visually-distinct (non-alarming) treatment.

## Verification

- New unit tests (`tests/test_viz_frontier_chart.py`, 5 tests, no network):
  the exact degenerate (all three markers identical) case, QA's own close-
  but-distinct repro shape, a close-but-not-coincident collision case, the
  `max_sharpe=None` two-marker case, and a baseline far-apart/right-edge-flip
  regression check — all assert on real rendered label text/positions, not
  just "no exception."
- New/updated `tests/test_dashboard.py` cases (live, network): duplicate-
  symbol and bad-date-range submissions assert the plain-language message
  and the *absence* of `"validation error"` / `"errors.pydantic.dev"` in the
  response; a single-asset (100% AAPL) submission asserts both the
  degenerate-frontier note text and the merged
  `"GMV = Max Sharpe = Your portfolio"` label text end-to-end.
- Full suite: 51/51 passing (42 pre-existing + 9 new), `ruff check .` clean.
- Manual verification in the in-app Browser tools against QA's exact repro
  steps: the sample-portfolio quick-start (AAPL/MSFT/GOOGL/AMZN — close-but-
  distinct GMV/current markers merge into `"GMV = Your portfolio"`, Max
  Sharpe stays separate, no overlap), a single-asset 100% AAPL submission
  (three-way merge to `"GMV = Max Sharpe = Your portfolio"` plus the
  degenerate-frontier note), a duplicate-symbol submission, and a bad date
  range — all confirmed in both light and dark mode, and at a 375px mobile
  width.

## Consequences / handoff

- Phase 11 (`devops`): no changes to this decision's scope block deployment;
  noting only that the frontier chart's label logic is now materially more
  complex (clustering + collision-avoidance passes) — any future frontier-
  chart change should re-run `tests/test_viz_frontier_chart.py` specifically,
  not just the live end-to-end suite.
