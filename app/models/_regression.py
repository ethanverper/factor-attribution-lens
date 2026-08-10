"""Shared OLS regression helper for CAPM and Fama-French factor models.

Private module (leading underscore) -- not part of the package's public
interface; `capm.py` and `fama_french.py` both build on this so the
standard-error convention (see decision 0003) is applied consistently
rather than reimplemented twice.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import statsmodels.api as sm

from app.models.schemas import RegressionCoefficient

STANDARD_ERROR_CONVENTION = "HAC (Newey-West)"


def newey_west_maxlags(n_obs: int) -> int:
    """Newey & West (1994) plug-in bandwidth: floor(4*(n/100)^(2/9)), min 1."""
    return max(1, int(math.floor(4 * (n_obs / 100.0) ** (2.0 / 9.0))))


def fit_ols_hac(y: pd.Series, x: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Fit y ~ X (with intercept) via OLS, reporting Newey-West HAC standard errors.

    Daily/monthly asset returns are routinely heteroskedastic and mildly
    autocorrelated, so classical OLS standard errors understate estimation
    uncertainty on the factor loadings. HAC (Newey-West) is the standard
    correction and is what this package always applies -- see decision
    0003 for the full rationale.
    """
    X = sm.add_constant(x, has_constant="add")
    n_obs = len(y)
    maxlags = newey_west_maxlags(n_obs)
    model = sm.OLS(y.values, X.values, missing="raise")
    return model.fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})


def coefficients_from_fit(
    fit: sm.regression.linear_model.RegressionResultsWrapper, names: list[str]
) -> list[RegressionCoefficient]:
    """Extract every coefficient (including the intercept, named 'alpha') as a RegressionCoefficient."""
    ci = fit.conf_int(alpha=0.05)
    out = []
    for i, name in enumerate(names):
        out.append(
            RegressionCoefficient(
                name=name,
                estimate=float(fit.params[i]),
                std_error=float(fit.bse[i]),
                t_stat=float(fit.tvalues[i]),
                p_value=float(fit.pvalues[i]),
                ci_lower_95=float(np.asarray(ci)[i, 0]),
                ci_upper_95=float(np.asarray(ci)[i, 1]),
            )
        )
    return out
