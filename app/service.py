"""Orchestrates a PortfolioRequest into aligned, structured return data."""
from __future__ import annotations

import pandas as pd

from app.data import equity, factors, portfolio
from app.data.benchmark import fetch_benchmark_returns
from app.schemas import (
    FactorReturnPoint,
    PortfolioRequest,
    PortfolioReturnData,
    RequestMeta,
    ReturnPoint,
)

_FACTOR_COLUMN_MAP = {
    "Mkt-RF": "mkt_rf",
    "SMB": "smb",
    "HML": "hml",
    "RMW": "rmw",
    "CMA": "cma",
    "RF": "rf",
}


def _series_to_points(series: pd.Series) -> list[ReturnPoint]:
    return [ReturnPoint(date=idx.date(), value=float(val)) for idx, val in series.items()]


def _factors_to_points(df: pd.DataFrame) -> list[FactorReturnPoint]:
    points = []
    for idx, row in df.iterrows():
        kwargs = {"date": idx.date()}
        for col, field in _FACTOR_COLUMN_MAP.items():
            kwargs[field] = float(row[col]) if col in df.columns else None
        points.append(FactorReturnPoint(**kwargs))
    return points


def build_portfolio_return_data(request: PortfolioRequest) -> PortfolioReturnData:
    symbols = [h.symbol for h in request.holdings]
    weights = {h.symbol: h.weight for h in request.holdings}

    prices = equity.fetch_prices(symbols, request.start_date, request.end_date, frequency=request.frequency)
    equity_returns = equity.prices_to_returns(prices)

    benchmark_returns = fetch_benchmark_returns(
        request.benchmark, request.start_date, request.end_date, frequency=request.frequency
    )

    factor_returns = factors.fetch_factor_returns(
        request.factor_model, request.frequency, request.start_date, request.end_date
    )

    portfolio_returns = portfolio.compute_portfolio_returns(equity_returns, weights)

    equity_returns_aligned, portfolio_returns_aligned, benchmark_returns_aligned, factor_returns_aligned = (
        portfolio.align_on_common_dates(equity_returns, portfolio_returns, benchmark_returns, factor_returns)
    )

    if len(portfolio_returns_aligned) == 0:
        raise ValueError(
            "no overlapping dates across equity, benchmark, and factor data for the requested range"
        )

    aligned_index = portfolio_returns_aligned.index

    meta = RequestMeta(
        holdings=request.holdings,
        benchmark=request.benchmark,
        factor_model=request.factor_model,
        frequency=request.frequency,
        requested_start_date=request.start_date,
        requested_end_date=request.end_date,
        aligned_start_date=aligned_index.min().date(),
        aligned_end_date=aligned_index.max().date(),
        n_periods=len(aligned_index),
        equity_provider="yfinance (via OpenBB Open Data Platform)",
        factor_provider="Kenneth French Data Library (via pandas-datareader)",
    )

    return PortfolioReturnData(
        meta=meta,
        equity_returns={sym: _series_to_points(equity_returns_aligned[sym]) for sym in symbols},
        portfolio_returns=_series_to_points(portfolio_returns_aligned),
        benchmark_returns=_series_to_points(benchmark_returns_aligned),
        factor_returns=_factors_to_points(factor_returns_aligned),
    )
