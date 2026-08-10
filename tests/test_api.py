"""End-to-end tests for the /portfolio/returns endpoint (real network calls)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

END = date.today() - timedelta(days=1)
START = END - timedelta(days=60)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_portfolio_returns_end_to_end():
    payload = {
        "holdings": [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "MSFT", "weight": 0.4},
        ],
        "benchmark": "^GSPC",
        "start_date": START.isoformat(),
        "end_date": END.isoformat(),
        "factor_model": "3",
        "frequency": "daily",
    }
    resp = client.post("/portfolio/returns", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["meta"]["n_periods"] > 5
    assert set(body["equity_returns"].keys()) == {"AAPL", "MSFT"}
    assert len(body["portfolio_returns"]) == body["meta"]["n_periods"]
    assert len(body["benchmark_returns"]) == body["meta"]["n_periods"]
    assert len(body["factor_returns"]) == body["meta"]["n_periods"]

    # Every date series must be exactly aligned (same dates across the bundle).
    equity_dates = {p["date"] for p in body["equity_returns"]["AAPL"]}
    portfolio_dates = {p["date"] for p in body["portfolio_returns"]}
    benchmark_dates = {p["date"] for p in body["benchmark_returns"]}
    factor_dates = {p["date"] for p in body["factor_returns"]}
    assert equity_dates == portfolio_dates == benchmark_dates == factor_dates

    # Spot-check the portfolio return is genuinely the weighted sum of holdings.
    first_date = sorted(portfolio_dates)[0]
    aapl_ret = next(p["value"] for p in body["equity_returns"]["AAPL"] if p["date"] == first_date)
    msft_ret = next(p["value"] for p in body["equity_returns"]["MSFT"] if p["date"] == first_date)
    port_ret = next(p["value"] for p in body["portfolio_returns"] if p["date"] == first_date)
    assert abs(port_ret - (0.6 * aapl_ret + 0.4 * msft_ret)) < 1e-9


def test_weights_must_sum_to_one():
    payload = {
        "holdings": [{"symbol": "AAPL", "weight": 0.6}, {"symbol": "MSFT", "weight": 0.6}],
        "start_date": START.isoformat(),
        "end_date": END.isoformat(),
    }
    resp = client.post("/portfolio/returns", json=payload)
    assert resp.status_code == 422


def test_invalid_symbol_returns_502():
    payload = {
        "holdings": [{"symbol": "THIS_IS_NOT_A_REAL_TICKER_XYZ", "weight": 1.0}],
        "start_date": START.isoformat(),
        "end_date": END.isoformat(),
    }
    resp = client.post("/portfolio/returns", json=payload)
    assert resp.status_code == 502
