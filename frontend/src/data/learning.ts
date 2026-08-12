// Ported from the removed `app/dashboard/shell.py::render_learning_section`
// (Phase 9/9e), restructured into a curriculum per decision 0020 (Phase 10l)
// -- a numbered `id`, a plain-text `teaser` (the collapsed-accordion preview,
// Udemy's own lesson-list pattern), and diagrams as separate React
// components (`src/components/diagrams/`), referenced here by id.
//
// Content decomposed per decision 0021 (Phase 10n, `educator`) into five
// primitives per register -- lead, bullets, callout, pull-quote, plus one
// worked example shared across both registers -- replacing the previous
// plain/technical paragraph pairs. Worked examples use real, live-verified
// numbers (see decision 0021's "How the worked-example numbers were
// obtained"), not invented illustrative ones.

export interface LearningRegister {
  lead: string
  bullets: string[]
  callout: { tone: "definition" | "caveat"; text: string } | null
  pullQuote: string
  /** Optional-depth citation only (decision 0021 §3) -- never a
   * comprehension-critical caveat, those render as `callout` instead. */
  footnote?: string
}

export interface LearningCard {
  id: string
  tag: string
  title: string
  teaser: string
  plain: LearningRegister
  technical: LearningRegister
  workedExample: string
  xrefs: { to: string; label: string }[]
  diagram: "capm" | "ci" | "frontier" | null
}

