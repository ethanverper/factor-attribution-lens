# Factor Lens — Glossary

Owned by `educator`. Every term this project's own app uses (Results, Learning, References & Formulas sections),
in the same dual-register format the live app renders under **Glossary** (`app/dashboard/shell.py::render_glossary_section()`).
This file is the source-of-truth archive; the app's own Glossary tab is where a visitor actually reads these —
keep both in sync by hand if either changes. Terms here also feed the Cowork OS portfolio-wide glossary at
`docs/glossary.md` (root), with a "First seen in" pointer back to this project.

Entry format:
```
### <Term>
**Plain language:** ...
**Technical:** ...
**Where it shows up here:** ...
```

---

### Alpha (α)
**Plain language:** The part of your average return that isn't explained by the market (or, in Fama-French, by any of the named factors) — whatever's left over.
**Technical:** The OLS regression intercept. Reported both as the raw periodic estimate and, annualized by compounding, as "alpha (annualized)." A statistically significant nonzero alpha means the model's factors don't fully account for your realized average return.
**Where it shows up here:** `app/models/capm.py`, `app/models/fama_french.py`; Results §1 (Factor exposure); Learning §04; References & Formulas.

### Beta (β)
**Plain language:** How much your portfolio historically moves for every 1% the benchmark moves.
**Technical:** The CAPM regression's slope coefficient on benchmark excess return; reported with a Newey-West HAC standard error, t-stat, p-value, and 95% confidence interval, not as a bare point estimate.
**Where it shows up here:** `app/models/capm.py`; Results §1; Learning §04; References & Formulas.

### CAPM (Capital Asset Pricing Model)
**Plain language:** A one-factor way of explaining a portfolio's return: how much of it is just "the market, scaled up or down."
**Technical:** Sharpe (1964)/Lintner (1965)/Mossin (1966): R<sub>p</sub> − R<sub>f</sub> = α + β(R<sub>m</sub> − R<sub>f</sub>) + ε, fit by OLS with HAC standard errors in this project.
**Where it shows up here:** `app/models/capm.py`; Results §1; Learning §04; References & Formulas.

### Efficient frontier
**Plain language:** The best return historically achievable, for each level of risk, by re-weighting the exact holdings you entered — no new stocks, no leverage, no shorting.
**Technical:** The set of long-only portfolios minimizing w<sup>T</sup>Σw for each target return w<sup>T</sup>μ, solved point-by-point via SLSQP since long-only mean-variance optimization has no closed form (Markowitz, 1952).
**Where it shows up here:** `app/models/optimization.py`; Results §2; Learning §04; References & Formulas.

### Factor loading
**Plain language:** How much your portfolio leans toward a particular style of stock — small vs. large, cheap vs. expensive, profitable vs. not, conservative vs. aggressive.
**Technical:** A partial-regression coefficient in the Fama-French model — sensitivity to one factor's spread-portfolio return, holding the other included factors fixed.
**Where it shows up here:** `app/models/fama_french.py`; Results §1; Learning §04; References & Formulas.

### Fama-French 3-/5-factor model
**Plain language:** An extension of CAPM that explains a portfolio's return using several named style factors instead of just "the market."
**Technical:** Fama & French (1993, 2015). 3-factor adds SMB and HML to CAPM's market factor; 5-factor adds RMW and CMA on top of that. Fit by OLS with HAC standard errors in this project; factor return series sourced from Kenneth French's Data Library, not OpenBB (decision 0002).
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

### R² (R-squared)
**Plain language:** How much of your portfolio's up-and-down movement is explained by the factor(s) in the model, versus left unexplained.
**Technical:** Coefficient of determination for the CAPM/Fama-French OLS fit; doubles as the risk-attribution split (factor-explained share = R², idiosyncratic share = 1 − R²).
**Where it shows up here:** `app/models/capm.py`, `app/models/fama_french.py`, `app/dashboard/attribution.py`; Results §1 & §3; Learning §04; References & Formulas.

### Idiosyncratic risk
**Plain language:** The part of your portfolio's risk that's specific to the individual companies you hold, not shared with the market or with any named style factor.
**Technical:** 1 − R² of the fitted factor model — the residual variance share unexplained by market/size/value/profitability/investment exposure.
**Where it shows up here:** `app/dashboard/attribution.py::compute_risk_attribution`; Results §3; Learning §04.

