// Ported from the removed `app/dashboard/shell.py::render_real_world_section`
// (Phase 9), restructured per decision 0017 §5 into a pull-quote/stat-callout
// pattern — the one real number or named fact per card pulled to the top,
// rather than a paragraph wall behind tag pills. Body copy is unchanged.

export interface RealWorldCard {
  title: string
  stat: string
  statLabel: string
  tags: string[]
  body: string[] // paragraphs, HTML-safe static copy
}

export const REAL_WORLD_CARDS: RealWorldCard[] = [
  {
    title: "Institutional factor-risk desks",
    stat: "Barra / Axioma",
    statLabel: "the direct commercial ancestor of this project",
    tags: ["Multi-factor risk models", "Barra / Axioma / MSCI", "Risk decomposition"],
    body: [
      "Large asset managers and hedge funds run exactly this kind of factor decomposition &mdash; at far greater scale and with proprietary factor sets &mdash; through commercial multi-factor risk platforms like MSCI Barra and (now Qontigo/SimCorp) Axioma. A risk desk uses this output the same way this app's Results tab is structured: break a portfolio's exposure into named, interpretable factors; attribute realized return and risk to those factors versus stock-specific noise; and flag when a portfolio's risk concentration doesn't match the mandate it's supposed to be running against. This project's roadmap says so explicitly &mdash; it is scoped as &ldquo;Barra/Axioma-style factor risk tooling, just built transparent and accessible.&rdquo;",
      "The gap this project targets is real, not invented: Barra/Axioma-class tooling is licensed to institutions at a price point and integration complexity that puts it entirely out of reach for a retail investor or a two-person RIA &mdash; the same factor-attribution logic, built open and cheaply enough to run for a single portfolio, is the differentiator.",
    ],
  },
  {
    title: "RIA client reporting & the advisor-tech stack",
    stat: "21,000+",
    statLabel: "funds in YCharts/Zephyr's attribution database",
    tags: ["Advisor-tech", "YCharts / Zephyr", "Explainability & suitability"],
    body: [
      "Small registered investment advisors don't build their own factor models &mdash; they buy reporting and proposal tooling that produces client-facing explanations of &ldquo;why did my portfolio perform this way.&rdquo; That category is actively consolidating: YCharts' 2026 acquisition of Zephyr added a 21,000+ fund performance-attribution database directly into its advisor platform, and Advyzon shipped &ldquo;Advyzon AI&rdquo; for meeting notes and next-action recommendations &mdash; both signals that plain-language, defensible explanation of portfolio behavior is treated as a core advisor-tech feature, not a nice-to-have.",
      "A transparent factor-attribution tool that shows its exact math (this project's References &amp; Formulas tab) alongside a plain-language read (this project's Learning tab) is built for exactly that client-conversation use case &mdash; an advisor explaining to a client why their account moved the way it did, with statistical diagnostics (t-stats, p-values, confidence intervals) available if the client's own due diligence goes that deep.",
    ],
  },
  {
    title: "Wealthtech optimization & automated rebalancing",
    stat: "14% &rarr; 30%",
    statLabel: "wealth managers on one integrated platform, 2020&ndash;2024",
    tags: ["Robo-advisor engines", "Platform consolidation", "Mean-variance optimization"],
    body: [
      "Robo-advisor &ldquo;smart rebalance&rdquo; features (the kind Betterment- and Wealthfront-style platforms market as automated portfolio management) run mean-variance optimization internally &mdash; conceptually the same long-only Markowitz solve this project's <code>optimization.py</code> implements, just hidden behind a single button with no visibility into the frontier, the constraints, or the tradeoff being made. The share of U.S. wealth managers consolidated onto a single integrated investment platform rose from 14% in 2020 to 30% in 2024 and continued climbing through 2026, with automated rebalancing and AI-driven personalization cited as the differentiating features driving that consolidation.",
      "This project demonstrates the same underlying optimization engine, deliberately kept visible &mdash; the frontier, the global minimum-variance point, the tangency portfolio, and the exact gap between a user's holdings and the efficient set are all shown, not abstracted behind a single &ldquo;optimize&rdquo; action.",
    ],
  },
  {
    title: "Where this fits, and why it's worth evaluating the person who built it",
    stat: "Thin coverage",
    statLabel: "the source brief's own finding for this exact category",
    tags: ["Build signal", "Quant + product engineering", "Recruiting-facing"],
    body: [
      "The research brief behind this project flags a specific, real gap: general &ldquo;factor investing explained&rdquo; pedagogy is everywhere, but concrete, funded products doing factor-model analytics for retail or small-team use are thin on the ground &mdash; institutional-grade tooling (Barra, Axioma) and consumer-grade black-box optimizers (Composer, QuantConnect) exist, with comparatively little built specifically for the transparent middle.",
      "Building this project end-to-end &mdash; live market-data integration (OpenBB, Kenneth French's Data Library), statistically rigorous regression diagnostics (Newey-West HAC standard errors, not classical OLS), a real constrained quadratic program solved numerically (SLSQP) with covariance regularization for edge cases, and a shipped, sectioned web application with a real React/TypeScript frontend, not a notebook &mdash; demonstrates the same combination of applied-quant methodology and product engineering that institutional risk desks, RIA platform vendors, and wealthtech optimization teams hire for. Any team evaluating whether to build or buy this class of capability, or evaluating a candidate for a quant-adjacent engineering role, can read this project's code, its methodology decision log (<code>docs/decisions/</code>), and this Learning section itself as direct evidence of that work, not a claim about it.",
    ],
  },
]

export const REAL_WORLD_SOURCE_NOTE =
  'Sources: this project\'s own roadmap ("Why this project, why this shape") and <code>docs/research/finance/2026-08-10-fintech-ai-quant-wealthtech.md</code> &mdash; see that brief\'s "Gaps / low-confidence areas" section for the explicit note that retail/small-team factor-model tooling coverage is thin, and its "Trends" section for the wealthtech-consolidation and advisor-tech figures cited above.'
