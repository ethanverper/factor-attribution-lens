"""Live end-to-end check: real Phase 1 data -> Phase 2 models (no mocking).

Mirrors Phase 1's own testing convention (`test_data_integration.py`,
`test_api.py`): real network calls, real OpenBB/Fama-French data, and
plausibility checks rather than exact reference values (live market data
changes daily, so there's no fixed expected beta/loading to assert against).
This is the sanity check that the Phase 1 -> Phase 2 hand-off actually works
against the live bundle, not just synthetic fixtures.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.models.analysis import analyze_portfolio
from app.schemas import HoldingInput, PortfolioRequest
from app.service import build_portfolio_return_data

END = date.today() - timedelta(days=1)
START = END - timedelta(days=365)  # generous window; aligned_start/end will narrow it


def test_live_portfolio_analysis_is_plausible():
    request = PortfolioRequest(
        holdings=[
            HoldingInput(symbol="AAPL", weight=0.5),
            HoldingInput(symbol="MSFT", weight=0.3),
            HoldingInput(symbol="GOOGL", weight=0.2),
        ],
        benchmark="^GSPC",
        start_date=START,
        end_date=END,
        factor_model="3",
        frequency="daily",
    )
    bundle = build_portfolio_return_data(request)
    analysis = analyze_portfolio(bundle, n_frontier_points=20)

    # CAPM: a mega-cap tech portfolio vs S&P 500 should have a plausible, positive beta.
    assert analysis.capm.n_obs == bundle.meta.n_periods
    assert 0.3 < analysis.capm.beta.estimate < 3.0
    assert 0.0 <= analysis.capm.r_squared <= 1.0

    # Fama-French: R^2 should be at least as high as (or comparable to) single-factor CAPM's,
    # since it's a superset regression on the same market factor plus SMB/HML.
    assert 0.0 <= analysis.factor_model.r_squared <= 1.0
    assert analysis.factor_model.n_obs == bundle.meta.n_periods

    # Markowitz: weights sum to 1 everywhere, current portfolio matches input weights.
    frontier = analysis.efficient_frontier
    assert set(frontier.symbols) == {"AAPL", "MSFT", "GOOGL"}
    assert frontier.current_portfolio.weights == {"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2}
    for point in frontier.frontier:
        assert abs(sum(point.weights.values()) - 1.0) < 1e-6
    if frontier.frontier:
        gmv_vol = frontier.global_min_variance.volatility_annualized
        assert all(p.volatility_annualized >= gmv_vol - 1e-6 for p in frontier.frontier)
