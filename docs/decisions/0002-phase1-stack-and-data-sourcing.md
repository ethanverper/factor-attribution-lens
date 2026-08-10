# 0002. Phase 1 stack: Python/FastAPI, OpenBB for equity/benchmark, pandas-datareader for Fama-French

Date: 2026-08-10
Status: accepted

## Context

Phase 1 needed to stand up a running app/API that takes holdings + weights and
returns live, structured return data (equity, benchmark, Fama-French factors)
for `quant-analyst` to model against in Phase 2. This is a brand-new project
with no established conventions, so the stack was an open technical call
(per the roadmap and `developer`'s own process: check for existing
conventions, and since none exist, decide and record).

Two things needed deciding: the application stack, and — once inside OpenBB —
where the Fama-French factor series actually comes from, since OpenBB's Open
Data Platform turned out not to carry it natively.

## Decision

**Stack: Python 3.11 + FastAPI + Pydantic v2, dependency-managed with `uv`.**
OpenBB's Open Data Platform is Python-native, and `quant-analyst` will also be
working in Python for Phase 2 (CAPM/Fama-French/Markowitz). A Python backend
avoids a cross-language handoff for no benefit — there's no UI requirement in
Phase 1 (that's Phase 3/`business-intelligence`'s job), so a data API is the
right-sized deliverable, not a full web frontend. FastAPI was chosen over
Flask/Django for its native Pydantic integration (matches OpenBB's own
Pydantic-based data models) and automatic request validation, which was worth
having in v1 given holdings/weights input needs real validation (weights sum
to 1, duplicate symbols, date ranges).

**OpenBB version: `openbb>=4.7,<5` (latest stable 4.x, 4.7.2 at build time)
rather than pinning to the roadmap's reference `v4.5`.** The roadmap's "v4.5"
was the version current when the research brief was written; 4.7.x is the
same Open Data Platform generation (no breaking API changes to
`equity.price.historical` between them) and simply carries more provider bug
fixes. Pinned to `<5` to avoid an unplanned major-version break.

**Equity + benchmark prices: OpenBB's `equity.price.historical`, `yfinance`
provider, `adjustment="splits_and_dividends"`.** yfinance requires no API key,
which keeps Phase 1 runnable without secrets management. Dividend adjustment
was a deliberate correctness choice: Fama-French's own market factor is a
CRSP *total* return series, so equity/benchmark returns need to include
dividends too or Phase 2's CAPM/factor regressions would be comparing
apples (price-only returns) to oranges (total returns) — a bug that would
have been invisible until Phase 2's numbers looked systematically off.
Benchmark index data reuses the same endpoint (index tickers like `^GSPC`
resolve through the same provider) rather than a separate integration.

**Fama-French factor series: `pandas-datareader`'s `famafrench` reader
against Kenneth French's Data Library directly, not OpenBB.** OpenBB's Open
Data Platform aggregates market/economic data providers (FMP, Intrinio,
Tiingo, yfinance, FRED, SEC, etc.) but has no endpoint for academic
factor-return series — confirmed by inspecting `obb`'s full namespace. Ken
French's Dartmouth library is the canonical, industry-standard source for
these series (this is where Fama-French factors originate; even commercial
vendors ultimately source from here), and `pandas-datareader` has a
purpose-built, actively maintained reader for it. This was flagged as a
possible risk in the roadmap's assumptions ("OpenBB's free tier... provides
sufficient... Fama-French factor return series") — the resolution is that
OpenBB was never the right tool for that specific series; French's library
is, and it's free with no API key required.

## Consequences

- Two independent live data dependencies now exist: OpenBB/yfinance (equity,
  benchmark) and Ken French's Data Library via pandas-datareader (factors).
  Both are unauthenticated and free, so Phase 1 has no secrets to manage, but
  it also means no SLA — either could rate-limit or reformat without notice.
  Worth revisiting if this ever needs a paid, higher-reliability provider
  (OpenBB supports swapping to `fmp`/`intrinio`/`tiingo` for equity data via
  the same interface, just needs an API key).
- Kenneth French's library updates on its own cadence (observed ~5-6 week
  lag from "today" during Phase 1 verification, e.g. daily factor data
  available through late June while equity prices were current to early
  August). The API aligns all series on their date intersection, so a
  portfolio's *usable* date range for Phase 2 modeling is bounded by
  whichever series is most stale — currently the Fama-French factors, not
  equity prices. `quant-analyst` should read `meta.aligned_start_date` /
  `meta.aligned_end_date` rather than assuming the requested date range was
  fully honored.
- Dependency management via `uv` (not plain `pip`/`venv` or `poetry`) — no
  prior convention existed; `uv` was chosen for fast, reproducible installs
  (`uv.lock`) and because it's already available in this environment.
