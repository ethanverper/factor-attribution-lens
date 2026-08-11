# 0010. Phase 9e: real inline diagrams in Learning, and a glossary
completeness/organization audit

Date: 2026-08-10
Status: accepted

## Context

Ethan's direct feedback on the live Phase 9 Learning and Glossary sections: "La parte de
las explicaciones me gusta pero aún le falta calidad, es mucho texto solamente, añade
elementos visuales o interactivos de mejor calidad, como diagramas" (Learning is
text-only, needs real visual elements like diagrams) and "quiero que seas aún más claro
en la parte del glosario con todos los términos que se necesitan" (the glossary needs to
be clearer, with all necessary terms). `docs/project-standards.md` rule 5 already requires
this ("Every non-trivial concept explained should have a real visual aid... built inline,
not just described in prose") -- Phase 9 shipped four solid dual-register cards but no
diagrams, which is the gap Ethan is naming directly.

## Part 1: three inline SVG diagrams in Learning

Loaded the `artifact-diagramming` skill for its inline-SVG construction principles
(content-sized `viewBox`, labeled arrows over a legend, `<figure>/<figcaption>` with
`role="img"`/`aria-label`, hand-built shapes, no libraries) and applied them directly in
`app/dashboard/diagrams.py` (new module) rather than publishing a separate claude.ai
Artifact -- a visitor to the deployed app needs to see these in place, per the assignment
and rule 5's explicit instruction.

**Which concepts got a diagram, and why (judgment call against the assignment's own
three candidates plus a fourth considered and rejected):**

1. **CAPM decomposition** (`capm_decomposition_diagram`) -- three connected blocks
   (risk-free baseline, β-scaled market exposure, alpha) that sum exactly to the total
   return, echoing the app's existing `risk_split_bar` segmented-bar visual language from
   `viz.py` but clearly distinct (illustrative widths, not live data) so it doesn't read as
   a second Results chart.
2. **What a factor-loading confidence interval actually shows** (`factor_loading_ci_diagram`)
   -- two generic example loadings with 95% CI whiskers, one whose interval excludes zero
   (labeled a real exposure) and one whose interval straddles zero (labeled inconclusive).
   Deliberately a *different* dataset from the Results diverging-bar chart, per the
   assignment: this one teaches the *idea* of reading a whisker, the Results chart shows
   *this run's* actual whiskers.
3. **Frontier position** (`frontier_position_diagram`) -- a conceptual concave frontier
   curve with a portfolio dot below it and two labeled dashed arrows showing the two
   equivalent readings of the same gap ("more return, same risk" vs. "same return, less
   risk"), word-labeled axes ("Lower"/"Higher") rather than numeric ticks specifically so
   it can't be mistaken for a real chart.
4. **Return/risk attribution -- deliberately no diagram.** This card's claim is an exact
   algebraic identity already rendered as real notation in its Technical register and as a
   literal table on the Results tab (`mean(Rp − Rf) = α + Σᵢβᵢ·mean(factorᵢ)`, which sums
   to the displayed total). A diagram here would just redraw the same equation as boxes
   with no new mechanism made visible -- the guidance to "not force a diagram where a clean
   stat/example genuinely explains it better" applies directly. Kept text-only.

All three diagrams reuse the shared design tokens Phase 9c/9d established
(`--signal`, `--series-1`, `--diverging-neg`, `--status-good`, `--status-warning`,
`--font-mono`, `--baseline`, `--text-secondary`/`--text-muted`) with **no new colors
introduced** -- `--signal` (amber) marks the "current portfolio" dot in the frontier
diagram and the alpha block in the CAPM diagram (the same semantic role it already plays
everywhere else: "the thing that's yours/the emphasis"); `--series-1` (blue) marks
positive/market-linked marks, matching the Results diverging-bar chart's own color
assignment exactly. `.learn-diagram svg text` routes through `var(--font-mono)`, matching
decision 0008/9d's "every number/label drawn inside an SVG uses the mono readout face"
convention rather than falling back to the body sans.

**A real bug caught during this phase's own verification, not hypothetical:** the first
draft of the CAPM diagram sized its "risk-free" block too narrow for its own
plain-language label, which then rendered left-clipped ("-free baseline" instead of
"Risk-free baseline") because the centered label text extended past the SVG's own
`viewBox` origin; separately, the "alpha" block's label was wide enough to visually
collide with the total-return box's label immediately to its right. Caught via an
element-scoped Playwright screenshot of the diagram (not just eyeballing the full page),
root-caused to label width vs. block width rather than assumed away, and fixed by widening
the blocks and shortening in-diagram labels to a word-or-three (moving the fuller
explanation into the figure's `<figcaption>`, consistent with the `artifact-diagramming`
skill's own guidance that explanatory sentences belong in the caption, not the drawing).
The factor-loading CI diagram had the same class of bug (verdict text overflowing the
`viewBox`'s right edge) with the same fix (shorter verdict labels, wider right margin).
Re-verified via fresh element screenshots, light and dark mode, after the fix.

## Part 2: glossary completeness audit and reorganization

Read every tab of the live app end to end (Overview, Inputs, Results, Learning, References
& Formulas, Real World / Corporate Applications, Tools & Technologies) checking every
technical term against `render_glossary_section()`. Found two distinct kinds of real gaps:

1. **Four terms already correctly written in `docs/glossary.md` had never actually been
   ported into the live `render_glossary_section()`** -- a visitor could see "Covariance
   regularization," "Return attribution," "Risk attribution," and "Markowitz mean-variance
   optimization" used repeatedly on the Results and References & Formulas tabs (the
   frontier warning banner, the §3 section titles, the Markowitz reference card, the Real
   World wealthtech card) but could not find any of the four defined in the app's own
   Glossary tab. This is exactly the kind of drift a docs-archive-vs-live-app split
   produces if not audited directly against the running app rather than against the docs
   file alone.
2. **Five more terms appear repeatedly in the app's own text with no definition
   anywhere** (neither the live Glossary tab nor `docs/glossary.md`): F-statistic (its own
   Results stat tile, "Fama-French R² (and adjusted R², and the overall F-statistic)" in
   the Learning card), excess return (the quantity every regression in the app is actually
   fit on), the risk-free rate itself (used in nearly every formula, never independently
   defined even though "Sharpe ratio" presupposes the reader already knows what it is),
   the covariance matrix Σ as a concept distinct from its regularization (portfolio
   variance's actual mechanism, `w^TΣw`), and the annualization-convention split
   (compounding vs. linear scaling) that three separate cards/cards' notes reference by
   pointing at decision 0003 without ever stating the idea itself as a term. Adjusted R²
   (shown on its own stat tile next to R²) was folded into the existing R² entry rather
   than given a standalone one -- it's a minor variant of the same statistic, not a
   separate concept.

All nine gaps closed in `app/dashboard/shell.py::render_glossary_section()`, ported/synced
into `projects/finance/factor-lens/docs/glossary.md`, and rolled into the Cowork OS
portfolio-wide `docs/glossary.md` (which had its own independent version of the same
gap -- missing the same four ported terms plus "Statistical significance," pre-dating this
phase). Term count: 19 → 27 in both the project glossary and the live app; 18 → 27 in the
portfolio-wide glossary (which also picked up "Statistical significance," a pre-existing
gap there, not introduced this phase).

**Reorganization.** A single 19-entry flat list was already borderline hard to scan; a
27-entry one would be worse. Grouped into three concept areas matching how the app itself
is organized (Results §1 vs. §2 vs. §3):

- **Factor models & regression** -- CAPM through Statistical significance (how a return
  gets explained, and how confident you should be in the explanation).
- **Portfolio theory & optimization** -- Efficient frontier through Annualization
  convention (how the frontier is built and read).
- **Attribution** -- Return attribution, Risk attribution, Idiosyncratic risk (putting the
  exposures back together into the realized numbers).

Each group has a one-line description above its entries (`app/dashboard/shell.py`'s new
`group()` helper), and groups are visually separated by a dashed rule matching the
existing `--baseline`-dashed divider convention used elsewhere in the app (References &
Formulas' source note, the Learning section's own footer note) -- no new visual pattern
invented. CSS added to `SHELL_STYLE`'s existing Glossary block
(`.glossary-group`, `.glossary-group-head`), reusing `--font-display`/`--text-secondary`
tokens already in use by every other card heading in the app.

## Verification

- Full 42-test suite: passing (unchanged count -- no new user-facing behavior beyond the
  Learning/Glossary content itself, which existing tests don't assert on term-by-term).
- `ruff check .`: clean.
- Manual pass in the in-app Browser tools (Playwright): element-scoped screenshots of all
  three new diagrams individually, in both light and dark mode, confirming the shared
  design tokens render correctly in both themes and catching/fixing the two label-overflow
  bugs described above; a full-page screenshot of the Learning tab confirming the diagrams
  sit correctly inside their cards; a full-page screenshot of the regrouped Glossary tab in
  both themes confirming the three group headings, dashed separators, and all 27 entries
  render without overflow; a 375px mobile check on both the Learning and Glossary tabs
  confirming no horizontal page overflow (`document.documentElement.scrollWidth ===
  clientWidth` both before and after, matching the check method decision 0008 used for its
  own mobile bug).

## Consequences / handoff

- **Phase 10 (`qa-tester`):** Learning and Glossary are now real content with visual
  elements and a completeness-audited, grouped glossary; no known open items from this
  phase. The frontier-chart marker-label overlap bug (flagged across Phases 3, 7, 8, 9d) is
  unrelated to this phase's work (that's `viz.py`'s Results chart, not the new Learning
  diagrams) and remains open for Phase 10 as previously flagged.
- Any future new term introduced by a later phase should be added to all three surfaces in
  the same pass (`app/dashboard/shell.py::render_glossary_section()`, the project
  `docs/glossary.md`, and the portfolio-wide `docs/glossary.md`) rather than one at a time
  -- this phase's two biggest gaps were both exactly this kind of partial update drifting
  across the three copies.
