# 0016. Phase 10g: implementing the interaction/motion layer + Tools & Technologies

Date: 2026-08-11
Status: accepted

## Context

Decision 0015 (`brand-creative`, Phase 10f) specified the interaction/motion language and the
Tools & Technologies replacement content in full detail. This phase (`developer`, Phase 10g)
builds that spec, plus fixes the unscoped `--reload` dev-server watcher (rule 12) and runs
`impeccable` as a final polish pass.

## 1. Dev-server watcher fix (rule 12)

`README.md`'s documented run command was `uv run uvicorn app.main:app --reload` — with no
`--reload-dir`, uvicorn's `--reload` watches the entire project root by default, including
`.venv/` (thousands of dependency files: pandas, numpy, statsmodels, etc.), causing constant
spurious reloads on package-internal file access unrelated to any real code change. Fixed to
`uv run uvicorn app.main:app --reload --reload-dir app` everywhere the command is documented
(`README.md`'s two run blocks). Verified directly: started the corrected command, confirmed
uvicorn's own startup log states `Will watch for changes in these directories:
['.../factor-lens/app']` (not the project root), then touched a file inside `app/` and
confirmed the reloader fired, and confirmed `.venv/` file activity does not trigger a reload
(no `WatchFiles detected changes` log line from any `.venv` path over a full test run).

## 2. Interaction/motion layer (decision 0015 §1–§7)

New module `app/dashboard/motion.py` holds the client-side implementation — kept separate
from `shell.py`'s existing script (`_shell_script()`, tab/combobox/allocation-form logic) and
`viz.py`'s `CHART_SCRIPT` (hover tooltips, theme toggle) rather than folded into either,
mirroring the project's existing one-module-per-concern convention (`diagrams.py`,
`mark.py`). Exports `GSAP_VENDOR_SCRIPT_TAG` and `MOTION_SCRIPT`, both wired into
`shell.py::render_app_shell`'s script tags, after `_shell_script()`.

**GSAP is vendored, not CDN-loaded** (decision 0015's own flag): `app/static/vendor/gsap.min.js`
(GSAP 3.15.0 core, ~72KB unminified-adjacent/~26KB gzip-equivalent, downloaded once from
jsDelivr's npm mirror and committed as a static file — no build step, no bundler, served by
the existing `StaticFiles` mount). No ScrollTrigger or other plugin is included, matching
decision 0015's explicit "deliberately no ScrollTrigger" call — every scroll-linked reveal in
this app is a plain, once-only `IntersectionObserver`, not scroll-scrubbing.

**Progressive enhancement, enforced structurally, not just by convention**: every reveal
function in `motion.py` follows the same shape — the server-rendered HTML is already the
correct final state (a stat tile's real number, a bar at its real width, a fully-drawn
frontier polyline); JS only ever *hides* an element (`gsap.set(..., {scaleX: 0})` /
`{autoAlpha: 0}` / a computed `strokeDashoffset`) immediately before animating it back to
that already-correct state. No CSS in `shell.py`/`viz.py`/`diagrams.py` hides anything by
default. This means: (a) a no-JS client sees the correct final page with zero flicker, (b) a
`prefers-reduced-motion` client sees the correct final page with zero flicker (the shared
`FL_REDUCED` flag, set once via `gsap.matchMedia('(prefers-reduced-motion: reduce)', ...)`,
short-circuits every reveal function before it hides anything), and (c) `httpx`-based tests
(no JS execution at all) keep seeing the true SSR'd values untouched, exactly as decision
0015 flagged.

**Per-surface implementation, matching decision 0015's exact spec:**

- **Buttons/nav hover-press** (`shell.py::SHELL_STYLE`): the exact CSS block from decision
  0015 §1, verbatim — `transition` on the classes that already had hover states defined but
  snapped instantly, `scale(0.97)` on `:active`. No JS.
- **Tab fade** (`shell.py::_shell_script`'s `activate()`): calls `window.__flTabFadeIn(panel)`
  (defined in `motion.py`) right before `scrollIntoView` — a 120ms `power1.out` opacity fade
  via `gsap.fromTo(panel, {autoAlpha:0}, {autoAlpha:1, ...})`. Only fires on an actual tab
  switch (a click or hash navigation), never on the initially-active panel at page load.
- **Results entrance choreography** (`motion.py::initResultsEntrance`): the freshness banner
  fades/slides in (`y: 8→0`, 260ms `power2.out`); section 1 (`data-reveal-section="1"`, the
  factor-exposure cards) reveals immediately (tiles stagger, then its bar chart);
  sections 2/3 (frontier, attribution) are wrapped in their own `data-reveal-section`
  containers and observed via `IntersectionObserver({threshold: 0.3}, once)` — they do not
  fire on page load. `pages.py`'s three section-builder functions now each wrap their output
  in `<div class="results-section" data-reveal-section="N">`, which also required a small CSS
  fix (`.results-section:first-of-type .section-title` replacing a `.section-title:first-of-type`
  selector that would otherwise have matched *all three* section titles once each became the
  sole `.section-title` child of its own wrapper, not just the first).
- **Data reveal, per mark type** (decision 0015 §4):
  - *Stat-tile count-up*: `viz.py::stat_tile()` gained the signature change decision 0015
    flagged — optional `count_target`/`count_decimals`/`count_suffix`/`count_signed` kwargs,
    rendered as `data-count-*` attributes alongside the real text. Three thin wrappers
    (`stat_tile_pct`/`stat_tile_num`/`stat_tile_ratio`) compute the right attributes from the
    same raw numeric value already being formatted, so call sites in `pages.py` changed from
    `viz.stat_tile(label, viz.fmt_pct(x, d, signed=s), sub)` to
    `viz.stat_tile_pct(label, x, d, signed=s, sub=sub)` — same call shape, now animatable.
    `motion.py`'s `startCountUps` tweens a proxy number 0→target (550ms `power2.out`),
    reformats it on every tick using the *same* sign/decimals/suffix logic as the Python
    formatter, and restores the exact original `textContent` on completion (not a
    recomputed string) so there is no risk of a JS/Python formatting drift.
  - *Diverging bars*: each bar's `<path>` is wrapped in `<g class="viz-bar-reveal"
    data-reveal-order="i" style="transform-origin:{zero_x}px ...">` — `motion.py` sets
    `scaleX: 0` then tweens to `1` (450ms `power2.out`, 60ms stagger). CI whisker groups
    (`viz-whisker-reveal`, same `data-reveal-order`) fade in 100ms after their own bar's
    tween completes (via that tween's own `onComplete`, not a fixed global delay, so it stays
    correct regardless of stagger position). `risk_split_bar`'s two segments reuse the same
    `viz-bar-reveal` class/technique, anchored at each segment's own left edge instead of a
    shared zero baseline (a stacked split-bar has no zero baseline to speak of).
  - *Frontier curve*: `<polyline class="viz-frontier-polyline">` — length measured client-side
    (`getTotalLength()`, no server change), drawn in via `stroke-dashoffset` (500ms
    `power2.out`). The three named markers (GMV, max-Sharpe, current-portfolio — the halo now
    travels *inside* the current-portfolio marker's own `<g>` rather than as a separate
    top-level element) are each wrapped in `<g class="viz-marker-pop" data-marker-order="i">`
    and pop in, in that order, once the curve finishes (`scale 0.8→1`, `autoAlpha 0→1`,
    `back.out(1.4)`, 80ms stagger) — the one sanctioned overshoot ease in the whole spec. A
    degenerate/empty frontier (single-asset portfolios, decision 0011) has no polyline points;
    `motion.py` detects this (`points` attribute empty) and pops the markers in directly
    without attempting to measure a zero-length path.
- **Allocation inputs — paired number + range** (decision 0015 §5): `pages.py::_holding_row_html`
  now renders both `<input type="number" name="weight" class="weight-number">` (unchanged
  contract — still the value FastAPI/Pydantic actually receives) and
  `<input type="range" data-weight-range>` inside a `.weight-control` wrapper. Two-way
  binding lives in `motion.py`: dragging the range writes the number's `.value` and dispatches
  a synthetic `input` event on it (picked up for free by the existing delegated
  `rowsContainer.addEventListener('input', ...)` in `_shell_script`, which already
  recalculates the allocation total — zero changes needed to that validation logic); typing
  in the number syncs the range back via a small `shell.py`-side hook
  (`window.__flSyncWeightRange`) added to the same existing delegated listener. Track fill is
  painted as a two-stop CSS gradient computed in JS on every input (no cross-browser-reliable
  CSS-only way to show "filled to value" on a native range). "Split evenly"/"Normalize to
  100%" now sweep the changed values into place over 150ms (`window.__flTweenWeight`,
  `power1.out`) instead of snapping instantly, calling the existing `recalcAlloc()` on every
  tick so the total badge visibly tracks the sweep — this is specifically what Ethan's
  "desplazamiento visual más interactivo" ask meant in practice for this control.
- **Learning diagrams — scroll-triggered reveal, and *only* these three** (decision 0015 §6):
  `diagrams.py::_figure()` gained a `diagram_id` parameter, rendered as `data-diagram="capm
  |ci|frontier"` — the single hook `motion.py::initLearningDiagramReveal` needs to observe
  (`IntersectionObserver({threshold: 0.4}, once)`) and dispatch to a per-diagram reveal
  sequence. CAPM: four blocks (`diag-reveal-item`, including the total/answer box) fade in
  left-to-right, 150ms stagger. CI whisker: each row's bar (`diag-ci-bar`) appears, then its
  whisker draws outward (`diag-ci-whisker-line`, `stroke-dashoffset`, 300ms) with its two cap
  lines/CI label fading in alongside, then its verdict (`diag-ci-verdict`) fades in last — the
  two example rows run this sequence 150ms apart. Frontier-position: the curve
  (`diag-frontier-curve`) draws in via genuine `stroke-dashoffset` (it is a plain solid
  stroke); the current-portfolio dot (`diag-frontier-current`) pops in with `back.out(1.4)`;
  the two gap arrows (`diag-frontier-arrow`) scale in from the current-portfolio point's own
  origin rather than using a `stroke-dashoffset` draw — those connectors are already
  decoratively dashed (`stroke-dasharray="4 3"`, an existing visual, not new), and a
  dashoffset-based draw-in would either fight that fixed short-dash pattern or require
  overwriting and restoring it, for a shorter/less legible line than the frontier curve
  itself. A scale-from-the-dot pop reads as "the arrow grows outward from the dot" just as
  intended, without that complication — a deliberate, documented technique deviation from the
  spec's general "stroke-dashoffset for the one literal path" framing, scoped to this one
  decorative-dash case only. **No** `data-diagram` attribute (and therefore no scroll
  observation at all) exists anywhere in Glossary, References & Formulas, Tools &
  Technologies, or Real World — satisfying decision 0015's explicit anti-pattern warning by
  construction, not by a rule someone has to remember to keep following.

## 3. Tools & Technologies (decision 0015 Part 2, rule 13)

`shell.py::render_tools_section()` replaced wholesale with decision 0015's five-category
content (Languages, Frameworks & Libraries, Data & Quant Methods, Presentation & Rendering,
Infrastructure & Delivery) plus its framing line — dropped in from the decision doc, not
re-originated. The list markup changed from a cramped `name | short phrase` inline-flex row
(Phase 9c's original, sized for one-line tags) to a stacked `name` then full-sentence
description, since several entries are now a genuine sentence or two — the old fixed
`min-width: 168px` name column either truncated or forced awkward wrapping at that length.

## 4. `impeccable` pass — not run this phase

Scoped for this phase but not completed: the implementation work above (section 2/3) plus
verification against a heavily resource-contended sandbox (system load average 11-15, an
unrelated ~9.5-minute full test-suite run) consumed the phase's available turns before the
`impeccable` polish pass was reached. Interactivity implementation, the watcher fix, and the
Tools & Technologies content are complete and verified (75/75 tests passing after a follow-up
fix to an overly-broad test assertion, done directly rather than via a further agent resume —
see `docs/roadmap.md` Phase 10g). The `impeccable` pass remains open — flagged explicitly
rather than silently marked done, per this team's own escalation discipline (don't claim a
step happened when it didn't).

## Consequences

- `app/static/vendor/gsap.min.js` is a new, versioned, checked-in binary-ish asset (minified
  JS) — no license concern (GSAP's standard license permits this use, including commercial,
  per the current GreenSock/Webflow terms), but it does mean a future GSAP upgrade is a manual
  re-download-and-commit, not a `uv`/npm-managed dependency bump. Acceptable for a small,
  rarely-changing core library in a no-build-step project.
- `viz.py::stat_tile()`'s new keyword-only parameters are additive and default to "no
  count-up" (`count_target=None`) — every pre-existing call site that wasn't touched (there
  are none left un-migrated, but the signature itself is backward compatible) keeps working
  unchanged.
- The three `stat_tile_*` helper functions are a thin, deliberate convenience layer over
  `stat_tile()` — not a new abstraction speculatively covering cases that don't exist yet,
  just the three formatting shapes `pages.py` actually uses (percent, plain number, ratio).
