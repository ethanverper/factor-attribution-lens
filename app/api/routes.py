"""FastAPI routes for Factor Lens's pure JSON API (Phase 10i).

`POST /api/analysis` is the primary endpoint the React frontend calls: it
runs the exact `build_portfolio_return_data` -> `analyze_portfolio` pipeline
Phase 1/2 built and Phase 3's now-removed server-rendered dashboard used
internally, plus the Phase 3 return/risk attribution, and returns the whole
bundle as JSON -- this pipeline was previously only reachable from inside a
server-rendered route, never as its own JSON contract.

`GET /api/tickers` serves the curated ticker/benchmark universe
(`app/api/tickers.py`) the frontend's Combobox/Select components search
over. `GET /api/sample` serves the fixed sample-portfolio quick-start
default so the Overview hero and the Inputs "run a live example" action
don't hardcode it twice.

Submitted holding/benchmark symbols are re-validated against the curated
universe server-side (`docs/project-standards.md`'s "invalid values in a
constrained field shouldn't be able to reach the backend at all") --
defense in depth against a request that bypasses the frontend's own
Combobox constraint.
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from app.api import tickers
from app.api.attribution import compute_return_attribution, compute_risk_attribution
from app.api.interpretation import compute_interpretation
from app.api.schemas import (
    AnalysisResponse,
    BenchmarkInfo,
    InterpretationFlag,
    InterpretationResponse,
    InterpretationTakeaway,
    RiskAttributionResponse,
    ReturnAttributionResponse,
    SampleHolding,
    SamplePortfolioResponse,
    TickerInfo,
    TickerUniverseResponse,
)
from app.data.equity import EquityDataError
from app.data.factors import FactorDataError
from app.models.analysis import analyze_portfolio
from app.models.capm import InsufficientDataError as CAPMInsufficientDataError
from app.models.fama_french import (
    InsufficientDataError as FactorModelInsufficientDataError,
    MissingFactorsError,
)
from app.models.optimization import InsufficientDataError as FrontierInsufficientDataError
from app.schemas import PortfolioRequest
from app.service import build_portfolio_return_data

router = APIRouter(prefix="/api")

_MODELING_ERRORS = (
    CAPMInsufficientDataError,
    FactorModelInsufficientDataError,
    FrontierInsufficientDataError,
    MissingFactorsError,
)

# The one-click sample-portfolio quick-start (`docs/project-standards.md` rule 8):
# four well-known large-caps, weighted so no two holdings tie (makes the resulting
# return/risk attribution chart visibly non-uniform) -- unchanged from Phase 9c.
SAMPLE_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN"]
SAMPLE_WEIGHTS_PCT = [40.0, 30.0, 20.0, 10.0]
SAMPLE_BENCHMARK = "^GSPC"

_DEFAULT_END = date.today() - timedelta(days=1)
_DEFAULT_START = _DEFAULT_END - timedelta(days=365)

_TICKER_SOURCE_NOTE = (
    "Ticker and benchmark options are drawn from a curated S&P 500 constituent snapshot "
    "(~496 symbols, mirroring the official index list) plus a small set of major index/ETF "
    "benchmarks -- not a live index-membership feed, so it can drift from the current S&P "
    "500 roster over time. A holding outside this list (a small-cap, an ADR, a non-US "
    "listing) can't be entered yet, even if it trades on Yahoo Finance/yfinance. See "
    "docs/decisions/0005-phase7-ticker-universe.md for the full sourcing and refresh policy."
)


@router.get("/tickers", response_model=TickerUniverseResponse)
def get_tickers() -> TickerUniverseResponse:
    return TickerUniverseResponse(
        tickers=[TickerInfo(symbol=s, name=n, sector=sec) for s, n, sec in tickers.SP500_CONSTITUENTS],
        benchmarks=[BenchmarkInfo(symbol=s, name=n) for s, n in tickers.BENCHMARKS],
        source_note=_TICKER_SOURCE_NOTE,
    )


@router.get("/sample", response_model=SamplePortfolioResponse)
def get_sample_portfolio() -> SamplePortfolioResponse:
    return SamplePortfolioResponse(
        holdings=[SampleHolding(symbol=s, weight_pct=w) for s, w in zip(SAMPLE_SYMBOLS, SAMPLE_WEIGHTS_PCT)],
        benchmark=SAMPLE_BENCHMARK,
        start_date=_DEFAULT_START,
        end_date=_DEFAULT_END,
        factor_model="3",
        frequency="daily",
    )


@router.post("/analysis", response_model=AnalysisResponse)
def post_analysis(request: PortfolioRequest) -> AnalysisResponse:
    for holding in request.holdings:
        if not tickers.is_valid_ticker(holding.symbol):
            raise HTTPException(
                status_code=400,
                detail=f"'{holding.symbol}' is not in the curated ticker universe. Choose a holding from the search list.",
            )
    if not tickers.is_valid_benchmark(request.benchmark):
        raise HTTPException(
            status_code=400,
            detail=f"'{request.benchmark}' is not in the curated benchmark list. Choose a benchmark from the search list.",
        )

    try:
        data = build_portfolio_return_data(request)
        analysis = analyze_portfolio(data)
    except (EquityDataError, FactorDataError) as exc:
        raise HTTPException(status_code=502, detail=f"Data source error: {exc}") from exc
    except _MODELING_ERRORS as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return_attribution = compute_return_attribution(analysis.factor_model, data)
    risk_attribution = compute_risk_attribution(analysis.factor_model)
    interpretation = compute_interpretation(analysis)

    return AnalysisResponse(
        meta=data.meta,
        analysis=analysis,
        return_attribution=ReturnAttributionResponse(
            contributions=[
                {"name": c.name, "label": c.label, "contribution_periodic": c.contribution_periodic}
                for c in return_attribution.contributions
            ],
            total_periodic=return_attribution.total_periodic,
            frequency=return_attribution.frequency,
        ),
        risk_attribution=RiskAttributionResponse(
            factor_explained_share=risk_attribution.factor_explained_share,
            idiosyncratic_share=risk_attribution.idiosyncratic_share,
            r_squared_raw=risk_attribution.r_squared_raw,
        ),
        interpretation=InterpretationResponse(
            headline=interpretation.headline,
            takeaways=[
                InterpretationTakeaway(id=t.id, title=t.title, body=t.body, is_headline=t.is_headline)
                for t in interpretation.takeaways
            ],
            flags=[InterpretationFlag(id=f.id, severity=f.severity, message=f.message) for f in interpretation.flags],
        ),
    )
