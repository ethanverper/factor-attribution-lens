// Ported from the removed `app/dashboard/shell.py::render_tools_section`
// (decision 0015 §2, rule 13), updated in two places for the Phase 10i
// architecture change (React/Tailwind/shadcn frontend, `app/api/`
// replacing `app/dashboard/`) — everything else is unchanged content.
import { Blocks, Braces, Server, Sigma, SquareStack } from "lucide-react"
import type { LucideIcon } from "lucide-react"

export interface ToolEntry {
  name: string
  description: string
}

export interface ToolGroup {
  title: string
  icon: LucideIcon
  items: ToolEntry[]
}

export const TOOL_GROUPS: ToolGroup[] = [
  {
    title: "Languages",
    icon: Braces,
    items: [
      {
        name: "Python 3.11",
        description:
          "the entire backend, from the OpenBB/Kenneth French data layer through the FastAPI JSON API to CAPM/Fama-French/Markowitz modeling.",
      },
      {
        name: "TypeScript",
        description:
          "the entire frontend (Phase 10i) &mdash; every component, chart, and data-fetch hook is typed against the API's own Pydantic response shapes.",
      },
    ],
  },
  {
    title: "Frameworks & libraries",
    icon: Blocks,
    items: [
      {
        name: "FastAPI",
        description:
          "the pure JSON API (<code>app/api/</code>) &mdash; holdings/benchmark analysis, the curated ticker universe, and the sample-portfolio default.",
      },
      {
        name: "Pydantic v2",
        description:
          "typed request/response schemas for holdings, weights, date ranges, and every analysis result; the layer that rejects invalid submissions before any model runs.",
      },
      {
        name: "React (Vite + TypeScript) + Tailwind CSS + shadcn/ui",
        description:
          "the frontend (Phase 10i) &mdash; a real component system and build step, replacing the original hand-rolled server-rendered/inline-SVG/vanilla-JS architecture per the team's default stack decision.",
      },
      {
        name: "Recharts",
        description:
          "the factor-loading and efficient-frontier data charts, wrapped in shadcn's <code>Chart</code> primitive &mdash; a real charting library in place of hand-drawn SVG for data (hand-drawn SVG stays only for the Learning section's conceptual diagrams).",
      },
      {
        name: "GSAP",
        description:
          "the interaction/motion layer: route-transition fades, entrance choreography on Results, count-up/bar/frontier data reveals, and the scroll-triggered Learning diagrams.",
      },
      {
        name: "uv",
        description:
          "backend dependency management and a reproducible lockfile; also the tool that made trimming the OpenBB dependency footprint from 62 packages to 3 (Phase 10e) auditable and reproducible.",
      },
    ],
  },
  {
    title: "Data & quant methods",
    icon: Sigma,
    items: [
      {
        name: "OpenBB Open Data Platform",
        description: "(yfinance provider) &mdash; live equity and benchmark price history; the real market-data backbone, not a static CSV.",
      },
      {
        name: "Kenneth French's Data Library",
        description:
          "(via pandas-datareader) &mdash; the actual Fama-French 3-/5-factor and risk-free return series, sourced directly since OpenBB's Open Data Platform doesn't carry factor series at all (a real integration finding &mdash; decision 0002).",
      },
      { name: "CAPM", description: "single-factor market-beta regression with Newey-West HAC standard errors, not a raw OLS slope." },
      {
        name: "Fama-French 3-/5-factor model",
        description: "multi-factor loadings (size, value, profitability, investment) with the same HAC-robust diagnostics.",
      },
      {
        name: "statsmodels",
        description:
          "the OLS engine underneath both, configured for heteroskedasticity/autocorrelation-consistent standard errors rather than textbook-default OLS.",
      },
      {
        name: "Markowitz mean-variance optimization",
        description:
          "via <strong>SciPy (SLSQP)</strong> &mdash; long-only constrained efficient frontier, with eigenvalue-clipping covariance regularization for near-singular holding sets.",
      },
      {
        name: "NumPy / pandas",
        description:
          "aligning return series across sources with different native frequencies (equities, benchmark, factors) and the array/matrix math underneath the optimizer and regressions.",
      },
    ],
  },
  {
    title: "Presentation & rendering",
    icon: SquareStack,
    items: [
      {
        name: "shadcn/ui component system",
        description:
          "Sidebar, Chart, Combobox, Slider, Accordion, Card &mdash; real, accessible primitives (Phase 10i), not hand-rolled CSS equivalents.",
      },
      {
        name: "Hand-built inline SVG",
        description:
          "reserved for the Learning section's three conceptual diagrams (CAPM decomposition, a CI-whisker teaching example, frontier position) &mdash; illustrative, not this run's live data, per the standard's own guidance that hand-drawn SVG stays right for concepts, not data visualization.",
      },
    ],
  },
  {
    title: "Infrastructure & delivery",
    icon: Server,
    items: [
      {
        name: "pytest + httpx",
        description: "the backend test suite, including live (non-mocked) end-to-end tests against real market data, not fixtures.",
      },
      { name: "Railway", description: "(Phase 11) &mdash; planned deployment target, one service serving both the API and the built frontend." },
      {
        name: "Git/GitHub",
        description:
          "public repo with <code>docs/roadmap.md</code> and <code>docs/decisions/</code> published alongside the code &mdash; the decision trail is itself part of the deliverable, not just the app.",
      },
    ],
  },
]
