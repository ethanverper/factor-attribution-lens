# 0013. Implementing the aperture identity (Phase 10d)

Date: 2026-08-11
Status: accepted

## Context

Decision 0012 specified five concrete changes: drop headline/display type weight, give
"Factor Lens" an actual mark, make the aperture motif functional (not decorative) in two
named places, audit the amber signal accent for one-accent discipline, and preserve the
graphite-navy dark mode / JetBrains Mono / `[NN]` bracket nav. This is the implementation
log for the two pieces that involved a real construction decision, plus the amber audit's
actual findings (the spec asked `developer` to check this in implementation, not a fixed
list to apply).

## Type weight

Every `var(--font-display)` heading that had an explicit `font-weight: 600` or `700`
(`h1`/`h2`, card headings across Overview/References/Learning/Glossary/Real World, the
masthead wordmark, the frontier/attribution chart card titles in `viz.py`) was dropped to
`500`. Two headings with no explicit weight (`.tool-group h3`, `.empty-results h2`) were
inheriting the browser's default bold via `<h2>`/`<h3>` — given an explicit `500` too,
since an implicit 700 is the same problem decision 0012 flagged, just less obvious in the
CSS. The Google Fonts request for Space Grotesk was trimmed from `500;600;700` to `500`
only, since nothing in the display face needs any other weight now.

Two exceptions, both matching decision 0012's carve-out ("a stat that's the literal point
of a card"): `.viz-stat-tile .stat-value` (27px mono, `font-weight: 600`) and
`.alloc-total-value` (15px mono, `font-weight: 700`) — both are the one number a card
exists to show, in the mono data face rather than the display face the decision was
actually targeting. In-SVG chart annotation text (marker labels, diagram totals) was also
left alone — those are small data-chart readouts, not "headline/display type."

## The aperture mark (`app/dashboard/mark.py`)

One construction (`_rings_markup`: an outer focus ring, a mid ring, a solid core) feeds
three places so the identity is genuinely one system:

- `aperture_svg()` — the masthead glyph, colored via `currentColor` so it inherits
  `--signal` and switches with the theme toggle for free, no second asset.
- `favicon_data_uri()` — the same rings on a rounded graphite housing, hardcoded
  `#0a0d13`/`#f0a63e` (the dark-mode tokens) since a `<link rel="icon">` can't resolve the
  page's CSS custom properties or `currentColor`.
- The frontier chart's "current portfolio" marker (`viz.py`'s new `shape == "iris"` case
  in `marker_shape_svg`) — concentric-ring proportions reproduced directly in that
  function's own SVG-attribute terms rather than imported from `mark.py`, since the chart
  plots in already-resolved pixel space (`px()`/`py()` output), not `mark.py`'s fixed local
  viewBox. Kept in sync by proportion (outer/mid/core ≈ 1 / 0.64 / 0.27 of the marker's `r`
  in both places) rather than by sharing code across two genuinely different coordinate
  systems.

Chose concentric circles over literal camera-iris blades (overlapping polygon shutters):
matches decision 0012's own wording ("concentric circles, clean geometric construction")
exactly, stays legible at favicon scale (16-32px, where blade geometry would just be
noise), and reads unambiguously as a focus ring/target rather than a gear or sunburst.

## The loading-state iris (`shell.py`)

This app has no fetch/XHR to hook a progress indicator off of — every entry point that
touches OpenBB (`POST /dashboard`, `GET /dashboard/sample`, `GET /dashboard/view`) is a
real, full-page browser navigation, not a client-side request. There was no prior loading
state at all (a real gap, not a restyle): a slow first fetch just left the previous page
sitting inert with no feedback until the new page arrived.

Mechanics: a single overlay (`.iris-loading-overlay`, `position: fixed`, hidden by
default) lives once in the shared shell, so both the form page and results page get it for
free. `[data-loading-trigger]` marks every element that's about to cause a live fetch (the
holdings form, and both sample-quickstart links — Overview's "Run a live example" and
Inputs' "Run the sample portfolio"); a shared listener in `_shell_script` shows the overlay
on `submit`/`click` and lets the browser's own navigation take over from there. No teardown
code is needed for the success path — a full navigation replaces the whole document,
overlay included. The one edge case that isn't a fresh document load is the bfcache
restoring a frozen "is-visible" DOM if the user hits Back mid-load; a `pageshow` listener
clears it so Back can never reopen the page stuck showing the loading state.

The animation itself is CSS keyframes animating SVG `r` (radius) on the mid ring and core
circle — a breathing open/close — plus a slow continuous rotation of the whole glyph for a
mechanical "adjusting focus" read, gated behind `prefers-reduced-motion`. This is the one
new decorative-adjacent motion in the app, and it's deliberate per decision 0012 #5 (motion
stays restrained everywhere else; this is the one named exception, tied to the brand mark
rather than a generic spinner).

## Amber accent audit — actual findings, not just a CSS read

Checked the *rendered* app (in-browser `getComputedStyle` scan per tab, not a grep of the
CSS) for where `--signal` actually painted pixels on each of the eight tabs. Real,
measured overuse found and pulled back to neutral (`--text-muted`/`--border`):

- `.viz-stat-tile` border-top — every stat tile (8-10 on a single Results page) had an
  amber cap; none of them is individually "the one important number" more than any other.
- `.ref-tag` module-tag pills — all 6 References cards, purely a "which file" label.
- `.formula-block` left border — repeated on every formula, multiple per card.
- `.method-mark` (CAPM/Fama-French/Markowitz labels) — 3 uses on the Overview hero alone.
- `.source-note .sn-mark` "source" badge, `.quickstart-btn` — the quickstart link was a
  second solid-filled CTA competing with the Inputs form's own "Run analysis" submit
  button; changed to the same outline treatment as `.hero-cta-secondary`/`.share-btn`
  rather than removing the shortcut.
- `.learn-register.is-technical`/`.glossary-row.is-technical` label color — measured
  directly on the live Glossary tab: **28 amber elements on one view** (27 glossary
  entries' "Technical" row label + the section eyebrow), the single clearest violation
  found. The register was already named in the label text itself, so the color was pure
  repetition; changed to neutral. Left the "Plain language" label's blue (`--signal-cool`)
  alone — that's a distinct chart color already established elsewhere, not the accent this
  audit was scoped to.

Post-fix, the same per-tab scan: Overview 3 (eyebrow, hero top-border, the one hero CTA),
Inputs 2 (eyebrow, the one submit CTA), Results 2 (eyebrow, the frontier legend swatch that
names the iris marker's color), everything else 1 (just the eyebrow, which is the same
`[NN]` bracket-nav echo on every tab, not a per-view "extra" accent). The frontier chart's
iris marker itself and the loading-overlay glyph are the two functional uses decision 0012
named; everything else is now either that eyebrow or a single primary action per view.

## Consequences

- `app/dashboard/mark.py` is a new, small, dependency-free module — no SVG/icon library
  added, consistent with decision 0004's no-client-library convention.
- The loading overlay only fires on entry points explicitly marked
  `data-loading-trigger`; a future new fetch-triggering control (e.g. a different
  quick-start portfolio) needs that attribute added by hand, not something the pattern
  discovers automatically.
- The amber pull-backs are a real (if small) visual change beyond decision 0012's literal
  five-item list, since the decision explicitly delegated the audit's actual scope to
  `developer` ("developer to check in implementation"). Worth a quick look from Ethan since
  it touches more surface area than the other four items.
