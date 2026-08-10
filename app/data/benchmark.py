"""Benchmark index data via the OpenBB Open Data Platform.

Benchmarks (e.g. ^GSPC for the S&P 500) are fetched through the same
`equity.price.historical` path as individual holdings — index tickers are
served by the same yfinance provider — kept as a separate module because it
is a distinct data concern from an individual holding's return series.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from app.data.equity import fetch_prices, prices_to_returns


def fetch_benchmark_returns(symbol: str, start: date, end: date, frequency: str = "daily") -> pd.Series:
    prices = fetch_prices([symbol], start, end, frequency=frequency)
    returns = prices_to_returns(prices)
    return returns[symbol]
