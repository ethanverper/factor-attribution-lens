"""Live end-to-end checks for the Phase 3 dashboard (no mocking).

Mirrors the project's existing convention (`test_api.py`,
`test_models_integration.py`): real network calls, real OpenBB/Fama-French
data, plausibility/structure checks rather than fixed reference values.
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.dashboard.attribution import compute_return_attribution, compute_risk_attribution
from app.main import app
from app.models.analysis import analyze_portfolio
from app.schemas import HoldingInput, PortfolioRequest
from app.service import build_portfolio_return_data

client = TestClient(app)

END = date.today() - timedelta(days=1)
START = END - timedelta(days=365)


def test_dashboard_form_renders():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "<form" in resp.text
    assert 'name="symbol"' in resp.text
    assert 'name="weight"' in resp.text


def test_dashboard_submit_end_to_end():
    payload = {
        "symbol": ["AAPL", "MSFT", "GOOGL"],
        "weight": ["0.5", "0.3", "0.2"],
        "benchmark": "^GSPC",
        "start_date": START.isoformat(),
        "end_date": END.isoformat(),
        "factor_model": "3",
        "frequency": "daily",
    }
    resp = client.post("/dashboard", data=payload)
    assert resp.status_code == 200, resp.text
    body = resp.text

    # All three required Phase 3 views are present.
    assert "Factor exposure" in body
    assert "Efficient frontier" in body
    assert "Return" in body and "attribution" in body
    assert "CAPM beta" in body
    assert "Fama-French" in body
    assert "<svg" in body  # charts actually rendered, not just section headers

    # Decision-support framing, not advice. Whitespace-normalized since the source HTML wraps
    # prose across multiple lines (harmless for rendering -- browsers collapse whitespace --
    # but a raw substring check needs the same normalization to be meaningful).
    lowered = " ".join(body.split()).lower()
    assert "not investment advice" in lowered or "not a rebalancing recommendation" in lowered
    assert "you should" not in lowered  # no imperative advice language

    # Live data freshness is stated, not silently omitted.
    assert "Data as of" in body


def test_return_attribution_identity_holds():
    """Sum of return-attribution contributions must equal the realized mean excess return (OLS identity)."""
    request = PortfolioRequest(
        holdings=[HoldingInput(symbol="AAPL", weight=0.6), HoldingInput(symbol="MSFT", weight=0.4)],
        benchmark="^GSPC",
        start_date=START,
        end_date=END,
        factor_model="3",
        frequency="daily",
    )
    data = build_portfolio_return_data(request)
    analysis = analyze_portfolio(data)
    return_attr = compute_return_attribution(analysis.factor_model, data)
    risk_attr = compute_risk_attribution(analysis.factor_model)

    rf_by_date = {f.date: f.rf for f in data.factor_returns}
    realized_excess = [p.value - rf_by_date[p.date] for p in data.portfolio_returns]
    realized_mean_excess = sum(realized_excess) / len(realized_excess)

    assert abs(return_attr.total_periodic - realized_mean_excess) < 1e-6
    assert abs(risk_attr.factor_explained_share + risk_attr.idiosyncratic_share - 1.0) < 1e-9


def test_dashboard_missing_holdings_reprompts_form():
    resp = client.post(
        "/dashboard",
        data={
            "benchmark": "^GSPC",
            "start_date": START.isoformat(),
            "end_date": END.isoformat(),
            "factor_model": "3",
            "frequency": "daily",
        },
    )
    assert resp.status_code == 400
    assert "Enter at least one holding" in resp.text
