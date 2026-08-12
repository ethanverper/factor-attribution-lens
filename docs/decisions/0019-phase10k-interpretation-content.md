# 0019. Phase 10k: Interpretation & Key Takeaways — content spec

Date: 2026-08-11
Status: accepted (content spec; implementation is Phase 10m, `developer`)

## Context

`docs/project-standards.md` rule 9a (added after the fifth round of feedback)
requires every project to carry a dedicated, visually prominent
"Interpretation & Key Takeaways" section that synthesizes what a result
*means*, not a restatement of numbers already on the page — and, for this
project specifically, to do so without ever crossing into personalized
investment/trading advice (this role's standing hard limit, which this spec
is written to satisfy exactly, not just gesture at).

This document is the content spec for that section: real conditional logic,
grounded in the actual fields `analyze_portfolio()` already produces
(`app/models/schemas.py::PortfolioAnalysis` — `CAPMResult`, `FactorModelResult`,
`EfficientFrontierResult`), not generic commentary. It's written as an
implementable rule set (thresholds, branches, exact response shape) plus
worked examples computed against **live data** (not invented numbers) for
three real portfolios, so `developer` (Phase 10m) can verify the rules
produce the example text below before wiring it into the UI.

### Why this lives server-side, in a new module, not in the React frontend

Every field this logic needs (`CAPMResult`, `FactorModelResult`,
`EfficientFrontierResult`) is already present in `AnalysisResponse`
(`app/api/schemas.py`), so it *could* be computed client-side in TypeScript.
It should not be, for the same reason `app/api/attribution.py` already
lives server-side: this project's established pattern is "business/analytical
logic in Python, tested by `pytest`; presentation in React." Putting
threshold logic in TypeScript would create a second, untested copy of
judgment calls (what counts as a "wide" CI, a "material" loading) that
`qa-tester` can't verify against reference values the same way it verified
CAPM/Fama-French/Markowitz math in Phase 10. Recommendation: a new
`app/api/interpretation.py`, mirroring `attribution.py`'s shape exactly —
a pure function of `PortfolioAnalysis` in, a Pydantic response model out,
added to `AnalysisResponse` as a fourth field alongside `analysis`,
`return_attribution`, `risk_attribution`. It does **not** modify
`app/models/schemas.py` — Phase 2's stable contract stays untouched, exactly
as `attribution.py`'s own docstring establishes as the pattern.

## The hard limit, and how this spec satisfies it

