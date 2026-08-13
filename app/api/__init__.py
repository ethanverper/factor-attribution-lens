"""Factor Attribution Lens's pure JSON API for the React frontend (Phase 10i).

Everything here is data in, data out -- no HTML rendering. `routes.py`
exposes the full CAPM/Fama-French/Markowitz analysis pipeline
(`POST /api/analysis`, previously only reachable from the now-removed
server-rendered dashboard), the curated ticker/benchmark universe
(`GET /api/tickers`), and the sample-portfolio quick-start default
(`GET /api/sample`).
"""
