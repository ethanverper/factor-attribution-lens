"""Fama-French 3- or 5-factor regression on portfolio excess returns.

R_p - R_f = alpha + b1*Mkt-RF + b2*SMB + b3*HML [+ b4*RMW + b5*CMA] + e

3-factor is this package's default (see decision 0003 for why); 5-factor
is supported as the roadmap's stated stretch goal whenever the caller's
factor bundle carries RMW/CMA (i.e. was requested with `factor_model="5"`
from Phase 1's API).
"""
from __future__ import annotations

import math
from typing import Literal

import pandas as pd

from app.models._regression import STANDARD_ERROR_CONVENTION, coefficients_from_fit, fit_ols_hac
from app.models.adapters import PERIODS_PER_YEAR
from app.models.schemas import FactorModelResult

FactorModelChoice = Literal["3", "5"]

FACTOR_COLUMNS: dict[str, list[str]] = {
    "3": ["mkt_rf", "smb", "hml"],
    "5": ["mkt_rf", "smb", "hml", "rmw", "cma"],
}


class InsufficientDataError(ValueError):
    """Raised when there are too few overlapping observations to regress."""


class MissingFactorsError(ValueError):
    """Raised when the requested factor model needs columns the bundle doesn't have."""


def estimate_factor_model(
    portfolio_returns: pd.Series,
    factor_returns: pd.DataFrame,
    *,
    factor_model: FactorModelChoice = "3",
    frequency: str = "daily",
) -> FactorModelResult:
    """Estimate Fama-French factor loadings for `portfolio_returns`.

    `factor_returns` must have an 'rf' column plus at least the 3-factor
    set (mkt_rf, smb, hml); rmw/cma are required only if factor_model="5".
    """
    cols = FACTOR_COLUMNS[factor_model]
    missing = [c for c in cols + ["rf"] if c not in factor_returns.columns]
    if missing:
        raise MissingFactorsError(
            f"factor_model='{factor_model}' requires columns {cols + ['rf']}, missing: {missing}"
        )

    df = pd.concat(
        {"portfolio": portfolio_returns, **{c: factor_returns[c] for c in cols + ["rf"]}},
        axis=1,
        join="inner",
    ).dropna()

    min_obs = 5 * (len(cols) + 1)  # rule of thumb: >= 5 obs per estimated parameter
    if len(df) < min_obs:
        raise InsufficientDataError(
            f"only {len(df)} overlapping observations available; need at least {min_obs} "
            f"for a {len(cols)}-factor regression"
        )

    excess_portfolio = df["portfolio"] - df["rf"]
    X = df[cols]

    fit = fit_ols_hac(excess_portfolio, X)
    coefs = coefficients_from_fit(fit, ["alpha"] + cols)
    alpha, loadings = coefs[0], coefs[1:]

    periods_per_year = PERIODS_PER_YEAR[frequency]
    alpha_annualized = (1.0 + alpha.estimate) ** periods_per_year - 1.0

    return FactorModelResult(
        factor_model=factor_model,
        frequency=frequency,
        n_obs=len(df),
        alpha=alpha,
        factor_loadings=loadings,
        alpha_annualized=float(alpha_annualized),
        r_squared=float(fit.rsquared),
        adj_r_squared=float(fit.rsquared_adj),
        residual_std_error=float(math.sqrt(fit.mse_resid)),
        standard_error_convention=STANDARD_ERROR_CONVENTION,
        f_statistic=float(fit.fvalue),
        f_p_value=float(fit.f_pvalue),
    )
