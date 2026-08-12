"""Response schemas for the pure JSON API (Phase 10i).

`AnalysisResponse` is the hand-off contract with the React frontend: the
full Phase 2 `PortfolioAnalysis` (CAPM, Fama-French, Markowitz frontier) plus
the Phase 3 return/risk attribution and the Phase 1 request metadata a
results page needs to render a freshness banner, all in one bundle.
"""
from __future__ import annotations

from datetime import date as Date

from pydantic import BaseModel

from app.models.schemas import PortfolioAnalysis
from app.schemas import RequestMeta


class AttributionContribution(BaseModel):
    name: str
    label: str
    contribution_periodic: float


class ReturnAttributionResponse(BaseModel):
    contributions: list[AttributionContribution]
    total_periodic: float
    frequency: str


class RiskAttributionResponse(BaseModel):
    factor_explained_share: float
    idiosyncratic_share: float
    r_squared_raw: float


class AnalysisResponse(BaseModel):
    meta: RequestMeta
    analysis: PortfolioAnalysis
    return_attribution: ReturnAttributionResponse
    risk_attribution: RiskAttributionResponse


class TickerInfo(BaseModel):
    symbol: str
    name: str
    sector: str


class BenchmarkInfo(BaseModel):
    symbol: str
    name: str


class TickerUniverseResponse(BaseModel):
    tickers: list[TickerInfo]
    benchmarks: list[BenchmarkInfo]
    source_note: str


class SampleHolding(BaseModel):
    symbol: str
    weight_pct: float


class SamplePortfolioResponse(BaseModel):
    holdings: list[SampleHolding]
    benchmark: str
    start_date: Date
    end_date: Date
    factor_model: str
    frequency: str
