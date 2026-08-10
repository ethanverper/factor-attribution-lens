# Factor Lens — Roadmap

Domain: finance
Path: `projects/finance/factor-lens/`
Selected from: [`docs/ideation/finance/2026-08-10-fintech-quant-analytics-shortlist.md`](../../../../docs/ideation/finance/2026-08-10-fintech-quant-analytics-shortlist.md) (idea 1 of 6)
Source research: [`docs/research/finance/2026-08-10-fintech-ai-quant-wealthtech.md`](../../../../docs/research/finance/2026-08-10-fintech-ai-quant-wealthtech.md)
Stakeholder: Ethan (human operator)
Started: 2026-08-10

## Goal

Give retail investors and small RIAs a transparent, explainable answer to "why does my portfolio behave the way it does" — CAPM beta, Fama-French factor loadings, and Markowitz-efficient positioning — computed from live market data, delivered as a real product rather than a black-box optimizer or an academic notebook.

## Definition of done (v1)

A working single-portfolio web app where a user enters holdings and receives, from live OpenBB-sourced market data:
1. CAPM beta vs. a chosen benchmark.
2. Fama-French 3-factor loadings (5-factor as stretch) with statistical diagnostics (R², t-stats, standard errors) — not just point estimates.
3. A Markowitz efficient-frontier view showing the current portfolio's position against the efficient set, with explainable trade-offs (not just "here's the optimal weights").
4. A plain-language narrative (dual register: technical + plain-language) explaining what's driving the portfolio's risk/return profile.

All four verified for correctness by `qa-tester` against reference calculations, clearly labeled as internal decision-support analysis (no personalized investment advice, no trade execution, no custody of funds).

## Why this project, why this shape

This is Cowork OS's first finance-category project and is scoped deliberately against `docs/about-me.md`'s "why these projects exist" lens, not as a generic build plan:

- **Industry-trend grounding**: OpenBB's Open Data Platform (v4.5, with an MCP server extension) just became a free, agent-native data backbone for exactly this class of tool — the research brief flags this as a recent, real cost-to-build drop, and factor/quant tooling for retail-or-small-team use as a genuinely thin-covered gap.
- **Real corporate-skill value**: this is not a CAPM/Fama-French/Markowitz notebook exercise — it's scoped as a shippable product with a real data layer, a visualization layer, and a narrative layer, mirroring how this analysis actually gets delivered professionally (e.g., Barra/Axioma-style factor risk tooling, just built transparent and accessible).
- **Specialized, named tools**: Python + OpenBB Open Data Platform as the live data backbone — not a static CSV or a toy dataset.
- **Deliberate CV balance**: CAPM/Fama-French/Markowitz modeling directly reinforces Ethan's existing academic quant background (low risk, high depth); live data integration via OpenBB and building this as a real running app (vs. a notebook) is the genuinely new territory this project pushes into.

## Phases (v1)

Sequenced by real dependency — each phase needs the previous phase's output to do real work, not busywork ordering.

