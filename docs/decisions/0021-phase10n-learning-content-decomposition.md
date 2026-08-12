# 0021. Phase 10n: Learning content decomposition — per-card content spec

Date: 2026-08-12
Status: accepted (content spec; implementation is Phase 10n build, `developer`)

## Context

Sixth round of frontend feedback (`docs/project-standards.md` change log,
2026-08-12): even after Phase 10m rebuilt Learning as a real shadcn
`Accordion` with numbered lessons, a checkmark-per-lesson, and a persisted
progress bar (confirmed live by reading `frontend/src/pages/Learning.tsx`
and `frontend/src/data/learning.ts`), the content *inside* each opened
lesson is still exactly what it was before the rebuild: one "Plain
language" paragraph, then one "Technical" paragraph, back to back — real
component, undifferentiated prose inside it. That gap is what
`docs/project-standards.md` rule 15 now names explicitly and assigns to
`educator` to plan (for Learning/glossary content specifically) before
`developer` writes any JSX.

This document is that plan: a sentence-level decomposition of all four
existing `LEARNING_CARDS` (`beta`, `fama_french`, `frontier`, `attribution`
— confirmed these are the exact four by reading
`frontend/src/data/learning.ts` directly, not assumed) into the five rule-15
primitives — lead sentence, bullets, callout/aside, pull-quote/stat
highlight, worked example — plus a call on which existing/new component
mechanism each primitive should render as. Every worked example below uses
real, live-verified numbers, not invented ones (method below).

### How the worked-example numbers were obtained

Per the task's instruction to prefer real computed values over hypothetical
ones, `analyze_portfolio()` was re-run directly (not read from memory or
guessed) against **live data** for the app's own sample portfolio — AAPL
40% / MSFT 30% / GOOGL 20% / AMZN 10%, benchmark `^GSPC`, 3-factor, daily,
trailing 365 days ending 2026-08-11 — using the exact same
`build_portfolio_return_data` → `analyze_portfolio` → `compute_return_attribution`
/ `compute_risk_attribution` pipeline `POST /api/analysis` calls
(`app/api/routes.py`). Output matched decision
`0019-phase10k-interpretation-content.md`'s own live-verified "Example A"
almost exactly (small drift expected — different day's trailing window),
which cross-confirms both runs. Values used throughout this spec:

```
CAPM:  beta = 1.00 (0.9996), 95% CI [0.88, 1.12], t = 16.85, p < 0.001,
       R² = 50.3%, alpha (annualized) = −1.6%
FF-3:  mkt_rf = 0.88 (CI [0.72, 1.03], p < 0.001)
       smb    = −0.13 (CI [−0.32, 0.07], p = 0.199 — not significant)
       hml    = −0.39 (CI [−0.58, −0.21], p < 0.001 — significant, growth tilt)
       R² = 55.7% (adjusted 55.1%, per decision 0019 Example A)
Frontier: volatility 18.2%, realized return 17.6%, Sharpe 0.74
       frontier return at 18.2% vol = 20.1% → gap = +2.45 pp
       covariance condition number 3.65 (not regularized)
Return attribution (periodic, daily, exact identity):
       alpha       +2.95 bps/day
       mkt_rf      +5.82 bps/day
       smb         −0.34 bps/day
       hml         −3.06 bps/day
       total       +5.38 bps/day  (= realized mean daily excess return, exactly)
Risk attribution: factor-explained 55.7%, idiosyncratic 44.3%
```

These replace every invented illustrative number currently in
`learning.ts` (e.g. the hypothetical "beta of 1.20" / "beta of 0.60"
pair) — general *direction* statements (above/below 1.0, positive/negative
loading) stay as unqualified concepts since they're genuinely general
teaching points, but any *specific magnitude* used as a worked example is
now this portfolio's real, reproducible number.

### Compliance re-check (hard limit, unchanged from decisions 0009/0019)

Every rewritten sentence below was re-read against the same test decision
0019 already applies: *does it explain a pattern, or tell the reader what
to do with their money?* No sentence below contains "you should,"
"consider," "rebalance," "buy," "sell," or "hold" as an instruction. The
frontier card keeps the existing "not a suggestion to hold different
stocks, and not a signal to act on" disclaimer clause verbatim in its
pull-quote, matching established phrasing rather than inventing new
disclaimer language.

## 1. The five primitives, adapted from `information-architecture`'s
   structural method (site nav → per-card content hierarchy)

The `information-architecture` skill's template is built for site
structure (site map, nav model, content hierarchy per page, user flows,
naming conventions, component reuse map, growth plan, URL strategy). Per
rule 15, this is adapted one level down — from "which page" to "which
sentence becomes which primitive, in what order, inside one accordion
panel" — mapping each of that template's sections onto Learning's actual
unit of structure:

| IA template section | Adapted meaning here |
|---|---|
| Site Map | **Card map** — the four lesson IDs and their fixed order (§2) |
| Navigation Model | **Primitive model** — the five content primitives and which component renders each (§3) |
| Content Hierarchy | **Per-card decomposition** — the actual spec, sentence by sentence (§4) |
| User Flows | **Reading flow** — the fixed order primitives appear in within one panel (§5) |
| Naming Conventions | **Terminology consistency** — one word per concept, used identically across all four cards (§6) |
| Component Reuse Map | Which components are reused vs. net-new (§3) |
| Content Growth Plan | How a future fifth+ lesson card follows this same pattern (§7) |
| URL Strategy | N/A — no routing change; omitted |

## 2. Card map (unchanged from Phase 10l/10m — confirmed, not modified)

Fixed order, `beta` → `fama_french` → `frontier` → `attribution`, matching
the Results page's own section order (factor exposure → frontier →
attribution). This decision does not touch card order, IDs, tags, titles,
teasers, xrefs, or diagram assignment — only the `plain`/`technical`/`note`
content fields.

