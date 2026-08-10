"""Sanity/reference-value checks for the Fama-French factor regression, synthetic data (no network)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.models.fama_french import (
    InsufficientDataError,
    MissingFactorsError,
    estimate_factor_model,
)

RNG = np.random.default_rng(7)


def _make_ff3_data(n=600, true_alpha=0.0001, true_loadings=(1.1, 0.4, -0.3), noise_std=0.004):
    dates = pd.bdate_range("2022-01-03", periods=n)
    factors = pd.DataFrame(
        {
            "mkt_rf": RNG.normal(0.0004, 0.009, n),
            "smb": RNG.normal(0.0001, 0.004, n),
            "hml": RNG.normal(0.0001, 0.004, n),
            "rf": 0.0001,
        },
        index=dates,
    )
    b1, b2, b3 = true_loadings
    noise = RNG.normal(0.0, noise_std, n)
    portfolio = (
        factors["rf"]
        + true_alpha
        + b1 * factors["mkt_rf"]
        + b2 * factors["smb"]
        + b3 * factors["hml"]
        + noise
    )
    portfolio.name = "portfolio"
    return portfolio, factors


def test_ff3_recovers_known_loadings():
    true_alpha = 0.0001
    true_loadings = (1.1, 0.4, -0.3)
    portfolio, factors = _make_ff3_data(true_alpha=true_alpha, true_loadings=true_loadings)

    result = estimate_factor_model(portfolio, factors, factor_model="3", frequency="daily")

    assert result.factor_model == "3"
    assert result.n_obs == len(portfolio)
    assert len(result.factor_loadings) == 3
    names = [c.name for c in result.factor_loadings]
    assert names == ["mkt_rf", "smb", "hml"]

    estimates = {c.name: c.estimate for c in result.factor_loadings}
    assert abs(estimates["mkt_rf"] - true_loadings[0]) < 0.15
    assert abs(estimates["smb"] - true_loadings[1]) < 0.2
    assert abs(estimates["hml"] - true_loadings[2]) < 0.2
    assert abs(result.alpha.estimate - true_alpha) < 0.001

    # Given the noise level relative to factor variance, R^2 should be high but not perfect.
    assert 0.5 < result.r_squared < 1.0
    assert result.adj_r_squared <= result.r_squared
    assert result.f_p_value < 0.01  # jointly significant


def test_ff3_requires_all_three_factor_columns():
    dates = pd.bdate_range("2022-01-03", periods=50)
    factors = pd.DataFrame(
        {"mkt_rf": RNG.normal(0, 0.01, 50), "rf": 0.0}, index=dates
    )  # missing smb, hml
    portfolio = pd.Series(RNG.normal(0, 0.01, 50), index=dates)
    with pytest.raises(MissingFactorsError):
        estimate_factor_model(portfolio, factors, factor_model="3")


def test_ff5_requires_rmw_cma_columns():
    portfolio, factors = _make_ff3_data(n=100)  # no rmw/cma
    with pytest.raises(MissingFactorsError):
        estimate_factor_model(portfolio, factors, factor_model="5")


def test_raises_on_too_few_observations_for_factor_count():
    portfolio, factors = _make_ff3_data(n=8)  # fewer than 5*(3+1)=20 required
    with pytest.raises(InsufficientDataError):
        estimate_factor_model(portfolio, factors, factor_model="3")
