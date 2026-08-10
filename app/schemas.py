"""Pydantic request/response schemas for the Factor Lens data API.

These shapes are the hand-off contract with Phase 2 (quant-analyst): a
portfolio request in, an aligned bundle of equity/benchmark/factor return
series out, ready to feed CAPM / Fama-French / Markowitz code directly.
"""
from __future__ import annotations

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

FactorModel = Literal["3", "5"]
Frequency = Literal["daily", "monthly"]


class HoldingInput(BaseModel):
    symbol: str = Field(..., description="Equity ticker, e.g. 'AAPL'.")
    weight: float = Field(..., gt=0, le=1, description="Portfolio weight, 0 < w <= 1.")

    @field_validator("symbol")
    @classmethod
    def _normalize_symbol(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("symbol must not be empty")
        return v


class PortfolioRequest(BaseModel):
    holdings: list[HoldingInput] = Field(..., min_length=1)
    benchmark: str = Field(default="^GSPC", description="Benchmark index ticker (yfinance format).")
    start_date: Date
    end_date: Date
    factor_model: FactorModel = Field(default="3", description="'3' or '5' factor Fama-French model.")
    frequency: Frequency = Field(default="daily")

    @field_validator("benchmark")
    @classmethod
    def _normalize_benchmark(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def _validate(self) -> "PortfolioRequest":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")

        symbols = [h.symbol for h in self.holdings]
        if len(symbols) != len(set(symbols)):
            raise ValueError("duplicate symbols in holdings")

        total_weight = sum(h.weight for h in self.holdings)
        if abs(total_weight - 1.0) > 1e-3:
            raise ValueError(f"holding weights must sum to 1.0 (got {total_weight:.4f})")

        return self


class ReturnPoint(BaseModel):
    date: Date
    value: float


class FactorReturnPoint(BaseModel):
    date: Date
    mkt_rf: float
    smb: float
    hml: float
    rmw: float | None = None
    cma: float | None = None
    rf: float


class RequestMeta(BaseModel):
    holdings: list[HoldingInput]
    benchmark: str
    factor_model: FactorModel
    frequency: Frequency
    requested_start_date: Date
    requested_end_date: Date
    aligned_start_date: Date
    aligned_end_date: Date
    n_periods: int
    equity_provider: str
    factor_provider: str


class PortfolioReturnData(BaseModel):
    """Structured, date-aligned return data ready for Phase 2 modeling."""

    meta: RequestMeta
    equity_returns: dict[str, list[ReturnPoint]]
    portfolio_returns: list[ReturnPoint]
    benchmark_returns: list[ReturnPoint]
    factor_returns: list[FactorReturnPoint]
