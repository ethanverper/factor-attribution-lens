"""Full-page HTML assembly for the Phase 3 dashboard.

Two pages: the holdings-entry form (`render_form_page`) and the results
dashboard (`render_dashboard_page`), which renders live output from
`app.models.analysis.analyze_portfolio` via the chart components in
`viz.py`. Plain Python string templates, not Jinja2 -- see decision 0004
for why. Every user-originated string is passed through `viz.esc` before
interpolation.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from app.dashboard import viz
from app.dashboard.attribution import FACTOR_LABELS, RiskAttribution, ReturnAttribution
from app.dashboard.viz import esc
from app.models.schemas import PortfolioAnalysis
from app.schemas import PortfolioReturnData

PAGE_STYLE = """
* { box-sizing: border-box; }
body { margin: 0; }
.page-shell { max-width: 880px; margin: 0 auto; padding: 28px 20px 60px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 6px; }
.page-header h1 { font-size: 22px; margin: 0; font-weight: 700; }
.page-nav a { color: var(--text-secondary); font-size: 13px; text-decoration: none; }
.page-nav a:hover { text-decoration: underline; }
.theme-btn { background: var(--surface-1); border: 1px solid var(--border); border-radius: 6px;
  color: var(--text-secondary); font-size: 12px; padding: 5px 10px; cursor: pointer; }
.freshness-banner { background: var(--surface-1); border: 1px solid var(--border); border-radius: 8px;
  padding: 12px 14px; font-size: 12.5px; color: var(--text-secondary); margin: 14px 0 22px; }
.freshness-banner strong { color: var(--text-primary); }
.disclaimer { font-size: 12px; color: var(--text-muted); margin-top: 6px; }
.section-title { font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted);
  margin: 30px 0 10px; }
.section-title:first-of-type { margin-top: 8px; }
.form-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 22px; }
.form-card h1 { font-size: 20px; margin: 0 0 6px; }
.form-card p.intro { font-size: 13.5px; color: var(--text-secondary); margin: 0 0 20px; max-width: 60ch; }
.field-row { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.field { flex: 1 1 160px; display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 12px; color: var(--text-secondary); }
.field input, .field select { font: inherit; padding: 8px 10px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--page-plane); color: var(--text-primary); }
.holdings-label { font-size: 12px; color: var(--text-secondary); margin: 18px 0 6px; }
.holding-row { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }
.holding-row input[name="symbol"] { flex: 1 1 140px; text-transform: uppercase; }
.holding-row input[name="weight"] { flex: 0 1 120px; }
.row-remove { background: transparent; border: 1px solid var(--border); border-radius: 6px; color: var(--text-muted);
  width: 30px; height: 34px; cursor: pointer; font-size: 15px; }
.row-remove:hover { color: var(--diverging-neg); }
.add-row-btn { background: transparent; border: 1px dashed var(--baseline); border-radius: 6px;
  color: var(--text-secondary); padding: 7px 12px; font-size: 12.5px; cursor: pointer; margin-top: 2px; }
.submit-btn { background: var(--series-1); color: white; border: none; border-radius: 7px; padding: 11px 22px;
  font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 18px; }
.error-banner { background: color-mix(in srgb, var(--diverging-neg) 12%, var(--surface-1));
  border: 1px solid color-mix(in srgb, var(--diverging-neg) 40%, var(--border)); border-radius: 8px;
  padding: 12px 14px; font-size: 13px; color: var(--text-primary); margin-bottom: 18px; }
.form-footnote { font-size: 12px; color: var(--text-muted); margin-top: 16px; max-width: 60ch; }
"""


def _page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{viz.CHART_STYLE}{PAGE_STYLE}</style>
</head>
<body class="viz-root">
<div class="page-shell">
{body}
</div>
<script>{viz.CHART_SCRIPT}</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Form page
# ---------------------------------------------------------------------------


def _holding_row_html(symbol: str = "", weight: str = "") -> str:
    return (
        '<div class="holding-row">'
        f'<input type="text" name="symbol" placeholder="e.g. AAPL" maxlength="12" value="{esc(symbol)}">'
        f'<input type="number" name="weight" placeholder="0.00–1.00" step="0.0001" min="0" max="1" value="{esc(weight)}">'
        '<button type="button" class="row-remove" aria-label="Remove holding" '
        "onclick=\"this.parentElement.remove()\">×</button>"
        "</div>"
    )


def render_form_page(
    *,
    error: str | None = None,
    symbols: list[str] | None = None,
    weights: list[str] | None = None,
    benchmark: str = "^GSPC",
    start_date: date | None = None,
    end_date: date | None = None,
    factor_model: str = "3",
    frequency: str = "daily",
) -> str:
    symbols = symbols or ["", "", "", ""]
    weights = weights or ["", "", "", ""]
    rows = "".join(_holding_row_html(s, w) for s, w in zip(symbols, weights))

    error_html = f'<div class="error-banner"><strong>Could not build the dashboard.</strong> {esc(error)}</div>' if error else ""

    def selected(value: str, target: str) -> str:
        return "selected" if value == target else ""

    body = f"""
