"""Factor Lens API — Phase 1 data layer + Phase 3 dashboard.

`POST /portfolio/returns` (Phase 1) takes a holdings + weights input and
returns live, structured return data for Phase 2 modeling. `GET /` and
`POST /dashboard` (Phase 3, `app/dashboard/`) render a server-side HTML
view of live `analyze_portfolio()` output -- the explainable
attribution/visualization layer described in
`docs/decisions/0004-phase3-dashboard-architecture.md`.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.dashboard.routes import router as dashboard_router
from app.data.equity import EquityDataError
from app.data.factors import FactorDataError
from app.schemas import PortfolioRequest, PortfolioReturnData
from app.service import build_portfolio_return_data

app = FastAPI(
    title="Factor Lens Data API",
    description="Live equity, benchmark, Fama-French factor data, and an attribution dashboard for a given portfolio.",
    version="0.1.0",
)

# Serves the Phase 9c social-preview image (`static/og-image.png`) -- see decision 0008.
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

app.include_router(dashboard_router)


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
