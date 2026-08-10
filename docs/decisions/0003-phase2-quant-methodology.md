# 0003. Phase 2 quant methodology: HAC standard errors, long-only Markowitz via SLSQP, eigenvalue-clipping covariance regularization, 3-factor default

Date: 2026-08-10
Status: accepted

## Context

Phase 2 needed to turn Phase 1's aligned return bundle into three model
outputs — CAPM beta, Fama-French factor loadings with diagnostics, and a
Markowitz efficient frontier — as a reusable module (`app/models/`), not a
notebook. Several genuinely contestable methodology choices had to be made
along the way; this records them so Phase 3/4/5 know what assumptions the
numbers rest on, per this role's standing mandate to log real methodology
decisions rather than pick silently.

## Decisions

**1. Regression standard errors: Newey-West HAC by default, not classical OLS SEs.**
Both the CAPM regression (`capm.py`) and the Fama-French regression
(`fama_french.py`) go through a shared `_regression.py` helper that always
fits via `statsmodels.OLS(...).fit(cov_type="HAC", cov_kwds={"maxlags": ...})`,
using the Newey & West (1994) plug-in bandwidth
`floor(4*(n/100)^(2/9))`. Daily (and to a lesser extent monthly) equity
return series routinely exhibit heteroskedasticity and mild
autocorrelation; classical OLS standard errors would understate the true
uncertainty on beta/factor loadings, which matters because this project's
whole differentiator is reporting real statistical diagnostics (t-stats,
p-values, confidence intervals) rather than bare point estimates. This is
not configurable per-call today — a single, audited convention was judged
more valuable than a knob nobody outside `quant-analyst`/`qa-tester` would
know how to set correctly. `standard_error_convention` is echoed in every
`CAPMResult`/`FactorModelResult` so downstream consumers (and QA) know
exactly which covariance estimator produced the numbers.

**2. Annualization convention differs by context, and this is intentional, not inconsistent.**
- CAPM/Fama-French alpha is annualized by *compounding* the periodic
  estimate: `(1 + alpha)^periods_per_year - 1`. Alpha is a small
  per-period return; compounding is the correct way to express "what this
  would compound to over a year" and is the standard convention for
  reporting fund alpha.
- Markowitz frontier inputs (expected return, covariance) are annualized
  by *linear scaling* — periodic mean × periods_per_year, periodic
  covariance × periods_per_year — the textbook i.i.d.-returns assumption
  underlying mean-variance optimization itself. Compounding the covariance
  matrix has no clean closed form; linear scaling is what the Markowitz
  model assumes by construction.
These two conventions serve different purposes (one is a return-reporting
convenience, the other is a modeling assumption) and are not meant to be
reconciled into one rule — but Phase 3/4 should not assume "annualized"
means the same arithmetic everywhere in this module's output, and should
say so if narrating both numbers side by side.

