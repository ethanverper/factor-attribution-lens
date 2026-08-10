"""Pydantic output models for the Phase 2 quant core.

These are the hand-off contract with Phase 3 (`business-intelligence`) and
Phase 4 (`educator`): every model-fitting function in this package returns
one of these shapes (or `analysis.analyze_portfolio` returns the bundled
`PortfolioAnalysis`), so downstream phases have a single, stable, documented
interface instead of raw statsmodels/scipy objects.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Frequency = Literal["daily", "monthly"]


class RegressionCoefficient(BaseModel):
    """A single regression coefficient with full statistical diagnostics."""

    name: str = Field(..., description="Coefficient name, e.g. 'alpha', 'mkt_rf', 'smb'.")
    estimate: float
    std_error: float
    t_stat: float
    p_value: float
    ci_lower_95: float
    ci_upper_95: float


class CAPMResult(BaseModel):
    """CAPM single-factor regression: R_p - R_f = alpha + beta * (R_m - R_f) + e."""

    benchmark: str
    frequency: Frequency
    n_obs: int
    alpha: RegressionCoefficient
    beta: RegressionCoefficient
    alpha_annualized: float = Field(..., description="Periodic alpha compounded to an annual rate.")
    r_squared: float
    adj_r_squared: float
    residual_std_error: float = Field(..., description="Periodic (not annualized) residual std dev.")
    standard_error_convention: str = Field(
        ..., description="Which covariance estimator produced std_error/t_stat/p_value, e.g. 'HAC (Newey-West)'."
    )


class FactorModelResult(BaseModel):
    """Fama-French 3- or 5-factor regression on portfolio excess returns."""

    factor_model: Literal["3", "5"]
    frequency: Frequency
    n_obs: int
    alpha: RegressionCoefficient
    factor_loadings: list[RegressionCoefficient] = Field(
        ..., description="One entry per factor, in the order mkt_rf, smb, hml, [rmw, cma]."
    )
    alpha_annualized: float
    r_squared: float
    adj_r_squared: float
    residual_std_error: float
    standard_error_convention: str
    f_statistic: float
    f_p_value: float


class FrontierPoint(BaseModel):
    expected_return_annualized: float
    volatility_annualized: float
    weights: dict[str, float]
    sharpe_ratio: float | None = None


class PortfolioPosition(BaseModel):
    """Where the user's actual (as-input) portfolio sits relative to the frontier."""

    expected_return_annualized: float
    volatility_annualized: float
    sharpe_ratio: float | None = None
    weights: dict[str, float]
    frontier_return_at_same_volatility: float | None = Field(
        None,
        description=(
            "The efficient frontier's expected return at the portfolio's own volatility level "
            "(interpolated from frontier points). None if the portfolio's volatility falls "
            "outside the computed frontier's range."
        ),
    )
    return_gap_to_frontier: float | None = Field(
        None,
        description=(
            "frontier_return_at_same_volatility - portfolio's own return. "
            ">= 0 means the portfolio is on/inside the efficient frontier (as expected by "
            "construction); this is a descriptive distance measure, not a trading signal."
        ),
    )
    is_on_frontier: bool = Field(
        ..., description="True if the portfolio's own weights are (numerically) the min-variance weights for its return level."
    )


class EfficientFrontierResult(BaseModel):
    frequency: Frequency
    n_obs: int
    symbols: list[str]
    allow_short_selling: bool
    risk_free_rate_annualized: float
    covariance_regularized: bool = Field(
        ..., description="True if the sample covariance matrix required regularization (see decision 0003)."
    )
    covariance_condition_number: float
    frontier: list[FrontierPoint]
    global_min_variance: FrontierPoint
    max_sharpe: FrontierPoint | None = Field(
        None, description="Tangency (max Sharpe ratio) portfolio; None if not solvable (e.g. degenerate inputs)."
    )
    current_portfolio: PortfolioPosition


class PortfolioAnalysis(BaseModel):
    """Top-level Phase 2 output bundle: CAPM + factor model + frontier for one portfolio."""

    capm: CAPMResult
    factor_model: FactorModelResult
    efficient_frontier: EfficientFrontierResult