Every sentence in every template below was written, then re-read against one
test: *does it explain a pattern/implication, or does it tell the reader
what to do with their money?* Only the former is permitted — no "you
should," no "consider," no "rebalance into/out of," no "buy/sell," no
"this suggests [action]." Where a finding could tempt that framing (e.g. the
frontier-gap templates), the sentence is deliberately built around the
*pattern* ("historically, some combination of these same holdings could have
delivered more return for the same risk") with the same explicit
disclaimer clause the app already uses elsewhere (`frontend/src/data/learning.ts`
line 48: "not a suggestion to hold different stocks, and not a signal to
act on") rather than a softened recommendation. Compliance is re-checked
explicitly per example at the bottom of this document, and `developer`
should keep the existing page-level disclaimer banner (`Results.tsx` lines
143–145) directly adjacent to this section, not rely on this section's own
copy alone to carry that framing.

## 1. Response shape

```python
# app/api/schemas.py — additions

class InterpretationTakeaway(BaseModel):
    id: Literal["beta", "style_tilt", "explanatory_power", "frontier_position"]
    title: str
    body: str            # 2-4 sentences, plain-register prose, numbers inline
    is_headline: bool     # True for exactly one of the four

class InterpretationFlag(BaseModel):
    id: Literal["covariance_regularized", "short_data_window"]
    severity: Literal["info", "warning"]
    message: str

class InterpretationResponse(BaseModel):
    headline: str                       # one sentence, the "so what"
    takeaways: list[InterpretationTakeaway]   # always exactly 4, fixed order below
    flags: list[InterpretationFlag]     # 0-2, only the ones that actually triggered

class AnalysisResponse(BaseModel):
    meta: RequestMeta
    analysis: PortfolioAnalysis
    return_attribution: ReturnAttributionResponse
    risk_attribution: RiskAttributionResponse
    interpretation: InterpretationResponse   # new field
```

`takeaways` is always exactly four items, always in this order —
`beta`, `style_tilt`, `explanatory_power`, `frontier_position` — matching the
task's own four required dimensions and the existing Results page's own
section order (factor exposure → frontier → attribution). Nothing is ever
dropped; the headline is a *pointer* to whichever one is most worth reading
first, not a replacement for the other three. `frontend/src/lib/types.ts`
gets the mirrored interfaces (same pattern as every other response type
there).

## 2. Thresholds (every one a stated judgment call)

```python
# app/api/interpretation.py

R2_VERY_LOW = 0.15                 # CAPM/FF R^2 below this: "barely tracks the market"
R2_MATERIAL_LIFT = 0.03            # FF R^2 - CAPM R^2 >= this: style factors add real explanatory power
BETA_CI_WIDTH_TIGHT = 0.30         # absolute width of the beta 95% CI, in beta units
BETA_CI_WIDTH_WIDE = 0.60          # >= this: "wide", precision caveat
STYLE_LOADING_MATERIAL = 0.30      # |loading|, only evaluated on already-significant loadings,
                                    # used for headline selection (keeps a technically-significant
                                    # but tiny loading from hijacking the "so what")
FRONTIER_GAP_NEGLIGIBLE = 0.02     # annualized return gap, e.g. 0.02 = 2 percentage points
FRONTIER_GAP_LARGE = 0.08          # >= this: "large" gap
SHORT_WINDOW_OBS = {"daily": 60, "monthly": 24}   # below this: flag, above the hard MIN_OBS floor
                                                    # in capm.py/fama_french.py which already blocks
                                                    # regressions below a statistically defensible minimum —
                                                    # this is a second, more conservative bar for "ample," not
                                                    # "technically valid"
COV_REG_THIN_DATA_RATIO = 20       # n_obs / n_symbols below this: blame thin data for regularization,
                                    # not correlation structure (no pairwise-correlation stat exists in
                                    # the schema today to check directly — see Limitations)

FACTOR_TILT_LABELS = {
    # factor: (label if loading positive, label if loading negative)
    "smb": ("small-cap", "large-cap"),
    "hml": ("value", "growth"),
    "rmw": ("high-profitability / quality", "low-profitability"),
    "cma": ("conservative-investment", "aggressive-investment"),
}
```

**Significance** (used everywhere below) is always "the coefficient's 95% CI
excludes zero" (`ci_lower_95 > 0 or ci_upper_95 < 0`) — identical to what the
existing `significanceNote()` helper (`frontend/src/lib/format.ts`) already
uses, just computed server-side here so the narrative text and the chart
whiskers can never disagree.

## 3. The four takeaways — conditional logic

### 3a. `beta` — CAPM beta precision & market exposure

Inputs: `capm.beta` (estimate, ci_lower_95, ci_upper_95, t_stat, p_value),
`capm.benchmark`, `capm.n_obs`, `capm.frequency`.

```
width = ci_upper_95 - ci_lower_95
significant_vs_zero = ci_lower_95 > 0 or ci_upper_95 < 0
distinguishable_from_market = not (ci_lower_95 <= 1.0 <= ci_upper_95)
precision = "tight" if width < BETA_CI_WIDTH_TIGHT
            else "wide" if width >= BETA_CI_WIDTH_WIDE
            else "moderate"
```

- If **not** `significant_vs_zero`: body is *only* —
  "The 95% confidence interval for beta ([{lo:.2f}, {hi:.2f}]) includes
  zero — at this window's sample size ({n_obs} {frequency} observations),
  the data cannot rule out that this portfolio has no reliable linear
  relationship with {benchmark} at all. Read the point estimate
  ({estimate:.2f}) as suggestive, not established."
  (Distinguishable-from-market clause is skipped here — refining "is it
  different from 1?" is not useful once "is it different from 0?" already
  failed.)
- If `significant_vs_zero`, three clauses concatenated:
  1. "Beta is statistically distinguishable from zero (t={t_stat:.2f},
     p={p_fmt}) — there is real, measurable co-movement with {benchmark}."
  2. Precision clause, by bucket:
     - tight: "The interval is narrow (width {width:.2f}), so
       {estimate:.2f} is a reasonably precise read of this portfolio's
       market sensitivity over this window."
     - moderate: "The interval (width {width:.2f}) is moderate — treat
       {estimate:.2f} as a reasonable central estimate, but true market
       sensitivity could plausibly sit noticeably higher or lower."
     - wide: "The interval is wide (width {width:.2f}) relative to the
       point estimate — {estimate:.2f} is this window's best estimate, but
       the data doesn't pin down market sensitivity tightly; a longer
       window would narrow this."
  3. Vs.-market clause: if `distinguishable_from_market`: "It's also
     statistically distinguishable from beta = 1 — this portfolio's
     market sensitivity is genuinely different from simply holding
     {benchmark} itself, not just noisier." else: "The interval also
     includes 1.0, so beta isn't statistically distinguishable from
     moving in lockstep with {benchmark} either."

### 3b. `style_tilt` — Fama-French factor loading pattern

Inputs: `factor_model.factor_loadings` (mkt_rf + smb/hml[/rmw/cma]),
`capm.beta.estimate`.

```
non_market = [l for l in factor_loadings if l.name != "mkt_rf"]
significant = [l for l in non_market if ci excludes 0]
```

- If `significant` is empty: "None of the non-market factors
  ({', '.join(display names)}) are statistically distinguishable from zero
  at the 95% level. This portfolio's behavior is explained by broad market
  exposure, not a detectable size/value{/profitability/investment} tilt —
  whatever style characteristics these holdings have individually, they
  don't show up as a statistically reliable factor exposure over this
  window."
- Else, one clause per significant factor (loop in the fixed factor order
  smb, hml, rmw, cma): "{Display name} loading is {estimate:.2f} (95% CI
  [{lo:.2f}, {hi:.2f}]), excluding zero — a statistically real {tilt word}
  tilt." — where `tilt word` comes from `FACTOR_TILT_LABELS[name][0 if
  estimate > 0 else 1]`. Non-significant non-market factors get one shorter
  clause each: "{Display name} ({estimate:.2f}, 95% CI [{lo:.2f},
  {hi:.2f}]) {"falls just short of the 95% bar (p={p:.3f}) — a possible
  {tilt word} lean, not confirmed" if 0.05 <= p < 0.10 else "is not
  statistically distinguishable from zero — no reliable {tilt word
  root} signal detected"}."
  Then a closing synthesis clause: if exactly one factor is significant:
  "With only {significant count}/{non_market count} non-market factor(s)
  clearing the 95% bar, {tilt phrase} is this portfolio's one statistically
  reliable style signal beyond overall market exposure." If more than one:
  list them together in one closing sentence instead of "one signal."
- Divergence note (append only if triggered): if
  `abs(mkt_rf.estimate - capm.beta.estimate) > 0.10`: "Note: the market
  loading estimated jointly with the other factors ({mkt_rf.estimate:.2f})
  differs from the plain CAPM beta ({capm.beta.estimate:.2f}) — expected
  when, as here, one of the other factors' returns correlates with the
  market's own over this window."

### 3c. `explanatory_power` — R² / how much is "the market"

Inputs: `capm.r_squared`, `factor_model.r_squared`,
`factor_model.adj_r_squared`, `factor_model.f_statistic`,
`factor_model.f_p_value`, `factor_model.factor_model` ("3" or "5").

```
def bucket(r2):
    if r2 < 0.15: return "very low"
    if r2 < 0.30: return "low"
    if r2 < 0.60: return "moderate"
    if r2 < 0.85: return "high"
    return "very high"

