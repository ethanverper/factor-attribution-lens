// Ported verbatim (content, not markup) from the removed
// `app/dashboard/shell.py::render_glossary_section` (Phase 9/9e). All 27
// terms, grouped into the same three concept areas. HTML entities/tags
// (e.g. `&beta;`, `<code>`) are kept as-is and rendered via
// `dangerouslySetInnerHTML` in `GlossaryEntry` — this is static, trusted,
// hand-authored copy (not user input), the same trust model the original
// Python content used.

export interface GlossaryEntry {
  term: string
  where: string
  plain: string
  technical: string
}

export interface GlossaryGroup {
  title: string
  note: string
  entries: GlossaryEntry[]
}

const factorEntries: GlossaryEntry[] = [
  {
    term: "CAPM (Capital Asset Pricing Model)",
    where: "Overview, Results §1, Learning, References",
    plain: "A one-factor way of explaining a portfolio's return: how much of it is just &ldquo;the market, scaled up or down.&rdquo;",
    technical:
      "Sharpe (1964)/Lintner (1965)/Mossin (1966): <code>R<sub>p</sub> &minus; R<sub>f</sub> = &alpha; + &beta;(R<sub>m</sub> &minus; R<sub>f</sub>) + &epsilon;</code>, fit by OLS with HAC standard errors in this project.",
  },
  {
    term: "Beta (&beta;)",
    where: "Results §1, Learning, References",
    plain: "How much your portfolio historically moves for every 1% the benchmark moves.",
    technical:
      "The CAPM regression's slope coefficient on benchmark excess return; reported with a Newey-West HAC standard error, t-stat, p-value, and 95% confidence interval, not as a bare point estimate.",
  },
  {
    term: "Alpha (&alpha;)",
    where: "Results §1, Learning, References",
    plain: "The part of your average return that isn't explained by the market (or, in Fama-French, by any of the named factors) &mdash; whatever's left over.",
    technical:
      "The OLS regression intercept. Reported both as the raw periodic estimate and, annualized by compounding, as &ldquo;alpha (annualized).&rdquo; A statistically significant nonzero alpha means the model's factors don't fully account for your realized average return.",
  },
  {
    term: "Excess return",
    where: "Results §1 &amp; §3, Learning, References",
    plain: "Your return (or the market's, or a factor's) after subtracting what you could have earned with essentially no risk over the same period &mdash; the number every formula on this app is actually built from, not the raw return.",
    technical:
      "<code>R &minus; R<sub>f</sub></code> for whichever series is being described. CAPM and Fama-French are both fit on excess return, not raw return, so the risk-free rate is subtracted before &alpha;/&beta; are ever estimated.",
  },
  {
    term: "Risk-free rate (R<sub>f</sub>)",
    where: "Results §1, §2 &amp; §3, References",
    plain: "What you could earn with (essentially) no risk over the same period &mdash; the baseline every return in this app is measured against.",
    technical:
      "Sourced from Kenneth French's Data Library (not OpenBB, see decision 0002), aligned to the same dates/frequency as the portfolio and benchmark returns before any regression or optimization runs.",
  },
  {
    term: "Fama-French 3-/5-factor model",
    where: "Overview, Results §1, Learning, References",
    plain: "An extension of CAPM that explains a portfolio's return using several named style factors instead of just &ldquo;the market.&rdquo;",
    technical:
      "Fama &amp; French (1993, 2015). 3-factor adds SMB and HML to CAPM's market factor; 5-factor adds RMW and CMA on top of that. Fit by OLS with HAC standard errors in this project; factor return series sourced from Kenneth French's Data Library, not OpenBB.",
  },
  {
    term: "Factor loading",
    where: "Results §1, Learning, References",
    plain: "How much your portfolio leans toward a particular style of stock &mdash; small vs. large, cheap vs. expensive, profitable vs. not, conservative vs. aggressive.",
    technical:
      "A partial-regression coefficient in the Fama-French model &mdash; sensitivity to one factor's spread-portfolio return, holding the other included factors fixed.",
  },
  {
    term: "SMB (Small Minus Big) &mdash; the size factor",
    where: "Results §1, Learning, References",
    plain: "A positive loading here means your holdings behave more like small-company stocks than large-company stocks.",
    technical:
      "The return of a portfolio long small-cap stocks and short large-cap stocks; one of the explanatory variables in the Fama-French regression.",
  },
  {
    term: "HML (High Minus Low) &mdash; the value factor",
    where: "Results §1, Learning, References",
    plain: "A positive loading here means your holdings behave more like &ldquo;value&rdquo; stocks (cheap relative to book value) than &ldquo;growth&rdquo; stocks (expensive relative to book value).",
    technical:
      "The return of a portfolio long high book-to-market stocks and short low book-to-market stocks.",
  },
  {
    term: "RMW (Robust Minus Weak) &mdash; the profitability factor",
    where: "Results §1 (5-factor), Learning, References",
    plain: "A positive loading here means your holdings behave more like highly profitable companies than weakly profitable ones.",
    technical:
      "The return of a portfolio long robust-operating-profitability stocks and short weak-profitability stocks; Fama-French 5-factor only.",
  },
  {
    term: "CMA (Conservative Minus Aggressive) &mdash; the investment factor",
    where: "Results §1 (5-factor), Learning, References",
    plain: "A positive loading here means your holdings behave more like conservatively-run, slow-growing companies than aggressively-expanding ones.",
    technical:
      "The return of a portfolio long low-investment (conservative) firms and short high-investment (aggressive) firms; Fama-French 5-factor only.",
  },
  {
    term: "R&sup2; (R-squared) &amp; adjusted R&sup2;",
    where: "Results §1 &amp; §3, Learning, References",
    plain: "How much of your portfolio's up-and-down movement is explained by the factor(s) in the model, versus left unexplained. Adjusted R&sup2; is the same idea, penalized slightly for adding more factors, so it doesn't automatically go up just because 5-factor has more variables than 3-factor.",
    technical:
      "Coefficient of determination for the CAPM/Fama-French OLS fit; doubles as the risk-attribution split (factor-explained share = R&sup2;, idiosyncratic share = 1 &minus; R&sup2;). Adjusted R&sup2; is shown alongside R&sup2; on the Fama-French stat tile specifically so adding RMW/CMA isn't mistaken for a better fit when it's really just more free parameters.",
  },
  {
    term: "F-statistic",
    where: "Results §1 (Fama-French), References",
    plain: "A different question than any single factor's own p-value: taken together, do all of this model's factors explain your return better than assuming none of them matter at all?",
    technical:
      "The Fama-French regression's overall joint-significance test against an intercept-only model, reported with its own p-value (F p-value). A low F p-value means the factors jointly explain a statistically significant share of return, independent of whether any one loading's own confidence interval excludes zero.",
  },
  {
    term: "Newey-West HAC standard errors",
    where: "Results §1, References",
    plain: "A more honest way of measuring how uncertain a beta or factor loading really is, built to not be fooled by the fact that stock returns are choppier and stickier day-to-day than a textbook regression assumes.",
    technical:
      "Heteroskedasticity- and autocorrelation-consistent covariance estimator (Newey &amp; West, 1987/1994) used for every regression standard error/t-stat/p-value/CI in this project, in place of classical OLS standard errors, which would understate them.",
  },
  {
    term: "Statistical significance (t-stat, p-value, 95% CI)",
    where: "Results §1, Learning, References",
    plain: "A way of telling a real signal apart from noise: if the confidence interval around a number like beta or a factor loading includes zero, you can't be confident the true exposure isn't zero.",
    technical:
      "Standard OLS-regression diagnostics (t-statistic, two-sided p-value, 95% confidence interval) computed from the HAC standard error above for every coefficient this project reports.",
  },
]

