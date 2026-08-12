# Factor Lens

Built by [Ethan Verduzco](https://github.com/ethanverper).

A transparent factor-attribution and portfolio-optimization tool for retail
investors and small RIAs: enter your holdings and get CAPM beta, Fama-French
factor loadings, and Markowitz efficient-frontier positioning — computed from
live market data, with plain-language explanations and full statistical
diagnostics, not a black-box score.

**Status**: functionally complete and QA sign-off'd (Phases 1–10j; see
[Status](#status) below). Not yet deployed to a public URL — see
[Running it](#running-it) for dev mode in the meantime.

This is internal decision-support analytics only — no personalized
investment advice, no trade execution, no custody of funds.

## What makes this different from a factor-model script

Most factor-model code stops at the coefficients. Factor Lens treats the
step after the numbers — explaining what they actually mean for *this*
portfolio — as the core deliverable, not an afterthought:

- **Interpretation & Key Takeaways** (`app/api/interpretation.py` +
  `frontend/src/components/InterpretationSection.tsx`) — every analysis run
  produces a dedicated, visually prominent synthesis: four always-present
  takeaways (market-exposure precision, Fama-French style-tilt pattern,
  explanatory power, frontier position), a headline dynamically selected
  from what's actually most notable in *your* result, and data-quality
  flags (covariance regularization, a short sample window) surfaced
  in-line rather than buried in a methodology footnote. It's interpretation,
  never prescription — no "you should," no "consider rebalancing." See
  [`docs/decisions/0019-phase10k-interpretation-content.md`](docs/decisions/0019-phase10k-interpretation-content.md).
- **A real Learning section, not a wall of text** — a curriculum-style,
  single-open accordion (progress bar, numbered/checkmarked lessons) that
  breaks every concept into a lead line, bullets, a callout for the one
  caveat that would otherwise mislead you, a pull-quote for the number that
  matters most, and a worked example computed from this app's own live
  data — plus a predict-then-reveal check and a draggable-β diagnostic, not
  static prose next to a diagram. See
  [`docs/decisions/0021-phase10n-learning-content-decomposition.md`](docs/decisions/0021-phase10n-learning-content-decomposition.md).
- **An institutional-finance visual register**, researched directly against
  live JPMorgan/Goldman Sachs/Chase products rather than a generic SaaS
  dashboard template — see
  [`docs/decisions/0020-phase10l-institutional-refinement.md`](docs/decisions/0020-phase10l-institutional-refinement.md).

## Architecture

Two parts, one deployable service:

- **`app/`** — a Python/FastAPI JSON API. `app/data/` integrates live market
  data (OpenBB/`yfinance` for equity and benchmark prices, Kenneth French's
  Data Library for Fama-French factor series). `app/models/` is the quant
  core — CAPM, Fama-French 3-/5-factor regression (Newey-West HAC standard
  errors), and a long-only Markowitz efficient frontier (SciPy SLSQP, with
  eigenvalue-clipping covariance regularization for near-singular inputs).
  `app/api/` exposes the curated ticker/benchmark universe and the full
  analysis pipeline as JSON.
- **`frontend/`** — a React (Vite + TypeScript) + Tailwind CSS + shadcn/ui
  single-page app. Eight real routes (`/`, `/inputs`, `/results`,
  `/learning`, `/glossary`, `/tools`, `/references`, `/real-world`),
  Recharts-based data visualization (factor-loading bars with CI whiskers,
  the efficient frontier), GSAP-driven interaction (route transitions,
  data-reveal animations, scroll-triggered Learning diagrams), and full
  light/dark mode + mobile support.

In production, FastAPI serves the frontend's built static assets directly
(`app/main.py`'s `StaticFiles` mount + SPA catch-all route), so the whole
app is one process, not two separate services — see
[`docs/decisions/0018-phase10i-react-rebuild.md`](docs/decisions/0018-phase10i-react-rebuild.md).

The frontend replaced an earlier server-rendered/hand-drawn-SVG dashboard
(`app/dashboard/`, Phases 3–10h) per the team's default frontend-stack
decision (`docs/decisions/0004-react-tailwind-shadcn-default-frontend.md`,
logged at the internal team-workspace root — not part of this repo) — see
[`docs/decisions/0017-phase10h-identity-for-react-stack.md`](docs/decisions/0017-phase10h-identity-for-react-stack.md)
for the React-specific direction that applied it here.
`app/models/` and `app/data/` are untouched by that rebuild.

## API

`POST /api/analysis` — the primary endpoint: given holdings (symbol +
fractional weight), a benchmark, a date range, a Fama-French model choice
(`"3"`/`"5"`), and a frequency (`"daily"`/`"monthly"`), runs the full live
pipeline and returns CAPM/Fama-French/Markowitz results plus return/risk
attribution as one JSON bundle.

```bash
curl -X POST http://127.0.0.1:8000/api/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "holdings": [
      {"symbol": "AAPL", "weight": 0.5},
      {"symbol": "MSFT", "weight": 0.3},
      {"symbol": "GOOGL", "weight": 0.2}
    ],
    "benchmark": "^GSPC",
    "start_date": "2026-06-01",
    "end_date": "2026-08-09",
    "factor_model": "3",
    "frequency": "daily"
  }'
```

`GET /api/tickers` — the curated ~496-symbol S&P 500 + 6-benchmark universe
the frontend's selection controls search over (see
[`docs/decisions/0005-phase7-ticker-universe.md`](docs/decisions/0005-phase7-ticker-universe.md)).
`GET /api/sample` — the fixed sample-portfolio quick-start default
(AAPL/MSFT/GOOGL/AMZN vs. S&P 500). `POST /portfolio/returns` (Phase 1,
unchanged) returns the raw aligned return-series bundle without running any
model — the lower-level building block `POST /api/analysis` is built on.
`GET /health` is a liveness check.

Holdings/benchmark symbols are re-validated against the curated universe
server-side (400 on an invalid symbol) regardless of what the frontend
sends — defense in depth against a request that bypasses the browser.

## Running it

Backend:

```bash
uv sync
uv run uvicorn app.main:app --port 8000
```

Frontend (separate terminal, dev mode — proxies `/api/*` to the backend on
`:8000` via `frontend/vite.config.ts`):

```bash
cd frontend
npm install
npm run dev
```

Open the Vite dev server's printed URL (typically `http://localhost:5173`).

**Single-process / production shape**: build the frontend once, then the
backend serves it directly on its own port with no separate frontend
process:

```bash
cd frontend && npm install && npm run build && cd ..
uv run uvicorn app.main:app --port 8000
# http://localhost:8000 now serves the full app (API + built UI)
```

## Development

```bash
uv sync
uv run pytest -v          # backend test suite (see tests/ below)
uv run ruff check .        # backend lint

cd frontend
npm install
npx tsc -b                 # typecheck
npm run build               # production build
npm run lint                 # oxlint
```

Backend data-layer/API tests (`test_api.py`, `test_api_analysis.py`,
`test_data_integration.py`, `test_models_integration.py`) make real network
calls against OpenBB and Kenneth French's Data Library — no mocked fixture
data. The remaining `test_models_*.py` tests are synthetic/offline: they
validate the math against known data-generating processes (e.g. simulate
returns from a chosen true beta, check the regression recovers it), since
there's no single external "reference value" for a live-data regression the
way there is for, say, a known options price.

Note: `openbb`'s first-ever import triggers a one-time build of its static
API-tree files (cached to disk after that), which can take on the order of
tens of seconds depending on disk speed; every subsequent process start is
fast. Only `openbb-core`, `openbb-equity`, and `openbb-yfinance` are
installed (not the full `openbb` meta-package), since the app only ever
calls `obb.equity.price.historical` via the `yfinance` provider — see
[`docs/decisions/0014-phase10e-trim-openbb-dependency-bloat.md`](docs/decisions/0014-phase10e-trim-openbb-dependency-bloat.md).

## Project layout

```
app/
  main.py            FastAPI app: API routes + (in production) serves frontend/dist/
  schemas.py         Pydantic request/response models (the Phase 1/2 hand-off contract)
  service.py         Orchestrates fetch -> align -> respond
  data/               Live market-data integration (untouched by the Phase 10i rebuild)
    equity.py          OpenBB equity price fetch + return computation
    benchmark.py        Benchmark index returns (thin wrapper over equity.py)
    factors.py           Fama-French factor returns via pandas-datareader
    portfolio.py           Weighted portfolio returns + cross-series date alignment
  models/             Quant core (untouched by the Phase 10i rebuild)
    schemas.py          Pydantic output models
    adapters.py           PortfolioReturnData -> pandas
    _regression.py          shared OLS/HAC helper (capm.py + fama_french.py)
    capm.py                   CAPM beta estimation
    fama_french.py             Fama-French 3-/5-factor regression + diagnostics
    covariance.py                covariance estimation + eigenvalue-clipping regularization
    optimization.py               Markowitz efficient frontier + current-portfolio positioning
    analysis.py                    orchestrator: analyze_portfolio(bundle) -> PortfolioAnalysis
  api/                Pure JSON API for the React frontend (Phase 10i)
    routes.py           GET /api/tickers, GET /api/sample, POST /api/analysis
    attribution.py        return/risk attribution derived from Phase 2 output
    interpretation.py       Interpretation & Key Takeaways synthesis (Phase 10k)
    tickers.py              curated S&P 500 + benchmark universe (constrained-input data)
frontend/            React (Vite + TypeScript) + Tailwind + shadcn/ui SPA (Phase 10i)
  src/
    pages/              one component per section/route
    components/          shared UI: sidebar, charts, diagrams, ApertureMark,
                            InterpretationSection, FootnoteMarker, Callout/Highlight
                            (content-decomposition primitives), Lesson* (Learning content)
    data/                  curated content (glossary, references, tools, real-world, learning)
    lib/                    API client, formatting, aperture-mark geometry, URL-state helpers
    hooks/                   data-fetching + motion hooks
tests/
  test_api.py                    Live /portfolio/returns end-to-end checks (no mocking)
  test_api_analysis.py            Live /api/analysis, /api/tickers, /api/sample checks
  test_data_integration.py         Live Phase 1 data-layer checks (no mocking)
  test_interpretation.py            Interpretation & Key Takeaways logic (Phase 10k)
  test_models_*.py                    Phase 2 model tests (synthetic, offline)
  test_models_integration.py           Live Phase 1 -> Phase 2 end-to-end check
```

## Status

All core phases (quant models, live data integration, the React/Tailwind/
shadcn frontend, the Interpretation & Key Takeaways section, the
institutional visual refinement, and a full independent QA sign-off) are
done — see [`docs/roadmap.md`](docs/roadmap.md) for the phase-by-phase
history. QA's independent verdict (Phase 10j,
[full report](docs/status/2026-08-12-phase10j-qa-signoff.md)): **ready**,
nothing blocking. Public deployment (default platform: Railway) is the
one remaining phase, gated on an explicit go-ahead before provisioning
any hosting resource.

## Decision log

Every methodology and architecture choice — why HAC standard errors, why
long-only optimization, why React/Tailwind/shadcn over the original
server-rendered stack, the GSAP-vs-Framer-Motion call, the Interpretation
content rules, the institutional-register research, the deployment
shape — is logged in [`docs/decisions/`](docs/decisions/) (0002 through
0022 as of this writing). See [`docs/roadmap.md`](docs/roadmap.md) for the
full phase history.