incremental = factor_model.r_squared - capm.r_squared
```

Three clauses:

1. "The single-factor CAPM model explains {capm.r_squared:.1%} of this
   portfolio's return variance ({bucket(capm.r_squared)} for an equity
   portfolio) — the remaining {1-capm.r_squared:.1%} is idiosyncratic
   (stock-specific) movement the market factor alone doesn't capture."
2. Incremental clause: if `incremental >= R2_MATERIAL_LIFT`: "Adding
   size/value{, profitability, investment} lifts explained variance to
   {factor_model.r_squared:.1%} (adjusted {adj_r_squared:.1%}) —
   {"a modest absolute lift, but proportionally large: " if
   capm.r_squared < R2_VERY_LOW else ""}a real, {incremental:.1%}-point
   improvement attributable to those style factors, not the market alone."
   else: "Adding size/value{, profitability, investment} only lifts
   explained variance to {factor_model.r_squared:.1%} — a marginal
   {incremental:.1%}-point improvement; most of what these factors could
   explain, the market factor alone already captured."
3. F-test clause: if `f_p_value < 0.05`: "The joint F-test (F=
   {f_statistic:.1f}, p={p_fmt}) confirms the factor model as a whole
   explains statistically real variance{", even where R² itself is low —
   a genuine but small relationship, not noise" if factor_model.r_squared
   < R2_VERY_LOW else ""}." else: "The joint F-test does not clear the
   conventional 5% bar (p={p_fmt}) — treat the whole factor-model fit,
   not just the individual loadings above, cautiously here."

### 3d. `frontier_position` — where the portfolio sits vs. the modeled frontier

Inputs: `efficient_frontier.current_portfolio` (`is_on_frontier`,
`return_gap_to_frontier`, `frontier_return_at_same_volatility`,
`expected_return_annualized`, `volatility_annualized`), `efficient_frontier`
(`symbols`, `n_obs`, `covariance_regularized`), plus the same
`frontierIsDegenerate` check `Results.tsx` already computes client-side
(recommend moving that single boolean into `EfficientFrontierResult` or this
response so it's computed once, not twice — see Limitations).

```
gap = current_portfolio.return_gap_to_frontier   # None or a float
n = len(symbols)
```

- Degenerate (n < 2, or frontier vol range ~0): "With {"only one holding"
  if n < 2 else "holdings whose historical return/risk profiles are
  effectively identical"}, there's no meaningful spread of alternative
  portfolios to compare against — a frontier comparison isn't informative
  here."
- `gap is None` (portfolio's volatility falls outside the frontier's
  computed range): "This portfolio's volatility ({vol:.1%}) falls outside
  the range the modeled frontier covers for this holding set
  ({n_obs} observations, {n} holdings), so a same-volatility return
  comparison isn't available."
- `is_on_frontier` or `gap <= 0`: "This portfolio's specific weighting is
  numerically on the modeled frontier for its return level — among all
  long-only re-weightings of exactly these {n} holdings, none would have
  delivered more return at this same risk level, historically."
- `0 < gap < FRONTIER_GAP_NEGLIGIBLE`: "The gap to the frontier is small
  ({gap:.1%}) — small enough to be within the range explainable by
  estimation noise over a {n_obs}-observation window, not a structurally
  meaningful mismatch between these weights and this holding set's own
  risk/return relationships."
- `FRONTIER_GAP_NEGLIGIBLE <= gap < FRONTIER_GAP_LARGE`: "At this
  portfolio's volatility ({vol:.1%}), the modeled frontier's return is
  {frontier_return_at_same_volatility:.1%} versus this portfolio's realized
  {expected_return_annualized:.1%} — a {gap:.1%}-point gap. That's
  moderate: some of the historical return/risk relationship among just
  these {n} holdings wasn't captured by this specific weighting, without
  being a dramatic mismatch."
- `gap >= FRONTIER_GAP_LARGE`: "...a {gap:.1%}-point gap — large by this
  analysis's own standard. Historically, some combination of these same
  {n} holdings, long-only, could have delivered meaningfully more return
  for the same volatility (or the same return for meaningfully less
  volatility) than the as-entered weights — not a suggestion to reweight,
  and not a signal to act on, just a description of the historical
  relationship among the holdings you entered."

## 4. Headline selection (the "so what," picked dynamically)

First matching rule wins, in this order:

```
1. if capm.r_squared < R2_VERY_LOW:
     headline_id = "explanatory_power"