const portfolioEntries: GlossaryEntry[] = [
  {
    term: "Efficient frontier",
    where: "Overview, Results §2, Learning, References",
    plain: "The best return historically achievable, for each level of risk, by re-weighting the exact holdings you entered &mdash; no new stocks, no leverage, no shorting.",
    technical:
      "The set of long-only portfolios minimizing <code>w<sup>T</sup>&Sigma;w</code> for each target <code>w<sup>T</sup>&mu;</code>, solved point-by-point via SLSQP since long-only mean-variance optimization has no closed form (Markowitz, 1952).",
  },
  {
    term: "Markowitz mean-variance optimization",
    where: "Overview, References, Real World / Corporate Applications",
    plain: "The math behind &ldquo;what's the best possible return for a given amount of risk,&rdquo; using how your holdings have historically moved together.",
    technical:
      "Models portfolio return as <code>w<sup>T</sup>&mu;</code> and variance as <code>w<sup>T</sup>&Sigma;w</code>, then solves for the efficient set, the GMV portfolio, and the tangency (max-Sharpe) portfolio (Markowitz, 1952). &mu; and &Sigma; are annualized by linear scaling, not compounding &mdash; see Annualization convention below.",
  },
  {
    term: "Covariance matrix (&Sigma;)",
    where: "Results §2, References",
    plain: "A table of how every pair of your holdings has historically moved together &mdash; not just how volatile each one is on its own, but whether they tend to rise and fall together or offset each other.",
    technical:
      "The annualized covariance matrix of holding returns; portfolio variance is <code>w<sup>T</sup>&Sigma;w</code>. In the Markowitz framework, all diversification benefit comes from &Sigma;'s off-diagonal (co-movement) terms, not from any single holding's own variance.",
  },
  {
    term: "Covariance regularization (eigenvalue clipping)",
    where: "Results §2 (warning banner), Learning, References",
    plain: "A safety net for when a holding set is too small, too correlated, or has too little data to produce a trustworthy risk picture &mdash; the app flags it rather than silently producing a broken frontier.",
    technical:
      "If the sample covariance matrix's condition number exceeds 1e8 or it isn't positive-semi-definite, negative/near-zero eigenvalues are floored to 1e-6 &times; the largest eigenvalue and the matrix reconstructed &mdash; a standard &ldquo;nearest PSD matrix&rdquo; fix (decision 0003). Surfaced as &ldquo;covariance regularized&rdquo; on the Results tab whenever it triggers.",
  },
  {
    term: "Long-only constraint",
    where: "Results §2, Learning, References",
    plain: "The frontier never assumes you could short a stock or borrow money to invest more than you have &mdash; only re-weighting among positive holdings of what you actually entered.",
    technical:
      "<code>w<sub>i</sub> &ge; 0</code> for all holdings in the efficient-frontier optimization; this project's default (see decision 0003), reflecting how retail/small-RIA portfolios are actually held.",
  },
  {
    term: "Global minimum-variance (GMV) portfolio",
    where: "Results §2, Learning",
    plain: "Of every way you could re-weight your exact holdings, the single weighting that historically would have been the calmest (lowest volatility) &mdash; regardless of return.",
    technical:
      "The frontier point with minimum <code>w<sup>T</sup>&Sigma;w</code> subject to the long-only, sum-to-one constraints; the leftmost point on the plotted frontier.",
  },
  {
    term: "Tangency / max-Sharpe portfolio",
    where: "Results §2, Learning",
    plain: "Of every way you could re-weight your exact holdings, the single weighting with the best return per unit of risk.",
    technical:
      "The frontier point maximizing <code>S = (R<sub>p</sub> &minus; R<sub>f</sub>) / &sigma;<sub>p</sub></code> subject to the same long-only constraints as the rest of the frontier.",
  },
  {
    term: "Sharpe ratio",
    where: "Results §2, Learning, References",
    plain: "Return earned per unit of risk taken, after subtracting the risk-free rate &mdash; higher is better compensated risk-taking.",
    technical: "<code>S = (R<sub>p</sub> &minus; R<sub>f</sub>) / &sigma;<sub>p</sub></code> (Sharpe, 1966/1994).",
  },
  {
    term: "Annualization convention (compounding vs. linear scaling)",
    where: "Results §1, §2 &amp; §3, References",
    plain: "Two different, both-correct ways this app turns a per-day (or per-month) number into a per-year one &mdash; CAPM/Fama-French alpha uses one, the frontier's inputs use the other, on purpose, not by accident.",
    technical:
      "Alpha is annualized by compounding, <code>(1 + &alpha;)<sup>periods/yr</sup> &minus; 1</code>, matching how a return actually accrues. The frontier's &mu; and &Sigma; are annualized by <em>linear</em> scaling (periodic &times; periods/year), the textbook i.i.d.-returns convention mean-variance optimization assumes by construction. The two aren't interchangeable &mdash; mixing them would break both the return-attribution identity and the frontier's own assumptions (decision 0003).",
  },
]

