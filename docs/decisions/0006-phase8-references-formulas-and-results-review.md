# 0006. Phase 8: References & Formulas content, notation/citation convention,
and Results-section regression review

Date: 2026-08-10
Status: accepted

## Context

Phase 7 restructured the app into an eight-section sidebar shell and left
References & Formulas as a labeled placeholder (`render_placeholder_section`)
for Phase 8 to fill in, per `docs/project-standards.md` rule 1 ("the
math/financial formulas actually used, with sources, rendered properly —
not just prose describing them"). Phase 8 also had a second mandate: confirm
Phase 7's visual restyling of the Results tab didn't change any of the
underlying numbers or attribution logic from what Phase 2/3 originally
produced.

## Decisions

**1. References & Formulas documents what's actually implemented, one card
per module, not a generic textbook appendix.**
`app/dashboard/shell.py::render_references_section()` adds five cards —
CAPM (`app/models/capm.py`), Fama-French 3-/5-factor
(`app/models/fama_french.py`), Newey-West HAC regression diagnostics
(`app/models/_regression.py`), Markowitz mean-variance/efficient frontier
(`app/models/optimization.py`), and return/risk attribution
(`app/dashboard/attribution.py`) — each tagged with the file it documents,
so a reader can go straight from the formula to the code that computes it.
This is deliberate: the roadmap and the assignment both flag the risk of
publishing "a generic textbook version" instead of the project's actual
methodology (e.g. this app's CAPM/Fama-French regressions use Newey-West
HAC standard errors, not classical OLS SEs; the Markowitz frontier is
long-only by default with eigenvalue-clipping regularization — both
material deviations from the textbook object that the References section
now states explicitly rather than silently glossing over).

**2. Notation convention: inline HTML (`<sub>`/`<sup>` + named HTML
entities for Greek letters/operators), not an external math-typesetting
library (KaTeX/MathJax).**
Consistent with decision 0004 (no client-side charting library, no build
step, no new heavyweight dependency) and the project's plain-Python-string-
template architecture — pulling in a JS math renderer for one section would
be a new class of dependency for a small, static-content need. Formulas are
rendered as styled monospace blocks (`.formula-block`, new CSS in
`SHELL_STYLE`) with a left border in the site's signal accent color,
consistent with the "research memo" design system Phase 7 established.
**Bug caught during verification**: these strings are static/trusted
content (module docstrings' worth of prose, not user input), so they must
*not* be passed through `viz.esc()` — the first draft did escape the card
title/tag, which HTML-escaped the `&mdash;`/`&amp;` entities already in
those strings and rendered literal `&mdash;` text on the page instead of an
em dash. Fixed by not escaping title/tag/formula-label in
`render_references_section`'s `card()` helper (matching
`render_overview_section`/`render_tools_section`'s existing convention for
static content) — verified visually afterward, both light and dark mode.

**3. Citation style and sources used.**
Format: `Author, Initials. (Year). "Title." Journal, Volume(Issue), pages.`
— consistent across every card and the consolidated "Works cited" list at
the section's end. Primary sources cited (one per model, plus the
statistical-inference correction actually applied):
- CAPM: Sharpe, W.F. (1964), *Journal of Finance* 19(3), 425–442
  (independently derived in Lintner 1965 and Mossin 1966, both noted).
- Fama-French: Fama & French (1993), *Journal of Financial Economics*
  33(1), 3–56 (3-factor); Fama & French (2015), *Journal of Financial
  Economics* 116(1), 1–22 (5-factor).
- Newey-West HAC standard errors: Newey & West (1987), *Econometrica*
  55(3), 703–708 (the estimator); Newey & West (1994), *Review of Economic
  Studies* 61(4), 631–653 (the plug-in bandwidth rule
  `floor(4*(n/100)^(2/9))` this app actually uses, per
  `app/models/_regression.py`).
- Markowitz mean-variance: Markowitz, H. (1952), *Journal of Finance* 7(1),
  77–91; Sharpe ratio: Sharpe, W.F. (1966), *Journal of Business* 39(1),
  119–138.
- Return/risk attribution has no external citation — it's flagged in its
  own card as "a direct algebraic consequence of the OLS fit above," per
  `attribution.py`'s own module docstring, not a separately published
  result, to avoid implying a citation exists where the content is this
  project's own derivation.

**4. Results-section regression review: confirmed clean, no fixes needed.**
Ran the same AAPL(50%)/MSFT(30%)/GOOGL(20%) portfolio vs. `^GSPC`, 3-factor,
daily, used in Phase 3's own verification pass, two ways: (a) calling
`build_portfolio_return_data` → `analyze_portfolio` →
`compute_return_attribution`/`compute_risk_attribution` directly in a
throwaway script, and (b) submitting the same inputs through the live
`POST /dashboard` form in a headless browser. Every number rendered on the
Results tab matched the directly-computed reference values exactly (CAPM
beta 0.94, alpha +0.96% annualized, R² 44.1%; FF3 loadings mkt_rf +0.831,
smb −0.126, hml −0.350; FF alpha +9.50%, R² 48.2%/adj. 47.5%, F=78.4;
current-portfolio return 19.38%/vol 18.35%/Sharpe 0.83, return gap +2.31%;
return-attribution contributions +3.6/+5.5/−0.3/−2.7 bps summing to the
realized total +6.06 bps; risk attribution 48.2%/51.8%). Phase 7's
restyling only moved presentation chrome, as its own commit message
claimed — no regression in the underlying numbers or attribution logic.

**5. Pre-existing frontier-chart label overlap: confirmed present, not
fixed (out of Phase 8's scope, flagged for Phase 10/QA per the
assignment).**
Screenshotted the frontier chart for the same AAPL/MSFT/GOOGL portfolio —
"Your portfolio" and "Global min-variance" marker labels visibly overlap
into unreadable jumbled text, because this holding set's optimal long-only
portfolio (GMV return 18.2%/vol 18.30%) lands very close to the as-entered
portfolio (return 19.38%/vol 18.35%) on the chart. This matches exactly
what Phase 7 already flagged in the roadmap as a pre-existing `viz.py`
mark-placement issue, not something Phase 7's chrome changes introduced.
Confirmed seen, not fixed — `viz.py` chart logic is out of this phase's
scope per the assignment.

## Consequences

- `references` was removed from `shell.py`'s `_PENDING_TABS` set (no longer
  shows a "soon" badge in the sidebar nav) and `pages.py::_base_panels()`
  now calls `shell.render_references_section()` instead of
  `render_placeholder_section(tab_id="references", ...)`.
- The Overview panel's disclaimer strip, which previously said "References
  & Formulas for the exact math once Phase 8 publishes it," was updated to
  no longer reference Phase 8 as a future event.
- Phase 9 (`educator`) building Learning/Glossary/Real World can safely
  cross-link to `§07 References & Formulas` for the underlying math instead
  of re-deriving or re-explaining formulas there — Learning's job is the
  plain-language "what does this mean for you," not re-stating the
  notation this section already owns.
- Full 32-test suite passes unchanged; `ruff check app/` clean. No changes
  to `app/models/` or `app/dashboard/viz.py`/`attribution.py` — this phase
  only added presentation content and did not touch computation logic.
