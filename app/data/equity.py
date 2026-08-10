"""Equity (and benchmark) price/return data via the OpenBB Open Data Platform.

Uses OpenBB's `equity.price.historical` endpoint against the `yfinance`
provider, which requires no API key. Prices are fetched with
splits-and-dividends adjustment so the resulting return series is a total
return series, consistent with how the Fama-French factors are constructed.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
from openbb import obb

_INTERVAL_BY_FREQUENCY = {"daily": "1d", "monthly": "1M"}


class EquityDataError(RuntimeError):
    """Raised when OpenBB fails to return usable price data for a symbol set."""


def fetch_prices(
    symbols: list[str],
    start: date,
    end: date,
    frequency: str = "daily",
    provider: str = "yfinance",
) -> pd.DataFrame:
    """Fetch adjusted close prices for one or more symbols.

    Returns a wide DataFrame indexed by date, one column per symbol.
    """
    interval = _INTERVAL_BY_FREQUENCY[frequency]
    try:
        result = obb.equity.price.historical(
            symbols,
            start_date=start,
            end_date=end,
            interval=interval,
            adjustment="splits_and_dividends",
            provider=provider,
        )
        df = result.to_df()
    except Exception as exc:  # noqa: BLE001 - surface as a domain error
        raise EquityDataError(f"failed to fetch prices for {symbols}: {exc}") from exc

    if df.empty:
        raise EquityDataError(f"no price data returned for {symbols} in [{start}, {end}]")

    if "symbol" in df.columns:
        wide = df.pivot_table(index=df.index, columns="symbol", values="close")
    else:
        # Single-symbol requests come back without a 'symbol' column.
        wide = df[["close"]].rename(columns={"close": symbols[0]})

    wide.index = pd.to_datetime(wide.index).normalize()
    wide = wide.sort_index()

    missing = [s for s in symbols if s not in wide.columns]
    if missing:
        raise EquityDataError(f"no price data returned for symbol(s): {missing}")

    return wide[symbols]


def prices_to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple period-over-period percent returns, first (NaN) row dropped."""
    returns = prices.pct_change().dropna(how="all")
    return returns
