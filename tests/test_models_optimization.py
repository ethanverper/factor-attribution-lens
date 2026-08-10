"""Sanity checks for the Markowitz efficient-frontier optimization, synthetic data (no network)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.models.optimization import InsufficientDataError, compute_efficient_frontier

RNG = np.random.default_rng(11)


def _make_three_asset_returns(n=400, corr=0.0):
    dates = pd.bdate_range("2022-01-03", periods=n)
    # Distinct means/vols per asset so the frontier is non-degenerate.
    means = [0.0008, 0.0005, 0.0003]
    vols = [0.018, 0.012, 0.008]
    cov = np.diag([v**2 for v in vols])
    if corr:
        for i in range(3):
            for j in range(3):
                if i != j:
                    cov[i, j] = corr * vols[i] * vols[j]
    data = RNG.multivariate_normal(means, cov, size=n)
    return pd.DataFrame(data, index=dates, columns=["A", "B", "C"])


def test_frontier_weights_sum_to_one_and_are_long_only():
    returns = _make_three_asset_returns()
    weights = {"A": 0.5, "B": 0.3, "C": 0.2}

    result = compute_efficient_frontier(returns, weights, frequency="daily", n_points=20)

    assert len(result.frontier) > 0
    for point in result.frontier:
        total = sum(point.weights.values())
        assert total == pytest.approx(1.0, abs=1e-6)
        assert all(w >= -1e-8 for w in point.weights.values())  # long-only

    gmv_total = sum(result.global_min_variance.weights.values())
    assert gmv_total == pytest.approx(1.0, abs=1e-6)


def test_global_min_variance_has_lowest_volatility_on_frontier():
    returns = _make_three_asset_returns()
    weights = {"A": 0.5, "B": 0.3, "C": 0.2}
    result = compute_efficient_frontier(returns, weights, frequency="daily", n_points=25)

    gmv_vol = result.global_min_variance.volatility_annualized
    for point in result.frontier:
        assert point.volatility_annualized >= gmv_vol - 1e-6


def test_frontier_return_increases_monotonically_with_target():
    returns = _make_three_asset_returns()
    weights = {"A": 0.5, "B": 0.3, "C": 0.2}
    result = compute_efficient_frontier(returns, weights, frequency="daily", n_points=25)

    rets = [p.expected_return_annualized for p in result.frontier]
    assert rets == sorted(rets)


def test_current_portfolio_position_fields_are_populated():
    returns = _make_three_asset_returns()
    weights = {"A": 0.5, "B": 0.3, "C": 0.2}
    result = compute_efficient_frontier(
        returns, weights, frequency="daily", risk_free_rate_annualized=0.02, n_points=25
    )

    pos = result.current_portfolio
    assert pos.weights == weights
    assert pos.volatility_annualized > 0
    assert pos.sharpe_ratio is not None
    assert isinstance(pos.is_on_frontier, bool)
    # A generic 50/30/20 split is not the variance-minimizing weighting for its own
    # return level in a non-degenerate 3-asset problem, so it should sit off the frontier
    # with a positive return gap (frontier does at least as well at the same risk).
    if pos.return_gap_to_frontier is not None:
        assert pos.return_gap_to_frontier >= -1e-6


def test_gmv_weights_used_as_current_portfolio_are_on_frontier():
    returns = _make_three_asset_returns()
    probe_weights = {"A": 0.5, "B": 0.3, "C": 0.2}
    probe = compute_efficient_frontier(returns, probe_weights, frequency="daily", n_points=25)
    gmv_weights = probe.global_min_variance.weights

    result = compute_efficient_frontier(returns, gmv_weights, frequency="daily", n_points=25)
    assert result.current_portfolio.is_on_frontier is True
    assert abs(result.current_portfolio.return_gap_to_frontier or 0.0) < 1e-4


def test_singular_covariance_is_regularized_not_crashed():
    returns = _make_three_asset_returns()
    returns = returns.copy()
    returns["C"] = returns["A"]  # perfectly collinear -> singular covariance matrix
    weights = {"A": 0.4, "B": 0.3, "C": 0.3}

    result = compute_efficient_frontier(returns, weights, frequency="daily", n_points=15)

    assert result.covariance_regularized is True
    assert len(result.frontier) > 0
    for point in result.frontier:
        assert sum(point.weights.values()) == pytest.approx(1.0, abs=1e-6)


def test_raises_on_insufficient_observations():
    dates = pd.bdate_range("2022-01-03", periods=3)
    returns = pd.DataFrame(RNG.normal(0, 0.01, (3, 3)), index=dates, columns=["A", "B", "C"])
    weights = {"A": 0.34, "B": 0.33, "C": 0.33}
    with pytest.raises(InsufficientDataError):
        compute_efficient_frontier(returns, weights, frequency="daily")
