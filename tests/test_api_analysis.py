"""Tests for the Phase 10i pure JSON API (`app/api/`) that replaced the
server-rendered dashboard -- `POST /api/analysis` (the full CAPM/Fama-French/
Markowitz pipeline, exposed as its own endpoint for the first time),
`GET /api/tickers`, and `GET /api/sample`.
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

END = date.today() - timedelta(days=1)
START = END - timedelta(days=180)


def _payload(**overrides):
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
    payload.update(overrides)
    return payload


def test_get_tickers():
    resp = client.get("/api/tickers")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["tickers"]) > 400
    assert any(t["symbol"] == "AAPL" for t in body["tickers"])
    assert any(b["symbol"] == "^GSPC" for b in body["benchmarks"])
    assert body["source_note"]


def test_get_sample_portfolio():
    resp = client.get("/api/sample")
    assert resp.status_code == 200
    body = resp.json()
    symbols = [h["symbol"] for h in body["holdings"]]
    assert symbols == ["AAPL", "MSFT", "GOOGL", "AMZN"]
    assert sum(h["weight_pct"] for h in body["holdings"]) == 100.0
    assert body["benchmark"] == "^GSPC"


def test_post_analysis_end_to_end():
    resp = client.post("/api/analysis", json=_payload())
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["meta"]["n_periods"] > 5
    capm = body["analysis"]["capm"]
    assert capm["benchmark"] == "^GSPC"
    assert "estimate" in capm["beta"]
    assert "ci_lower_95" in capm["beta"]

    ff = body["analysis"]["factor_model"]
    assert ff["factor_model"] == "3"
    assert len(ff["factor_loadings"]) == 3

    ef = body["analysis"]["efficient_frontier"]
    assert ef["symbols"] == ["AAPL", "MSFT"]
    assert "global_min_variance" in ef
    assert "current_portfolio" in ef

    ra = body["return_attribution"]
    assert ra["contributions"][0]["name"] == "alpha"
    # Return attribution is an exact OLS identity -- the contributions must
    # sum to the reported total.
    total = sum(c["contribution_periodic"] for c in ra["contributions"])
    assert abs(total - ra["total_periodic"]) < 1e-9

    risk = body["risk_attribution"]
    assert abs(risk["factor_explained_share"] + risk["idiosyncratic_share"] - 1.0) < 1e-9


def test_post_analysis_rejects_invalid_ticker():
    resp = client.post("/api/analysis", json=_payload(holdings=[{"symbol": "NOTAREALTICKERXYZ", "weight": 1.0}]))
    assert resp.status_code == 400
    assert "curated ticker universe" in resp.json()["detail"]


def test_post_analysis_rejects_invalid_benchmark():
    resp = client.post("/api/analysis", json=_payload(benchmark="^NOTAREALBENCHMARK"))
    assert resp.status_code == 400
    assert "curated benchmark list" in resp.json()["detail"]


def test_post_analysis_rejects_weights_not_summing_to_one():
    resp = client.post(
        "/api/analysis",
        json=_payload(holdings=[{"symbol": "AAPL", "weight": 0.6}, {"symbol": "MSFT", "weight": 0.6}]),
    )
    assert resp.status_code == 422