<div class="page-header">
  <h1>Factor Lens</h1>
  <button class="theme-btn" type="button" data-theme-toggle>Toggle theme</button>
</div>
<div class="form-card">
  <h1>Portfolio attribution dashboard</h1>
  <p class="intro">Enter your holdings and a benchmark to get CAPM beta, Fama-French factor loadings,
  an efficient-frontier view, and a return/risk attribution breakdown, computed live from market data.
  This is decision-support analytics, not investment advice.</p>
  {error_html}
  <form method="post" action="/dashboard">
    <div class="holdings-label">Holdings (ticker + portfolio weight; weights must sum to 1.0)</div>
    <div id="holdings-rows">{rows}</div>
    <button type="button" class="add-row-btn" id="add-holding-btn">+ Add holding</button>

    <div class="field-row" style="margin-top:20px;">
      <div class="field">
        <label for="benchmark">Benchmark</label>
        <input type="text" id="benchmark" name="benchmark" value="{esc(benchmark)}">
      </div>
      <div class="field">
        <label for="factor_model">Fama-French model</label>
        <select id="factor_model" name="factor_model">
          <option value="3" {selected(factor_model, "3")}>3-factor</option>
          <option value="5" {selected(factor_model, "5")}>5-factor</option>
        </select>
      </div>
      <div class="field">
        <label for="frequency">Frequency</label>
        <select id="frequency" name="frequency">
          <option value="daily" {selected(frequency, "daily")}>Daily</option>
          <option value="monthly" {selected(frequency, "monthly")}>Monthly</option>
        </select>
      </div>
    </div>
    <div class="field-row">
      <div class="field">
        <label for="start_date">Start date</label>
        <input type="date" id="start_date" name="start_date" value="{esc(start_date.isoformat() if start_date else '')}">
      </div>
      <div class="field">
        <label for="end_date">End date</label>
        <input type="date" id="end_date" name="end_date" value="{esc(end_date.isoformat() if end_date else '')}">
      </div>
    </div>
    <button type="submit" class="submit-btn">Run analysis</button>
  </form>
  <p class="form-footnote">Data sources: yfinance (via the OpenBB Open Data Platform) for equity/benchmark
  prices, Kenneth French's Data Library for factor returns. The efficient frontier is long-only by default.
  See <code>docs/decisions/</code> for the full modeling methodology.</p>
</div>
<template id="holding-row-template">{_holding_row_html()}</template>
<script>
document.getElementById('add-holding-btn').addEventListener('click', function () {{
  var tpl = document.getElementById('holding-row-template');
  document.getElementById('holdings-rows').appendChild(tpl.content.cloneNode(true));
}});
</script>
"""
    return _page_shell("Factor Lens — Portfolio attribution", body)


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------


def render_dashboard_page(
    data: PortfolioReturnData,
    analysis: PortfolioAnalysis,
    return_attribution: ReturnAttribution,
    risk_attribution: RiskAttribution,
) -> str:
    meta = data.meta
    capm = analysis.capm
    ff = analysis.factor_model
    ef = analysis.efficient_frontier
    cp = ef.current_portfolio

    holdings_str = ", ".join(f"{h.symbol} {viz.fmt_pct(h.weight, 1)}" for h in meta.holdings)

    header = f"""
<div class="page-header">
  <div>
    <h1>Factor Lens — Attribution Dashboard</h1>
    <div class="page-nav"><a href="/">&larr; New holdings</a></div>
  </div>
  <button class="theme-btn" type="button" data-theme-toggle>Toggle theme</button>
