"""Markowitz mean-variance efficient frontier and current-portfolio positioning.

Methodology (see decision 0003 for the full rationale):
- Sample mean/covariance of historical per-period holding returns, scaled
  to annual terms under the standard i.i.d.-returns assumption (mean *
  periods_per_year, covariance * periods_per_year) -- the textbook
  Markowitz convention, distinct from the compounding convention used for
  CAPM/factor-model alpha reporting elsewhere in this package.
- Long-only by default (`allow_short=False`): retail/small-RIA holdings
  are long positions in practice, and unconstrained short-selling produces
  frontiers that don't reflect what most users can actually implement.
  Settable via `allow_short=True` for analysts who want the textbook
  unconstrained frontier.
- Solver: `scipy.optimize.minimize` with SLSQP (sequential least squares
  quadratic programming), which natively handles the equality (weights
  sum to 1, and for frontier points, target return) and inequality
  (long-only bounds) constraints this problem needs.
- Covariance regularization: see `covariance.py`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from app.models.adapters import PERIODS_PER_YEAR
from app.models.covariance import estimate_covariance
from app.models.schemas import EfficientFrontierResult, FrontierPoint, PortfolioPosition

_SOLVER_OPTIONS = {"maxiter": 1000, "ftol": 1e-14}
_ON_FRONTIER_REL_TOL = 1e-4


class InsufficientDataError(ValueError):
    pass


def _portfolio_stats(w: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> tuple[float, float]:
    ret = float(w @ mean)
    vol = float(np.sqrt(max(w @ cov @ w, 0.0)))
    return ret, vol


def _solve_min_variance(
    cov: np.ndarray,
    n: int,
    *,
    mean: np.ndarray | None = None,
    target_return: float | None = None,
    allow_short: bool,
) -> np.ndarray | None:
    x0 = np.repeat(1.0 / n, n)
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    if target_return is not None:
        constraints.append({"type": "eq", "fun": lambda w: w @ mean - target_return})
    bounds = None if allow_short else [(0.0, 1.0)] * n

    result = minimize(
        lambda w: w @ cov @ w,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options=_SOLVER_OPTIONS,
    )
    if not result.success:
        return None
    return result.x


def _solve_max_sharpe(
    cov: np.ndarray, mean: np.ndarray, rf: float, n: int, *, allow_short: bool
) -> np.ndarray | None:
    x0 = np.repeat(1.0 / n, n)
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = None if allow_short else [(0.0, 1.0)] * n

    def neg_sharpe(w: np.ndarray) -> float:
        ret, vol = _portfolio_stats(w, mean, cov)
        if vol < 1e-12:
            return 1e6
        return -(ret - rf) / vol

    result = minimize(
        neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=constraints, options=_SOLVER_OPTIONS
    )
    if not result.success:
        return None
    return result.x


def compute_efficient_frontier(
    equity_returns: pd.DataFrame,
    weights: dict[str, float],
    *,
    risk_free_rate_annualized: float = 0.0,
    frequency: str = "daily",
    n_points: int = 25,
    allow_short: bool = False,
) -> EfficientFrontierResult:
    """Compute the Markowitz efficient frontier and locate the current portfolio on it.

    `equity_returns` must be a wide DataFrame (columns = symbols, index =
    date, one column per holding in `weights`). `weights` are the user's
    actual as-input holding weights (already validated to sum to 1 by
    Phase 1) -- this is the portfolio plotted against the frontier, not an
    optimization target.
    """
    symbols = list(weights.keys())
    missing = [s for s in symbols if s not in equity_returns.columns]
    if missing:
        raise ValueError(f"equity_returns is missing columns for holdings: {missing}")

    returns = equity_returns[symbols].dropna(how="any")
    n = len(symbols)
    min_obs = n + 2
    if len(returns) < min_obs:
        raise InsufficientDataError(
            f"only {len(returns)} overlapping observations across {n} holdings; "
            f"need at least {min_obs} to estimate a covariance matrix"
        )

    periods_per_year = PERIODS_PER_YEAR[frequency]
    cov_periodic, was_regularized, condition_number = estimate_covariance(returns)
    cov_annual = cov_periodic * periods_per_year
    mean_annual = returns.mean().to_numpy() * periods_per_year

    w_current = np.array([weights[s] for s in symbols])
    current_return, current_vol = _portfolio_stats(w_current, mean_annual, cov_annual)
    current_sharpe = (
        (current_return - risk_free_rate_annualized) / current_vol if current_vol > 1e-12 else None
    )

    gmv_weights = _solve_min_variance(cov_annual, n, allow_short=allow_short)
    if gmv_weights is None:
        raise RuntimeError("global minimum-variance solve failed to converge")
    gmv_return, gmv_vol = _portfolio_stats(gmv_weights, mean_annual, cov_annual)
    gmv_sharpe = (gmv_return - risk_free_rate_annualized) / gmv_vol if gmv_vol > 1e-12 else None
    gmv_point = FrontierPoint(
        expected_return_annualized=gmv_return,
        volatility_annualized=gmv_vol,
        weights=dict(zip(symbols, gmv_weights.tolist())),
        sharpe_ratio=gmv_sharpe,
    )

    max_return = float(mean_annual.max()) if allow_short is False else float(mean_annual.max())
    target_returns = np.linspace(gmv_return, max_return, n_points)

    frontier_points: list[FrontierPoint] = []
    for target in target_returns:
        w = _solve_min_variance(cov_annual, n, mean=mean_annual, target_return=float(target), allow_short=allow_short)
        if w is None:
            continue
        ret, vol = _portfolio_stats(w, mean_annual, cov_annual)
        sharpe = (ret - risk_free_rate_annualized) / vol if vol > 1e-12 else None
        frontier_points.append(
            FrontierPoint(
                expected_return_annualized=ret,
                volatility_annualized=vol,
                weights=dict(zip(symbols, w.tolist())),
                sharpe_ratio=sharpe,
            )
        )

    max_sharpe_point = None
    max_sharpe_weights = _solve_max_sharpe(cov_annual, mean_annual, risk_free_rate_annualized, n, allow_short=allow_short)
    if max_sharpe_weights is not None:
        ms_return, ms_vol = _portfolio_stats(max_sharpe_weights, mean_annual, cov_annual)
        ms_sharpe = (ms_return - risk_free_rate_annualized) / ms_vol if ms_vol > 1e-12 else None
        max_sharpe_point = FrontierPoint(
            expected_return_annualized=ms_return,
            volatility_annualized=ms_vol,
            weights=dict(zip(symbols, max_sharpe_weights.tolist())),
            sharpe_ratio=ms_sharpe,
        )

    frontier_return_at_same_vol = _interpolate_frontier_return(frontier_points, current_vol)
    return_gap = (
        frontier_return_at_same_vol - current_return if frontier_return_at_same_vol is not None else None
    )

    is_on_frontier = _is_on_frontier(
        cov_annual, mean_annual, n, current_return, current_vol, allow_short=allow_short
    )

    current_position = PortfolioPosition(
        expected_return_annualized=current_return,
        volatility_annualized=current_vol,
        sharpe_ratio=current_sharpe,
        weights=weights,
        frontier_return_at_same_volatility=frontier_return_at_same_vol,
        return_gap_to_frontier=return_gap,
        is_on_frontier=is_on_frontier,
    )

    return EfficientFrontierResult(
        frequency=frequency,
        n_obs=len(returns),
        symbols=symbols,
        allow_short_selling=allow_short,
        risk_free_rate_annualized=risk_free_rate_annualized,
        covariance_regularized=was_regularized,
        covariance_condition_number=condition_number,
        frontier=frontier_points,
        global_min_variance=gmv_point,
        max_sharpe=max_sharpe_point,
        current_portfolio=current_position,
    )


def _interpolate_frontier_return(frontier_points: list[FrontierPoint], target_vol: float) -> float | None:
    if not frontier_points:
        return None
    vols = np.array([p.volatility_annualized for p in frontier_points])
    rets = np.array([p.expected_return_annualized for p in frontier_points])
    order = np.argsort(vols)
    vols, rets = vols[order], rets[order]
    if target_vol < vols.min() or target_vol > vols.max():
        return None
    return float(np.interp(target_vol, vols, rets))


def _is_on_frontier(
    cov: np.ndarray,
    mean: np.ndarray,
    n: int,
    current_return: float,
    current_vol: float,
    *,
    allow_short: bool,
) -> bool:
    lo, hi = float(mean.min()), float(mean.max())
    if not (lo - 1e-9 <= current_return <= hi + 1e-9):
        return False
    target = min(max(current_return, lo), hi)
    w = _solve_min_variance(cov, n, mean=mean, target_return=target, allow_short=allow_short)
    if w is None:
        return False
    _, min_vol = _portfolio_stats(w, mean, cov)
    tol = max(_ON_FRONTIER_REL_TOL * max(current_vol, 1e-12), 1e-8)
    return abs(current_vol - min_vol) <= tol
