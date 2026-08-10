"""Sanity/reference-value checks for CAPM beta estimation, synthetic data (no network).

Approach: simulate returns from a known data-generating process (a chosen
true alpha/beta plus noise), then check the OLS estimate recovers the true
parameters within a statistically reasonable tolerance. This is the
appropriate validation for an estimator (there's no single external
"reference value" for CAPM beta the way there is for, say, a known
options price) -- see roadmap Phase 2 definition of done and Phase 5's
independent QA charter for further verification.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.models.capm import InsufficientDataError, estimate_capm_beta

RNG = np.random.default_rng(42)


def _make_capm_series(n=500, true_alpha=0.0002, true_beta=1.3, noise_std=0.006, rf_level=0.0001):
    dates = pd.bdate_range("2023-01-02", periods=n)
    rf = pd.Series(rf_level, index=dates)
    benchmark = pd.Series(RNG.normal(0.0005, 0.01, n), index=dates)
    noise = RNG.normal(0.0, noise_std, n)
    portfolio = rf + true_alpha + true_beta * (benchmark - rf) + noise
    return portfolio, benchmark, rf


def test_capm_recovers_known_beta_and_alpha():
    true_alpha, true_beta = 0.0002, 1.3
    portfolio, benchmark, rf = _make_capm_series(true_alpha=true_alpha, true_beta=true_beta)

    result = estimate_capm_beta(portfolio, benchmark, rf, benchmark_name="^GSPC", frequency="daily")

    assert result.n_obs == len(portfolio)
    assert abs(result.beta.estimate - true_beta) < 0.15
    assert abs(result.alpha.estimate - true_alpha) < 0.001
    # Beta should be estimated with high confidence given 500 obs and this noise level.
    assert result.beta.p_value < 0.01
    assert result.beta.ci_lower_95 < true_beta < result.beta.ci_upper_95
    assert 0.6 < result.r_squared <= 1.0
    assert result.standard_error_convention == "HAC (Newey-West)"


def test_capm_beta_near_one_for_market_matching_portfolio():
    # A portfolio that IS the benchmark (beta=1, alpha=0, no noise) should recover beta ~ 1.0 exactly.
    dates = pd.bdate_range("2023-01-02", periods=100)
    rf = pd.Series(0.0, index=dates)
    benchmark = pd.Series(RNG.normal(0.0004, 0.008, 100), index=dates)
    result = estimate_capm_beta(benchmark, benchmark, rf, frequency="daily")
    assert result.beta.estimate == pytest.approx(1.0, abs=1e-6)
    assert result.alpha.estimate == pytest.approx(0.0, abs=1e-9)
    assert result.r_squared == pytest.approx(1.0, abs=1e-9)


def test_capm_raises_on_insufficient_overlap():
    dates_a = pd.bdate_range("2023-01-02", periods=5)
    dates_b = pd.bdate_range("2023-06-02", periods=5)  # no overlap with dates_a
    portfolio = pd.Series(RNG.normal(0, 0.01, 5), index=dates_a)
    benchmark = pd.Series(RNG.normal(0, 0.01, 5), index=dates_b)
    rf = pd.Series(0.0, index=dates_a)
    with pytest.raises(InsufficientDataError):
        estimate_capm_beta(portfolio, benchmark, rf)


def test_capm_annualization_is_compounding_not_linear():
    portfolio, benchmark, rf = _make_capm_series(n=252, true_alpha=0.0002, true_beta=1.0, noise_std=0.0)
    result = estimate_capm_beta(portfolio, benchmark, rf, frequency="daily")
    expected = (1.0 + result.alpha.estimate) ** 252 - 1.0
    assert result.alpha_annualized == pytest.approx(expected, rel=1e-9)
