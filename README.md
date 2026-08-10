# Factor Lens

A transparent factor-attribution and portfolio-optimization tool for retail
investors and small RIAs: enter your holdings and get CAPM beta, Fama-French
factor loadings, and Markowitz efficient-frontier positioning — computed from
live market data, with plain-language explanations, not a black-box score.

This repository currently implements **Phase 1: Foundation & Data
Integration** (the live data backbone), **Phase 2: Quant Core** (CAPM,
Fama-French, and Markowitz modeling), **Phase 3: Explainable Attribution &
Visualization Layer** (a server-rendered dashboard), and **Phase 7: UI/UX
Overhaul & Constrained Inputs** (a full sidebar app shell across all eight
`docs/project-standards.md` sections, and a constrained ticker/benchmark
combobox in place of free text). It does not yet have the plain-language
Learning/Glossary content or the rendered References & Formulas section —
those are clearly marked "coming soon" in the running app and are Phase 8/9.

## What this phase does

Given a portfolio (holdings + weights, a benchmark, a date range, and a
Fama-French factor model choice), the API fetches and returns a fully
date-aligned bundle of return series:

- **Equity returns** — per-holding daily or monthly total returns.
- **Benchmark returns** — same, for a chosen index (default S&P 500,
  `^GSPC`).
- **Portfolio returns** — the weighted-average return series across
  holdings.
- **Fama-French factor returns** — 3-factor (Mkt-RF, SMB, HML) or 5-factor
  (adds RMW, CMA), plus the risk-free rate.

All four series are aligned to their common trading dates so the response is
immediately usable for regression — no NaNs, no mismatched calendars.

## Stack

