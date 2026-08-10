"""Factor Lens API — Phase 1 data layer.

Takes a holdings + weights input and returns live, structured return data
(equity, benchmark, and Fama-French factor series) for Phase 2 modeling.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.data.equity import EquityDataError
from app.data.factors import FactorDataError
from app.schemas import PortfolioRequest, PortfolioReturnData
from app.service import build_portfolio_return_data

app = FastAPI(
    title="Factor Lens Data API",
    description="Live equity, benchmark, and Fama-French factor return data for a given portfolio.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/portfolio/returns", response_model=PortfolioReturnData)
def portfolio_returns(request: PortfolioRequest) -> PortfolioReturnData:
    try:
        return build_portfolio_return_data(request)
    except (EquityDataError, FactorDataError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