2. elif significant_vs_zero(beta) and distinguishable_from_market(beta):
     headline_id = "beta"
3. elif any significant non-market loading has |estimate| >= STYLE_LOADING_MATERIAL:
     headline_id = "style_tilt"   # use the largest such loading by |estimate|
4. elif gap is not None and gap >= FRONTIER_GAP_LARGE:
     headline_id = "frontier_position"
5. else:
     headline_id = "explanatory_power"   # default: "nothing stands out" is itself the finding
```

Headline text per branch (one sentence, always ends on the pattern, never
an instruction):

1. "Despite being built from individual equities, this portfolio's returns
   are only weakly explained by {benchmark} — R² of {r2:.1%} means the
   benchmark's own moves account for only about {r2:.0%} of this
   portfolio's return variance; the rest comes from something other than
   broad market direction."
2. "This portfolio's market sensitivity (beta {estimate:.2f}, 95% CI
   [{lo:.2f}, {hi:.2f}]) is statistically distinguishable from both zero
   and from 1.0 — it moves {"more" if estimate > 1 else "less"} than
   one-for-one with {benchmark}, and that's a measured relationship, not
   just noise around beta = 1."
3. "This portfolio carries a statistically significant {tilt word} tilt
   ({display name} loading {estimate:.2f}, 95% CI [{lo:.2f}, {hi:.2f}]) —
   a real, measurable style exposure beyond plain market direction."
4. "At the volatility this portfolio is already carrying, the modeled
   frontier's historical return was {gap:.1%} points higher — a gap this
   size (this analysis's own bar for 'large' is {FRONTIER_GAP_LARGE:.0%})
   means the specific combination of correlations and weights here left
   real room on the table within just these holdings' own historical
   risk/return relationship."
5. "Nothing here is statistically extreme: beta sits within range of
   {benchmark}-average risk (or isn't reliably estimated as different), no
   individual style factor clears both significance and a material
   magnitude, and this portfolio's realized return/risk sits close to what
   its own holdings' history could support. That combination is itself the
   finding — a fairly plain, market-tracking allocation with no strong,
   statistically detectable secondary bet."

## 5. Flags (cross-cutting data-quality caveats, not tied to one card)

- `covariance_regularized` (severity `warning`), only if
  `efficient_frontier.covariance_regularized`:
  `ratio = n_obs / n_symbols`; `likely_cause = "the data window is short
  relative to the number of holdings" if ratio < COV_REG_THIN_DATA_RATIO
  else "these holdings move in an unusually tightly correlated way (e.g.
  near-duplicate exposures or single-sector concentration)"`. Message:
  "The covariance matrix for these {n_symbols} holdings needed
  regularization (condition number {cond:.1e}) before the frontier could
  be computed — likely because {likely_cause}. Read the frontier
  comparison above as indicative, not precise."
