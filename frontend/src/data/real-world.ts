// Ported from the removed `app/dashboard/shell.py::render_real_world_section`
// (Phase 9), restructured per decision 0017 §5 into a pull-quote/stat-callout
// pattern, then decomposed per decision 0022 (Phase 10n, `brand-creative`)
// into lead / bullets / pull-quote / callout primitives, replacing the
// previous two-paragraph prose blocks per card.

export interface RealWorldCard {
  title: string
  stat: string
  statLabel: string
  tags: string[]
  lead: string // one sentence, the "so what," HTML-safe
  bulletsIntro?: string // short mono label preceding the bullet list
  bullets: string[] // enumerable points, HTML-safe
  // `quote.text` renders via `dangerouslySetInnerHTML` (HTML-safe), but
  // `quote.attribution` is interpolated as plain JSX text by `Highlight`
  // (same convention as `stat`/`statLabel` below) -- literal Unicode
  // characters only, no HTML entities, or they'll render undecoded.
  quote: { text: string; attribution?: string }
  callout?: { variant: "note" | "caveat"; label?: string; text: string }
}

export const REAL_WORLD_CARDS: RealWorldCard[] = [
  {
    title: "Institutional factor-risk desks",
    // Written as the literal Unicode character, not an HTML entity -- `stat`/
    // `statLabel` render as plain JSX text (decision 0022's bug fix), so an
    // entity here would render literally instead of decoding.
    stat: "Barra / Axioma",
    statLabel: "the direct commercial ancestor of this project",
    tags: ["Multi-factor risk models", "Barra / Axioma / MSCI", "Risk decomposition"],
    lead: "Large asset managers and hedge funds run this exact kind of factor decomposition through commercial multi-factor risk platforms like MSCI Barra and (now Qontigo/SimCorp) Axioma &mdash; just at institutional scale, with proprietary factor sets.",
    bullets: [
      "Breaks a portfolio's exposure into named, interpretable factors, the same shape as this app's Results tab",
      "Attributes realized return and risk to those factors versus stock-specific noise",
      "Flags when a portfolio's risk concentration doesn't match the mandate it's supposed to be running against",
    ],
    quote: {
      text: "This project is scoped explicitly as &ldquo;Barra/Axioma-style factor risk tooling, just built transparent and accessible.&rdquo;",
      attribution: "— project roadmap",
    },
    callout: {
      variant: "note",
      label: "Why it's a real gap",
      text: "Barra/Axioma-class tooling is licensed to institutions at a price point and integration complexity entirely out of reach for a retail investor or a two-person RIA. The same factor-attribution logic, built open and cheap enough to run for a single portfolio, is the differentiator.",
    },
  },
  {
    title: "RIA client reporting & the advisor-tech stack",
    stat: "21,000+",
    statLabel: "funds in YCharts/Zephyr's attribution database",
    tags: ["Advisor-tech", "YCharts / Zephyr", "Explainability & suitability"],
    lead: "Small registered investment advisors don't build their own factor models &mdash; they buy reporting and proposal tooling that explains, in client-facing language, why a portfolio performed the way it did.",
    bullets: [
      "YCharts' 2026 acquisition of Zephyr added a 21,000+ fund performance-attribution database directly into its advisor platform",
      "Advyzon shipped &ldquo;Advyzon AI&rdquo; for meeting notes and next-action recommendations",
      "Both treat plain-language, defensible explanation of portfolio behavior as a core advisor-tech feature, not a nice-to-have",
    ],
    quote: {
      text: "An advisor explaining why a client's account moved the way it did &mdash; with statistical diagnostics available if the client's own due diligence goes that deep.",
      attribution: "What this project is built for",
    },
    callout: {
      variant: "note",
      label: "How this project fits",
      text: "Factor Attribution Lens pairs the exact math (References &amp; Formulas) with a plain-language read (Learning) &mdash; the same dual-register explanation an advisor gives a client, just self-serve.",
    },
  },
  {
    title: "Wealthtech optimization & automated rebalancing",
    // Unicode arrow, not `&rarr;` -- see the note on card 1 above.
    stat: "14% → 30%",
    statLabel: "wealth managers on one integrated platform, 2020–2024",
    tags: ["Robo-advisor engines", "Platform consolidation", "Mean-variance optimization"],
    lead: "Robo-advisor &ldquo;smart rebalance&rdquo; features (the kind Betterment- and Wealthfront-style platforms market as automated portfolio management) run mean-variance optimization internally &mdash; conceptually the same long-only Markowitz solve this project's <code>optimization.py</code> implements &mdash; just hidden behind a single button.",
    bulletsIntro: "What this project keeps visible",
    bullets: [
      "The efficient frontier itself, not just an &ldquo;optimize&rdquo; action",
      "The global minimum-variance and tangency (max-Sharpe) portfolios",
      "The exact gap between your holdings and the efficient set",
    ],
    quote: {
      text: "The share of U.S. wealth managers on one integrated investment platform rose from 14% (2020) to 30% (2024), and kept climbing through 2026 &mdash; automated rebalancing and AI-driven personalization cited as the differentiators.",
      attribution: "Platform-consolidation trend",
    },
    callout: {
      variant: "caveat",
      label: "Not a recommendation",
      text: "This is a transparency device, not an automated trade &mdash; Factor Attribution Lens shows the tradeoff, it doesn't rebalance anything for you.",
    },
  },
  {
    title: "Where this fits, and why it's worth evaluating the person who built it",
    stat: "Thin coverage",
    statLabel: "the source brief's own finding for this exact category",
    tags: ["Build signal", "Quant + product engineering", "Recruiting-facing"],
    lead: "General &ldquo;factor investing explained&rdquo; content is everywhere; concrete, funded products doing factor-model analytics for retail or small-team use are thin on the ground &mdash; this project's own source research brief's explicit finding.",
    bullets: [
      "Live market-data integration (OpenBB, Kenneth French's Data Library)",
      "Statistically rigorous diagnostics (Newey-West HAC standard errors, not classical OLS)",
      "A real constrained quadratic program (SLSQP) with covariance regularization for edge cases",
      "A shipped, sectioned web application with a real React/TypeScript frontend &mdash; not a notebook",
    ],
    quote: {
      text: "Read the code, the methodology decision log, and this Learning section as direct evidence of the work &mdash; not a claim about it.",
      attribution: "— Ethan Verduzco, builder",
    },
    callout: {
      variant: "note",
      label: "See the evidence",
      text: "Full stack: Tools &amp; Technologies. Full methodology trail: <code>docs/decisions/</code>.",
    },
  },
]

export const REAL_WORLD_SOURCE_NOTE =
  'Sources: this project\'s own roadmap ("Why this project, why this shape") and <code>docs/research/finance/2026-08-10-fintech-ai-quant-wealthtech.md</code> &mdash; see that brief\'s "Gaps / low-confidence areas" section for the explicit note that retail/small-team factor-model tooling coverage is thin, and its "Trends" section for the wealthtech-consolidation and advisor-tech figures cited above.'
