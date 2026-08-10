"""Phase 3 — Explainable Attribution & Visualization Layer.

Turns Phase 2's `PortfolioAnalysis` (CAPM + Fama-French + efficient
frontier) into a server-rendered HTML dashboard: `routes.py` wires a form
(`GET /`) and a submit endpoint (`POST /dashboard`) into the FastAPI app;
`attribution.py` derives the return/risk attribution view from Phase 2's
output plus Phase 1's raw factor series; `viz.py` builds the SVG charts;
`pages.py` assembles full pages from those pieces. See
`docs/decisions/0004-phase3-dashboard-architecture.md` for the design
choices (server-side SVG rendering, no client charting library, why no
Jinja2).
"""
