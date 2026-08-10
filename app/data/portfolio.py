"""Portfolio-level aggregation: weighted returns and cross-series alignment."""
from __future__ import annotations

import pandas as pd


def compute_portfolio_returns(equity_returns: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """Fixed-weight weighted-average return series across holdings.

    Rows with any missing symbol return are dropped so the series stays
    dense (no NaNs) for downstream modeling.
    """
    ordered_symbols = list(weights.keys())
    clean = equity_returns[ordered_symbols].dropna(how="any")
    weight_vector = pd.Series(weights)[ordered_symbols]
    portfolio = clean.mul(weight_vector, axis=1).sum(axis=1)
    portfolio.name = "portfolio"
    return portfolio


def align_on_common_dates(*series: pd.Series | pd.DataFrame) -> list[pd.Series | pd.DataFrame]:
    """Inner-join every series/frame on their shared date index.

    Ensures the bundle handed to Phase 2 is fully dense — no NaNs from
    provider trading-calendar mismatches (e.g. equity vs. Fama-French).
    """
    common_index = series[0].index
    for s in series[1:]:
        common_index = common_index.intersection(s.index)
    common_index = common_index.sort_values()
    return [s.loc[common_index] for s in series]
