# Factor Attribution Lens — Glossary

Owned by `educator`. Every term this project's own app uses (Overview, Results, Learning, References & Formulas,
Real World sections), in the same dual-register format the live app renders under **Glossary**
(`app/dashboard/shell.py::render_glossary_section()`). This file is the source-of-truth archive; the app's own
Glossary tab is where a visitor actually reads these — keep both in sync by hand if either changes. Terms here
also feed the Cowork OS portfolio-wide glossary at `docs/glossary.md` (root), with a "First seen in" pointer
back to this project.

**Phase 9e completeness audit (2026-08-10):** re-read every tab of the live app end to end and found two kinds
of real gaps, not cosmetic ones — (1) four terms already written here (Covariance regularization, Return
attribution, Risk attribution, Markowitz mean-variance optimization) had never actually been ported into the
live `render_glossary_section()`, so a visitor could see all four used on Results/References but not find them
defined in the Glossary tab; (2) five more terms appear repeatedly in the app's own text with no definition
anywhere — F-statistic, excess return, the risk-free rate, the covariance matrix itself (distinct from its
regularization), and the compounding-vs-linear-scaling annualization split. Both closed below, and the growing
term count (19 → 27) is now grouped into three concept areas — Factor models & regression, Portfolio theory &
optimization, Attribution — instead of one flat list, matching the live app's regrouped Glossary tab. See
`docs/decisions/0010-phase9e-learning-diagrams-and-glossary-audit.md`.

Entry format:
```
### <Term>
**Plain language:** ...
**Technical:** ...
**Where it shows up here:** ...
```

---

## Factor models & regression

How a return gets explained: CAPM's single market factor, Fama-French's style factors, and the statistical
diagnostics that separate a real exposure from noise.

### CAPM (Capital Asset Pricing Model)
**Plain language:** A one-factor way of explaining a portfolio's return: how much of it is just "the market, scaled up or down."
**Technical:** Sharpe (1964)/Lintner (1965)/Mossin (1966): R<sub>p</sub> − R<sub>f</sub> = α + β(R<sub>m</sub> − R<sub>f</sub>) + ε, fit by OLS with HAC standard errors in this project.
**Where it shows up here:** `app/models/capm.py`; Overview, Results §1; Learning §04; References & Formulas.

### Beta (β)
**Plain language:** How much your portfolio historically moves for every 1% the benchmark moves.
**Technical:** The CAPM regression's slope coefficient on benchmark excess return; reported with a Newey-West HAC standard error, t-stat, p-value, and 95% confidence interval, not as a bare point estimate.
**Where it shows up here:** `app/models/capm.py`; Results §1; Learning §04; References & Formulas.

### Alpha (α)
**Plain language:** The part of your average return that isn't explained by the market (or, in Fama-French, by any of the named factors) — whatever's left over.
**Technical:** The OLS regression intercept. Reported both as the raw periodic estimate and, annualized by compounding, as "alpha (annualized)." A statistically significant nonzero alpha means the model's factors don't fully account for your realized average return.
**Where it shows up here:** `app/models/capm.py`, `app/models/fama_french.py`; Results §1; Learning §04; References & Formulas.