- `short_data_window` (severity `info`), only if
  `min(capm.n_obs, factor_model.n_obs, efficient_frontier.n_obs) <
  SHORT_WINDOW_OBS[frequency]`: "This analysis rests on {min_n}
  {frequency} observations — thinner than this analysis's own bar for an
  ample sample ({threshold}). All estimates above should be read as
  provisional; a longer window is what would narrow the confidence
  intervals."

Both flags echo the pattern already shipping today (the amber
"covariance_regularized" banner already inline in the frontier chart card,
`Results.tsx` lines 237–243) — `developer` should decide during Phase 10m
whether to keep both copies (inline near the chart *and* here) or make the
Interpretation section's flags list the single authoritative copy and
simplify the inline banner to a shorter pointer back to it. That's a UI
de-duplication call, not a content-logic one, and is left to Phase 10m's
judgment.

## 6. Worked examples — computed against live data, not invented

All three were run directly against `analyze_portfolio()` on 2026-08-11
against live yfinance/Kenneth French data (see the script used, not
committed — one-off verification, not a fixture). Numbers below are exact
outputs, not illustrative approximations.

### Example A — the existing sample portfolio: AAPL 40% / MSFT 30% / GOOGL 20% / AMZN 10%, benchmark ^GSPC, 3-factor, daily, n=222

Raw results: CAPM beta 1.000, 95% CI [0.883, 1.116], R²=0.503. FF: mkt_rf
0.876 (CI [0.718, 1.033], p<0.0001), smb −0.126 (CI [−0.319, 0.067],
p=0.199), hml −0.393 (CI [−0.581, −0.205], p<0.0001), FF R²=0.557. Frontier:
not regularized (condition number 3.65), gap to frontier at matched
volatility = +2.45 percentage points.

- **Headline** (priority 3: hml is the only significant non-market loading
  with |estimate| ≥ 0.30): *"This portfolio carries a statistically
  significant growth tilt (Value (HML) loading −0.39, 95% CI [−0.58,
  −0.21]) — a real, measurable style exposure beyond plain market
  direction."*