## 3. Primitive model — which component renders each primitive

| Primitive | Mechanism | Reuses | Net-new component |
|---|---|---|---|
| Lead sentence | Plain paragraph, same as today (`<p>` first line), just isolated as its own short line rather than opening a longer paragraph | Existing `<p>` styling | — |
| Bullets | Real `<ul>/<li>` list | New — Learning currently has zero list markup anywhere | `LessonList` (thin wrapper matching the card's type scale/spacing; no new dependency) |
| Callout/aside | **Split by criticality — see call below** | `InterpretationSection`'s flag-box visual language (`bg-{tone}/10 border-{tone}/40 rounded-md p-2.5` + icon) for always-visible asides; existing `FootnoteMarker`/`Popover` for genuine citations | `LessonCallout` (always-visible variant) |
| Pull-quote / stat highlight | Visually pulled-out block, bordered, larger type | `InterpretationSection`'s headline treatment (`border-primary bg-card rounded-lg border border-l-4 p-5`, `font-display`) | `LessonPullQuote` |
| Worked example | Labeled block with real numbers, monospace for the figures (matches `StatTile`'s numeral treatment) | `StatTile`/mono numeral convention | `LessonExample` |

### The call on `FootnoteMarker` vs. an always-visible callout

**`FootnoteMarker` (Popover, click-to-reveal) is the wrong mechanism for
either of the two asides it currently carries** (`frontier`'s "long-only"
note, `attribution`'s annualization-convention note) **and should be
replaced with an always-visible `LessonCallout` for both.** Reasoning:

- Decision 0020 §2d modeled `FootnoteMarker` on Chase's regulated-finance
  citation convention — a numbered marker that opens *legal/regulatory
  disclosure text*, content a reader doesn't need in order to correctly
  understand the claim next to it (that's the whole point of disclosure
  footnotes — they're compliance text, not comprehension text). Both of
  Learning's current notes are a different kind of content: they're
  **scope-defining caveats that change what the main claim actually
  means** — "best-achievable return for every level of risk" silently
  means "long-only, no leverage, no shorting," and "your average return
  splits exactly into these pieces" silently means "in per-period terms,
  not annualized." A reader who never clicks the marker walks away with a
  *wrong* mental model of the claim, not just a less-complete one — that's
  a materially different failure mode than skipping a citation.
- This project already has a working, in-house precedent for exactly this
  distinction: `InterpretationSection.tsx`'s `flags` array
  (`covariance_regularized`, `short_data_window`, decision 0019 §5) is
  content of the identical *kind* — a caveat that changes how to read the
  numbers next to it — and it already renders as an always-visible colored
  box with an icon, never gated behind a click. Matching that existing
  pattern is more internally consistent than continuing to gate
  comprehension-critical caveats behind Chase's citation mechanism.
- `FootnoteMarker` isn't being removed from the app — it's the right
  mechanism for genuine optional-depth citations, and this spec adds two
  new legitimate uses for it: a pointer from `beta`'s technical block to
  decision 0003 (methodology rationale) and from `frontier`'s technical
  block to decision 0003 again (long-only vs. unconstrained frontier,
  where to get the textbook version) — both "go read more if curious,"
  neither required to understand the sentence it's attached to.

Net effect: `LessonCallout` (always-visible) is the new default for any
caveat/definition that's load-bearing for correctly reading the main
claim; `FootnoteMarker` (click-to-reveal) stays reserved for true
optional-depth references to source/decision docs.

## 4. Per-card decomposition — exact text

Reading order within one accordion panel, applied identically to all four
cards (rationale in §5): **Lead → Bullets → Callout → Pull-quote →
(repeat Lead/Bullets/Callout/Pull-quote for the Technical register) →
Worked example (shared, once per card) → existing diagram → xrefs.**

---

### 4a. `beta` — CAPM beta

**Plain language**

- **Lead:** "Beta answers one question: when the market moves 1%, how much does your portfolio tend to move?"
- **Bullets:**
  - "A beta above 1.0 means the portfolio has historically swung harder than the benchmark in both directions — bigger gains when the market's up, bigger losses when it's down."
  - "A beta below 1.0 means the opposite — the portfolio has historically been calmer than the market."
- **Callout** (`LessonCallout`, tone: definition): "Beta alone doesn't say whether that's good or bad. It only describes how much of the portfolio's risk is simply 'the market, amplified or dampened' — not whether that exposure is well-compensated."
- **Pull-quote:** "Beta measures amplification of market moves — not whether that's a good bet."

**Technical**

- **Lead:** "β is the slope coefficient from regressing the portfolio's excess return on the benchmark's excess return — a point estimate with real sampling uncertainty, not a fixed fact."
- **Bullets:**
  - "β (beta) — the slope: how much the portfolio's excess return has moved per 1-unit move in the benchmark's excess return."
  - "α (alpha) — the regression intercept: the average excess return not explained by market exposure at all."
  - "R² — the share of the portfolio's return variance the single market factor explains on its own."
- **Callout** (`LessonCallout`, tone: caveat): "Two portfolios can share the exact same beta estimate and mean very different things: a beta of 1.20 with a 95% CI of [0.4, 2.0] is a far weaker claim than the same 1.20 with a CI of [1.1, 1.3] — width is precision, not the estimate itself."
- **Pull-quote:** "A low CAPM R² isn't a data problem — it's the finding: a one-factor market story is incomplete for this portfolio."
- **FootnoteMarker** (new use, attached to the lead sentence): "See the exact regression specification and standard-error convention in decision 0003."

**Worked example** (shared, real data — see full derivation in §"How the worked-example numbers were obtained"): "The app's own sample portfolio — AAPL 40% / MSFT 30% / GOOGL 20% / AMZN 10% vs. the S&P 500, trailing 12 months, daily — measures beta 1.00, 95% CI [0.88, 1.12], t = 16.85, p < 0.001, R² = 50.3%. The point estimate says this portfolio moved almost exactly one-for-one with the market, and the CI is narrow enough (width 0.23) to trust that read, not just treat it as a rough guess."

---

### 4b. `fama_french` — Fama-French loadings

**Plain language**

- **Lead:** "CAPM only asks 'how much market.' Fama-French asks a follow-up: what kind of market exposure."
- **Bullets:**
  - "Size (SMB) — tilted toward small companies or large ones?"
  - "Value (HML) — cheap-relative-to-book ('value') stocks, or expensive-growth ones?"
  - "Profitability (RMW) — highly profitable companies, or not?"
  - "Investment (CMA) — conservatively-run companies, or aggressively-expanding ones?"
- **Callout** (`LessonCallout`, tone: definition): "Reading the sign: a positive Size (SMB) loading means the holdings behave more like small-cap stocks than large-cap; a positive Value (HML) loading means more like cheap value stocks than expensive growth — the same logic extends to Profitability (RMW) and Investment (CMA)."
- **Pull-quote:** "None of this is prescriptive — it's a description of the exposures already present, in the same language professional factor investors use to describe theirs."

**Technical**

- **Lead:** "Each βᵢ is a partial-regression coefficient — the portfolio's sensitivity to one factor's spread-portfolio return, holding the other factors fixed."
- **Bullets:**
  - "Significance test: a loading only counts as a real exposure — not noise — when its 95% CI excludes zero (equivalently, p < 0.05)."
  - "Where to check it: the Results chart plots that CI as a whisker under every bar; the table view gives the exact standard error, t-stat, and p-value per factor."
  - "Fit comparison: Fama-French R², adjusted R², and the overall F-statistic together say how much better this multi-factor story fits than CAPM's single factor did."
- **Callout** (`LessonCallout`, tone: definition): "'95% CI excludes zero' and 'p < 0.05' are the same significance test stated two different ways — this app always shows the CI directly, not just the p-value, so the range is visible, not just a pass/fail."
- **Pull-quote:** "A materially higher Fama-French R² than CAPM R² means style tilts — size, value, profitability, investment — not just raw market exposure, are doing real explanatory work for this portfolio."

**Worked example** (shared, real data): "Sample portfolio: CAPM R² = 50.3%; Fama-French (3-factor) R² = 55.7% (adjusted 55.1%). Loadings: mkt_rf 0.88 (CI [0.72, 1.03], significant), smb −0.13 (CI [−0.32, 0.07], not significant — the interval straddles zero), hml −0.39 (CI [−0.58, −0.21], significant — a statistically real growth tilt, since a negative HML loading means behaving more like expensive-growth stocks than cheap-value ones). Only one of the two non-market factors clears the 95% bar here — growth-vs-value positioning is this portfolio's one statistically reliable style signal beyond plain market exposure."

---

### 4c. `frontier` — Frontier position

**Plain language**

- **Lead:** "Given exactly the holdings entered — nothing added, nothing swapped — there's a best-achievable return for every level of risk, just by re-weighting those same holdings."
- **Bullets:**
  - "Long-only — every holding stays at zero or positive weight; nothing is shorted."
  - "No leverage — weights sum to exactly the money entered, not more."
  - "Same names only — the frontier never swaps in a holding outside what was entered."
- **Callout** (`LessonCallout`, tone: caveat — **replaces the current `note`/`%%FN%%` footnote**, per §3's call): "Why 'long-only' matters: this is a narrower, more realistic object than the textbook unconstrained frontier — it's strictly the best return achievable by re-weighting exactly the holdings already picked, not by adding leverage or shorting anything."
- **Pull-quote:** "A mirror, not an instruction: if the as-entered dot sits below the line, a different weighting of these same names could historically have earned more for that same risk — not a suggestion to hold different stocks, and not a signal to act on."

**Technical**

- **Lead:** "The frontier solves, for each target return, the minimum-variance weighting: `min_w wᵀΣw` subject to `wᵀμ = target`, `Σwᵢ = 1`, `wᵢ ≥ 0` — long-only by default."
- **Bullets:**
  - "Global minimum-variance portfolio — the lowest possible volatility on this frontier, regardless of return."
  - "Max-Sharpe / tangency portfolio — the point maximizing return per unit of risk, `S = (Rₚ − R_f) / σₚ`."
- **Callout** (`LessonCallout`, tone: caveat): "A flagged 'covariance regularized' warning means the holding set's correlation structure was numerically unstable (few holdings, few observations, near-duplicate positions) — read the frontier as directional, not exact, when this fires."
- **Pull-quote:** "'Return gap at matched volatility' is the single cleanest number for how far below the achievable set the as-entered weights currently sit."
- **FootnoteMarker** (new use, attached to the lead sentence): "Retail and small-RIA holdings are actually held long, so long-only is this app's default — see decision 0003 for the rationale and how to get the unconstrained textbook frontier instead."

**Worked example** (shared, real data): "Sample portfolio: 18.2% annualized volatility, 17.6% realized annualized return, Sharpe 0.74. The modeled frontier's return at that same 18.2% volatility is 20.1% — a 2.45-percentage-point gap. Covariance condition number 3.65, well below the regularization trigger, so this read is exact, not regularized. Historically, some other long-only re-weighting of the same four holdings could have earned about 2.5 points more return for the same risk — not a suggestion to reweight, just a description of the historical relationship among those four holdings."

---

### 4d. `attribution` — Return & risk attribution

**Plain language**

- **Lead:** "The three views above are exposures; this one is accounting."
- **Bullets:**
  - "Return split: average per-period return divides exactly into market exposure, plus style tilts (size, value, profitability, investment), plus alpha (unexplained)."
  - "Risk split: return variance divides into factor-explained (market and style tilts together) versus idiosyncratic (specific to the individual names held, not shared with the market or the style tilts)."
- **Callout** (`LessonCallout`, tone: definition): "Alpha isn't automatically 'skill.' It's simply whatever the return split can't attribute to market or style-factor exposure — that could be real stock-picking, or it could just be noise in this particular sample window."
- **Pull-quote:** "Mostly idiosyncratic risk is a bet on specific companies. Mostly factor risk is, whether intended or not, mostly a bet on the market and a couple of style tilts."

**Technical**

- **Lead:** "Return attribution is an exact algebraic identity, not an approximation."
- **Pull-quote** (formula, treated as the card's single most important claim): `mean(Rₚ − R_f) = α + Σᵢ βᵢ · mean(factorᵢ)`
- **Bullets:**
  - "The Fama-French OLS fit includes an intercept, so the fitted residual has zero mean over the regression sample — that's what makes this an identity, not an approximation."
  - "Risk attribution needs no extra computation: it's just R² (factor-explained share) and 1 − R² (idiosyncratic share), already produced by the same regression."
- **Callout** (`LessonCallout`, tone: caveat — **replaces the current `note`/`%%FN%%` footnote**, per §3's call): "Contributions are shown per-period, not re-annualized — CAPM/Fama-French alpha and the frontier's inputs use two deliberately different annualization conventions (compounding vs. linear scaling, see decision 0003), so summing already-annualized pieces from different conventions would silently break the identity above."
- **FootnoteMarker** (retained — genuine source-code citation, not a comprehension-critical caveat): "Full derivation: see the module docstring in `app/api/attribution.py`."

**Worked example** (shared, real data): "Sample portfolio, daily: alpha contributes +2.95 bps/day, market (Mkt-RF) +5.82 bps/day, Size (SMB) −0.34 bps/day, Value (HML) −3.06 bps/day — summing to +5.38 bps/day, matching the portfolio's realized mean daily excess return exactly, as the identity guarantees. Risk side: 55.7% of this portfolio's return variance is explained by the three factors together; the remaining 44.3% is idiosyncratic — specific to holding exactly AAPL/MSFT/GOOGL/AMZN rather than the market or style tilts they share."

## 5. Reading flow (adapted "User Flows")

Fixed order inside every open accordion panel, both registers:

```
1. Lead sentence            -- orients: what question is this card answering
2. Bullets                  -- the enumerable detail (was buried in commas)
3. Callout/aside            -- the caveat/definition, visually set apart,
                                doesn't interrupt the lead->bullets line
4. Pull-quote                -- the one claim/number worth remembering even
                                by someone only scanning
   [repeat 1-4 for the Technical register]
5. Worked example (shared)  -- concrete, real numbers grounding both
                                registers at once
6. Existing diagram          -- unchanged, still renders after both registers
7. Existing xrefs             -- unchanged
```

Worked example is deliberately **shared once per card**, not duplicated
per register — the same real numbers ground both the plain and technical
claims, and duplicating them would reintroduce the "wall of repeated
content" problem this spec exists to fix.

## 6. Terminology consistency (adapted "Naming Conventions")

| Concept | Term used everywhere in this spec | Notes |
|---|---|---|
| Positive HML | "value tilt" | Never "cheap tilt" or other synonym |
| Negative HML | "growth tilt" | Matches `FACTOR_TILT_LABELS` in `app/api/interpretation.py` exactly (decision 0019 §2) — Learning's prose and the server-computed Interpretation section now use identical vocabulary |
| Positive SMB | "small-cap [lean/signal]" | Matches `FACTOR_TILT_LABELS` |
| The unexplained residual | "alpha (unexplained)" | Never "skill" or "outperformance" standalone — always paired with the noise/sample caveat per the hard limit |
| Statistical significance | "statistically real" / "clears the 95% bar" / "CI excludes zero" | Same three interchangeable phrasings decision 0019 already established; no new synonym introduced |

## 7. Content growth plan (adapted)

A future fifth Learning card (e.g. if a new model — Carhart 4-factor, a
different optimization objective — is added) should ship with content
already authored in this five-primitive shape from the start, not as a
plain/technical paragraph pair to be decomposed retroactively. `educator`
plans that decomposition the same way this document does, before
`developer` builds it — this is now the standing process, not a one-time
cleanup.

## 8. Data-model implications (spec only — `developer` implements)

`LearningCard`'s `plain: string` / `technical: string` / `note: string |
null` fields no longer hold the full content; they should become
structured objects. Suggested shape (not binding on `developer`'s exact
TypeScript, but the content this decision hands off maps directly onto
it):

```ts
interface LearningRegister {
  lead: string
  bullets: string[]
  callout: { tone: "definition" | "caveat"; text: string } | null
  pullQuote: string  // may contain inline HTML for a formula, per the attribution technical card
  footnote?: string  // only when a genuine citation exists (beta, frontier technical)
}

interface LearningCard {
  id: string
  tag: string
  title: string
  teaser: string
  plain: LearningRegister
  technical: LearningRegister
  workedExample: string  // shared, rendered once per card
  xrefs: { to: string; label: string }[]
  diagram: "capm" | "ci" | "frontier" | null
}
```

This replaces the `%%FN%%`-splice pattern (`TextWithFootnote` in
`Learning.tsx`) for the two notes that graduate to `LessonCallout`
(frontier, attribution) — `FootnoteMarker` stays wired, just attached to
`footnote` on the two registers that keep a genuine citation (beta,
frontier technical) instead of a scope-defining caveat.

## Consequences

- `developer` builds four net-new presentational components
  (`LessonList`, `LessonCallout`, `LessonPullQuote`, `LessonExample`) per
  §3's visual-language mapping, and restructures
  `frontend/src/data/learning.ts` to the shape in §8, using the exact text
  in §4 close to verbatim (not re-improvised).
- `Learning.tsx`'s `TextWithFootnote` helper is retired for the frontier
  and attribution cards (their notes are no longer footnotes) but the
  underlying `Popover`-based `FootnoteMarker` component itself is
  unchanged and gets two new, genuine call sites (§4a, §4c).
- No change to card order, IDs, tags, titles, teasers, xrefs, diagrams, or
  the progress-bar/accordion mechanics Phase 10m already built — this is
  strictly a content-and-primitive-mapping change inside each panel.
- No change to any backend file, endpoint, or computed value — all worked
  examples read from already-existing, already-verified output; nothing
  here required a new field or a new computation.
- `qa-tester` should re-run the existing advice-language guardrail check
  (decision 0019 §7's "no 'you should'/'buy'/'sell'/'hold'/'rebalance'/
  'consider'" substring check) against the new `learning.ts` content
  specifically, since this decision rewrote every sentence in the file.

## Open questions for `pm`/Ethan (rule 15 ambiguities encountered)

1. **Rule 15 doesn't say whether a worked example belongs once per card or
   once per register.** This spec chose "once per card, shared" to avoid
   re-introducing repeated content — flagging in case the intent was
   register-specific examples (e.g., a technical-only worked example with
   more decimal precision).
2. **Rule 15 doesn't address whether the Plain/Technical dual-register
   split itself is in scope to change.** This spec preserved it as the
   outer structure (each register gets its own lead/bullets/callout/
   pull-quote) because dual-register explanation is `educator`'s own core
   mandate, not something rule 15 appeared to be asking to remove — but
   that's an inference, not something rule 15 states directly. Worth
   confirming this reading is correct before it's assumed for every future
   card.
3. **The FootnoteMarker-vs-always-visible-callout line (§3) wasn't
   specified by rule 15** — rule 15 says callouts must be "visually
   distinct from body text, not another paragraph" but doesn't say whether
   click-gating still counts as "visually distinct." This decision drew
   the line at *comprehension-critical vs. optional-depth*, using
   `InterpretationSection`'s existing flags as the precedent for the
   comprehension-critical case. Reasonable, but it's a real judgment call
   this project hadn't made explicitly before.
