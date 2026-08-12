"""Factor Lens API — Phase 1 data layer + Phase 10i pure JSON API.

`POST /portfolio/returns` (Phase 1) takes a holdings + weights input and
returns live, structured return data for Phase 2 modeling. `app/api/`
(Phase 10i) exposes the full CAPM/Fama-French/Markowitz analysis pipeline
and the curated ticker universe as JSON for the React frontend
(`frontend/`), which replaces the old server-rendered dashboard entirely --
see `docs/decisions/0004-react-tailwind-shadcn-default-frontend.md` (root)
and `docs/decisions/0018-phase10i-react-rebuild.md` (this project).

In production, this process also serves the frontend's built static assets
(`frontend/dist/`) directly via `StaticFiles`, so the whole app -- API and
UI -- is one deployable service (see decision 0018 for why, over a two-
service split). In development, the frontend runs its own Vite dev server
(`npm run dev`) and proxies `/api/*` to this process instead. The SPA
catch-all route is registered last so it never shadows a real API route.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.api.routes import router as api_router
from app.data.equity import EquityDataError
from app.data.factors import FactorDataError
from app.schemas import PortfolioRequest, PortfolioReturnData
from app.service import build_portfolio_return_data

app = FastAPI(
    title="Factor Lens API",
    description="Live equity, benchmark, and Fama-French factor data, plus CAPM/Fama-French/Markowitz portfolio analysis, as a pure JSON API.",
    version="0.2.0",
)

app.include_router(api_router)


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


_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str) -> FileResponse:
        """SPA fallback: any path not already matched above (no API route, no
        `/assets/*` file) serves `index.html` so React Router's client-side
        routes (`/inputs`, `/results`, ...) resolve on a hard refresh or a
        deep link too, not just on in-app navigation."""
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")