### Excess return
**Plain language:** Your return (or the market's, or a factor's) after subtracting what you could have earned with essentially no risk over the same period — the number every formula on this app is actually built from, not the raw return.
**Technical:** R − R<sub>f</sub> for whichever series is being described (portfolio, benchmark, or a factor's own spread portfolio). CAPM and Fama-French are both fit on excess return, not raw return, so the risk-free rate is subtracted before α/β are ever estimated.
**Where it shows up here:** `app/models/capm.py`, `app/models/fama_french.py`; Results §1 & §3; Learning §04; References & Formulas.

### Risk-free rate (R<sub>f</sub>)
**Plain language:** What you could earn with (essentially) no risk over the same period — the baseline every return in this app is measured against.
**Technical:** Sourced from Kenneth French's Data Library, not OpenBB (decision 0002), aligned to the same dates/frequency as the portfolio and benchmark returns before any regression or optimization runs.
**Where it shows up here:** `app/models/capm.py`, `app/models/optimization.py`; Results §1, §2 & §3; References & Formulas.

### Fama-French 3-/5-factor model
**Plain language:** An extension of CAPM that explains a portfolio's return using several named style factors instead of just "the market."
**Technical:** Fama & French (1993, 2015). 3-factor adds SMB and HML to CAPM's market factor; 5-factor adds RMW and CMA on top of that. Fit by OLS with HAC standard errors in this project; factor return series sourced from Kenneth French's Data Library, not OpenBB (decision 0002).
**Where it shows up here:** `app/models/fama_french.py`; Overview, Results §1; Learning §04; References & Formulas.

### Factor loading
**Plain language:** How much your portfolio leans toward a particular style of stock — small vs. large, cheap vs. expensive, profitable vs. not, conservative vs. aggressive.
**Technical:** A partial-regression coefficient in the Fama-French model — sensitivity to one factor's spread-portfolio return, holding the other included factors fixed.
**Where it shows up here:** `app/models/fama_french.py`; Results §1; Learning §04; References & Formulas.

### SMB (Small Minus Big) — the size factor
**Plain language:** A positive loading here means your holdings behave more like small-company stocks than large-company stocks.
**Technical:** The return of a portfolio long small-cap stocks and short large-cap stocks; one of the explanatory variables in the Fama-French regression.
**Where it shows up here:** `app/dashboard/attribution.py::FACTOR_LABELS`; Results §1; Learning §04; Glossary §05.

### HML (High Minus Low) — the value factor
**Plain language:** A positive loading here means your holdings behave more like "value" stocks (cheap relative to book value) than "growth" stocks (expensive relative to book value).
**Technical:** The return of a portfolio long high book-to-market stocks and short low book-to-market stocks.
**Where it shows up here:** `app/dashboard/attribution.py::FACTOR_LABELS`; Results §1; Learning §04; Glossary §05.

### RMW (Robust Minus Weak) — the profitability factor
**Plain language:** A positive loading here means your holdings behave more like highly profitable companies than weakly profitable ones.
**Technical:** The return of a portfolio long robust-operating-profitability stocks and short weak-profitability stocks; Fama-French 5-factor only.
**Where it shows up here:** `app/models/fama_french.py` (5-factor path); Results §1 (5-factor); Glossary §05.

### CMA (Conservative Minus Aggressive) — the investment factor
**Plain language:** A positive loading here means your holdings behave more like conservatively-run, slow-growing companies than aggressively-expanding ones.
**Technical:** The return of a portfolio long low-investment (conservative) firms and short high-investment (aggressive) firms; Fama-French 5-factor only.
**Where it shows up here:** `app/models/fama_french.py` (5-factor path); Results §1 (5-factor); Glossary §05.

### R² (R-squared) & adjusted R²
**Plain language:** How much of your portfolio's up-and-down movement is explained by the factor(s) in the model, versus left unexplained. Adjusted R² is the same idea, penalized slightly for adding more factors, so it doesn't automatically go up just because 5-factor has more variables than 3-factor.
**Technical:** Coefficient of determination for the CAPM/Fama-French OLS fit; doubles as the risk-attribution split (factor-explained share = R², idiosyncratic share = 1 − R²). Adjusted R² is shown alongside R² on the Fama-French stat tile specifically so adding RMW/CMA isn't mistaken for a better fit when it's really just more free parameters.
**Where it shows up here:** `app/models/capm.py`, `app/models/fama_french.py`, `app/dashboard/attribution.py`; Results §1 & §3; Learning §04; References & Formulas.

### F-statistic
**Plain language:** A different question than any single factor's own p-value: taken together, do all of this model's factors explain your return better than assuming none of them matter at all?
**Technical:** The Fama-French regression's overall joint-significance test against an intercept-only model, reported with its own p-value (F p-value). A low F p-value means the factors jointly explain a statistically significant share of return, independent of whether any one loading's own confidence interval excludes zero.
**Where it shows up here:** `app/models/fama_french.py`; Results §1 (Fama-French stat tiles); References & Formulas.

### Newey-West HAC standard errors
**Plain language:** A more honest way of measuring how uncertain a beta or factor loading really is, built to not be fooled by the fact that stock returns are choppier and stickier day-to-day than a textbook regression assumes.
**Technical:** Heteroskedasticity- and autocorrelation-consistent covariance estimator (Newey & West, 1987/1994), plug-in bandwidth L = floor(4·(n/100)^(2/9)), used for every regression standard error/t-stat/p-value/CI in this project, in place of classical OLS standard errors, which would understate them.
**Where it shows up here:** `app/models/_regression.py`; Results §1 ("Standard errors: HAC (Newey-West)"); References & Formulas.

### Statistical significance (t-stat, p-value, 95% CI)
**Plain language:** A way of telling a real signal apart from noise: if the confidence interval around a number like beta or a factor loading includes zero, you can't be confident the true exposure isn't zero.
**Technical:** Standard OLS-regression diagnostics (t-statistic, two-sided p-value, 95% confidence interval) computed from the HAC standard error above for every coefficient this project reports.
**Where it shows up here:** `app/models/schemas.py`; Results §1; Learning §04; References & Formulas.

## Portfolio theory & optimization

How the efficient frontier is built and read: the math behind "best return for a given risk," and the
conventions/safeguards behind it.

### Efficient frontier
**Plain language:** The best return historically achievable, for each level of risk, by re-weighting the exact holdings you entered — no new stocks, no leverage, no shorting.
**Technical:** The set of long-only portfolios minimizing w<sup>T</sup>Σw for each target return w<sup>T</sup>μ, solved point-by-point via SLSQP since long-only mean-variance optimization has no closed form (Markowitz, 1952).
**Where it shows up here:** `app/models/optimization.py`; Overview, Results §2; Learning §04; References & Formulas.

### Markowitz mean-variance optimization
**Plain language:** The math behind "what's the best possible return for a given amount of risk," using how your holdings have historically moved together.
**Technical:** Models portfolio return as w<sup>T</sup>μ and variance as w<sup>T</sup>Σw, then solves for the efficient set, the GMV portfolio, and the tangency (max-Sharpe) portfolio (Markowitz, 1952). μ and Σ are annualized by linear scaling (periodic × periods/year), a deliberately different convention from CAPM/Fama-French alpha's compounding annualization (decision 0003).
**Where it shows up here:** `app/models/optimization.py`; Overview; References & Formulas; Real World / Corporate Applications.

### Covariance matrix (Σ)
**Plain language:** A table of how every pair of your holdings has historically moved together — not just how volatile each one is on its own, but whether they tend to rise and fall together or offset each other.
**Technical:** The annualized covariance matrix of holding returns; portfolio variance is w<sup>T</sup>Σw. In the Markowitz framework, all diversification benefit comes from Σ's off-diagonal (co-movement) terms, not from any single holding's own variance.
**Where it shows up here:** `app/models/optimization.py`, `app/models/covariance.py`; Results §2; References & Formulas.

### Covariance regularization (eigenvalue clipping)
**Plain language:** A safety net for when a holding set is too small, too correlated, or has too little data to produce a trustworthy risk picture — the app flags it rather than silently producing a broken frontier.
**Technical:** If the sample covariance matrix's condition number exceeds 1e8 or it isn't positive-semi-definite, negative/near-zero eigenvalues are floored to 1e-6 × the largest eigenvalue and the matrix reconstructed — a standard "nearest PSD matrix" fix, chosen over Ledoit-Wolf shrinkage for simplicity (decision 0003). Surfaced as `covariance_regularized` on `EfficientFrontierResult`.
**Where it shows up here:** `app/models/covariance.py`; Results §2 (warning banner when triggered); Learning §04; References & Formulas.

### Long-only constraint
**Plain language:** The frontier never assumes you could short a stock or borrow money to invest more than you have — only re-weighting among positive holdings of what you actually entered.
**Technical:** w<sub>i</sub> ≥ 0 for all holdings in the efficient-frontier optimization; this project's default (decision 0003), reflecting how retail/small-RIA portfolios are actually held. `allow_short=True` gives the classical unconstrained frontier instead.
**Where it shows up here:** `app/models/optimization.py`; Results §2; Learning §04; References & Formulas.

### Global minimum-variance (GMV) portfolio
**Plain language:** Of every way you could re-weight your exact holdings, the single weighting that historically would have been the calmest (lowest volatility) — regardless of return.
**Technical:** The frontier point with minimum w<sup>T</sup>Σw subject to the long-only, sum-to-one constraints; the leftmost point on the plotted frontier.
**Where it shows up here:** `app/models/optimization.py`; Results §2; Learning §04.

### Tangency / max-Sharpe portfolio
**Plain language:** Of every way you could re-weight your exact holdings, the single weighting with the best return per unit of risk.
**Technical:** The frontier point maximizing S = (R<sub>p</sub> − R<sub>f</sub>) / σ<sub>p</sub> subject to the same long-only constraints as the rest of the frontier.
**Where it shows up here:** `app/models/optimization.py`; Results §2; Learning §04.

### Sharpe ratio
**Plain language:** Return earned per unit of risk taken, after subtracting the risk-free rate — higher is better compensated risk-taking.
**Technical:** S = (R<sub>p</sub> − R<sub>f</sub>) / σ<sub>p</sub> (Sharpe, 1966/1994).
**Where it shows up here:** `app/models/optimization.py`; Results §2; Learning §04; References & Formulas.

### Annualization convention (compounding vs. linear scaling)
**Plain language:** Two different, both-correct ways this app turns a per-day (or per-month) number into a per-year one — CAPM/Fama-French alpha uses one, the frontier's inputs use the other, on purpose, not by accident.
**Technical:** Alpha is annualized by compounding, (1 + α)^(periods/yr) − 1, matching how a return actually accrues over time. The frontier's μ and Σ are annualized by linear scaling (periodic value × periods/year), the textbook i.i.d.-returns convention mean-variance optimization assumes by construction. The two are not interchangeable — mixing them would break both the return-attribution identity and the frontier's own assumptions (decision 0003).
**Where it shows up here:** `app/models/capm.py`, `app/models/fama_french.py` (compounding), `app/models/optimization.py` (linear scaling); Results §1, §2 & §3; References & Formulas.

## Attribution

Putting the exposures back together: exactly how much of your realized return and risk each piece above actually
accounts for.

### Return attribution
**Plain language:** Splitting your portfolio's average return into pieces — how much came from market exposure, how much from each style tilt, and how much is unexplained ("alpha").
**Technical:** An exact OLS identity, not an approximation: because the Fama-French fit includes an intercept, the fitted residual has zero mean over the sample, so mean(R<sub>p</sub> − R<sub>f</sub>) = α + Σᵢ βᵢ·mean(factorᵢ) reproduces the realized mean exactly.
**Where it shows up here:** `app/dashboard/attribution.py::compute_return_attribution`; Results §3; Learning §04; References & Formulas.

### Risk attribution
**Plain language:** Splitting your portfolio's risk into the share explained by broad factors versus the share specific to your individual holdings.
**Technical:** factor-explained share = R² (clipped to [0,1] for display), idiosyncratic share = 1 − R², of the fitted factor model.
**Where it shows up here:** `app/dashboard/attribution.py::compute_risk_attribution`; Results §3; Learning §04; References & Formulas.

### Idiosyncratic risk
**Plain language:** The part of your portfolio's risk that's specific to the individual companies you hold, not shared with the market or with any named style factor.
**Technical:** 1 − R² of the fitted factor model — the residual variance share unexplained by market/size/value/profitability/investment exposure.
**Where it shows up here:** `app/dashboard/attribution.py::compute_risk_attribution`; Results §3; Learning §04.
