"""FastAPI routes for the app's dashboard: a holdings form and its results page.

`GET /` renders the holdings-entry form (Phase 7: now one tab of the full
app shell, see `app/dashboard/shell.py`). `POST /dashboard` takes that form
submission, builds a `PortfolioRequest` (Phase 1's own request schema --
no parallel input model), runs it through the same `build_portfolio_return_data`
-> `analyze_portfolio` pipeline `POST /portfolio/returns` and Phase 2 use,
computes the Phase 3 attribution view, and renders the dashboard. On any
data or validation error, it re-renders the form with the submitted values
preserved and an inline error banner, rather than a bare 500/422.

Phase 7 adds one more validation step ahead of all of this: submitted
holding/benchmark symbols must be in the curated universe
(`app/dashboard/tickers.py`). The combobox UI is the primary constraint (a
user can't type an arbitrary ticker into it), but a submission that bypasses
the browser entirely (a hand-crafted POST) is still checked server-side
before it ever reaches Phase 1's `PortfolioRequest`/`build_portfolio_return_data` --
per `docs/project-standards.md`'s "invalid values in a constrained field
shouldn't be able to reach the backend at all."

Phase 9b: the submitted `weight` form field is a percentage (0-100), matching
what the Inputs form now shows/collects -- this handler converts each to the
0-1 fraction `HoldingInput.weight` expects before it ever reaches Phase 1's
schema, and checks the allocations sum to 100% (with a plain-language error)
ahead of `PortfolioRequest`'s own fraction-sum-to-1.0 check, which still runs
as a defense-in-depth backstop for a hand-crafted POST that skips this loop
entirely.

Phase 9c adds two more entry points that share the same validation/analysis
core (`_run_dashboard`, factored out of the old `dashboard_submit` body so
all three routes stay in lockstep):

- `GET /dashboard/sample` -- the one-click sample-portfolio quick-start
  (`docs/project-standards.md` rule 8). A fixed, well-known four-holding
  portfolio with no query params required, so a visitor with no tickers in
  mind can see the full Results tab in one click.
- `GET /dashboard/view` -- the shareable-link target (rule 8). Carries the
  exact holdings/benchmark/date-range/model/frequency of a completed
  analysis as query params so the same configuration can be replayed by
  anyone who opens the link -- see decision 0008 for why a re-computed
  permalink was chosen over PDF generation as this feature's primary form.
  `render_dashboard_page` builds this URL from `PortfolioReturnData.meta` at
  render time, so the Results tab's "Copy shareable link" control never has
  to reconstruct it client-side.

Both new routes also thread the request's base URL through to the page
renderers so Open Graph/Twitter meta tags (`shell.render_app_shell`) can
carry an absolute `og:image`/`og:url` -- required for LinkedIn/Slack link
unfurling, which will not resolve a relative image URL.
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.dashboard import tickers
from app.dashboard.attribution import compute_return_attribution, compute_risk_attribution
from app.dashboard.pages import render_dashboard_page, render_form_page
from app.data.equity import EquityDataError
from app.data.factors import FactorDataError
from app.models.analysis import analyze_portfolio
from app.models.capm import InsufficientDataError as CAPMInsufficientDataError
from app.models.fama_french import (
    InsufficientDataError as FactorModelInsufficientDataError,
    MissingFactorsError,
)
from app.models.optimization import InsufficientDataError as FrontierInsufficientDataError
from app.schemas import HoldingInput, PortfolioRequest
from app.service import build_portfolio_return_data

router = APIRouter()

_DEFAULT_END = date.today() - timedelta(days=1)
_DEFAULT_START = _DEFAULT_END - timedelta(days=365)

_MODELING_ERRORS = (
    CAPMInsufficientDataError,
    FactorModelInsufficientDataError,
    FrontierInsufficientDataError,
    MissingFactorsError,
)

# The one-click sample-portfolio quick-start (`docs/project-standards.md`
# rule 8): four well-known large-caps, weighted so no two holdings tie
# (makes the resulting return/risk attribution chart visibly non-uniform,
# a slightly more informative demo than an even split).
SAMPLE_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN"]
SAMPLE_WEIGHTS = ["40", "30", "20", "10"]
SAMPLE_BENCHMARK = "^GSPC"


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _plain_validation_message(exc: ValidationError) -> str:
    """Turn a pydantic `ValidationError` into a single plain-language sentence instead
    of its raw multi-line dump (type, input value, docs URL, etc.) -- matching the
    plain-language convention every other error path in this module already follows."""
    errors = exc.errors()
    if errors:
        msg = errors[0].get("msg", "")
        prefix = "Value error, "
        if msg.startswith(prefix):
            msg = msg[len(prefix):]
        if msg:
            return f"Your submission couldn't be processed: {msg}."
    return "Your submission couldn't be processed. Check your inputs and try again."


@router.get("/", response_class=HTMLResponse)
def dashboard_form(request: Request) -> str:
    return render_form_page(start_date=_DEFAULT_START, end_date=_DEFAULT_END, request_base_url=_base_url(request))


def _run_dashboard(
    *,
    symbol: list[str],
    weight: list[str],
    benchmark: str,
    start_date: date,
    end_date: date,
    factor_model: str,
    frequency: str,
    request_base_url: str,
) -> HTMLResponse:
    """Shared validation + analysis core for `POST /dashboard`, `GET /dashboard/sample`,
    and `GET /dashboard/view` -- see module docstring."""

    def re_render_form(message: str, status_code: int) -> HTMLResponse:
        html = render_form_page(
            error=message,
            symbols=symbol or None,
            weights=weight or None,
            benchmark=benchmark,
            start_date=start_date,
            end_date=end_date,
            factor_model=factor_model,
            frequency=frequency,
            request_base_url=request_base_url,
        )
        return HTMLResponse(html, status_code=status_code)

    holdings: list[HoldingInput] = []
    total_pct = 0.0
    for raw_symbol, raw_weight in zip(symbol, weight):
        raw_symbol = raw_symbol.strip()
        raw_weight = raw_weight.strip()
        if not raw_symbol and not raw_weight:
            continue
        if not raw_symbol or not raw_weight:
            return re_render_form(
                f"Holding row with '{raw_symbol or raw_weight}' needs both a symbol and an allocation.", 400
            )
        if not tickers.is_valid_ticker(raw_symbol):
            return re_render_form(
                f"'{raw_symbol}' is not in the curated ticker universe. Choose a holding from the search list.", 400
            )
        try:
            pct = float(raw_weight)
        except ValueError:
            return re_render_form(f"'{raw_weight}' is not a valid allocation for '{raw_symbol}'.", 400)
        if not (0 < pct <= 100):
            return re_render_form(f"Allocation for '{raw_symbol}' must be greater than 0 and no more than 100%.", 400)
        total_pct += pct
        try:
            holdings.append(HoldingInput(symbol=raw_symbol, weight=pct / 100))
        except ValidationError as exc:
            return re_render_form(f"Invalid holding '{raw_symbol}': {exc}", 400)

    if not holdings:
        return re_render_form("Enter at least one holding.", 400)

    if abs(total_pct - 100) > 0.1:
        return re_render_form(
            f"Your allocations add up to {total_pct:.1f}%, not 100%. Adjust the weights so they total 100% before submitting.",
            400,
        )

    holding_symbols = [h.symbol for h in holdings]
    if len(holding_symbols) != len(set(holding_symbols)):
        dupes = sorted({s for s in holding_symbols if holding_symbols.count(s) > 1})
        return re_render_form(
            f"You entered {', '.join(dupes)} more than once. Each holding must be a distinct ticker.", 400
        )

    if not tickers.is_valid_benchmark(benchmark):
        return re_render_form(
            f"'{benchmark}' is not in the curated benchmark list. Choose a benchmark from the search list.", 400
        )

    if start_date >= end_date:
        return re_render_form(
            "Start date must be before end date. Adjust the date range before submitting.", 400
        )

    try:
        request_model = PortfolioRequest(
            holdings=holdings,
            benchmark=benchmark,
            start_date=start_date,
            end_date=end_date,
            factor_model=factor_model,
            frequency=frequency,
        )
    except ValidationError as exc:
        # Defense-in-depth backstop for a hand-crafted POST/GET that skips the plain-
        # language checks above entirely (duplicate symbols, bad date range are both
        # caught earlier now) -- still never leak pydantic's raw multi-line dump.
        return re_render_form(_plain_validation_message(exc), 400)

    try:
        data = build_portfolio_return_data(request_model)
        analysis = analyze_portfolio(data)
    except (EquityDataError, FactorDataError) as exc:
        return re_render_form(f"Data source error: {exc}", 502)
    except _MODELING_ERRORS as exc:
        return re_render_form(str(exc), 400)
    except ValueError as exc:
        return re_render_form(str(exc), 400)

    return_attribution = compute_return_attribution(analysis.factor_model, data)
    risk_attribution = compute_risk_attribution(analysis.factor_model)

    html = render_dashboard_page(
        data, analysis, return_attribution, risk_attribution, request_base_url=request_base_url
    )
    return HTMLResponse(html)


@router.post("/dashboard", response_class=HTMLResponse)
async def dashboard_submit(
    request: Request,
    symbol: list[str] = Form(default=[]),
    weight: list[str] = Form(default=[]),
    benchmark: str = Form("^GSPC"),
    start_date: date = Form(...),
    end_date: date = Form(...),
    factor_model: str = Form("3"),
    frequency: str = Form("daily"),
) -> HTMLResponse:
    return _run_dashboard(
        symbol=symbol,
        weight=weight,
        benchmark=benchmark,
        start_date=start_date,
        end_date=end_date,
        factor_model=factor_model,
        frequency=frequency,
        request_base_url=_base_url(request),
    )


@router.get("/dashboard/sample", response_class=HTMLResponse)
def dashboard_sample(request: Request) -> HTMLResponse:
    """One-click sample-portfolio quick-start (`docs/project-standards.md` rule 8) --
    a visitor doesn't need real tickers in mind to see the full Results tab."""
    return _run_dashboard(
        symbol=list(SAMPLE_SYMBOLS),
        weight=list(SAMPLE_WEIGHTS),
        benchmark=SAMPLE_BENCHMARK,
        start_date=_DEFAULT_START,
        end_date=_DEFAULT_END,
        factor_model="3",
        frequency="daily",
        request_base_url=_base_url(request),
    )


@router.get("/dashboard/view", response_class=HTMLResponse)
def dashboard_view(
    request: Request,
    symbol: list[str] = Query(default=[]),
    weight: list[str] = Query(default=[]),
    benchmark: str = Query("^GSPC"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    factor_model: str = Query("3"),
    frequency: str = Query("daily"),
) -> HTMLResponse:
    """Shareable-link target (rule 8) -- replays a specific holdings/benchmark/date-range/
    model configuration from URL query params through the same live pipeline every other
    entry point uses. Recomputed from live data on each visit (not a stored snapshot), so
    the exact numbers can drift day-to-day even though the configuration is identical --
    see decision 0008 and the "Shared configuration" note rendered on the Results tab."""
    return _run_dashboard(
        symbol=symbol,
        weight=weight,
        benchmark=benchmark,
        start_date=start_date,
        end_date=end_date,
        factor_model=factor_model,
        frequency=frequency,
        request_base_url=_base_url(request),
    )