export const LEARNING_CARDS: LearningCard[] = [
  {
    id: "beta",
    tag: "Results · 1. Factor exposure",
    title: "CAPM beta &mdash; your market sensitivity",
    teaser: "Beta answers one question: when the market moves 1%, how much does your portfolio tend to move?",
    plain: {
      lead: "Beta answers one question: when the market moves 1%, how much does your portfolio tend to move?",
      bullets: [
        "A beta above 1.0 means the portfolio has historically swung harder than the benchmark in both directions &mdash; bigger gains when the market's up, bigger losses when it's down.",
        "A beta below 1.0 means the opposite &mdash; the portfolio has historically been calmer than the market.",
      ],
      callout: {
        tone: "definition",
        text: "Beta alone doesn't say whether that's good or bad. It only describes how much of the portfolio's risk is simply &ldquo;the market, amplified or dampened&rdquo; &mdash; not whether that exposure is well-compensated.",
      },
      pullQuote: "Beta measures amplification of market moves &mdash; not whether that's a good bet.",
    },
    technical: {
      lead: "&beta; is the slope coefficient from regressing the portfolio's excess return on the benchmark's excess return &mdash; a point estimate with real sampling uncertainty, not a fixed fact.",
      bullets: [
        "&beta; (beta) &mdash; the slope: how much the portfolio's excess return has moved per 1-unit move in the benchmark's excess return.",
        "&alpha; (alpha) &mdash; the regression intercept: the average excess return not explained by market exposure at all.",
        "R&sup2; &mdash; the share of the portfolio's return variance the single market factor explains on its own.",
      ],
      callout: {
        tone: "caveat",
        text: "Two portfolios can share the exact same beta estimate and mean very different things: a beta of 1.20 with a 95% CI of <code>[0.4, 2.0]</code> is a far weaker claim than the same 1.20 with a CI of <code>[1.1, 1.3]</code> &mdash; width is precision, not the estimate itself.",
      },
      pullQuote: "A low CAPM R&sup2; isn't a data problem &mdash; it's the finding: a one-factor market story is incomplete for this portfolio.",
      footnote: "See the exact regression specification and standard-error convention in decision 0003.",
    },
    workedExample:
      "The app's own sample portfolio &mdash; AAPL 40% / MSFT 30% / GOOGL 20% / AMZN 10% vs. the S&amp;P 500, trailing 12 months, daily &mdash; measures beta 1.00, 95% CI [0.88, 1.12], t = 16.85, p &lt; 0.001, R&sup2; = 50.3%. The point estimate says this portfolio moved almost exactly one-for-one with the market, and the CI is narrow enough (width 0.23) to trust that read, not just treat it as a rough guess.",
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
    plain: {
      lead: "CAPM only asks &ldquo;how much market.&rdquo; Fama-French asks a follow-up: what kind of market exposure.",
      bullets: [
        "Size (SMB) &mdash; tilted toward small companies or large ones?",
        "Value (HML) &mdash; cheap-relative-to-book (&ldquo;value&rdquo;) stocks, or expensive-growth ones?",
        "Profitability (RMW) &mdash; highly profitable companies, or not?",
        "Investment (CMA) &mdash; conservatively-run companies, or aggressively-expanding ones?",
      ],
      callout: {
        tone: "definition",
        text: "Reading the sign: a positive Size (SMB) loading means the holdings behave more like small-cap stocks than large-cap; a positive Value (HML) loading means more like cheap value stocks than expensive growth &mdash; the same logic extends to Profitability (RMW) and Investment (CMA).",
      },
      pullQuote:
        "None of this is prescriptive &mdash; it's a description of the exposures already present, in the same language professional factor investors use to describe theirs.",
    },
    technical: {
      lead: "Each &beta;<sub>i</sub> is a partial-regression coefficient &mdash; the portfolio's sensitivity to one factor's spread-portfolio return, holding the other factors fixed.",
      bullets: [
        "Significance test: a loading only counts as a real exposure &mdash; not noise &mdash; when its 95% CI excludes zero (equivalently, p &lt; 0.05).",
        "Where to check it: the Results chart plots that CI as a whisker under every bar; the table view gives the exact standard error, t-stat, and p-value per factor.",
        "Fit comparison: Fama-French R&sup2;, adjusted R&sup2;, and the overall F-statistic together say how much better this multi-factor story fits than CAPM's single factor did.",
      ],
      callout: {
        tone: "definition",
        text: "&ldquo;95% CI excludes zero&rdquo; and &ldquo;p &lt; 0.05&rdquo; are the same significance test stated two different ways &mdash; this app always shows the CI directly, not just the p-value, so the range is visible, not just a pass/fail.",
      },
      pullQuote:
        "A materially higher Fama-French R&sup2; than CAPM R&sup2; means style tilts &mdash; size, value, profitability, investment &mdash; not just raw market exposure, are doing real explanatory work for this portfolio.",
    },
    workedExample:
      "Sample portfolio: CAPM R&sup2; = 50.3%; Fama-French (3-factor) R&sup2; = 55.7% (adjusted 55.1%). Loadings: mkt_rf 0.88 (CI [0.72, 1.03], significant), smb &minus;0.13 (CI [&minus;0.32, 0.07], not significant &mdash; the interval straddles zero), hml &minus;0.39 (CI [&minus;0.58, &minus;0.21], significant &mdash; a statistically real growth tilt, since a negative HML loading means behaving more like expensive-growth stocks than cheap-value ones). Only one of the two non-market factors clears the 95% bar here &mdash; growth-vs-value positioning is this portfolio's one statistically reliable style signal beyond plain market exposure.",
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
    plain: {
      lead: "Given exactly the holdings entered &mdash; nothing added, nothing swapped &mdash; there's a best-achievable return for every level of risk, just by re-weighting those same holdings.",
      bullets: [
        "Long-only &mdash; every holding stays at zero or positive weight; nothing is shorted.",
        "No leverage &mdash; weights sum to exactly the money entered, not more.",
        "Same names only &mdash; the frontier never swaps in a holding outside what was entered.",
      ],
      callout: {
        tone: "caveat",
        text: "Why &ldquo;long-only&rdquo; matters: this is a narrower, more realistic object than the textbook unconstrained frontier &mdash; it's strictly the best return achievable by re-weighting exactly the holdings already picked, not by adding leverage or shorting anything.",
      },
      pullQuote:
        "A mirror, not an instruction: if the as-entered dot sits below the line, a different weighting of these same names could historically have earned more for that same risk &mdash; not a suggestion to hold different stocks, and not a signal to act on.",
    },
    technical: {
      lead: "The frontier solves, for each target return, the minimum-variance weighting: <code>min<sub>w</sub> w<sup>T</sup>&Sigma;w</code> subject to <code>w<sup>T</sup>&mu; = target</code>, <code>&Sigma;w<sub>i</sub> = 1</code>, <code>w<sub>i</sub> &ge; 0</code> &mdash; long-only by default.",
      bullets: [
        "Global minimum-variance portfolio &mdash; the lowest possible volatility on this frontier, regardless of return.",
        "Max-Sharpe / tangency portfolio &mdash; the point maximizing return per unit of risk, <code>S = (R<sub>p</sub> &minus; R<sub>f</sub>) / &sigma;<sub>p</sub></code>.",
      ],
      callout: {
        tone: "caveat",
        text: "A flagged &ldquo;covariance regularized&rdquo; warning means the holding set's correlation structure was numerically unstable (few holdings, few observations, near-duplicate positions) &mdash; read the frontier as directional, not exact, when this fires.",
      },
      pullQuote:
        "&ldquo;Return gap at matched volatility&rdquo; is the single cleanest number for how far below the achievable set the as-entered weights currently sit.",
      footnote:
        "Retail and small-RIA holdings are actually held long, so long-only is this app's default &mdash; see decision 0003 for the rationale and how to get the unconstrained textbook frontier instead.",
    },
    workedExample:
      "Sample portfolio: 18.2% annualized volatility, 17.6% realized annualized return, Sharpe 0.74. The modeled frontier's return at that same 18.2% volatility is 20.1% &mdash; a 2.45-percentage-point gap. Covariance condition number 3.65, well below the regularization trigger, so this read is exact, not regularized. Historically, some other long-only re-weighting of the same four holdings could have earned about 2.5 points more return for the same risk &mdash; not a suggestion to reweight, just a description of the historical relationship among those four holdings.",
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
    plain: {
      lead: "The three views above are exposures; this one is accounting.",
      bullets: [
        "Return split: average per-period return divides exactly into market exposure, plus style tilts (size, value, profitability, investment), plus alpha (unexplained).",
        "Risk split: return variance divides into factor-explained (market and style tilts together) versus idiosyncratic (specific to the individual names held, not shared with the market or the style tilts).",
      ],
      callout: {
        tone: "definition",
        text: "Alpha isn't automatically &ldquo;skill.&rdquo; It's simply whatever the return split can't attribute to market or style-factor exposure &mdash; that could be real stock-picking, or it could just be noise in this particular sample window.",
      },
      pullQuote:
        "Mostly idiosyncratic risk is a bet on specific companies. Mostly factor risk is, whether intended or not, mostly a bet on the market and a couple of style tilts.",
    },
    technical: {
      lead: "Return attribution is an exact algebraic identity, not an approximation.",
      bullets: [
        "The Fama-French OLS fit includes an intercept, so the fitted residual has zero mean over the regression sample &mdash; that's what makes this an identity, not an approximation.",
        "Risk attribution needs no extra computation: it's just R&sup2; (factor-explained share) and 1 &minus; R&sup2; (idiosyncratic share), already produced by the same regression.",
      ],
      callout: {
        tone: "caveat",
        text: "Contributions are shown per-period, not re-annualized &mdash; CAPM/Fama-French alpha and the frontier's inputs use two deliberately different annualization conventions (compounding vs. linear scaling, see decision 0003), so summing already-annualized pieces from different conventions would silently break the identity above.",
      },
      pullQuote: "mean(R<sub>p</sub> &minus; R<sub>f</sub>) = &alpha; + &Sigma;<sub>i</sub> &beta;<sub>i</sub> &middot; mean(factor<sub>i</sub>)",
      footnote: "Full derivation: see the module docstring in <code>app/api/attribution.py</code>.",
    },
    workedExample:
      "Sample portfolio, daily: alpha contributes +2.95 bps/day, market (Mkt-RF) +5.82 bps/day, Size (SMB) &minus;0.34 bps/day, Value (HML) &minus;3.06 bps/day &mdash; summing to +5.38 bps/day, matching the portfolio's realized mean daily excess return exactly, as the identity guarantees. Risk side: 55.7% of this portfolio's return variance is explained by the three factors together; the remaining 44.3% is idiosyncratic &mdash; specific to holding exactly AAPL/MSFT/GOOGL/AMZN rather than the market or style tilts they share.",
    xrefs: [
      { to: "/references", label: "See the exact identity" },
      { to: "/results", label: "See your attribution" },
    ],
    diagram: null,
  },
]

export const LEARNING_MACRO_TAKEAWAY =
  "Macro takeaway: these four views are one story told from four angles &mdash; how much market you carry (CAPM), what <em>kind</em> of market exposure it is (Fama-French), whether you're being compensated efficiently for the risk in your specific holdings (the frontier), and how those pieces actually add up to your realized return and risk (attribution). None of it is advice about what to buy, sell, or hold &mdash; it's a transparent account of exposures you already have."
