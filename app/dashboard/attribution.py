"""Return/risk attribution derived from Phase 2 outputs.

This is presentation-layer analysis, not a new Phase 2 model: it does not
touch `app/models/schemas.py`'s stable contract. It combines
`FactorModelResult` (Phase 2) with the raw aligned factor series Phase 1
already returned in `PortfolioReturnData.factor_returns`.

**Return attribution** is an exact OLS identity, not an approximation. The
Fama-French regression fit in `app/models/fama_french.py` is
`excess_portfolio = alpha + sum(loading_i * factor_i) + residual`, fit by
OLS with an intercept — which guarantees the fitted residual has zero mean
over the regression sample. Rearranging at the mean:

    mean(excess_portfolio) = alpha + sum(loading_i * mean(factor_i))

So splitting the portfolio's realized mean excess return into "alpha" plus
each factor's own contribution (its loading times its own mean return over
the same window) reproduces the realized mean exactly, up to the same
sample the regression used. Contributions are left in **periodic** terms
(not annualized) — per decision 0003, alpha's annualization (compounding)
and the frontier's annualization (linear scaling) are different
conventions for different purposes, and summing already-annualized,
differently-convention'd pieces back into a whole would misstate the
identity above. Phase 4 should present these as periodic (per-day or
per-month) contributions, not re-annualize them piecewise.

**Risk attribution** is the factor model's own R-squared: the share of
portfolio return variance the factor model explains, versus the
idiosyncratic (residual, unexplained) share. This is standard and requires
no extra computation beyond what `FactorModelResult.r_squared` already
reports.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import FactorModelResult
from app.schemas import PortfolioReturnData

FACTOR_LABELS: dict[str, str] = {
    "mkt_rf": "Market (Mkt-RF)",
    "smb": "Size (SMB)",
    "hml": "Value (HML)",
    "rmw": "Profitability (RMW)",
    "cma": "Investment (CMA)",
}

_FACTOR_COLUMNS = ("mkt_rf", "smb", "hml", "rmw", "cma")


@dataclass(frozen=True)
class ReturnContribution:
    name: str
    label: str
    contribution_periodic: float


@dataclass(frozen=True)
class ReturnAttribution:
    """Alpha + each factor's contribution to the portfolio's mean periodic excess return."""

    contributions: list[ReturnContribution]  # alpha first, then one entry per fitted factor
    total_periodic: float
    frequency: str


@dataclass(frozen=True)
class RiskAttribution:
    """Share of portfolio return variance explained by the factor model vs. idiosyncratic."""

    factor_explained_share: float  # R^2, clipped to [0, 1] for display
    idiosyncratic_share: float
    r_squared_raw: float  # unclipped, for the diagnostics table (adj R^2 can dip slightly negative)


def compute_return_attribution(
    factor_result: FactorModelResult, data: PortfolioReturnData
) -> ReturnAttribution:
    """Decompose the portfolio's mean periodic excess return into alpha + per-factor contributions."""
    factor_means = _factor_period_means(data)

    contributions = [
        ReturnContribution(
            name="alpha",
            label="Alpha (unexplained)",
            contribution_periodic=factor_result.alpha.estimate,
        )
    ]
    for loading in factor_result.factor_loadings:
        mean = factor_means.get(loading.name, 0.0)
        contributions.append(
            ReturnContribution(
                name=loading.name,
                label=FACTOR_LABELS.get(loading.name, loading.name),
                contribution_periodic=loading.estimate * mean,
            )
        )

    total = sum(c.contribution_periodic for c in contributions)
    return ReturnAttribution(contributions=contributions, total_periodic=total, frequency=factor_result.frequency)


def compute_risk_attribution(factor_result: FactorModelResult) -> RiskAttribution:
    r2 = factor_result.r_squared
    explained = max(0.0, min(1.0, r2))
    return RiskAttribution(
        factor_explained_share=explained,
        idiosyncratic_share=1.0 - explained,
        r_squared_raw=r2,
    )


def _factor_period_means(data: PortfolioReturnData) -> dict[str, float]:
    sums = dict.fromkeys(_FACTOR_COLUMNS, 0.0)
    counts = dict.fromkeys(_FACTOR_COLUMNS, 0)
    for point in data.factor_returns:
        for col in _FACTOR_COLUMNS:
            value = getattr(point, col)
            if value is not None:
                sums[col] += value
                counts[col] += 1
    return {col: (sums[col] / counts[col] if counts[col] else 0.0) for col in _FACTOR_COLUMNS}
