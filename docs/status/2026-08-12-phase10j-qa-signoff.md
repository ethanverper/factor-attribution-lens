# Phase 10j — QA Sign-off on the React/Tailwind/shadcn Rebuild

Date: 2026-08-12
Tester: `qa-tester`
Scope: full independent re-verification of Phases 10i–10o (React rebuild, `POST /api/analysis`, Interpretation & Key Takeaways, institutional refinement, content decomposition) against `docs/project-standards.md` and this project's own definition of done, on `dev` (commit `a3ca81a`).

## Verdict: READY (with two non-blocking items to fix, and two interactions flagged as unconfirmed due to test-tooling limits, not observed defects)

Nothing found in this pass rises to blocking. The four things logged below are either cosmetic (two) or genuinely could not be exercised in this session because of a reproducible browser-automation-tool hang unrelated to the app (two) — server logs, console logs, and every non-drag interaction confirm the app itself stayed responsive throughout. Recommend shipping; the two cosmetic items and the two unconfirmed interactions should get a quick follow-up pass (by `developer` for the cosmetic fixes, by `qa-tester` for a re-check of the two interactions in a fresh session) but none of them should hold up Phase 11 (Deploy).

## What was covered

**Automated regression**
- Backend: `uv run pytest -q` — **76/76 passing**, including the dedicated synthetic `tests/test_interpretation.py` suite (priority-1..5 headline branches, both `covariance_regularized` sub-cases, `short_data_window`, no-advice-language guardrail, thresholds matching decision 0019).
- Frontend: `npx tsc -b` clean, `npm run build` clean (one pre-existing, expected warning: main JS chunk >500kB — not a new regression, no code-splitting was ever in scope for this phase).

