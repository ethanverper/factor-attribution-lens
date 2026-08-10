"""Phase 2 quant core: CAPM, Fama-French, and Markowitz models.

This package is a reusable modeling layer, not a notebook: every public
function/class here takes plain pandas/numpy inputs (or the Phase 1
`PortfolioReturnData` bundle via `adapters.py`) and returns structured,
JSON-serializable Pydantic results. Phase 3 (`business-intelligence`) and
Phase 4 (`educator`) are expected to consume `analysis.analyze_portfolio`
directly rather than reaching into individual model functions, but the
individual functions (`capm.estimate_capm_beta`,
`fama_french.estimate_factor_model`,
`optimization.compute_efficient_frontier`) are public and independently
testable/usable.

See `docs/decisions/0003-phase2-quant-methodology.md` for the methodology
choices made in this package (regression SE convention, optimization
solver, covariance regularization, factor model default).
"""
from __future__ import annotations

from app.models.analysis import analyze_portfolio
from app.models.capm import estimate_capm_beta
from app.models.fama_french import estimate_factor_model
from app.models.optimization import compute_efficient_frontier

__all__ = [
    "analyze_portfolio",
    "estimate_capm_beta",
    "estimate_factor_model",
    "compute_efficient_frontier",
]