const attributionEntries: GlossaryEntry[] = [
  {
    term: "Return attribution",
    where: "Results §3, Learning, References",
    plain: "Splitting your portfolio's average return into pieces &mdash; how much came from market exposure, how much from each style tilt, and how much is unexplained (&ldquo;alpha&rdquo;).",
    technical:
      "An exact OLS identity, not an approximation: because the Fama-French fit includes an intercept, the fitted residual has zero mean over the sample, so <code>mean(R<sub>p</sub> &minus; R<sub>f</sub>) = &alpha; + &Sigma;<sub>i</sub> &beta;<sub>i</sub>&middot;mean(factor<sub>i</sub>)</code> reproduces the realized mean exactly.",
  },
  {
    term: "Risk attribution",
    where: "Results §3, Learning, References",
    plain: "Splitting your portfolio's risk into the share explained by broad factors versus the share specific to your individual holdings.",
    technical:
      "factor-explained share = R&sup2; (clipped to [0,1] for display), idiosyncratic share = 1 &minus; R&sup2;, of the fitted factor model.",
  },
  {
    term: "Idiosyncratic risk",
    where: "Results §3, Learning",
    plain: "The part of your portfolio's risk that's specific to the individual companies you hold, not shared with the market or with any named style factor.",
    technical:
      "<code>1 &minus; R&sup2;</code> of the fitted factor model &mdash; the residual variance share unexplained by market/size/value/profitability/investment exposure.",
  },
]

export const GLOSSARY_GROUPS: GlossaryGroup[] = [
  {
    title: "Factor models &amp; regression",
    note: "How a return gets explained: CAPM's single market factor, Fama-French's style factors, and the statistical diagnostics that separate a real exposure from noise.",
    entries: factorEntries,
  },
  {
    title: "Portfolio theory &amp; optimization",
    note: "How the efficient frontier is built and read: the math behind &ldquo;best return for a given risk,&rdquo; and the conventions/safeguards behind it.",
    entries: portfolioEntries,
  },
  {
    title: "Attribution",
    note: "Putting the exposures back together: exactly how much of your realized return and risk each piece above actually accounts for.",
    entries: attributionEntries,
  },
]
