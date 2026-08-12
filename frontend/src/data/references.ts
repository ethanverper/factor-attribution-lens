// Ported verbatim from the removed `app/dashboard/shell.py::render_references_section`
// (Phase 8/9d). HTML notation (`<sub>/<sup>`, entities) is kept and rendered via
// `dangerouslySetInnerHTML` — static, trusted, hand-authored copy.

export interface Formula {
  label: string
  eq: string
}

export interface ReferenceCard {
  tag: string
  title: string
  what: string
  formulas: Formula[]
  legend: string
  note: string
  source: string
}

export const REFERENCE_CARDS: ReferenceCard[] = [
  {
    tag: "app/models/capm.py",
    title: "CAPM &mdash; single-factor market beta",
    what: "Regresses the portfolio's excess return on the chosen benchmark's excess return over the aligned sample. &beta; is the reported market beta; &alpha; is reported both as the raw periodic OLS intercept and, annualized by compounding, as &ldquo;CAPM alpha (annualized)&rdquo; on the Results tab.",
    formulas: [
      { label: "Regression", eq: "R<sub>p,t</sub> &minus; R<sub>f,t</sub> = &alpha; + &beta;(R<sub>m,t</sub> &minus; R<sub>f,t</sub>) + &epsilon;<sub>t</sub>" },
    ],
    legend:
      "<code>R<sub>p,t</sub></code> portfolio return at t &middot; <code>R<sub>f,t</sub></code> risk-free rate (Ken French Data Library) &middot; <code>R<sub>m,t</sub></code> benchmark return &middot; <code>&beta;</code> market beta &middot; <code>&alpha;</code> intercept (excess return unexplained by the market).",
    note: "Fit by OLS with an intercept, standard errors via Newey-West HAC (see the Regression diagnostics card below) &mdash; not classical OLS SEs. &alpha; is annualized as (1 + &alpha;)<sup>periods/yr</sup> &minus; 1 (compounding convention; see decision 0003).",
    source:
      "<strong>Source:</strong> Sharpe, W.F. (1964). &ldquo;Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk.&rdquo; <em>Journal of Finance</em>, 19(3), 425&ndash;442. Independently derived in Lintner, J. (1965) and Mossin, J. (1966).",
  },
  {
    tag: "app/models/fama_french.py",
    title: "Fama-French 3-/5-factor model",
    what: "Extends CAPM with additional priced return factors, fit the same way (OLS, HAC standard errors) on the portfolio's excess return. 3-factor is this app's default; 5-factor is supported end-to-end whenever selected on the Inputs tab. Factor return series come from Kenneth French's Data Library, not OpenBB (see decision 0002).",
    formulas: [
      { label: "3-factor", eq: "R<sub>p,t</sub> &minus; R<sub>f,t</sub> = &alpha; + &beta;<sub>1</sub>Mkt-RF<sub>t</sub> + &beta;<sub>2</sub>SMB<sub>t</sub> + &beta;<sub>3</sub>HML<sub>t</sub> + &epsilon;<sub>t</sub>" },
      { label: "5-factor", eq: "R<sub>p,t</sub> &minus; R<sub>f,t</sub> = &alpha; + &beta;<sub>1</sub>Mkt-RF<sub>t</sub> + &beta;<sub>2</sub>SMB<sub>t</sub> + &beta;<sub>3</sub>HML<sub>t</sub> + &beta;<sub>4</sub>RMW<sub>t</sub> + &beta;<sub>5</sub>CMA<sub>t</sub> + &epsilon;<sub>t</sub>" },
    ],
    legend:
      "<code>SMB</code> Small Minus Big (size) &middot; <code>HML</code> High Minus Low (value, book-to-market) &middot; <code>RMW</code> Robust Minus Weak (profitability) &middot; <code>CMA</code> Conservative Minus Aggressive (investment). Each is itself a spread portfolio return, not a raw price series.",
    note: "F-statistic and both R&sup2; and adjusted R&sup2; are reported alongside the loadings on the Results tab so overall model fit is visible, not just per-coefficient significance.",
    source:
      "<strong>Source:</strong> Fama, E.F. &amp; French, K.R. (1993). &ldquo;Common Risk Factors in the Returns on Stocks and Bonds.&rdquo; <em>Journal of Financial Economics</em>, 33(1), 3&ndash;56. 5-factor extension: Fama, E.F. &amp; French, K.R. (2015). &ldquo;A Five-Factor Asset Pricing Model.&rdquo; <em>Journal of Financial Economics</em>, 116(1), 1&ndash;22.",
  },
  {
    tag: "app/models/_regression.py",
    title: "Regression diagnostics &mdash; Newey-West HAC standard errors",
    what: "Every coefficient reported by the CAPM and Fama-French regressions above (standard error, t-stat, p-value, 95% CI) uses this correction, not classical OLS standard errors &mdash; daily and monthly equity returns are routinely heteroskedastic and mildly autocorrelated, which classical SEs understate.",
    formulas: [{ label: "Newey-West plug-in bandwidth", eq: "L = floor(4 &middot; (n / 100)<sup>2/9</sup>)" }],
    legend:
      "<code>n</code> number of aligned observations in the regression sample &middot; <code>L</code> number of autocorrelation lags included in the HAC covariance estimate.",
    note: "Reported on every Results page as &ldquo;Standard errors: HAC (Newey-West)&rdquo; so the convention producing a given t-stat/CI is never left implicit.",
    source:
      "<strong>Source:</strong> Newey, W.K. &amp; West, K.D. (1987). &ldquo;A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix.&rdquo; <em>Econometrica</em>, 55(3), 703&ndash;708. Plug-in bandwidth rule: Newey, W.K. &amp; West, K.D. (1994). &ldquo;Automatic Lag Selection in Covariance Matrix Estimation.&rdquo; <em>Review of Economic Studies</em>, 61(4), 631&ndash;653.",
  },
  {
    tag: "app/models/optimization.py",
    title: "Markowitz mean-variance efficient frontier",
    what: "For the entered holdings, models portfolio expected return and variance as a function of weights, then solves for the long-only efficient frontier, the global minimum-variance portfolio, and the max-Sharpe (tangency) portfolio &mdash; and locates the as-entered portfolio against all three. This is a positioning view, not a rebalancing recommendation.",
    formulas: [
      { label: "Portfolio return", eq: "R<sub>p</sub> = w<sup>T</sup>&mu;" },
      { label: "Portfolio variance", eq: "&sigma;<sub>p</sub><sup>2</sup> = w<sup>T</sup>&Sigma;w" },
      { label: "Efficient point (long-only)", eq: "min<sub>w</sub> w<sup>T</sup>&Sigma;w &nbsp; s.t. &nbsp; w<sup>T</sup>&mu; = target, &nbsp; &Sigma;w<sub>i</sub> = 1, &nbsp; w<sub>i</sub> &ge; 0" },
      { label: "Max Sharpe (tangency)", eq: "max<sub>w</sub> (w<sup>T</sup>&mu; &minus; R<sub>f</sub>) / &radic;(w<sup>T</sup>&Sigma;w) &nbsp; s.t. &nbsp; same constraints" },
      { label: "Sharpe ratio", eq: "S = (R<sub>p</sub> &minus; R<sub>f</sub>) / &sigma;<sub>p</sub>" },
    ],
    legend:
      "<code>w</code> holding weight vector &middot; <code>&mu;</code> vector of expected (annualized) holding returns &middot; <code>&Sigma;</code> annualized covariance matrix of holding returns &middot; <code>R<sub>f</sub></code> risk-free rate.",
    note: "&mu; and &Sigma; are annualized by <em>linear scaling</em> (periodic mean/covariance &times; periods per year) &mdash; the textbook i.i.d.-returns convention mean-variance optimization assumes by construction, and deliberately different from CAPM/Fama-French alpha's compounding convention above (decision 0003). Long-only (<code>w<sub>i</sub> &ge; 0</code>) is this app's default, reflecting how retail/small-RIA holdings are actually held; each frontier point is solved numerically via SLSQP since long-only mean-variance optimization has no closed form. If the sample covariance matrix is ill-conditioned or non-PSD, it is regularized by eigenvalue clipping before solving &mdash; the Results tab flags this explicitly (&ldquo;covariance regularized&rdquo;) whenever it happens.",
    source:
      "<strong>Source:</strong> Markowitz, H. (1952). &ldquo;Portfolio Selection.&rdquo; <em>Journal of Finance</em>, 7(1), 77&ndash;91. Sharpe ratio: Sharpe, W.F. (1966). &ldquo;Mutual Fund Performance.&rdquo; <em>Journal of Business</em>, 39(1), 119&ndash;138 (reframed as &ldquo;The Sharpe Ratio,&rdquo; <em>Journal of Portfolio Management</em>, 1994).",
  },
  {
    tag: "app/api/attribution.py",
    title: "Return &amp; risk attribution",
    what: "Not a separate model &mdash; an exact algebraic decomposition of the Fama-French regression above, evaluated at the sample mean. Because OLS with an intercept guarantees the fitted residual has zero mean over the regression sample, splitting the realized mean excess return into &alpha; plus each factor's own contribution reproduces the realized total exactly, not approximately.",
    formulas: [
      { label: "Return attribution (exact identity)", eq: "mean(R<sub>p</sub> &minus; R<sub>f</sub>) = &alpha; + &Sigma;<sub>i</sub> &beta;<sub>i</sub> &middot; mean(factor<sub>i</sub>)" },
      { label: "Risk attribution", eq: "factor-explained share = R&sup2; &nbsp;&nbsp; idiosyncratic share = 1 &minus; R&sup2;" },
    ],
    legend:
      "<code>&beta;<sub>i</sub></code> the fitted loading on factor <em>i</em> &middot; <code>mean(factor<sub>i</sub>)</code> that factor's own realized mean return over the same aligned window.",
    note: "Contributions are shown per-period (not re-annualized), since annualizing pieces under two different conventions and summing them would no longer reconcile to the realized total the way the per-period identity above does exactly &mdash; see decision 0003.",
    source:
      "<strong>Source:</strong> Direct algebraic consequence of the OLS fit above (standard regression identity, not a separately published result) &mdash; see the derivation in <code>app/api/attribution.py</code>'s module docstring.",
  },
  {
    tag: "app/api/tickers.py",
    title: "Ticker &amp; benchmark universe &mdash; curated S&amp;P 500 snapshot",
    what: "Backs the Holdings and Benchmark selection controls on the Inputs tab &mdash; the constrained-input control <code>docs/project-standards.md</code> rule 2 requires for anything that must resolve to real, fetchable data. Equity holdings are drawn from a curated S&amp;P 500 constituent snapshot; the benchmark field is a separate, small set of major index/ETF proxies (<code>^GSPC</code>, <code>^DJI</code>, <code>^IXIC</code>, <code>^NDX</code>, <code>^RUT</code>, <code>VTI</code>). This is not a formula card like the others above &mdash; it documents the provenance of a curated dataset shown to the user, per rule 7.",
    formulas: [
      { label: "Coverage", eq: "496 equities + 6 benchmark proxies, captured 2026-08-10" },
      { label: "Symbol convention", eq: "BRK.B &rarr; BRK-B (dot &rarr; yfinance dash, at entry)" },
    ],
    legend:
      "This card documents rule 7 (<code>docs/project-standards.md</code>) &mdash; cite the source of any curated/constrained option set shown to the user. A brief version of this note also appears directly on the Inputs tab, next to the selector, per rule 7's &ldquo;near the input&rdquo; half.",
    note: "Share-class tickers are normalized to <code>yfinance</code> dash form (not the source dataset's dot form) at data-entry time, so every entry is directly usable by Phase 1's unmodified price-fetch path with no translation layer needed downstream. Enforced at two layers: the frontend's submitted field is only ever set by selecting a real option from this list (never raw typed text), and <code>app/api/routes.py</code> independently re-validates every submitted symbol/benchmark against <code>tickers.is_valid_ticker</code>/<code>is_valid_benchmark</code> server-side before any analysis runs. <strong>Known limitation:</strong> this is a static snapshot, not a live index-membership feed &mdash; it will drift from the real S&amp;P 500 roster as constituents change (several times a year), and a holding outside this list (a small-cap, an ADR, a non-US listing) cannot be entered even if it would be perfectly valid on <code>yfinance</code>/OpenBB. Refreshing it requires re-running the sourcing process by hand, not a live sync.",
    source:
      "<strong>Source:</strong> S&amp;P 500 constituent list snapshot captured 2026-08-10, sourced from a public constituents dataset mirroring the official S&amp;P Dow Jones Indices membership (the same underlying data as Wikipedia's &ldquo;List of S&amp;P 500 companies&rdquo; and the commonly-used <code>datasets/s-and-p-500-companies</code> public dataset). Benchmark proxies are standard Yahoo Finance index/ETF tickers, not a separately sourced list. Full sourcing/refresh policy: <code>docs/decisions/0005-phase7-ticker-universe.md</code>.",
  },
]

