"""CAPM beta estimation: R_p - R_f = alpha + beta * (R_m - R_f) + e.

Single-factor OLS of the portfolio's excess return on the benchmark's
excess return. See `_regression.py` for the standard-error convention
(Newey-West HAC) applied here and in `fama_french.py`.
"""
from __future__ import annotations

import math

import pandas as pd

from app.models._regression import STANDARD_ERROR_CONVENTION, coefficients_from_fit, fit_ols_hac
from app.models.adapters import PERIODS_PER_YEAR
from app.models.schemas import CAPMResult

MIN_OBS = 10


class InsufficientDataError(ValueError):
    """Raised when there are too few overlapping observations to regress."""


def estimate_capm_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_returns: pd.Series,
    *,
    benchmark_name: str = "benchmark",
    frequency: str = "daily",
) -> CAPMResult:
    """Estimate CAPM alpha/beta of `portfolio_returns` vs. `benchmark_returns`.

    All three series are inner-joined on their date index first (in case
    the caller passes series that aren't already aligned); the aligned
    length after dropping any remaining NaNs is `n_obs`.
    """
    df = pd.concat(
        {"portfolio": portfolio_returns, "benchmark": benchmark_returns, "rf": risk_free_returns},
        axis=1,
        join="inner",
    ).dropna()

    if len(df) < MIN_OBS:
        raise InsufficientDataError(
            f"only {len(df)} overlapping observations available; need at least {MIN_OBS} to regress"
        )

    excess_portfolio = df["portfolio"] - df["rf"]
    excess_benchmark = (df["benchmark"] - df["rf"]).to_frame(name="mkt_rf")

    fit = fit_ols_hac(excess_portfolio, excess_benchmark)
    coefs = coefficients_from_fit(fit, ["alpha", "beta"])
    alpha, beta = coefs

    periods_per_year = PERIODS_PER_YEAR[frequency]
    alpha_annualized = (1.0 + alpha.estimate) ** periods_per_year - 1.0

    return CAPMResult(
        benchmark=benchmark_name,
        frequency=frequency,
        n_obs=len(df),
        alpha=alpha,
        beta=beta,
        alpha_annualized=float(alpha_annualized),
        r_squared=float(fit.rsquared),
        adj_r_squared=float(fit.rsquared_adj),
        residual_std_error=float(math.sqrt(fit.mse_resid)),
        standard_error_convention=STANDARD_ERROR_CONVENTION,
    )