- **`beta`**: *"Beta is statistically distinguishable from zero (t=16.85,
  p<0.001) — there is real, measurable co-movement with ^GSPC. The
  interval is narrow (width 0.23), so 1.00 is a reasonably precise read of
  this portfolio's market sensitivity over this window. The interval also
  includes 1.0, so beta isn't statistically distinguishable from moving in
  lockstep with ^GSPC either."*
- **`style_tilt`**: *"Value (HML) loading is −0.39 (95% CI [−0.58, −0.21]),
  excluding zero — a statistically real growth tilt. Size (SMB) (−0.13,
  95% CI [−0.32, 0.07]) is not statistically distinguishable from zero —
  no reliable size signal detected. With only 1/2 non-market factors
  clearing the 95% bar, growth-vs-value positioning is this portfolio's
  one statistically reliable style signal beyond overall market exposure.
  Note: the market loading estimated jointly with the other factors (0.88)
  differs from the plain CAPM beta (1.00) — expected when, as here, one of
  the other factors' returns correlates with the market's own over this
  window."*
- **`explanatory_power`**: *"The single-factor CAPM model explains 50.3% of
  this portfolio's return variance (moderate for an equity portfolio) —
  the remaining 49.7% is idiosyncratic (stock-specific) movement the
  market factor alone doesn't capture. Adding size/value only lifts
  explained variance to 55.7% (adjusted 55.1%) — a marginal 5.4%-point
  improvement; most of what these factors could explain, the market factor
  alone already captured. The joint F-test (F=103.0, p<0.001) confirms the
  factor model as a whole explains statistically real variance."*
- **`frontier_position`**: *"At this portfolio's volatility (18.2%), the
  modeled frontier's return is 20.1% versus this portfolio's realized
  17.7% — a 2.5%-point gap. That's moderate: some of the historical
  return/risk relationship among just these 4 holdings wasn't captured by
  this specific weighting, without being a dramatic mismatch."*
- **Flags**: none (222 observations, no regularization).

### Example B — a different real portfolio: JNJ 25% / PG 25% / KO 25% / WMT 25% (defensive consumer staples), benchmark ^GSPC, 3-factor, daily, n=222

Raw results: CAPM beta −0.134, 95% CI [−0.325, 0.058], p=0.173, R²=0.015.
FF: mkt_rf −0.111 (p=0.331), smb 0.189 (CI [−0.022, 0.400], p=0.080), hml
0.237 (CI [0.042, 0.432], p=0.017), FF R²=0.067. Frontier: not regularized,
gap = +15.39 percentage points.

- **Headline** (priority 1: CAPM R²=0.015 < 0.15): *"Despite being built
  from individual equities, this portfolio's returns are only weakly
  explained by ^GSPC — R² of 1.5% means the benchmark's own moves account
  for only about 2% of this portfolio's return variance; the rest comes
  from something other than broad market direction."*
- **`beta`**: *"The 95% confidence interval for beta ([−0.33, 0.06])
  includes zero — at this window's sample size (222 daily observations),
  the data cannot rule out that this portfolio has no reliable linear
  relationship with ^GSPC at all. Read the point estimate (−0.13) as
  suggestive, not established."*
- **`style_tilt`**: *"Value (HML) loading is 0.24 (95% CI [0.04, 0.43]),
  excluding zero — a statistically real value tilt. Size (SMB) (0.19, 95%
  CI [−0.02, 0.40]) falls just short of the 95% bar (p=0.080) — a possible
  small-cap lean, not confirmed. With only 1/2 non-market factors clearing
  the 95% bar, value-vs-growth positioning is this portfolio's one
  statistically reliable style signal beyond overall market exposure."*
- **`explanatory_power`**: *"The single-factor CAPM model explains 1.5% of
  this portfolio's return variance (very low for an equity portfolio) —
  the remaining 98.5% is idiosyncratic (stock-specific) movement the
  market factor alone doesn't capture. Adding size/value lifts explained
  variance to 6.7% (adjusted 5.5%) — a modest absolute lift, but
  proportionally large: a real, 5.2%-point improvement attributable to
  those style factors, not the market alone. The joint F-test (F=4.3,
  p=0.006) confirms the factor model as a whole explains statistically
  real variance, even where R² itself is low — a genuine but small
  relationship, not noise."* (Worth calling out explicitly in the doc,
  not just the template: this low-R² read is **not** a data-quality
  problem — 222 observations is ample by the `short_data_window` flag's
  own bar — it's a substantive finding about this specific holding set.)
