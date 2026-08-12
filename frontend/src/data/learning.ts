// Ported from the removed `app/dashboard/shell.py::render_learning_section`
// (Phase 9/9e), restructured into a curriculum per decision 0020 (Phase 10l)
// -- a numbered `id`, a plain-text `teaser` (the collapsed-accordion preview,
// Udemy's own lesson-list pattern), and `note` repurposed as footnote-marker
// content (institutional citation device, decision 0020 section 2d) rather
// than an always-visible dashed-border paragraph. Diagrams are separate React
// components (`src/components/diagrams/`), referenced here by id.

export interface LearningCard {
  id: string
  tag: string
  title: string
  teaser: string
  plain: string
  technical: string
  note: string | null
  xrefs: { to: string; label: string }[]
  diagram: "capm" | "ci" | "frontier" | null
}

export const LEARNING_CARDS: LearningCard[] = [
  {
    id: "beta",
    tag: "Results · 1. Factor exposure",
    title: "CAPM beta &mdash; your market sensitivity",
    teaser: "Beta answers one question: when the market moves 1%, how much does your portfolio tend to move?",
    plain:
      "Beta answers one question: when the market moves 1%, how much does your portfolio tend to move? A beta of 1.20 means your portfolio has historically swung about 20% harder than the benchmark in both directions &mdash; bigger gains in up markets, bigger losses in down markets. A beta of 0.60 means the opposite: your portfolio has historically been noticeably calmer than the market. Beta on its own doesn't say whether that's good or bad &mdash; it says how much of your risk is simply &ldquo;the market, amplified or dampened,&rdquo; versus something else.",
    technical:
      "&beta; is the slope coefficient from regressing your portfolio's excess return on the benchmark's excess return (see the CAPM regression in References &amp; Formulas). It is a point estimate with sampling uncertainty, which is why the Results tab always shows it with a 95% confidence interval, a t-stat, and a p-value rather than the bare number &mdash; a beta of 1.20 with a CI of <code>[0.4, 2.0]</code> is a much weaker claim than the same 1.20 with a CI of <code>[1.1, 1.3]</code>. <code>&alpha;</code> (the regression intercept) is the average excess return <em>not</em> explained by market exposure at all; <code>R&sup2;</code> is the share of your portfolio's return variance the single market factor explains &mdash; a low CAPM R&sup2; is itself informative: it means a one-factor market story is incomplete for this portfolio, which is exactly what the Fama-French model below is for.",
    note: null,
    xrefs: [
      { to: "/references", label: "See the exact regression" },
      { to: "/results", label: "See your beta" },
    ],
    diagram: "capm",
  },
  {
    id: "fama_french",
    tag: "Results · 1. Factor exposure",
    title: "Fama-French loadings &mdash; what kind of stocks you actually hold",
    teaser: "CAPM only asks how much market. Fama-French asks a follow-up: what kind of market exposure.",
    plain:
      "CAPM only asks &ldquo;how much market.&rdquo; Fama-French asks a follow-up: <em>what kind</em> of market exposure &mdash; is your portfolio tilted toward small companies or large ones, cheap-relative-to-book (&ldquo;value&rdquo;) stocks or expensive-growth ones, highly profitable companies or not, conservatively-run companies or aggressively-expanding ones? Each factor loading is a lean, not a bet: a positive Size (SMB) loading means your holdings behave more like small-cap stocks than large-cap ones; a positive Value (HML) loading means they behave more like cheap value stocks than expensive growth stocks; and so on for Profitability (RMW) and Investment (CMA). None of this is prescriptive &mdash; it's a description of the exposures you already have, in the same language professional factor investors use to describe theirs.",
    technical:
      "Each &beta;<sub>i</sub> is a partial-regression coefficient: your portfolio's sensitivity to that one factor's spread-portfolio return, holding the other factors in the regression fixed. A loading is only worth reading as a real exposure &mdash; not noise &mdash; when its 95% CI excludes zero (equivalently, p &lt; 0.05); the Results tab plots the CI as a whisker under every bar for exactly this reason, and the table view gives the exact standard error, t-stat, and p-value per factor. Fama-French R&sup2; (and adjusted R&sup2;, and the overall F-statistic) tell you how much better this multi-factor story fits than CAPM's single factor did &mdash; a materially higher Fama-French R&sup2; than CAPM R&sup2; means style tilts (size/value/profitability/investment), not just raw market exposure, are doing real explanatory work for this portfolio.",
    note: null,
    xrefs: [
      { to: "/references", label: "See the exact regression" },
      { to: "/results", label: "See your loadings" },
    ],
    diagram: "ci",
  },
  {
    id: "frontier",
    tag: "Results · 2. Efficient frontier",
    title: "Frontier position &mdash; are you getting paid for the risk you're taking",
    teaser:
      "Given exactly the holdings you entered and how they've historically moved together, there's a best-achievable return for every level of risk.",
    plain:
      "Given exactly the holdings you entered (nothing added, nothing swapped out) and how they've historically moved together, there's a best-achievable return for every level of risk (volatility) &mdash; just by re-weighting the same holdings, long-only, no leverage, no shorting. That curve is the modeled efficient frontier. Your as-entered portfolio is one dot; the frontier is the outer edge of what your own holdings-set could have achieved. If your dot sits noticeably below the line, it means: at the amount of risk you're already carrying, a different weighting of the exact same names could historically have earned more return for that same risk &mdash; not a suggestion to hold different stocks, and not a signal to act on. It's a mirror, not an instruction.",
    technical:
      "The frontier solves, for each target return, <code>min<sub>w</sub> w<sup>T</sup>&Sigma;w</code> subject to <code>w<sup>T</sup>&mu; = target</code>, <code>&Sigma;w<sub>i</sub> = 1</code>, <code>w<sub>i</sub> &ge; 0</code> &mdash; long-only by default (retail/small-RIA holdings are actually held long; see decision 0003 for the rationale and for how to get the unconstrained textbook frontier instead). Two other points are marked alongside your own: the <strong>global minimum-variance</strong> portfolio (lowest possible volatility on this frontier, regardless of return) and the <strong>max-Sharpe / tangency</strong> portfolio (the point maximizing return per unit of risk, <code>S = (R<sub>p</sub> &minus; R<sub>f</sub>) / &sigma;<sub>p</sub></code>). &ldquo;Return gap at matched volatility&rdquo; is the frontier's return at your exact volatility minus your own return &mdash; the single cleanest number for how far below the achievable set your as-entered weights currently sit. A flagged &ldquo;covariance regularized&rdquo; warning means your holding set's correlation structure was numerically unstable (few holdings, few observations, near-duplicate positions) and the frontier should be read as directional, not exact.",
    note:
      "Long-only means the frontier never assumes you can short a holding or use leverage &mdash; it is strictly &ldquo;the best return achievable by re-weighting exactly the stocks you already picked,&rdquo; which is why it's a narrower, more realistic object than the textbook unconstrained frontier.",
    xrefs: [
      { to: "/references", label: "See the exact optimization" },
      { to: "/results", label: "See your frontier" },
    ],
    diagram: "frontier",
  },
  {
    id: "attribution",
    tag: "Results · 3. Return &amp; risk attribution",
    title: "Return &amp; risk attribution &mdash; putting it back together",
    teaser: "The three views above are exposures; this one is accounting.",
    plain:
      "The three views above are exposures; this one is accounting. Your portfolio's average per-period return gets split, exactly, into how much came from being exposed to the market, how much from your size/value/profitability/investment tilts, and how much is unexplained by any of that (&ldquo;alpha&rdquo; &mdash; could be stock-picking, could just be noise in this sample). Separately, your risk (return variance) gets split into how much is explained by those same broad factors versus how much is <em>idiosyncratic</em> &mdash; specific to the individual names you hold rather than the market or style tilts they share. A portfolio that's mostly idiosyncratic risk is a bet on specific companies; a portfolio that's mostly factor risk is, whether you meant it to be or not, mostly a bet on the market and a couple of style tilts.",
    technical:
      "Return attribution is an exact algebraic identity, not an approximation: because the Fama-French OLS fit includes an intercept, the fitted residual has zero mean over the regression sample, so <code>mean(R<sub>p</sub> &minus; R<sub>f</sub>) = &alpha; + &Sigma;<sub>i</sub> &beta;<sub>i</sub> &middot; mean(factor<sub>i</sub>)</code> reproduces your realized mean excess return exactly, not approximately (see the module docstring in <code>app/api/attribution.py</code> for the full derivation). Risk attribution is simply the factor model's own <code>R&sup2;</code> (factor-explained share) and <code>1 &minus; R&sup2;</code> (idiosyncratic share) &mdash; no extra computation beyond what the regression already reports.",
    note:
      "Contributions are shown per-period, not re-annualized: CAPM/Fama-French alpha and the frontier's inputs use two deliberately different annualization conventions (compounding vs. linear scaling &mdash; decision 0003), so summing already-annualized pieces from different conventions would silently break the identity above.",
    xrefs: [
      { to: "/references", label: "See the exact identity" },
      { to: "/results", label: "See your attribution" },
    ],
    diagram: null,
  },
]

export const LEARNING_MACRO_TAKEAWAY =
  "Macro takeaway: these four views are one story told from four angles &mdash; how much market you carry (CAPM), what <em>kind</em> of market exposure it is (Fama-French), whether you're being compensated efficiently for the risk in your specific holdings (the frontier), and how those pieces actually add up to your realized return and risk (attribution). None of it is advice about what to buy, sell, or hold &mdash; it's a transparent account of exposures you already have."
