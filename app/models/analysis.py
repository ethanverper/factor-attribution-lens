"""Top-level orchestrator: Phase 1 return bundle -> full Phase 2 analysis.

This is the primary entry point Phase 3 (`business-intelligence`) and
Phase 4 (`educator`) should call: `analyze_portfolio(data)` where `data`
is exactly what `POST /portfolio/returns` returns (a `PortfolioReturnData`).
It runs CAPM, the Fama-French regression (3- or 5-factor, matching
whatever `data.meta.factor_model` was requested from Phase 1), and the
Markowitz efficient frontier, and returns one bundled `PortfolioAnalysis`.
"""
from __future__ import annotations

from app.models.adapters import bundle_to_frames
from app.models.capm import estimate_capm_beta
from app.models.fama_french import estimate_factor_model
from app.models.optimization import compute_efficient_frontier
from app.models.schemas import PortfolioAnalysis
from app.schemas import PortfolioReturnData


def analyze_portfolio(
    data: PortfolioReturnData,
    *,
    n_frontier_points: int = 25,
    allow_short: bool = False,
) -> PortfolioAnalysis:
    """Run CAPM, Fama-French, and Markowitz frontier analysis on a return bundle.

    `n_frontier_points` and `allow_short` are the only knobs exposed here;
    everything else (standard-error convention, covariance regularization,
    annualization convention) is a fixed methodology choice documented in
    `docs/decisions/0003-phase2-quant-methodology.md` so results are
    reproducible and comparable across portfolios.
    """
    frames = bundle_to_frames(data)

    capm_result = estimate_capm_beta(
        frames.portfolio_returns,
        frames.benchmark_returns,
        frames.factor_returns["rf"],
        benchmark_name=frames.benchmark_name,
        frequency=frames.frequency,
    )

    factor_result = estimate_factor_model(
        frames.portfolio_returns,
        frames.factor_returns,
        factor_model=data.meta.factor_model,
        frequency=frames.frequency,
    )

    rf_periodic_mean = float(frames.factor_returns["rf"].mean())
    rf_annualized = (1.0 + rf_periodic_mean) ** frames.periods_per_year - 1.0

    frontier_result = compute_efficient_frontier(
        frames.equity_returns,
        frames.weights,
        risk_free_rate_annualized=rf_annualized,
        frequency=frames.frequency,
        n_points=n_frontier_points,
        allow_short=allow_short,
    )

    return PortfolioAnalysis(
        capm=capm_result,
        factor_model=factor_result,
        efficient_frontier=frontier_result,
    )