- **`frontier_position`**: *"...a 15.4%-point gap — large by this
  analysis's own standard. Historically, some combination of these same 4
  holdings, long-only, could have delivered meaningfully more return for
  the same volatility (or the same return for meaningfully less
  volatility) than the as-entered weights — not a suggestion to reweight,
  and not a signal to act on, just a description of the historical
  relationship among the holdings you entered."*
- **Flags**: none (222 observations, condition number 5.70 — clean data,
  the low R² is compositional, not a data artifact).

### Example C — a third real portfolio, chosen to exercise the `short_data_window` flag: GOOG 40% / GOOGL 40% / MSFT 20%, benchmark ^GSPC, 3-factor, daily, n=54 (a ~3-month window, deliberately short)

Raw results: CAPM beta 1.322, 95% CI [0.836, 1.809], p<0.0001, R²=0.340. FF:
mkt_rf 0.925 (p=0.0004), smb 0.217 (p=0.534), hml −0.812 (CI [−1.238,
−0.386], p=0.0002), FF R²=0.449. Frontier: not regularized (condition
number 501 — GOOG/GOOGL are near-duplicate share classes but not
duplicate enough over this window to trip the 1e8 regularization bar),
gap = +0.89 percentage points.

- **Headline** (priority 3: hml is the only significant non-market loading
  with |estimate| ≥ 0.30): *"This portfolio carries a statistically
  significant growth tilt (Value (HML) loading −0.81, 95% CI [−1.24,
  −0.39]) — a real, measurable style exposure beyond plain market
  direction."*
- **`beta`**: *"Beta is statistically distinguishable from zero (t=5.33,
  p<0.001) — there is real, measurable co-movement with ^GSPC. The
  interval is wide (width 0.97) relative to the point estimate — 1.32 is
  this window's best estimate, but the data doesn't pin down market
  sensitivity tightly; a longer window would narrow this. The interval
  also includes 1.0, so beta isn't statistically distinguishable from
  moving in lockstep with ^GSPC either."* (Note the coherent, appropriately
  humble read: the point estimate looks elevated, but with only 54
  observations the data can't even rule out plain beta = 1.)
- **`style_tilt`**: *"Value (HML) loading is −0.81 (95% CI [−1.24, −0.39]),
  excluding zero — a statistically real growth tilt. Size (SMB) (0.22, 95%
  CI [−0.47, 0.90]) is not statistically distinguishable from zero — no
  reliable size signal detected. With only 1/2 non-market factors clearing
  the 95% bar, growth-vs-value positioning is this portfolio's one
  statistically reliable style signal beyond overall market exposure."*
- **`explanatory_power`**: *"The single-factor CAPM model explains 34.0% of
  this portfolio's return variance (moderate for an equity portfolio) —
  the remaining 66.0% is idiosyncratic movement the market factor alone
  doesn't capture. Adding size/value lifts explained variance to 44.9%
  (adjusted 41.5%) — a real, 10.8%-point improvement attributable to those
  style factors, not the market alone. The joint F-test (F=19.5, p<0.001)
  confirms the factor model as a whole explains statistically real
  variance."*
- **`frontier_position`**: *"The gap to the frontier is small (0.9%) —
  small enough to be within the range explainable by estimation noise over
  a 54-observation window, not a structurally meaningful mismatch between
  these weights and this holding set's own risk/return relationships."*
- **Flags**: **`short_data_window`** (info) — *"This analysis rests on 54
  daily observations — thinner than this analysis's own bar for an ample
  sample (60). All estimates above should be read as provisional; a longer
  window is what would narrow the confidence intervals."*

### Illustrative-only note on `covariance_regularized` (not from a live run)

None of the three real portfolios above triggered eigenvalue-clipping
regularization — confirmed this is genuinely hard to hit with real,
distinct tickers even in an adversarial case (GOOG+GOOGL, near-identical
share classes, only pushed the condition number to ~501, far below the
1e8 trigger). This is worth stating plainly rather than papering over: on
real market data, the regularization path is a safety net for genuinely
degenerate inputs (e.g., a data outage collapsing several holdings' return
series to all-zero or all-identical over the requested window), not
something a normal, even highly-correlated, real portfolio is likely to
hit. The flag logic (§5) still needs to exist and be tested — `qa-tester`
should exercise it the same way Phase 10's own QA pass exercised the
"singular covariance" edge case (synthetic input), not by hunting for a
real ticker combination.