**3. Markowitz frontier: long-only by default (`allow_short=False`), solved via `scipy.optimize.minimize` (SLSQP).**
Retail investors and small RIAs — this project's stated persona — hold
long positions in practice; an unconstrained (short-allowed) frontier is
the textbook object but not what most users could actually implement, and
would materially overstate achievable Sharpe ratios by exploiting the
worst-covariance handful of legs. The long-only constraint is the default,
not a hardcoded limitation: `compute_efficient_frontier(..., allow_short=True)`
gives the classical unconstrained frontier for an analyst who wants it. Long-only
mean-variance optimization has no closed-form solution (it's a quadratic
program with inequality constraints), so it's solved numerically via SLSQP
per frontier point; this is a standard, well-audited solver choice
(scipy's implementation of a well-established QP algorithm) rather than a
hand-rolled optimizer.

**4. Covariance matrix regularization: eigenvalue clipping, triggered by condition number or non-PSD-ness.**
Per the roadmap's own flagged risk ("degenerate/singular covariance
matrices"), a small holdings set with correlated or near-duplicate
positions (or few observations relative to the number of assets) can
produce a sample covariance matrix that is singular or numerically
ill-conditioned, which breaks optimization (division by a near-zero
eigenvalue, unstable solver behavior). `covariance.py` checks the sample
covariance's condition number (threshold `1e8`) and positive-definiteness;
if either check fails, it applies eigenvalue clipping — floor
negative/near-zero eigenvalues to `1e-6 × largest eigenvalue`, reconstruct
the symmetric matrix — a standard, easily-audited "nearest PSD matrix"
fix. This was chosen over Ledoit-Wolf shrinkage (would add a dependency
and require choosing a shrinkage target/intensity) as the simpler,
equally-standard option for a case that's meant to be a safety net, not
the default path. `EfficientFrontierResult.covariance_regularized` and
`.covariance_condition_number` are always reported so it's visible
whenever this path was triggered — this should never happen silently.

**5. Fama-French model default stays 3-factor; 5-factor is supported end-to-end, not just a stub.**
Matches the roadmap's own framing (3-factor primary, 5-factor stretch).
`estimate_factor_model` takes `factor_model: Literal["3","5"]` and works
for either, reading whichever the caller's Phase 1 request already
specified (`data.meta.factor_model`) — there's no separate Phase 2 toggle
disconnected from what data was actually fetched. If a 5-factor regression
is requested but the bundle only carries 3-factor columns (RMW/CMA
missing), it raises `MissingFactorsError` rather than silently downgrading.

**6. Frontier target-return range: global-min-variance return up to the maximum single-asset return, long-only.**
The "efficient" (upper) branch of the frontier is what's shown — target
returns span `[gmv_return, max(asset mean returns)]`, evenly spaced
(`n_points`, default 25). The lower/inefficient branch (same risk, worse
return) isn't computed since it's never useful to plot or explain. This
range is also the max deliverable long-only return, since target returns
above the best single asset's mean aren't achievable under a sum-to-1,
no-short constraint.

**7. Minimum observation thresholds are conservative, not just "regression didn't crash."**
CAPM requires ≥10 overlapping observations; Fama-French requires ≥5× the
number of estimated parameters (i.e. ≥20 for 3-factor, ≥30 for 5-factor —
a common regression rule of thumb); Markowitz requires ≥ n_assets + 2
observations to get a non-degenerate covariance matrix before
regularization even kicks in. Below these thresholds the functions raise
(`InsufficientDataError`) rather than returning a technically-computable
but statistically meaningless result — relevant because Phase 1's
`aligned_start_date`/`aligned_end_date` can legitimately produce a short
window (Ken French's data lag, a short requested date range, etc.).

## Consequences

- Every `CAPMResult`/`FactorModelResult` in this project's output is a HAC
  (not classical-OLS) regression — anyone benchmarking these numbers
  against a plain `statsmodels.OLS(...).fit()` or a spreadsheet
  `LINEST`/`SLOPE` call will see different (typically slightly wider)
  standard errors and should not read that as a bug.
- The efficient frontier is long-only by default; anyone expecting the
  textbook unconstrained Markowitz frontier (e.g. for teaching/comparison
  purposes) needs to explicitly pass `allow_short=True`.
- `covariance_regularized=True` on a real portfolio is a signal worth
  surfacing to the end user in Phase 3/4 (e.g. "this frontier is less
  reliable — your holdings are highly correlated or the data window is
  short relative to the number of holdings"), not just an internal flag.
- This module makes no claim about which portfolio a user "should" hold —
  `EfficientFrontierResult`/`PortfolioPosition` describe where the
  as-input portfolio sits relative to a modeled frontier and by how much
  return per unit of risk it falls short of the modeled optimum; they are
  not, and must not be presented as, a buy/sell/rebalance recommendation.
  This is internal decision-support analytics only, consistent with the
  project's hard limit on personalized investment advice.