</div>
<div class="freshness-banner">
  <div><strong>Portfolio:</strong> {esc(holdings_str)} &nbsp;·&nbsp; <strong>Benchmark:</strong> {esc(meta.benchmark)}
  &nbsp;·&nbsp; <strong>Model:</strong> Fama-French {esc(meta.factor_model)}-factor, {esc(meta.frequency)}</div>
  <div><strong>Data as of:</strong> {esc(meta.aligned_start_date)} to {esc(meta.aligned_end_date)}
  ({esc(meta.n_periods)} {esc(meta.frequency)} observations; requested {esc(meta.requested_start_date)}
  to {esc(meta.requested_end_date)}) &nbsp;·&nbsp; Sources: {esc(meta.equity_provider)}; {esc(meta.factor_provider)}
  &nbsp;·&nbsp; Standard errors: {esc(capm.standard_error_convention)}</div>
  <div class="disclaimer">Internal decision-support analytics only. This is not investment advice, not a recommendation to buy, sell, or rebalance, and not a signal of any kind — it describes where your as-entered portfolio sits relative to modeled benchmarks and factors, historically.</div>
</div>
"""

    exposure_section = _render_exposure_section(capm, ff)
    frontier_section = _render_frontier_section(ef, cp)
    attribution_section = _render_attribution_section(return_attribution, risk_attribution, ff)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    footer = f'<p class="form-footnote">Report generated {esc(generated_at)}. Data freshness is stated above and may lag this timestamp — see the "data as of" line.</p>'

    body = header + exposure_section + frontier_section + attribution_section + footer
    return _page_shell("Factor Lens — Attribution Dashboard", body)


def _render_exposure_section(capm, ff) -> str:
    tiles = viz.stat_row(
        [
            viz.stat_tile(
                f"CAPM beta vs {capm.benchmark}",
                viz.fmt_num(capm.beta.estimate, 2),
                f"95% CI [{viz.fmt_num(capm.beta.ci_lower_95, 2)}, {viz.fmt_num(capm.beta.ci_upper_95, 2)}] · "
                f"t={viz.fmt_num(capm.beta.t_stat, 2)}, p={viz.fmt_pvalue(capm.beta.p_value)}",
            ),
            viz.stat_tile(
                "CAPM alpha (annualized)",
                viz.fmt_pct(capm.alpha_annualized, 2, signed=True),
                f"periodic t={viz.fmt_num(capm.alpha.t_stat, 2)}, p={viz.fmt_pvalue(capm.alpha.p_value)} "
                f"({viz.significance_note(capm.alpha.p_value)})",
            ),
            viz.stat_tile(
                "CAPM R²",
                viz.fmt_pct(capm.r_squared, 1),
                f"n={capm.n_obs} {capm.frequency} obs",
            ),
        ]
    )

    loading_rows = [
        viz.DivergingBarRow(
            name=coef.name,
            label=_factor_label(coef.name),
            value=coef.estimate,
            std_error=coef.std_error,
            t_stat=coef.t_stat,
            p_value=coef.p_value,
            ci_lower=coef.ci_lower_95,
            ci_upper=coef.ci_upper_95,
        )
        for coef in ff.factor_loadings
    ]
    loadings_chart = viz.diverging_bar_chart(
        "ff-loadings", loading_rows, value_fmt=lambda v: viz.fmt_num(v, 2, signed=True)
    )
    loadings_legend = viz.legend(
        [
            viz.LegendItem("Positive loading", "var(--series-1)"),
            viz.LegendItem("Negative loading", "var(--diverging-neg)"),
        ]
    )
    loadings_table = viz.table_view(
        "ff-loadings-table",
        ["Factor", "Loading", "Std. error", "t-stat", "p-value", "95% CI"],
        [
            [
                _factor_label(coef.name),
                viz.fmt_num(coef.estimate, 3, signed=True),
                viz.fmt_num(coef.std_error, 4),
                viz.fmt_num(coef.t_stat, 2),
                viz.fmt_pvalue(coef.p_value),
                f"[{viz.fmt_num(coef.ci_lower_95, 3)}, {viz.fmt_num(coef.ci_upper_95, 3)}]",
            ]
            for coef in ff.factor_loadings
        ],
    )

    ff_stats = viz.stat_row(
        [
            viz.stat_tile("Fama-French alpha (annualized)", viz.fmt_pct(ff.alpha_annualized, 2, signed=True)),
            viz.stat_tile("Fama-French R²", viz.fmt_pct(ff.r_squared, 1), f"adj. {viz.fmt_pct(ff.adj_r_squared, 1)}"),
            viz.stat_tile(
                "F-statistic",
                viz.fmt_num(ff.f_statistic, 1),
                f"p={viz.fmt_pvalue(ff.f_p_value)}, n={ff.n_obs} {ff.frequency} obs",
            ),
        ]
    )

    return f"""