### Honest gap: the priority-5 ("nothing stands out") headline branch

None of the three real portfolios tested triggered the default headline
branch — every one tested (including a five-name, cross-sector
AAPL/JPM/JNJ/XOM/PG portfolio run during this spec's verification, CAPM
R²=6.3%) landed in the low-R² or style-tilt branches. Over a one-year
daily window, small (4-5 holding) real portfolios apparently tend to carry
enough idiosyncratic or style-factor signal to avoid looking "plain
vanilla" by this rule set's own bar — that's a genuine, if informal,
observation from this verification pass, not a claim the rule is wrong.
The branch still needs to exist (a rule set with no fallback is a bug
waiting to happen) and should be exercised by `qa-tester` with a
deliberately-constructed case (a larger, more diversified holding set, or
a single broad-market index-fund holding against its own index as
benchmark) during Phase 10j.

## 7. No-advice compliance check (rule 9a's hard limit)

Re-read every template and every worked-example sentence above against:
*does this tell the reader what to do with their money?* None do. The two
places most likely to drift — the frontier-gap "large" branch and its
headline counterpart — are the ones carrying the explicit "not a
suggestion to reweight, and not a signal to act on" clause, matching
`frontend/src/data/learning.ts`'s existing established phrasing for the
same concept rather than inventing new disclaimer language. "Read the
point estimate as suggestive, not established" and "treat ... cautiously"
describe how much to trust a *statistic*, not what to do with a
*position* — the same register the app already ships in the existing
covariance-regularization banner ("treat this frontier as less reliable
than usual," `Results.tsx` line 242). No sentence anywhere in this spec
contains "buy," "sell," "hold," "rebalance," "consider," or "you should."

## Consequences

- `developer` (Phase 10m) implements `app/api/interpretation.py` per §1-§5,
  wires `interpretation` into `AnalysisResponse`, adds the mirrored
  TypeScript types, and builds a new prominent component (recommend:
  directly under the existing portfolio-summary/disclaimer banner at the
  top of `Results.tsx`, above "1. Factor exposure" — first thing a reader
  sees after confirming what they ran) — visual treatment is Phase 10l/10m's
  call within the institutional-register system Phase 10l is defining in
  parallel, not prescribed here.
- `qa-tester` (Phase 10j) should verify: (a) the three worked examples
  above reproduce exactly when re-run against live data close to
  2026-08-11 (small drift expected as more recent trading days enter the
  window — verify the *branch selected* and *rule application*, not
  bit-exact prose, since the input data itself will have moved by the time
  Phase 10j runs); (b) the `short_data_window` and `covariance_regularized`
  flags fire/don't-fire correctly on constructed edge cases; (c) the
  priority-5 default headline branch, not hit by this spec's own live
  testing, gets at least one real or constructed portfolio that exercises
  it; (d) no output anywhere contains advice-coded language (extend the
  existing Phase 9 guardrail test — the "you should" substring check — to
  the new `interpretation.*` fields specifically).
- **Limitation, logged not silently worked around**: `EfficientFrontierResult`
  has no pairwise-correlation statistic today, so the
  `covariance_regularized` flag's "likely cause" attribution (§5) is a
  heuristic based only on the `n_obs`/`n_symbols` ratio, not a direct
  correlation measurement. If this proves unsatisfying in practice, a
  future phase could add a `max_pairwise_correlation` field to
  `EfficientFrontierResult` (a small, well-scoped addition to Phase 2's
  covariance step) rather than reaching for it now, out of this content
  spec's scope.
- **Limitation, logged**: the `frontierIsDegenerate` check currently lives
  only in `Results.tsx` (client-side, recomputed from `ef.frontier`) — the
  `frontier_position` takeaway (§3d) needs the same boolean and should not
  become a third independent re-implementation of it; recommend Phase 10m
  either exposes it as a field on `EfficientFrontierResult`/
  `InterpretationResponse` computed once server-side, or has the frontend
  compute the flag once and pass it into whatever renders the
  `frontier_position` card.
