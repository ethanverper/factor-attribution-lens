"""Live integration tests against real OpenBB / Fama-French data sources.

These tests make real network calls (no mocking) to verify the data
backbone is actually wired up, per Phase 1's definition of done. They
require network access; if you're offline, they will fail with a
connection error rather than a silent skip -- that's intentional so a
broken integration is never mistaken for a passing one.
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from app.data import equity, factors
from app.data.benchmark import fetch_benchmark_returns

END = date.today() - timedelta(days=1)
START = END - timedelta(days=45)


def test_equity_prices_are_live_and_recent():
    prices = equity.fetch_prices(["AAPL"], START, END, frequency="daily")
    assert not prices.empty
    assert "AAPL" in prices.columns
    # Data should be within the requested window, not some fixed/mocked stub.
    assert prices.index.max().date() <= END
    assert prices.index.max().date() >= END - timedelta(days=10)
    # Real prices are not suspiciously round or constant.
    assert prices["AAPL"].nunique() > 1


def test_equity_returns_are_plausible_daily_pct_moves():
    prices = equity.fetch_prices(["AAPL", "MSFT"], START, END, frequency="daily")
    returns = equity.prices_to_returns(prices)
    assert set(returns.columns) == {"AAPL", "MSFT"}
    # Daily equity returns should almost always be within +/-25%.
    assert returns.abs().max().max() < 0.25


def test_benchmark_returns_are_live():
    benchmark_returns = fetch_benchmark_returns("^GSPC", START, END, frequency="daily")
    assert isinstance(benchmark_returns, pd.Series)
    assert len(benchmark_returns) > 5
    assert benchmark_returns.abs().max() < 0.15


def test_famafrench_3factor_daily_is_live():
    df = factors.fetch_factor_returns("3", "daily", START, END)
    assert set(["Mkt-RF", "SMB", "HML", "RF"]).issubset(df.columns)
    assert len(df) > 0
    # Stored as decimal fractions (French's raw files are in percent).
    assert df["Mkt-RF"].abs().max() < 0.25


def test_famafrench_5factor_monthly_is_live():
    df = factors.fetch_factor_returns("5", "monthly", date(2025, 1, 1), END)
    assert set(["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]).issubset(df.columns)
    assert len(df) > 0
