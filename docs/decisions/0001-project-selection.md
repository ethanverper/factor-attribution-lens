# 0001. Select Factor Lens as Cowork OS's first finance project

Date: 2026-08-10
Status: accepted

## Context

`trend-scout` produced a fintech/quant/wealthtech research brief (`docs/research/finance/2026-08-10-fintech-ai-quant-wealthtech.md`), and `innovation-strategist` turned it into a 6-idea shortlist (`docs/ideation/finance/2026-08-10-fintech-quant-analytics-shortlist.md`): Factor Lens, Ruin Radar, Backtest Skeptic, IC-in-a-Box, WarrantyIQ, Ledger & Ruin. This is Cowork OS's first project in the `finance` domain and the first project started under the weekly cadence policy (decision 0001 at the root) for the week of 2026-08-10 → 2026-08-17.

## Decision

Ethan selected **Factor Lens** — a transparent factor-attribution and portfolio-optimization tool (CAPM beta, Fama-French factor loadings, Markowitz efficient-frontier positioning) for retail investors and small RIAs, built on live OpenBB data.

This matches the shortlist's own top recommendation: it's the idea most directly grounded in the research brief's explicit gap analysis (factor/portfolio-optimization tooling for retail/small-team use called out as thin and "squarely in the team's stated capability area"), it maps closely onto Ethan's existing CAPM/Fama-French/Markowitz academic background, it's buildable with the current active roster with no agent gaps, and it carries the lowest regulatory/trust risk of the six shortlisted ideas (pure decision-support analytics, no execution, no regulated disclosure output) — unlike `Ledger & Ruin`, which was explicitly flagged as needing a `legal-compliance` agent to exist first.

## Consequences

- Scaffolded at `projects/finance/factor-lens/` with a v1 roadmap phased Foundation & Data Integration → Quant Core Models → Explainable Visualization → Plain-Language Narrative → QA Sign-off, against `developer` → `quant-analyst` → `business-intelligence` → `educator` → `qa-tester`.
- `docs/ideation/index.md` updated: this idea marked `selected → projects/finance/factor-lens/`.
- `docs/portfolio.md` and `docs/cadence.md` updated to reflect the first finance-category project of the week.
- The shortlist's runner-up (`Backtest Skeptic`) and the two held-back ideas (`Ledger & Ruin` pending `legal-compliance`, `WarrantyIQ` possibly mis-filed under `finance`) remain unselected in `docs/ideation/index.md` for future consideration — not rejected, just not picked this round.
