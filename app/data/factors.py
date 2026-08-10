"""Fama-French factor return series from Kenneth French's Data Library.

OpenBB's Open Data Platform does not itself carry academic factor-return
series (it aggregates market/economic data providers, not the Dartmouth
Fama-French library). `pandas-datareader`'s `famafrench` reader pulls
directly and live from Kenneth French's Data Library (Dartmouth), the
canonical, industry-standard source for these series — the same underlying
data OpenBB's own equity/benchmark prices are meant to be regressed against
in Phase 2.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
from pandas_datareader.famafrench import FamaFrenchReader

_DATASET_NAMES = {
    ("3", "daily"): "F-F_Research_Data_Factors_daily",
    ("3", "monthly"): "F-F_Research_Data_Factors",
    ("5", "daily"): "F-F_Research_Data_5_Factors_2x3_daily",
    ("5", "monthly"): "F-F_Research_Data_5_Factors_2x3",
}


class FactorDataError(RuntimeError):
    """Raised when the Fama-French factor library fails to return data."""


def fetch_factor_returns(
    factor_model: str,
    frequency: str,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Fetch Fama-French factor returns as decimal fractions (not percent).

    Returns a DataFrame indexed by date (period start, for monthly) with
    columns among {Mkt-RF, SMB, HML, RMW, CMA, RF} depending on factor_model.
    """
    dataset = _DATASET_NAMES[(factor_model, frequency)]
    try:
        reader = FamaFrenchReader(dataset, start=start, end=end)
        raw = reader.read()
    except Exception as exc:  # noqa: BLE001 - surface as a domain error
        raise FactorDataError(f"failed to fetch Fama-French dataset '{dataset}': {exc}") from exc

    df = raw[0]
    if df.empty:
        raise FactorDataError(
            f"no Fama-French data returned for dataset '{dataset}' in [{start}, {end}]"
        )

    if isinstance(df.index, pd.PeriodIndex):
        df = df.copy()
        df.index = df.index.to_timestamp(how="start")
    else:
        df.index = pd.to_datetime(df.index).normalize()

    df = df.sort_index() / 100.0  # French's files are in percent (e.g. -0.62 == -0.62%)
    df.columns = [c.strip() for c in df.columns]
    return df