<div class="section-title">1. Factor exposure</div>
<div class="viz-card">
  <h2>CAPM beta vs. {esc(capm.benchmark)}</h2>
  <p class="viz-subtitle">Single-factor market exposure and its statistical diagnostics — not a bare point estimate.</p>
  {tiles}
</div>
<div class="viz-card">
  <h2>Fama-French {esc(ff.factor_model)}-factor loadings</h2>
  <p class="viz-subtitle">Exposure to each factor, with a 95% confidence-interval whisker plotted under every bar.
  Hover or focus a bar for standard error, t-stat, and p-value.</p>
  {loadings_legend}
  {loadings_chart}
  {loadings_table}
  {ff_stats}
</div>
"""


def _factor_label(name: str) -> str:
    return FACTOR_LABELS.get(name, name)


def _render_frontier_section(ef, cp) -> str:
    warn_html = ""
    if ef.covariance_regularized:
        warn_html = viz.warn_banner(
            "The covariance matrix for this holding set required regularization (condition number "
            f"{viz.fmt_num(ef.covariance_condition_number, 1)}) — holdings may be highly correlated or the "
            "aligned data window may be short relative to the number of holdings. Treat this frontier as "
            "less reliable than usual."
        )

    frontier_points = [
        viz.FrontierPointVM(volatility=p.volatility_annualized, ret=p.expected_return_annualized, sharpe=p.sharpe_ratio)
        for p in ef.frontier
    ]
    current_vm = viz.FrontierPointVM(
        volatility=cp.volatility_annualized, ret=cp.expected_return_annualized, sharpe=cp.sharpe_ratio
    )
    gmv_vm = viz.FrontierPointVM(
        volatility=ef.global_min_variance.volatility_annualized,
        ret=ef.global_min_variance.expected_return_annualized,
        sharpe=ef.global_min_variance.sharpe_ratio,
    )
    max_sharpe_vm = (
        viz.FrontierPointVM(
            volatility=ef.max_sharpe.volatility_annualized,
            ret=ef.max_sharpe.expected_return_annualized,
            sharpe=ef.max_sharpe.sharpe_ratio,
        )
        if ef.max_sharpe
        else None
    )

    chart = viz.frontier_chart(
        frontier_points,
        current_vm,
        gmv_vm,
        max_sharpe_vm,
        frontier_return_at_current_vol=cp.frontier_return_at_same_volatility,
    )
    chart_legend = viz.legend(
        [
            viz.LegendItem("Modeled efficient frontier", "var(--series-1)", "line"),
            viz.LegendItem("Your portfolio", "var(--series-2)", "dot"),
            viz.LegendItem("Global min-variance", "var(--text-muted)", "dot"),
        ]
        + ([viz.LegendItem("Max Sharpe (tangency)", "var(--text-muted)", "diamond")] if max_sharpe_vm else [])
    )

    gap = cp.return_gap_to_frontier
    if cp.is_on_frontier:
        gap_sub = "your portfolio is (numerically) on the modeled frontier for its return level"
    elif gap is not None:
        gap_sub = f"the frontier offers {viz.fmt_pct(gap, 2)} more return at your volatility level"
    else:
        gap_sub = "outside the computed frontier's volatility range"

    stats = viz.stat_row(
        [
            viz.stat_tile("Your annualized return", viz.fmt_pct(cp.expected_return_annualized, 2)),
            viz.stat_tile("Your annualized volatility", viz.fmt_pct(cp.volatility_annualized, 2)),
            viz.stat_tile("Your Sharpe ratio", viz.fmt_ratio(cp.sharpe_ratio)),
            viz.stat_tile("Return gap at matched volatility", viz.fmt_pct(gap, 2, signed=True), gap_sub),
        ]
    )

    frontier_table = viz.table_view(
        "frontier-table",
        ["Point", "Volatility (ann.)", "Return (ann.)", "Sharpe"],
        [
            ["Your portfolio", viz.fmt_pct(cp.volatility_annualized, 2), viz.fmt_pct(cp.expected_return_annualized, 2), viz.fmt_ratio(cp.sharpe_ratio)],
            ["Global min-variance", viz.fmt_pct(ef.global_min_variance.volatility_annualized, 2), viz.fmt_pct(ef.global_min_variance.expected_return_annualized, 2), viz.fmt_ratio(ef.global_min_variance.sharpe_ratio)],
        ]
        + (
            [["Max Sharpe (tangency)", viz.fmt_pct(ef.max_sharpe.volatility_annualized, 2), viz.fmt_pct(ef.max_sharpe.expected_return_annualized, 2), viz.fmt_ratio(ef.max_sharpe.sharpe_ratio)]]
            if ef.max_sharpe
            else []
        )
        + [
            [f"Frontier point {i + 1}", viz.fmt_pct(p.volatility_annualized, 2), viz.fmt_pct(p.expected_return_annualized, 2), viz.fmt_ratio(p.sharpe_ratio)]
            for i, p in enumerate(ef.frontier)
        ],
    )

    return f"""