Python 3.11 + FastAPI + Pydantic v2, dependency-managed with
[`uv`](https://docs.astral.sh/uv/). Data sources:

- [OpenBB Open Data Platform](https://openbb.co/) (`yfinance` provider, no
  API key required) for equity and benchmark index prices.
- [Kenneth French's Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
  via `pandas-datareader` for Fama-French factor return series (OpenBB does
  not carry this series natively — see
  [`docs/decisions/0002-phase1-stack-and-data-sourcing.md`](docs/decisions/0002-phase1-stack-and-data-sourcing.md)).

## Running it

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Then, for example:

```bash
curl -X POST http://127.0.0.1:8000/portfolio/returns \
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

`GET /health` is available for a quick liveness check.

## Response shape

```jsonc
{
  "meta": {
    "holdings": [...], "benchmark": "^GSPC", "factor_model": "3", "frequency": "daily",
    "requested_start_date": "2026-06-01", "requested_end_date": "2026-08-09",
    "aligned_start_date": "2026-06-02", "aligned_end_date": "2026-06-30", // bounded by the most-stale source series
    "n_periods": 20,
    "equity_provider": "yfinance (via OpenBB Open Data Platform)",
    "factor_provider": "Kenneth French Data Library (via pandas-datareader)"
  },
  "equity_returns": { "AAPL": [{"date": "2026-06-02", "value": 0.0123}, ...], "MSFT": [...] },
  "portfolio_returns": [{"date": "2026-06-02", "value": 0.0091}, ...],
  "benchmark_returns": [{"date": "2026-06-02", "value": 0.0087}, ...],
  "factor_returns": [{"date": "2026-06-02", "mkt_rf": 0.0082, "smb": -0.0011, "hml": 0.0034, "rmw": null, "cma": null, "rf": 0.0001}, ...]
}
```

All returns are simple period-over-period percentage changes expressed as
decimal fractions (e.g. `0.01` = 1%), including the Fama-French series
(French's raw files are in percent; this API divides by 100 for
consistency). Equity/benchmark prices are fetched with dividends included, so
returns are total returns — consistent with how the Fama-French factors
themselves are constructed.

`aligned_start_date`/`aligned_end_date` reflect the actual usable date range
after intersecting all four series' trading calendars — this is very likely
narrower than the requested range, since Kenneth French's library updates on
its own lag (weeks behind live equity prices). Always read these fields
rather than assuming the request's `start_date`/`end_date` were fully
honored.

## Phase 2: Quant Core (`app/models/`)

Given a `PortfolioReturnData` bundle (whatever `POST /portfolio/returns`
returns, live or hand-built), `app/models/analysis.py` runs all three
models and returns one bundled result:

```python
from app.models.analysis import analyze_portfolio
from app.service import build_portfolio_return_data

bundle = build_portfolio_return_data(request)   # Phase 1
analysis = analyze_portfolio(bundle)             # Phase 2

analysis.capm.beta.estimate                      # CAPM beta vs. the benchmark
analysis.factor_model.factor_loadings             # Fama-French loadings + t-stats/SEs/p-values
analysis.efficient_frontier.frontier              # frontier coordinates (return, vol, weights)
analysis.efficient_frontier.current_portfolio     # where the input portfolio sits vs. the frontier
```

The individual model functions (`capm.estimate_capm_beta`,
`fama_french.estimate_factor_model`,
`optimization.compute_efficient_frontier`) are also public and independently
usable/testable on plain pandas Series/DataFrames, without needing a
`PortfolioReturnData` object.

Key methodology choices (regression standard-error convention, long-only
optimization by default, covariance regularization, annualization
conventions) are logged in
[`docs/decisions/0003-phase2-quant-methodology.md`](docs/decisions/0003-phase2-quant-methodology.md).

This is internal decision-support analytics only — `PortfolioAnalysis`
output (including frontier/Sharpe-ratio comparisons) is not, and must not
be presented as, personalized investment advice or a buy/sell/rebalance
recommendation.

## Phase 3: Attribution & Visualization Dashboard (`app/dashboard/`)

A server-rendered HTML dashboard reached from inside the running FastAPI
app — no separate frontend, no client-side charting library:

- **`GET /`** — a holdings-entry form (tickers + weights, benchmark, date
  range, Fama-French model, frequency).
- **`POST /dashboard`** — builds the exact same `PortfolioRequest` Phase
  1's `POST /portfolio/returns` uses, runs it through
  `build_portfolio_return_data` -> `analyze_portfolio` (live data, no
  mocking), and renders three views from the live result:
  1. **Factor exposure** — CAPM beta and Fama-French factor loadings as a
     diverging bar chart, with 95% CI whiskers plotted directly on the
     chart (not hidden behind a hover) plus t-stats/p-values/R² visible in
     stat tiles and a table-view twin.
  2. **Efficient frontier** — the modeled long-only frontier curve with the
     current portfolio, global-min-variance, and max-Sharpe points plotted
     on it, and the return gap at matched volatility labeled directly on
     the chart. Surfaces a visible warning banner if
     `covariance_regularized` was triggered (per decision 0003).
  3. **Return & risk attribution** — a diverging bar chart of alpha plus
     each factor's own contribution to the portfolio's realized mean
     per-period excess return (an exact OLS identity, not an
     approximation — see `app/dashboard/attribution.py`), and a
     part-to-whole split of return variance into factor-explained (R²) vs.
     idiosyncratic.

Every chart follows the `dataviz` skill's method (validated categorical
palette, fixed mark specs, hover tooltips, a `<details>` table-view twin
on every chart, light/dark mode). Design choices — why server-side SVG
instead of a JS charting library, why no Jinja2, why return/risk
attribution lives in the dashboard layer rather than as a new Phase 2
model output — are logged in
[`docs/decisions/0004-phase3-dashboard-architecture.md`](docs/decisions/0004-phase3-dashboard-architecture.md).

This is internal decision-support analytics, same limit as Phase 2: no
personalized investment advice, no buy/sell/rebalance signal. The
dashboard's disclaimer banner and section copy say so explicitly.

## Phase 7: UI/UX Overhaul & Constrained Inputs (`app/dashboard/shell.py`, `app/dashboard/tickers.py`)

Both `GET /` and `POST /dashboard` now render one persistent app shell — a
sidebar table-of-contents nav across all eight `docs/project-standards.md`
sections (Overview, Inputs, Results, Learning, Glossary, Tools &
Technologies, References & Formulas, Real World/Corporate Applications) —
instead of two disconnected pages. Overview/Inputs/Results/Tools &
Technologies are fully built; Learning/Glossary/References & Formulas/Real
World are clearly-marked placeholder panels for Phase 8 (`business-
intelligence`) and Phase 9 (`educator`) to fill in. Phase 3's charts
(`viz.py`, `attribution.py`) are unchanged — only re-homed into the Results
panel and restyled to the new visual system (Fraunces display serif + IBM
Plex Sans/Mono, reusing the existing validated chart palette's
`--series-2` as the one signature page accent).

The holdings and benchmark fields are no longer free text: they're a
hand-built accessible combobox backed by a curated ~496-symbol S&P 500
universe (`app/dashboard/tickers.py`) plus a 6-item benchmark list. The
value that actually gets submitted only ever comes from selecting a real
option — never from raw typed text — and `app/dashboard/routes.py`
independently re-validates every submitted symbol server-side as a
backstop against a non-browser submission. See
[`docs/decisions/0005-phase7-ticker-universe.md`](docs/decisions/0005-phase7-ticker-universe.md)
for why this universe, how it's sourced, and its known limitations (it's a
static snapshot, not a live index-membership feed).

## Development

```bash
uv sync                 # installs runtime + dev (pytest) dependencies
uv run pytest -v        # runs the full test suite
```

Phase 1's data-layer/API tests make real network calls against OpenBB and
Kenneth French's Data Library — no mocked fixture data. Phase 2's model
tests (`test_models_capm.py`, `test_models_fama_french.py`,
`test_models_optimization.py`, `test_models_analysis.py`,
`test_models_adapters.py`) are synthetic/offline — they validate the math
against known data-generating processes (e.g. simulate returns from a
chosen true beta, check the regression recovers it), since there's no
single external "reference value" for a live-data regression the way
there is for, say, a known options price. `test_models_integration.py` is
the one live exception: it chains the real Phase 1 endpoint through Phase
2's `analyze_portfolio` and checks the combined output is plausible
(weights sum to 1, beta/R² in sane ranges) end-to-end. `test_dashboard.py`
follows the same live-data convention for Phase 3: it drives `GET /` and
`POST /dashboard` through a real `TestClient` request (live market data,
no mocking) and separately asserts the return-attribution decomposition's
numeric identity (contributions sum to the realized mean excess return)
holds against live data, not just synthetic fixtures.

Note: `openbb`'s first import is slow (its dynamic API-tree build can take
several minutes on a cold run) — this affects `uv run pytest` and `uv run
uvicorn app.main:app` startup time alike; it is not specific to any one
test or route.

## Project layout

```
app/
  main.py        FastAPI app and routes (includes app/dashboard's router)
  schemas.py      Pydantic request/response models (the Phase 2 hand-off contract)
  service.py      Orchestrates fetch -> align -> respond
  data/
    equity.py     OpenBB equity price fetch + return computation
    benchmark.py  Benchmark index returns (thin wrapper over equity.py)
    factors.py    Fama-French factor returns via pandas-datareader
    portfolio.py  Weighted portfolio returns + cross-series date alignment
  models/                Phase 2 quant core
    schemas.py           Pydantic output models (Phase 3/4 hand-off contract)
    adapters.py          PortfolioReturnData -> pandas
    _regression.py       shared OLS/HAC helper (capm.py + fama_french.py)
    capm.py              CAPM beta estimation
    fama_french.py       Fama-French 3-/5-factor regression + diagnostics
    covariance.py        covariance estimation + eigenvalue-clipping regularization
    optimization.py      Markowitz efficient frontier + current-portfolio positioning
    analysis.py          orchestrator: analyze_portfolio(bundle) -> PortfolioAnalysis
  dashboard/             Phase 3 attribution & visualization layer + Phase 7 app shell
    routes.py            GET / (form), POST /dashboard (live-data results page)
    attribution.py       return/risk attribution derived from Phase 2 output
    viz.py               SVG chart components (dataviz-skill palette/marks/interaction)
    pages.py             per-page panel assembly (Inputs, Results + Phase 3 chart sections)
    shell.py             Phase 7 app shell: sidebar nav, tab panels, ticker/benchmark combobox
    tickers.py           Phase 7 curated S&P 500 + benchmark universe (constrained-input data)
tests/
  test_data_integration.py    Live Phase 1 data-layer checks (no mocking)
  test_api.py                 Live Phase 1 end-to-end API checks (no mocking)
  test_models_*.py            Phase 2 model tests (synthetic, offline)
  test_models_integration.py  Live Phase 1 -> Phase 2 end-to-end check
  test_dashboard.py           Live Phase 3 dashboard checks + return-attribution identity check
```

## What's next (Phase 8 `business-intelligence`, Phase 9 `educator`)

Phase 7 hands off a full eight-section app shell with Overview/Inputs/
Results/Tools & Technologies built and Learning/Glossary/References &
Formulas/Real World left as clearly-marked placeholder panels (see
`app/dashboard/pages.py`'s `_base_panels()` and
`shell.render_placeholder_section`). Phase 8 writes the References &
Formulas section and reviews the Results section's numbers/attribution
logic post-restyle; Phase 9 builds the dual-register Learning content, the
Glossary, and the Real World/Corporate Applications section — see
[`docs/decisions/0004-phase3-dashboard-architecture.md`](docs/decisions/0004-phase3-dashboard-architecture.md)
for return-attribution unit conventions (per-period, not annualized) and
[`docs/roadmap.md`](docs/roadmap.md) for the full phase plan.