### Newey-West HAC standard errors
**Plain language:** A more honest way of measuring how uncertain a beta or factor loading really is, built to not be fooled by the fact that stock returns are choppier and stickier day-to-day than a textbook regression assumes.
**Technical:** Heteroskedasticity- and autocorrelation-consistent covariance estimator (Newey & West, 1987/1994), plug-in bandwidth L = floor(4·(n/100)^(2/9)), used for every regression standard error/t-stat/p-value/CI in this project, in place of classical OLS standard errors, which would understate them.
**Where it shows up here:** `app/models/_regression.py`; Results §1 ("Standard errors: HAC (Newey-West)"); References & Formulas.

### Statistical significance (t-stat, p-value, 95% CI)
**Plain language:** A way of telling a real signal apart from noise: if the confidence interval around a number like beta or a factor loading includes zero, you can't be confident the true exposure isn't zero.
**Technical:** Standard OLS-regression diagnostics (t-statistic, two-sided p-value, 95% confidence interval) computed from the HAC standard error above for every coefficient this project reports.
**Where it shows up here:** `app/models/schemas.py`; Results §1; Learning §04; References & Formulas.

### Long-only constraint
**Plain language:** The frontier never assumes you could short a stock or borrow money to invest more than you have — only re-weighting among positive holdings of what you actually entered.
**Technical:** w<sub>i</sub> ≥ 0 for all holdings in the efficient-frontier optimization; this project's default (decision 0003), reflecting how retail/small-RIA portfolios are actually held. `allow_short=True` gives the classical unconstrained frontier instead.
**Where it shows up here:** `app/models/optimization.py`; Results §2; Learning §04; References & Formulas.

### Covariance regularization (eigenvalue clipping)
**Plain language:** A safety net for when a holding set is too small, too correlated, or has too little data to produce a trustworthy risk picture — the app flags it rather than silently producing a broken frontier.
**Technical:** If the sample covariance matrix's condition number exceeds 1e8 or it isn't positive-semi-definite, negative/near-zero eigenvalues are floored to 1e-6 × the largest eigenvalue and the matrix reconstructed — a standard "nearest PSD matrix" fix, chosen over Ledoit-Wolf shrinkage for simplicity (decision 0003). Surfaced as `covariance_regularized` on `EfficientFrontierResult`.
**Where it shows up here:** `app/models/covariance.py`; Results §2 (warning banner when triggered); References & Formulas.

### Return attribution
**Plain language:** Splitting your portfolio's average return into pieces — how much came from market exposure, how much from each style tilt, and how much is unexplained ("alpha").
**Technical:** An exact OLS identity, not an approximation: because the Fama-French fit includes an intercept, the fitted residual has zero mean over the sample, so mean(R<sub>p</sub> − R<sub>f</sub>) = α + Σᵢ βᵢ·mean(factorᵢ) reproduces the realized mean exactly.
**Where it shows up here:** `app/dashboard/attribution.py::compute_return_attribution`; Results §3; Learning §04.

### Risk attribution
**Plain language:** Splitting your portfolio's risk into the share explained by broad factors versus the share specific to your individual holdings.
**Technical:** factor-explained share = R² (clipped to [0,1] for display), idiosyncratic share = 1 − R², of the fitted factor model.
**Where it shows up here:** `app/dashboard/attribution.py::compute_risk_attribution`; Results §3; Learning §04.

### Markowitz mean-variance optimization
**Plain language:** The math behind "what's the best possible return for a given amount of risk," using how your holdings have historically moved together.
**Technical:** Models portfolio return as w<sup>T</sup>μ and variance as w<sup>T</sup>Σw, then solves for the efficient set, the GMV portfolio, and the tangency (max-Sharpe) portfolio (Markowitz, 1952). μ and Σ are annualized by linear scaling (periodic × periods/year), a deliberately different convention from CAPM/Fama-French alpha's compounding annualization (decision 0003).
**Where it shows up here:** `app/models/optimization.py`; Results §2; Learning §04; References & Formulas.
