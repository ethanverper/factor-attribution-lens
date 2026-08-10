"""Unit tests for the PortfolioReturnData -> pandas adapter."""
from __future__ import annotations

from datetime import date

from app.models.adapters import PERIODS_PER_YEAR, bundle_to_frames
from app.schemas import (
    FactorReturnPoint,
    HoldingInput,
    PortfolioReturnData,
    RequestMeta,
    ReturnPoint,
)


def _bundle() -> PortfolioReturnData:
    d0, d1 = date(2024, 1, 2), date(2024, 1, 3)
    meta = RequestMeta(
        holdings=[HoldingInput(symbol="AAPL", weight=0.6), HoldingInput(symbol="MSFT", weight=0.4)],
        benchmark="^GSPC",
        factor_model="3",
        frequency="daily",
        requested_start_date=d0,
        requested_end_date=d1,
        aligned_start_date=d0,
        aligned_end_date=d1,
        n_periods=2,
        equity_provider="test",
        factor_provider="test",
    )
    return PortfolioReturnData(
        meta=meta,
        equity_returns={
            "AAPL": [ReturnPoint(date=d0, value=0.01), ReturnPoint(date=d1, value=0.02)],
            "MSFT": [ReturnPoint(date=d0, value=0.005), ReturnPoint(date=d1, value=0.015)],
        },
        portfolio_returns=[ReturnPoint(date=d0, value=0.008), ReturnPoint(date=d1, value=0.018)],
        benchmark_returns=[ReturnPoint(date=d0, value=0.009), ReturnPoint(date=d1, value=0.017)],
        factor_returns=[
            FactorReturnPoint(date=d0, mkt_rf=0.007, smb=0.001, hml=-0.001, rmw=None, cma=None, rf=0.0001),
            FactorReturnPoint(date=d1, mkt_rf=0.016, smb=0.002, hml=-0.002, rmw=None, cma=None, rf=0.0001),
        ],
    )


def test_bundle_to_frames_shapes_and_values():
    frames = bundle_to_frames(_bundle())

    assert list(frames.equity_returns.columns) == ["AAPL", "MSFT"]
    assert len(frames.equity_returns) == 2
    assert frames.equity_returns.loc["2024-01-02", "AAPL"] == 0.01

    assert len(frames.portfolio_returns) == 2
    assert len(frames.benchmark_returns) == 2

    # rmw/cma are all-None (3-factor request) -> dropped, not carried as all-NaN columns.
    assert list(frames.factor_returns.columns) == ["mkt_rf", "smb", "hml", "rf"]

    assert frames.weights == {"AAPL": 0.6, "MSFT": 0.4}
    assert frames.frequency == "daily"
    assert frames.periods_per_year == PERIODS_PER_YEAR["daily"]
    assert frames.benchmark_name == "^GSPC"
