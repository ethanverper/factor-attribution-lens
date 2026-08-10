"""End-to-end check of analyze_portfolio() against a synthetic (no-network) Phase 1 bundle.

Builds a `PortfolioReturnData` object directly (the exact shape Phase 1's
`/portfolio/returns` endpoint returns) rather than calling the live API, so
this test is fast, deterministic, and runs offline -- complementary to
`test_models_integration.py`, which does exercise the real Phase 1 -> Phase 2
chain against live data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.models.analysis import analyze_portfolio
from app.schemas import (
    FactorReturnPoint,
    HoldingInput,
    PortfolioReturnData,
    RequestMeta,
    ReturnPoint,
)

RNG = np.random.default_rng(99)


def _build_synthetic_bundle(n=300) -> PortfolioReturnData:
    dates = pd.bdate_range("2023-01-03", periods=n)
    date_list = [d.date() for d in dates]

    mkt_rf = RNG.normal(0.0004, 0.009, n)
    smb = RNG.normal(0.0001, 0.004, n)
    hml = RNG.normal(0.0001, 0.004, n)
    rf = np.full(n, 0.0001)

    aapl = rf + 0.0001 + 1.2 * mkt_rf + 0.1 * smb - 0.2 * hml + RNG.normal(0, 0.006, n)
    msft = rf + 0.0001 + 1.0 * mkt_rf + 0.0 * smb - 0.1 * hml + RNG.normal(0, 0.006, n)
    benchmark = rf + mkt_rf  # by FF construction, Mkt-RF + RF ~= market return

    weights = {"AAPL": 0.6, "MSFT": 0.4}
    portfolio = weights["AAPL"] * aapl + weights["MSFT"] * msft

    def pts(values):
        return [ReturnPoint(date=d, value=float(v)) for d, v in zip(date_list, values)]

    holdings = [HoldingInput(symbol=s, weight=w) for s, w in weights.items()]
    meta = RequestMeta(
        holdings=holdings,
        benchmark="^GSPC",
        factor_model="3",
        frequency="daily",
        requested_start_date=date_list[0],
        requested_end_date=date_list[-1],
        aligned_start_date=date_list[0],
        aligned_end_date=date_list[-1],
        n_periods=n,
        equity_provider="synthetic-test",
        factor_provider="synthetic-test",
    )
    factor_points = [
        FactorReturnPoint(date=d, mkt_rf=float(m), smb=float(s), hml=float(h), rmw=None, cma=None, rf=float(r))
        for d, m, s, h, r in zip(date_list, mkt_rf, smb, hml, rf)
    ]
    return PortfolioReturnData(
        meta=meta,
        equity_returns={"AAPL": pts(aapl), "MSFT": pts(msft)},
        portfolio_returns=pts(portfolio),
        benchmark_returns=pts(benchmark),
        factor_returns=factor_points,
    )


def test_analyze_portfolio_end_to_end_shapes():
    bundle = _build_synthetic_bundle()
    analysis = analyze_portfolio(bundle, n_frontier_points=15)

    # CAPM
    assert analysis.capm.n_obs == 300
    assert 0.0 <= analysis.capm.r_squared <= 1.0
    assert analysis.capm.beta.estimate > 0  # both holdings are positive-beta by construction

    # Fama-French
    assert analysis.factor_model.factor_model == "3"
    assert {c.name for c in analysis.factor_model.factor_loadings} == {"mkt_rf", "smb", "hml"}
    assert 0.0 <= analysis.factor_model.r_squared <= 1.0

    # Markowitz frontier
    frontier = analysis.efficient_frontier
    assert set(frontier.symbols) == {"AAPL", "MSFT"}
    assert len(frontier.frontier) > 0
    for point in frontier.frontier:
        assert sum(point.weights.values()) == pytest.approx(1.0, abs=1e-6)
    assert frontier.current_portfolio.weights == {"AAPL": 0.6, "MSFT": 0.4}
    assert frontier.risk_free_rate_annualized > 0  # rf=0.0001/day compounds to a positive annual rate


def test_analyze_portfolio_respects_factor_model_choice_in_meta():
    bundle = _build_synthetic_bundle(n=200)
    # meta says "3" -- factor_model result should follow it even though caller didn't override.
    analysis = analyze_portfolio(bundle)
    assert analysis.factor_model.factor_model == bundle.meta.factor_model
