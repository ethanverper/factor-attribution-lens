# 0005. Phase 7 constrained inputs: S&P 500 curated ticker universe, native
combobox UI, server-side backstop validation

Date: 2026-08-10
Status: accepted

## Context

`docs/project-standards.md` rule 2 requires that any input which must match
real, specific data (a stock ticker is the canonical example given) use a
constrained-selection control, never bare free text — a user should not be
able to type an arbitrary/invalid ticker into the holdings or benchmark
fields. The Phase 3 form previously accepted a plain `<input type="text">`
for both. Trying to validate against *every* ticker that could ever exist
(the full universe of US-listed securities, let alone global) is neither a
one-phase-scoped task nor something a hand-maintained list should attempt.
The assignment explicitly scoped this down: "a curated, reasonably-sized
ticker universe (e.g. S&P 500 constituents or similar well-known large-cap
set)."

## Decisions

**1. Universe: S&P 500 constituents, ~496 symbols, sourced from a public
constituents dataset that mirrors the official S&P Dow Jones Indices list**
(the same data that backs Wikipedia's "List of S&P 500 companies" and the
commonly-used `datasets/s-and-p-500-companies` GitHub dataset), captured as
a static snapshot at build time in `app/dashboard/tickers.py`
(`SP500_CONSTITUENTS: tuple[(symbol, name, sector), ...]`). This was chosen
over alternatives considered:
   - *Every listed US ticker (thousands, via an exchange listing file)* —
     rejected: far larger than "reasonably-sized," would make the combobox's
     client-side filtering noticeably heavier, and most of that universe is
     illiquid/thinly-covered names this project's target persona (retail
     investors, small RIAs) wouldn't hold anyway.
   - *A live/dynamic ticker-validation API call per keystroke* — rejected:
     adds a network dependency and latency to what should be an instant,
     offline-capable input control, and there's no free, no-key data source
     already in this project's stack (OpenBB/yfinance) that exposes a clean
     "is this a valid US equity ticker" lookup independent of fetching full
     price history.
   - *S&P 500 static snapshot (chosen)* — well-known, large-cap, exactly the
     kind of holding this project's persona would realistically enter, small
     enough (~500 rows, ~15KB embedded as JSON) to filter instantly
     client-side with no network round-trip, and it's a *real* published
     index membership rather than an arbitrary hand-picked list — legible to
     anyone reviewing the project.

**2. Normalized to Yahoo Finance / `yfinance` ticker conventions at data-entry
time, not fetch time.** The source dataset uses dots for share classes
(`BRK.B`, `BF.B`); `yfinance` (Phase 1's actual price-data provider, via
OpenBB) expects dashes (`BRK-B`, `BF-B`). Rather than adding a translation
layer Phase 1's `app/data/equity.py` would need to apply on every fetch,
the curated list itself stores the dash form, so every entry in
`SP500_CONSTITUENTS` is directly usable by the existing, unmodified Phase 1
fetch path — Phase 1/2 backend logic stays untouched per this phase's scope.

**3. Enforced at two layers, not one.** The primary constraint is the
client-side combobox (`app/dashboard/shell.py`'s `render_combobox` +
its vanilla-JS `initCombobox`): the field a user types into is a plain text
input, but the value that actually gets submitted (`name="symbol"` /
`name="benchmark"`) lives in a separate hidden input that is *only* ever
set by selecting an option from the filtered list (click or
arrow-keys+Enter) — never by the raw typed text. If a user types something
that never resolves to a selection and then leaves the field (blur), the
hidden value stays empty and the visible text is cleared, so an invalid
value cannot reach form submission through the UI at all. That alone
satisfies "shouldn't be able to reach the backend" for the normal UI path,
but a hand-crafted POST (curl, a modified client, a bug in a future UI
change) bypasses the browser entirely — so `app/dashboard/routes.py`'s
`dashboard_submit` also checks every submitted symbol against
`tickers.is_valid_ticker` / `is_valid_benchmark` before constructing Phase
1's `PortfolioRequest`, returning the same inline-error-banner UX (400,
re-rendered form) as any other validation failure. Verified directly with a
raw `curl -X POST` carrying an invalid ticker and an invalid benchmark —
both correctly rejected with a 400 and a clear message, never reaching
`build_portfolio_return_data`.

**4. Benchmark gets its own small curated list, not the equity universe.**
`BENCHMARKS` in `tickers.py` is 6 well-known index/ETF proxies (`^GSPC`,
`^DJI`, `^IXIC`, `^NDX`, `^RUT`, `VTI`) rather than reusing
`SP500_CONSTITUENTS` — indices aren't equities, use different (often
`^`-prefixed) Yahoo Finance symbols, and the set of benchmarks a retail
user would plausibly choose is genuinely small; a 500-row list would be
wrong UX for a field with ~6 real answers.

## Consequences / maintenance

- **This list will drift from the live S&P 500 as index membership changes**
  (additions/removals happen several times a year). That's an accepted
  tradeoff for a portfolio-demonstration project, not a production index-
  membership product — it needs periodic manual refresh (re-running the same
  sourcing process and regenerating `SP500_CONSTITUENTS`), not live syncing.
  If this project ever needs to track membership changes automatically,
  that's a new, explicitly-scoped task, not an implicit expectation of this
  decision.
- A holding outside the S&P 500 (a small-cap, an ADR, a non-US listing)
  cannot be entered even though it might be perfectly valid on
  `yfinance`/OpenBB. This is a deliberate scope trade the assignment
  accepted explicitly ("rather than trying to validate against every
  possible ticker in existence") — flagged here so Phase 8–10 and any future
  iteration know it's a known, intentional limitation, not an oversight.
- Phase 8 (`business-intelligence`) and Phase 9 (`educator`) building the
  remaining sections don't need to touch `tickers.py`; it's presentation/
  validation-layer only and doesn't participate in the Phase 2 model
  contract (`app/models/schemas.py`) or Phase 1's `app/schemas.py`.
