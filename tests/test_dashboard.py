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


def test_dashboard_form_explains_allocation_and_shows_live_total():
    """Phase 9b: the weight field must be self-explanatory, not a bare unlabeled number input."""
    resp = client.get("/")
    body = resp.text
    assert "Allocation" in body
    assert "percentage of your total portfolio" in body
    assert 'id="alloc-total"' in body
    assert 'id="alloc-total-value"' in body
    assert 'id="split-evenly-btn"' in body
    assert 'id="normalize-btn"' in body
    # The weight input now collects a percent (0-100), not a 0-1 fraction.
    assert 'max="100"' in body


def test_dashboard_submit_rejects_allocations_not_summing_to_100():
    payload = {
        "symbol": ["AAPL", "MSFT"],
        "weight": ["50", "30"],  # totals 80%, not 100%
        "benchmark": "^GSPC",
        "start_date": START.isoformat(),
        "end_date": END.isoformat(),
        "factor_model": "3",
        "frequency": "daily",
    }
    resp = client.post("/dashboard", data=payload)
    assert resp.status_code == 400
    assert "add up to 80.0%" in resp.text
    assert "100%" in resp.text


def test_dashboard_submit_rejects_out_of_range_allocation():
    payload = {
        "symbol": ["AAPL", "MSFT"],
        "weight": ["150", "-30"],
        "benchmark": "^GSPC",
        "start_date": START.isoformat(),
        "end_date": END.isoformat(),
        "factor_model": "3",
        "frequency": "daily",
    }
    resp = client.post("/dashboard", data=payload)
    assert resp.status_code == 400
    assert "must be greater than 0 and no more than 100%" in resp.text


def test_dashboard_submit_end_to_end():
    payload = {
        "symbol": ["AAPL", "MSFT", "GOOGL"],
        "weight": ["50", "30", "20"],
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

    # Phase 9b: the re-shown Inputs form echoes weights back as percents (matching what was
    # typed), not the raw 0-1 fractions Phase 1's HoldingInput stores internally.
    assert 'value="50"' in body
    assert 'value="30"' in body
    assert 'value="20"' in body


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


def test_dashboard_form_surfaces_ticker_source_note():
    """Phase 9c / project-standards rule 7: the curated ticker universe's source and
    known limitation must be visible near the combobox, not just in a decision doc."""
    resp = client.get("/")
    body = resp.text
    assert "curated S&amp;P 500 constituent snapshot" in body
    assert "drift from the current S&amp;P 500 roster" in body


def test_dashboard_form_has_sample_quickstart_links():
    """Phase 9c / project-standards rule 8: a one-click sample-portfolio quick-start
    must be reachable from the Overview and Inputs tabs with no typed input required."""
    resp = client.get("/")
    body = resp.text
    assert body.count('href="/dashboard/sample"') >= 2


def test_dashboard_sample_quickstart_runs_end_to_end():
    """The one-click sample route must run the full live pipeline with no query params."""
    resp = client.get("/dashboard/sample")
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "AAPL" in body and "MSFT" in body and "GOOGL" in body and "AMZN" in body
    assert "<svg" in body
    assert "Data as of" in body


def test_dashboard_results_page_has_share_and_export_controls():
    payload = {
        "symbol": ["AAPL", "MSFT", "GOOGL"],
        "weight": ["50", "30", "20"],
        "benchmark": "^GSPC",
        "start_date": START.isoformat(),
        "end_date": END.isoformat(),
        "factor_model": "3",
        "frequency": "daily",
    }
    resp = client.post("/dashboard", data=payload)
    assert resp.status_code == 200, resp.text
    body = resp.text

    assert 'data-share-copy' in body
    assert "Export as PDF" in body
    assert "/dashboard/view?" in body
    assert "symbol=AAPL" in body and "symbol=MSFT" in body and "symbol=GOOGL" in body


def test_dashboard_view_shareable_link_reproduces_result():
    """Phase 9c / project-standards rule 8: a shareable link (GET, no form submission)
    must replay the exact holdings/benchmark/date-range/model through the same live
    pipeline as the POST form."""
    params = {
        "symbol": ["AAPL", "MSFT"],
        "weight": ["60", "40"],
        "benchmark": "^GSPC",
        "start_date": START.isoformat(),
        "end_date": END.isoformat(),
        "factor_model": "3",
        "frequency": "daily",
    }
    resp = client.get("/dashboard/view", params=params)
    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "AAPL" in body and "MSFT" in body
    assert "<svg" in body
    assert 'value="60"' in body and 'value="40"' in body


def test_dashboard_view_rejects_invalid_ticker():
    resp = client.get(
        "/dashboard/view",
        params={
            "symbol": ["ZZZZ"],
            "weight": ["100"],
            "benchmark": "^GSPC",
            "start_date": START.isoformat(),
            "end_date": END.isoformat(),
        },
    )
    assert resp.status_code == 400
    assert "not in the curated ticker universe" in resp.text


def test_dashboard_page_has_og_and_social_preview_meta():
    resp = client.get("/")
    body = resp.text
    assert 'property="og:title"' in body
    assert 'property="og:image"' in body
    assert "og-image.png" in body
    assert 'property="og:description"' in body
    assert 'name="twitter:card" content="summary_large_image"' in body
    assert '<link rel="canonical"' in body
