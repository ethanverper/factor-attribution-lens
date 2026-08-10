# Factor Lens

A transparent factor-attribution and portfolio-optimization tool for retail
investors and small RIAs: enter your holdings and get CAPM beta, Fama-French
factor loadings, and Markowitz efficient-frontier positioning — computed from
live market data, with plain-language explanations, not a black-box score.

This repository currently implements **Phase 1: Foundation & Data
Integration** — the live data backbone. It does not yet compute CAPM/factor
models or optimize portfolios; that's Phase 2.

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

## Development

```bash
uv sync                 # installs runtime + dev (pytest) dependencies
uv run pytest -v        # runs the full test suite
```

Tests make real network calls against OpenBB and Kenneth French's Data
Library — there is no mocked fixture data in this repo. This is deliberate:
Phase 1's job is to prove the data backbone is genuinely live, not to unit
test hypothetical inputs.

## Project layout

```
app/
  main.py        FastAPI app and routes
  schemas.py      Pydantic request/response models (the Phase 2 hand-off contract)
  service.py      Orchestrates fetch -> align -> respond
  data/
    equity.py     OpenBB equity price fetch + return computation
    benchmark.py  Benchmark index returns (thin wrapper over equity.py)
    factors.py    Fama-French factor returns via pandas-datareader
    portfolio.py  Weighted portfolio returns + cross-series date alignment
tests/
  test_data_integration.py   Live data-layer checks (no mocking)
  test_api.py                 Live end-to-end API checks (no mocking)
```

## What's next (Phase 2, `quant-analyst`)

This API hands off a clean, aligned return bundle. Phase 2 builds CAPM beta
estimation, Fama-French regression with statistical diagnostics, and
Markowitz efficient-frontier optimization on top of it — see
[`docs/roadmap.md`](docs/roadmap.md) for the full phase plan.
