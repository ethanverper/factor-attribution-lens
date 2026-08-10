"""Adapters from Phase 1's `PortfolioReturnData` wire format to pandas.

Kept as a thin, separate layer so the actual statistical code (capm.py,
fama_french.py, optimization.py) operates on plain pandas Series/DataFrames
and stays independently testable with synthetic data, without importing
FastAPI/Pydantic request plumbing.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.schemas import PortfolioReturnData

PERIODS_PER_YEAR = {"daily": 252, "monthly": 12}


@dataclass(frozen=True)
class ReturnFrames:
    """Pandas-native view of a Phase 1 return bundle."""

    equity_returns: pd.DataFrame  # columns = symbols, index = date
    portfolio_returns: pd.Series
    benchmark_returns: pd.Series
    factor_returns: pd.DataFrame  # columns among mkt_rf, smb, hml, rmw, cma, rf
    weights: dict[str, float]
    frequency: str
    periods_per_year: int
    benchmark_name: str


def _points_to_series(points, name: str) -> pd.Series:
    idx = pd.to_datetime([p.date for p in points])
    vals = [p.value for p in points]
    return pd.Series(vals, index=idx, name=name).sort_index()


def bundle_to_frames(data: PortfolioReturnData) -> ReturnFrames:
    """Convert a Phase 1 `PortfolioReturnData` response into pandas structures."""
    equity_cols = {
        sym: _points_to_series(points, sym) for sym, points in data.equity_returns.items()
    }
    equity_returns = pd.DataFrame(equity_cols).sort_index()

    portfolio_returns = _points_to_series(data.portfolio_returns, "portfolio")
    benchmark_returns = _points_to_series(data.benchmark_returns, data.meta.benchmark)

    factor_idx = pd.to_datetime([p.date for p in data.factor_returns])
    factor_rows = [
        {
            "mkt_rf": p.mkt_rf,
            "smb": p.smb,
            "hml": p.hml,
            "rmw": p.rmw,
            "cma": p.cma,
            "rf": p.rf,
        }
        for p in data.factor_returns
    ]
    factor_returns = pd.DataFrame(factor_rows, index=factor_idx).sort_index()
    factor_returns = factor_returns.dropna(axis=1, how="all")  # drop rmw/cma if 3-factor

    weights = {h.symbol: h.weight for h in data.meta.holdings}

    frequency = data.meta.frequency
    return ReturnFrames(
        equity_returns=equity_returns,
        portfolio_returns=portfolio_returns,
        benchmark_returns=benchmark_returns,
        factor_returns=factor_returns,
        weights=weights,
        frequency=frequency,
        periods_per_year=PERIODS_PER_YEAR[frequency],
        benchmark_name=data.meta.benchmark,
    )