**The two standing standard checks (rule 16 entity grep, advice-language grep)**
1. **HTML entity grep** (`grep -RnoE '&[a-zA-Z]+;'` across `frontend/src/data/*.ts`): many matches in `tools.ts`, `real-world.ts`, `glossary.ts`, `learning.ts`, `references.ts`. Traced every match to its rendering component: all render via `dangerouslySetInnerHTML` (`RealWorld.tsx`, `References.tsx`, `Glossary.tsx`, `Learning.tsx`, `Tools.tsx`), where entities decode correctly by design. Separately confirmed the fields that render as **plain JSX** (`real-world.ts`'s `stat`/`statLabel`/`quote.attribution`, `tools.ts`'s `name`/`title`, `learning.ts`'s `teaser`/xref `label`) contain **zero** entities — all literal Unicode (e.g. `"14% → 30%"`, em-dashes typed directly), exactly per decision 0022/0021's own documented convention and the code comments left in `real-world.ts` warning future editors about this exact bug class. Also checked `Overview.tsx`/`Results.tsx`/`InterpretationSection.tsx`/`SectionHeader.tsx` (component files with entities hardcoded directly in JSX markup, not interpolated from a string variable — these decode correctly under React's JSX-text-parsing rules, unlike `{variable}` interpolation). **No live rendering bug found** — confirmed visually too (Real World page rendered "14% → 30%", curly quotes, em-dashes all correctly, not literally).
2. **Advice-language grep** (`you should|consider (re)?balanc|\bbuy\b|\bsell\b|recommended|\brebalanc`) across all of `frontend/src/**/*.{ts,tsx}` and `app/**/*.py`: matches in `learning.ts` ("what to buy, sell, or hold" — inside an explicit disclaimer sentence), `real-world.ts` (RIAs "buy reporting tooling" — describing third-party industry behavior; four `rebalanc` hits, all either describing robo-advisors' own feature or the explicit "Factor Lens... doesn't rebalance anything for you" disclaimer), `references.ts` ("not a rebalancing recommendation" — disclaiming). **Zero real violations.** `InterpretationSection.tsx`, `LessonCallout.tsx`, and `app/api/interpretation.py` (the highest-risk surfaces per the task) had **zero matches at all**.

**Definition-of-done items**
- CAPM beta, Fama-French 3-/5-factor loadings with diagnostics, Markowitz efficient frontier, dual-register narrative — all present and, per Phase 10 (original)'s prior math verification plus this pass's live-vs-reference cross-checks on two new portfolios, numerically consistent.
- No personalized investment advice anywhere checked (see grep above).

**Interpretation & Key Takeaways (rule 9a)** — ran two genuinely different real portfolios live against `POST /api/analysis` (not the cached sample):
- AAPL 40/MSFT 30/GOOGL 20/AMZN 10, 5-factor: headline correctly picked the `style_tilt` branch (RMW loading 0.42, "high-profitability / quality tilt").
- JNJ 25/PG 25/KO 25/WMT 25, 3-factor: headline correctly picked the `explanatory_power` branch (CAPM R² 1.5%, "only weakly explained by ^GSPC") — closely reproduces decision 0019's own "Example B" live-verified text, confirming the rule set is stable against normal day-to-day data drift.
- AAPL 100% (single-asset, 3-factor): a bonus find — this hit the priority-5 **default "nothing stands out"** headline branch, which decision 0019 explicitly logged as never hit by its own live testing. Confirms the fallback branch is real and correctly triggered, not dead code.
- Visually prominent on Results: bordered `border-l-4` card directly under the run-metadata banner, above the numbered takeaway cards — matches decision 0019's placement spec.
- Data-quality flags: `short_data_window` **confirmed firing live** via a direct `POST /api/analysis` with a 20-observation window ("thinner than this analysis's own bar for an ample sample (60)"). `covariance_regularized` could not be triggered with real tickers in this session either (consistent with decision 0019's own finding — GOOG/GOOGL only reaches condition number ~501, far below the 1e8 trigger) but is covered by dedicated synthetic unit tests in `tests/test_interpretation.py` (`test_flag_covariance_regularized_thin_data`, `test_flag_covariance_regularized_correlation_structure`, `test_both_flags_can_fire_together`) — read those tests directly and confirmed the trigger logic (thin-data-ratio vs. correlation-structure attribution) is sound.

**Builder credit (rule 9b)** — confirmed live: sidebar footer (`Built by [Ethan Verduzco]` → `https://github.com/ethanverper/factor-lens`) and Overview's closing colophon sentence (`— Built by Ethan Verduzco`), both present, both linking correctly.

**30-second comprehension test (rule 14)** — Overview reviewed cold: one-sentence mechanism statement, a "You provide" chip row (holdings/benchmark/date range/factor model), a real live-computed frontier-chart miniature plus a precision-stat callout (`CAPM β 1.00 · R² 50.3% · AAPL/MSFT/GOOGL/AMZN vs. S&P 500`), three method cards (CAPM/Fama-French/Markowitz) with icons, and a one-click "Run a live example." All five rule-14 requirements present at a glance, no scrolling needed for any of them except the method cards which sit just below the fold on a 900px-tall viewport — reasonable.

**Constrained inputs (rule 2)** — combobox-only ticker/benchmark selection confirmed live (search-and-select, no free-text path to submission). Re-confirmed server-side independently of the UI via raw `curl POST /api/analysis`:
- Invalid ticker (`ZZZZFAKE`) → `400`, plain-language message.
- Invalid benchmark → `400`, plain-language message.
- Adversarial injection-style ticker (`<script>alert(1)</script>`) → `400`, safely rejected and echoed back only inside a JSON error field (no HTML-rendering surface, not a reflected-XSS path).
- Duplicate symbols → `422`, clear message (Phase 10b's dedupe check still in place).
- Weights not summing to 1.0 → `422`, clear message.
- Empty holdings list → `422`.

**Edge cases**
- **Single-asset / degenerate portfolio** (AAPL 100%): UI correctly reduces to a 1-row form (min-holdings-of-1 enforced, remove button hidden only when exactly one row remains), runs cleanly, frontier section shows a clear info banner ("Efficient frontier requires 2+ distinct holdings — showing your single position only") instead of a blank/broken chart, return-gap stat shows `—` with an explanation instead of a broken number. One cosmetic nit (see Bugs, below).
- **5-factor model path**: confirmed live — RMW/CMA loadings render correctly in the factor-loading chart, return attribution, and Interpretation copy (factor labels correctly pluralize to "size/value, profitability, investment").
- **Invalid ticker** (UI + server, both layers) — see above.
- **Dark mode**: confirmed working correctly (graphite-navy background, amber accent, themed chart, themed sidebar) — see note under Bugs/tooling about how long this took to confirm, purely a testing-coordinate issue, not an app defect.
- **Mobile 375px**: Overview reviewed at native 375×812 — chip row wraps correctly, buttons go full-width, no page-level horizontal scroll. One cosmetic label-clipping issue found on the Overview hero's mini frontier chart specifically (see Bugs).

**All 8 sections driven live**: Overview, Inputs, Results, Learning, Glossary, Tools & Technologies, References & Formulas, Real World — none read as an undifferentiated paragraph wall inside its component wrapper (rule 15 spot-checked directly, not inferred):
- **Real World**: 2-up grid (Phase 10o's own fix from the original 3-up-too-narrow finding) + a distinct spotlight card, each with lead → bullets → pull-quote → callout, real stat pulled to the card header. Confirmed all four cards render with correct Unicode (not literal entities).
- **References & Formulas**: `legend`/definition fields render as real `<dl>` term/definition lists, not run-on prose — confirmed visually.
- **Learning**: single-open `Accordion`, numbered badges with checkmarks, `Progress` bar (`N of 4 concepts explored`) — confirmed the progress bar **persists across a hard reload** (navigated away and back with `force: true`, count held at "2 of 4"). Each card's content is lead → bullets → callout → pull-quote → worked-example → diagram, not paired paragraphs.
- **Glossary**: grouped `Accordion` by concept area, dual-register term cards, all entities decode correctly.
- **Tools & Technologies**: five categorized groups with icons, each substantive entry tied to its actual use in this project (rule 13).

**Required Learning interaction (CI-whisker predict-then-reveal, decision 0020 §3c)** — confirmed working correctly end-to-end: both example rows show only point-estimate + whisker on open; clicking "Example A is the real exposure" reveals both verdicts (`✓ real exposure` / `≈ inconclusive`) plus the correct feedback line ("Correct — Example A's interval never crosses zero.").

## Bugs found

### Bug 1 — Frontier-chart marker label clipped on the Overview hero mini-chart at narrow widths
**Severity: Minor (non-blocking).**
**Repro:** Load `/` at a viewport ≤500px wide (reproduced at 375×812 and 500×700, on two separate tabs/sessions). Look at the "Live preview · sample portfolio" hero chart.
**Expected:** The "Max Sharpe (tangency)" marker label wraps, truncates with an ellipsis, or repositions to stay inside the card.
**Actual:** The label ("Max Sharpe (tange...") is clipped hard at the card's right edge with no ellipsis or wrap — legible enough to identify the marker but visibly cut off mid-word.
**Scope:** Only the Overview hero's compact Recharts mini-frontier-chart (its own separate, narrower instance from the full Results-page frontier chart, which has more width to work with and was not observed to have this issue at either desktop or the 900px width tested in this pass — not re-confirmed at 375px specifically for the full Results chart in this session, worth a quick follow-up check). Does not cause page-level horizontal overflow (confirmed no horizontal scroll on the page itself).

### Bug 2 — Minor copy/grammar nits (cosmetic only)
**Severity: Minor (non-blocking).**
- Results stat tiles format p-values as `p=<0.001` (redundant `=` before `<`) instead of `p<0.001` — appears on every stat tile with a very small p-value (CAPM beta, Fama-French alpha, F-statistic).
- Single-asset frontier section text reads "222 daily obs across 1 holdings" (should be "1 holding," singular) — `Results.tsx`'s frontier-section caption.
Both are text-template issues, not calculation errors — the underlying numbers are correct in every case checked.

## Unconfirmed (not failed — flagged for a fresh-session re-check)

### Item 3 — CAPM-decomposition draggable β slider (decision 0020 §3d, explicitly "recommended, not required")
Every attempt to drag or click this specific Radix `Slider` via the Browser automation tool (`left_click`, `left_click_drag`, both ref- and coordinate-based, across three different tabs) resulted in a reproducible 30-second tool timeout. Critically, **the page itself remained responsive throughout** — screenshots taken immediately after each timeout returned instantly, no console errors, no server errors, and other interactions on the same page (accordion clicks, the CI-whisker predict-then-reveal buttons two sections above this exact slider) worked correctly moments earlier. This strongly suggests a Radix `Slider` pointer-capture interaction that the CDP-driven synthetic drag/click doesn't resolve cleanly, rather than an app-level freeze — real mouse input from an actual user goes through native OS pointer events, not synthetic `dispatchEvent` calls, and Radix sliders are a widely-used, well-tested primitive elsewhere in this exact app (the Inputs page's allocation sliders were operated successfully via `form_input`/click without issue). Recorded as **could not verify**, not as a failure. Since this feature is explicitly optional per decision 0020, it should not block sign-off — recommend a quick manual mouse-drag check by a human, or a retry in a fresh automation session, before treating it as either confirmed-working or a real bug.

### Item 4 — Mobile Sheet-sidebar open/credit-reachability re-check
The same tool instability (30-second timeouts on `left_click` of the sidebar-toggle hamburger button at 375px) prevented re-confirming the Sheet-based mobile nav opens and that the builder-credit line is reachable inside it in this session, despite several retries across fresh tabs. This was previously verified by `developer` in Phase 10i's own manual pass ("mobile (375px, Sheet sidebar)... confirmed") and flagged again in decision 0020 §4 as needing a live check rather than an assumption — that live check did happen in Phase 10m ("desktop + mobile Sheet" for the credit line). Given two independent prior confirmations and no code change to `AppSidebar.tsx`'s Sheet wiring since, risk is low, but this pass could not independently re-verify it — flagged rather than silently assumed.

## What passed cleanly, worth stating explicitly (not just "everything else")

- Full backend test suite, `tsc`, `npm run build`.
- Both standard greps (entities, advice-language) — zero real violations found across the whole frontend/backend, not just the specifically-named files.
- Interpretation headline demonstrably varies across two real, different portfolios, plus incidentally exercised the previously-unhit default branch.
- Server-side constrained-input validation (ticker, benchmark, duplicate, weight-sum, empty-holdings, and one adversarial injection-style string) — all six cases correctly rejected with the right status code and a non-leaky message.
- Single-asset degenerate portfolio: clean handling end-to-end, no crash, no blank chart.
- 5-factor model path: fully functional, RMW/CMA loadings, attribution, and Interpretation copy all correct.
- Learning: accordion, progress persistence across a hard reload, and the required CI-whisker predict-then-reveal check all confirmed working.
- Dark mode: confirmed correct once properly targeted (see note below on the session's own coordinate-mapping false start).
- Builder credit, 30-second comprehension test, rule 15 content decomposition across all 8 sections: all confirmed live, not inferred from code.

## A methodology note on the session's own false starts (for transparency, not app-relevant)

Early in this pass, several `left_click` attempts on the sidebar theme-toggle button appeared to do nothing across ~5 tries at a 1280×900 viewport — this was traced to a coordinate-scaling mismatch between the reported screenshot size and the actual click target at that specific viewport/ref combination, **not** an app defect: switching to a smaller viewport (900×700, near 1:1 with the screenshot) made the exact same toggle work immediately and repeatedly. Recorded here so the "dark mode confirmed" finding above isn't mistaken for a shaky result — it was re-confirmed cleanly once the tooling issue was isolated and worked around.

## Files relevant to this sign-off

- Backend: `/Users/Ethan/Documents/Cowork OS/projects/finance/factor-lens/app/api/interpretation.py`, `/Users/Ethan/Documents/Cowork OS/projects/finance/factor-lens/tests/test_interpretation.py`
- Frontend data (entity/advice-language grep targets): `/Users/Ethan/Documents/Cowork OS/projects/finance/factor-lens/frontend/src/data/{tools,real-world,glossary,learning,references}.ts`
- Frontend components checked for rendering mechanism: `/Users/Ethan/Documents/Cowork OS/projects/finance/factor-lens/frontend/src/pages/{Overview,Results,RealWorld,References,Glossary,Tools,Learning}.tsx`, `/Users/Ethan/Documents/Cowork OS/projects/finance/factor-lens/frontend/src/components/{Highlight,InterpretationSection,LessonCallout}.tsx`
- Bug 1 location: `/Users/Ethan/Documents/Cowork OS/projects/finance/factor-lens/frontend/src/pages/Overview.tsx` (hero mini frontier chart)
- Bug 2 locations: `/Users/Ethan/Documents/Cowork OS/projects/finance/factor-lens/frontend/src/pages/Results.tsx` (p-value formatting, single-holding grammar)
- Slider component for item 3: `/Users/Ethan/Documents/Cowork OS/projects/finance/factor-lens/frontend/src/components/diagrams/CapmDecompositionDiagram.tsx`