<div class="section-title">2. Efficient frontier</div>
<div class="viz-card">
  <h2>Your portfolio vs. the modeled efficient frontier</h2>
  <p class="viz-subtitle">Long-only Markowitz frontier ({esc(ef.n_obs)} {esc(ef.frequency)} obs across
  {esc(len(ef.symbols))} holdings). This shows where your as-entered portfolio sits — it is not a rebalancing recommendation.</p>
  {warn_html}
  {chart_legend}
  {chart}
  {stats}
  {frontier_table}
</div>
"""


def _render_attribution_section(return_attribution: ReturnAttribution, risk_attribution: RiskAttribution, ff) -> str:
    contrib_rows = [
        viz.DivergingBarRow(name=c.name, label=c.label, value=c.contribution_periodic) for c in return_attribution.contributions
    ]
    contrib_chart = viz.diverging_bar_chart("return-attr", contrib_rows, value_fmt=lambda v: viz.fmt_bps(v, 1))
    contrib_legend = viz.legend(
        [viz.LegendItem("Positive contribution", "var(--series-1)"), viz.LegendItem("Negative contribution", "var(--diverging-neg)")]
    )
    contrib_table = viz.table_view(
        "return-attr-table",
        ["Source", f"Mean {return_attribution.frequency} contribution"],
        [[c.label, viz.fmt_bps(c.contribution_periodic, 2)] for c in return_attribution.contributions]
        + [["Total (= realized mean excess return)", viz.fmt_bps(return_attribution.total_periodic, 2)]],
    )

    risk_bar = viz.risk_split_bar(risk_attribution.factor_explained_share, risk_attribution.idiosyncratic_share)
    risk_legend = viz.legend(
        [
            viz.LegendItem(f"Factor-explained ({viz.fmt_pct(risk_attribution.factor_explained_share, 1)})", "var(--series-1)"),
            viz.LegendItem(f"Idiosyncratic ({viz.fmt_pct(risk_attribution.idiosyncratic_share, 1)})", "var(--text-muted)"),
        ]
    )

    return f"""
<div class="section-title">3. Return &amp; risk attribution</div>
<div class="viz-card">
  <h2>Return attribution</h2>
  <p class="viz-subtitle">Alpha plus each factor's own contribution (loading &times; that factor's mean return
  over the same window) — an exact decomposition of your portfolio's realized mean per-{esc(return_attribution.frequency)}
  excess return, not an approximation. Values are per-period (not annualized); see the methodology note below.</p>
  {contrib_legend}
  {contrib_chart}
  {contrib_table}
</div>
<div class="viz-card">
  <h2>Risk attribution</h2>
  <p class="viz-subtitle">Share of your portfolio's return variance the {esc(ff.factor_model)}-factor model
  explains (R²) vs. idiosyncratic (stock-specific, unexplained by these factors).</p>
  {risk_legend}
  {risk_bar}
  <p class="viz-note">Methodology note: per-period return contributions here use the compounding-vs-linear-scaling
  annualization split documented in the project's Phase 2 methodology decision — they are deliberately left
  per-period rather than re-annualized piecewise, since summing already-annualized, differently-convention'd
  pieces would not reconcile to the realized total the way the per-period figures above do exactly.</p>
</div>
"""