- [x] Phase 1 — Foundation & Data Integration (`developer`) — DONE 2026-08-10: Stood up a Python/FastAPI app (`uv`-managed) integrating the OpenBB Open Data Platform (yfinance provider) for equity/benchmark prices and Kenneth French's Data Library (via `pandas-datareader`) for Fama-French 3-/5-factor return series — OpenBB itself does not carry the factor series, see `docs/decisions/0002-phase1-stack-and-data-sourcing.md`. Holdings input is manual JSON entry (weights validated to sum to 1); CSV import stretch goal not built. `POST /portfolio/returns` takes holdings + weights + benchmark + date range and returns a fully date-aligned bundle of equity/benchmark/portfolio/factor returns, verified against live (non-mocked) data end-to-end. Ready for Phase 2.
- [x] Phase 2 — Quant Core: Factor & Optimization Models (`quant-analyst`) — DONE 2026-08-10: Built `app/models/` as a structured, reusable module — CAPM beta (`capm.py`), Fama-French 3-factor with 5-factor supported end-to-end (`fama_french.py`), and a long-only Markowitz efficient frontier with the current portfolio positioned against it (`optimization.py`), all via a single orchestrator `analysis.analyze_portfolio(portfolio_return_data)` that consumes Phase 1's `PortfolioReturnData` directly. Regression diagnostics use Newey-West HAC standard errors; covariance estimation includes eigenvalue-clipping regularization for near-singular inputs. 28 tests pass (18 new, synthetic + one live end-to-end Phase 1→Phase 2 chain); see `docs/decisions/0003-phase2-quant-methodology.md` for the full methodology log. Ready for Phase 3.
- [x] Phase 3 — Explainable Attribution & Visualization Layer (`business-intelligence`) — DONE 2026-08-10: Built `app/dashboard/` as a server-rendered part of the FastAPI app (no separate frontend/build step) — `GET /` (holdings-entry form) and `POST /dashboard` (results page) run the exact same `PortfolioRequest` -> `build_portfolio_return_data` -> `analyze_portfolio` pipeline Phase 1/2 use, then render three views from the live result: (1) CAPM beta + Fama-French loadings as a diverging bar chart with 95% CI whiskers plotted directly on the chart (not hover-only), (2) the long-only efficient frontier with the current portfolio/GMV/max-Sharpe plotted against it and the return gap at matched volatility, and (3) a return/risk attribution view (`app/dashboard/attribution.py`) — return contribution per factor is an exact OLS identity (sums to the realized mean excess return), risk attribution is R² vs. idiosyncratic. Every chart follows the `dataviz` skill's method (validated categorical palette, fixed mark specs, hover tooltips, table-view twin, light/dark mode). Verified two ways: `tests/test_dashboard.py` (32/32 suite passing, including a live end-to-end check and the return-attribution numeric identity against live data) and a manual pass driving the actual running server through a headless browser with real holdings (AAPL/MSFT/GOOGL), which caught and fixed two real rendering bugs (a frontier-chart label collision, a marker-label overflow at the plot's right edge) before sign-off. Explicitly framed as decision-support only, no advice/signal language. See `docs/decisions/0004-phase3-dashboard-architecture.md`. Ready for Phase 4.
- [ ] Phase 4 — Plain-Language Narrative Layer (`educator`): Build the "why" narrative generator — dual-register (technical + plain language) explanation of what a user's beta, factor loadings, and frontier position mean for their portfolio, feeding the project's own glossary. This is the idea's core differentiator and its most defensibility-fragile piece — worth building deliberately, not as an afterthought.
- [ ] Phase 5 — Verification & QA Sign-off (`qa-tester`): Independently verify CAPM/Fama-French/Markowitz math against known reference values, test edge cases (degenerate/singular covariance matrices, single-asset portfolios, missing/gappy data), and run end-to-end verification against the definition of done above. Produces the sign-off that moves this roadmap entry to "done."
- [~] Phase 6 — Publish (`developer`, gated by Ethan's explicit go-ahead) — IN PROGRESS, Ethan gave explicit go-ahead 2026-08-10: Write a professional-quality `README.md` (what it does, how to run it, what it demonstrates), initialize a git repo scoped to `projects/finance/factor-lens/` specifically (confirm it does not inherit the ambient home-directory-rooted repo), and — only once Ethan explicitly confirms in that moment — create the dedicated GitHub repo (`github.com/ethanverper/factor-lens`) and push, including this project's `docs/roadmap.md` and `docs/decisions/` alongside the code per the team's publishing standard (`docs/about-me.md`). No standing authorization from this roadmap entry alone.

Later (not v1, tracked here for continuity per the idea's own scalability case — not scheduled):
- v2 — multi-portfolio / household view for RIAs.
- v3 — B2B API product (portfolio-optimization/factor-attribution engine other fintech apps embed) — the research brief explicitly flags this as unexplored territory.

## RAID

**Risks:**
- The "explainability" differentiator is easy to claim and hard to defend durably — incumbents with existing distribution and data (Composer, QuantConnect, YCharts post-Zephyr acquisition) could bolt on similar attribution views quickly.
- Thin demand signal risk: the research brief's "thin coverage" of retail/small-team factor tooling may reflect thin *demand*, not just thin *supply* — worth a demand check before investing beyond v1.
- OpenBB Open Data Platform is a young, actively-changing dependency (v4.5 just shipped); provider/API surface changes could break the data integration mid-build.

**Assumptions:**
- OpenBB's free tier / Open Data Platform provides sufficient live equity price history and Fama-French factor return series for v1 scope without requiring a paid data subscription. **Confirmed in Phase 1 for equity/benchmark prices (OpenBB + yfinance provider, no key needed), with one correction: OpenBB's Open Data Platform does not carry Fama-French factor series at all — sourced instead from Kenneth French's Data Library directly via `pandas-datareader`, also free/no key needed. See `docs/decisions/0002-phase1-stack-and-data-sourcing.md`.**
- The "retail investor / small RIA" target persona is validated only against desk research (the source brief), not primary user interviews — v1 proceeds on that basis; a demand check is a recommended gate before committing to v2.

**Dependencies (internal, sequential):**
- Phase 2 depends on Phase 1's OpenBB integration returning clean, structured data.
- Phase 3 depends on Phase 2's model outputs being stable and structured.
- Phase 4 depends on both Phase 2 (numbers) and Phase 3 (visual framing) being in place to narrate against.
- Phase 5 depends on Phases 1–4 being functionally complete for end-to-end testing.

**Explicitly low risk (noted, not tracked as an open item):**
- No `legal-compliance` or custody review required. This is pure decision-support analytics — no trade execution, no custody of client funds, no regulated disclosure output — consistent with both the idea's own feasibility read and the source research brief's scope exclusion ("excludes anything requiring a banking license, custody of client funds, or large capital"). Contrast with the shortlist's `Ledger & Ruin` idea, which was explicitly held back for this exact reason.