export const WORKS_CITED: string[] = [
  "Sharpe, W.F. (1964). Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk. <em>Journal of Finance</em>, 19(3), 425&ndash;442.",
  "Lintner, J. (1965). The Valuation of Risk Assets and the Selection of Risky Investments in Stock Portfolios and Capital Budgets. <em>Review of Economics and Statistics</em>, 47(1), 13&ndash;37.",
  "Markowitz, H. (1952). Portfolio Selection. <em>Journal of Finance</em>, 7(1), 77&ndash;91.",
  "Sharpe, W.F. (1966). Mutual Fund Performance. <em>Journal of Business</em>, 39(1), 119&ndash;138.",
  "Fama, E.F. &amp; French, K.R. (1993). Common Risk Factors in the Returns on Stocks and Bonds. <em>Journal of Financial Economics</em>, 33(1), 3&ndash;56.",
  "Fama, E.F. &amp; French, K.R. (2015). A Five-Factor Asset Pricing Model. <em>Journal of Financial Economics</em>, 116(1), 1&ndash;22.",
  "Newey, W.K. &amp; West, K.D. (1987). A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix. <em>Econometrica</em>, 55(3), 703&ndash;708.",
  "Newey, W.K. &amp; West, K.D. (1994). Automatic Lag Selection in Covariance Matrix Estimation. <em>Review of Economic Studies</em>, 61(4), 631&ndash;653.",
]
