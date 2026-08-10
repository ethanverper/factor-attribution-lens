"""Server-rendered SVG chart components for the Phase 3 dashboard.

Built by hand against the `dataviz` skill's method (form -> color -> marks
-> interaction -> accessibility pass) rather than a client-side charting
library — see `docs/decisions/0004-phase3-dashboard-architecture.md` for
why. Every chart ships:

- thin marks (2px lines, <=24px bars, 4px rounded data-ends / square
  baseline, 2px surface rings on markers) per `marks-and-anatomy.md`;
- the documented default categorical palette (`references/palette.md`),
  validated with `scripts/validate_palette.js` (see decision 0004);
- a legend for every chart with 2+ series;
- a hover tooltip on every mark (native `<title>` plus a small shared JS
  enhancement — see `CHART_SCRIPT`), which only ever *supplements* values
  that are also in the table-view twin rendered under the chart;
- a `<details>` table-view twin, the WCAG-clean equivalent, per
  `interaction.md` / `anti-patterns.md`.

All user-originated strings (tickers, benchmark names) are HTML-escaped
before interpolation.
"""
from __future__ import annotations

import html
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Palette (references/palette.md, validated in decision 0004) and chart chrome
# ---------------------------------------------------------------------------

CHART_STYLE = """
.viz-root {
  color-scheme: light;
  --surface-1:      #fcfcfb;
  --page-plane:     #f9f9f7;
  --text-primary:   #0b0b0b;
  --text-secondary: #52514e;
  --text-muted:     #898781;
  --gridline:       #e1e0d9;
  --baseline:       #c3c2b7;
  --border:         rgba(11,11,11,0.10);
  --series-1:       #2a78d6;   /* blue: frontier line, factor-explained, positive */
  --series-2:       #eb6834;   /* orange: current-portfolio emphasis */
  --diverging-neg:  #e34948;   /* red: negative loadings/contributions */
  --status-warning: #fab219;
  --status-good:    #0ca30c;
  --tooltip-bg:     #0b0b0b;
  --tooltip-fg:     #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --page-plane:     #0d0d0d;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --gridline:       #2c2c2a;
    --baseline:       #383835;
    --border:         rgba(255,255,255,0.10);
    --series-1:       #3987e5;
    --series-2:       #d95926;
    --diverging-neg:  #e66767;
    --status-warning: #fab219;
    --status-good:    #0ca30c;
    --tooltip-bg:     #ffffff;
    --tooltip-fg:     #0b0b0b;
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --surface-1:      #1a1a19;
  --page-plane:     #0d0d0d;
  --text-primary:   #ffffff;
  --text-secondary: #c3c2b7;
  --text-muted:     #898781;
  --gridline:       #2c2c2a;
  --baseline:       #383835;
  --border:         rgba(255,255,255,0.10);
  --series-1:       #3987e5;
  --series-2:       #d95926;
  --diverging-neg:  #e66767;
  --status-warning: #fab219;
  --status-good:    #0ca30c;
  --tooltip-bg:     #ffffff;
  --tooltip-fg:     #0b0b0b;
}

.viz-root { background: var(--page-plane); color: var(--text-primary);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
.viz-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  padding: 20px 22px; margin-bottom: 20px; }
.viz-card h2 { font-size: 17px; margin: 0 0 2px; font-weight: 600; }
.viz-card .viz-subtitle { font-size: 13px; color: var(--text-secondary); margin: 0 0 14px; }
.viz-chart-wrap { overflow-x: auto; }
.viz-chart-wrap svg { width: 100%; height: auto; display: block; min-width: 480px; }
.viz-mark { cursor: pointer; }
.viz-legend { display: flex; flex-wrap: wrap; gap: 16px; margin: 4px 0 14px; font-size: 12.5px;
  color: var(--text-secondary); }
.viz-legend-item { display: inline-flex; align-items: center; gap: 6px; }
.viz-legend-swatch-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.viz-legend-swatch-line { width: 14px; height: 2px; display: inline-block; border-radius: 1px; }
.viz-legend-swatch-diamond { width: 9px; height: 9px; display: inline-block; transform: rotate(45deg); }
.viz-tooltip { position: fixed; pointer-events: none; background: var(--tooltip-bg); color: var(--tooltip-fg);
  font-size: 12px; padding: 6px 9px; border-radius: 6px; z-index: 1000; opacity: 0; transition: opacity 0.08s;
  max-width: 260px; line-height: 1.45; }
.viz-tooltip.is-visible { opacity: 0.97; }
.viz-tooltip .tt-value { font-weight: 700; }
.viz-table-twin { margin-top: 10px; }
.viz-table-twin summary { cursor: pointer; font-size: 12.5px; color: var(--text-secondary); }
.viz-table-twin table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12.5px; }
.viz-table-twin th, .viz-table-twin td { text-align: right; padding: 5px 8px; border-bottom: 1px solid var(--gridline); }
.viz-table-twin th:first-child, .viz-table-twin td:first-child { text-align: left; }
.viz-table-twin td { font-variant-numeric: tabular-nums; }
.viz-note { font-size: 12.5px; color: var(--text-secondary); margin-top: 8px; }
.viz-warn-banner { display: flex; align-items: flex-start; gap: 8px; background: color-mix(in srgb, var(--status-warning) 14%, var(--surface-1));
  border: 1px solid color-mix(in srgb, var(--status-warning) 45%, var(--border)); border-radius: 8px;
  padding: 10px 12px; font-size: 12.5px; color: var(--text-primary); margin-bottom: 14px; }
.viz-stat-row { display: flex; flex-wrap: wrap; gap: 14px; }
.viz-stat-tile { flex: 1 1 150px; min-width: 140px; }
.viz-stat-tile .stat-label { font-size: 11.5px; color: var(--text-secondary); text-transform: uppercase;
  letter-spacing: 0.03em; margin-bottom: 4px; }
.viz-stat-tile .stat-value { font-size: 26px; font-weight: 600; line-height: 1.1; }
.viz-stat-tile .stat-sub { font-size: 12px; color: var(--text-muted); margin-top: 3px; }
"""

CHART_SCRIPT = """
(function () {
  var tip = document.createElement('div');
  tip.className = 'viz-tooltip';
  document.body.appendChild(tip);
  function show(el, evt) {
    var label = el.getAttribute('data-tt-label') || '';
    var value = el.getAttribute('data-tt-value') || '';
    var extra = el.getAttribute('data-tt-extra') || '';
    tip.innerHTML = '';
    var l = document.createElement('div'); l.textContent = label; tip.appendChild(l);
    var v = document.createElement('div'); v.className = 'tt-value'; v.textContent = value; tip.appendChild(v);
    if (extra) { var e = document.createElement('div'); e.textContent = extra; tip.appendChild(e); }
    tip.classList.add('is-visible');
    move(evt);
  }
  function move(evt) {
    var x = evt.clientX + 14, y = evt.clientY + 14;
    var vw = window.innerWidth, vh = window.innerHeight;
    if (x + 260 > vw) x = evt.clientX - 260 - 14;
    if (y + 90 > vh) y = evt.clientY - 90 - 14;
    tip.style.left = x + 'px';
    tip.style.top = y + 'px';
  }
  function hide() { tip.classList.remove('is-visible'); }
  document.addEventListener('pointerover', function (evt) {
    var el = evt.target.closest('.viz-mark');
    if (el) show(el, evt);
  });
  document.addEventListener('pointermove', function (evt) {
    var el = evt.target.closest('.viz-mark');
    if (el) move(evt);
  });
  document.addEventListener('pointerout', function (evt) {
    var el = evt.target.closest('.viz-mark');
    if (el) hide();
  });
  document.addEventListener('focusin', function (evt) {
    var el = evt.target.closest('.viz-mark');
    if (el) show(el, evt);
  });
  document.addEventListener('focusout', function (evt) {
    var el = evt.target.closest('.viz-mark');
    if (el) hide();
  });

  var themeToggle = document.querySelector('[data-theme-toggle]');
  if (themeToggle) {
    var stored = window.localStorage.getItem('factor-lens-theme');
    if (stored) document.documentElement.setAttribute('data-theme', stored);
    themeToggle.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      window.localStorage.setItem('factor-lens-theme', next);
    });
  }
})();
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


# ---------------------------------------------------------------------------
# Number formatting
# ---------------------------------------------------------------------------


def fmt_pct(x: float | None, decimals: int = 2, signed: bool = False) -> str:
    if x is None:
        return "—"
    sign = "+" if signed and x > 0 else ""
    return f"{sign}{x * 100:.{decimals}f}%"


def fmt_num(x: float | None, decimals: int = 3, signed: bool = False) -> str:
    if x is None:
        return "—"
    sign = "+" if signed and x > 0 else ""
    return f"{sign}{x:.{decimals}f}"


def fmt_bps(x: float | None, decimals: int = 1, signed: bool = True) -> str:
    if x is None:
        return "—"
    sign = "+" if signed and x > 0 else ""
    return f"{sign}{x * 10000:.{decimals}f} bps"


def fmt_ratio(x: float | None, decimals: int = 2) -> str:
    if x is None:
        return "—"
    return f"{x:.{decimals}f}"


def fmt_pvalue(p: float) -> str:
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def significance_note(p: float) -> str:
    return "significant at 95% (p<0.05)" if p < 0.05 else "not significant at 95% (p≥0.05)"


# ---------------------------------------------------------------------------
# Small building blocks: stat tiles, legends, table-view twin
# ---------------------------------------------------------------------------


def stat_tile(label: str, value: str, sub: str | None = None) -> str:
    sub_html = f'<div class="stat-sub">{esc(sub)}</div>' if sub else ""
    return (
        '<div class="viz-stat-tile">'
        f'<div class="stat-label">{esc(label)}</div>'
        f'<div class="stat-value">{esc(value)}</div>'
        f"{sub_html}"
        "</div>"
    )


def stat_row(tiles: list[str]) -> str:
    return '<div class="viz-stat-row">' + "".join(tiles) + "</div>"


@dataclass(frozen=True)
class LegendItem:
    label: str
    color_css: str  # e.g. "var(--series-1)"
    kind: str = "dot"  # "dot" | "line" | "diamond"


def legend(items: list[LegendItem]) -> str:
    if len(items) < 2:
        return ""
    parts = []
    for item in items:
        cls = {"dot": "viz-legend-swatch-dot", "line": "viz-legend-swatch-line", "diamond": "viz-legend-swatch-diamond"}[
            item.kind
        ]
        parts.append(
            '<span class="viz-legend-item">'
            f'<span class="{cls}" style="background:{item.color_css}"></span>'
            f"{esc(item.label)}</span>"
        )
    return '<div class="viz-legend">' + "".join(parts) + "</div>"


def table_view(table_id: str, headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{esc(c)}</td>" for c in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        f'<details class="viz-table-twin" id="{esc(table_id)}">'
        "<summary>Table view</summary>"
        f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
        "</details>"
    )


def warn_banner(text: str) -> str:
    return f'<div class="viz-warn-banner"><strong>⚠</strong><span>{esc(text)}</span></div>'


# ---------------------------------------------------------------------------
# Diverging bar chart (factor loadings, return contributions)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DivergingBarRow:
    name: str
    label: str
    value: float
    std_error: float | None = None
    t_stat: float | None = None
    p_value: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None


def _hbar_path(x0: float, x1: float, y: float, h: float, r: float) -> str:
    """Horizontal bar: square corners at x0 (baseline), 4px-rounded at x1 (data end)."""
    r = max(0.0, min(r, h / 2.0, abs(x1 - x0)))
    if x1 >= x0:
        return (
            f"M{x0:.2f},{y:.2f} H{x1 - r:.2f} "
            f"Q{x1:.2f},{y:.2f} {x1:.2f},{y + r:.2f} "
            f"V{y + h - r:.2f} Q{x1:.2f},{y + h:.2f} {x1 - r:.2f},{y + h:.2f} "
            f"H{x0:.2f} Z"
        )
    return (
        f"M{x0:.2f},{y:.2f} H{x1 + r:.2f} "
        f"Q{x1:.2f},{y:.2f} {x1:.2f},{y + r:.2f} "
        f"V{y + h - r:.2f} Q{x1:.2f},{y + h:.2f} {x1 + r:.2f},{y + h:.2f} "
        f"H{x0:.2f} Z"
    )


def diverging_bar_chart(
    chart_id: str,
    rows: list[DivergingBarRow],
    *,
    value_fmt,
    width: int = 680,
) -> str:
    """A horizontal diverging bar chart, baseline at zero, with CI whiskers when provided."""
    n = len(rows)
    left_w, right_w = 190, 96
    row_h = 46
    bar_h = 22
    top_pad, bottom_axis_h = 8, 28
    height = top_pad + row_h * n + bottom_axis_h + top_pad
    plot_w = width - left_w - right_w
    half_plot = plot_w / 2.0
    zero_x = left_w + half_plot

    max_abs = max([abs(r.value) for r in rows] + [abs(r.ci_lower or r.value) for r in rows]
                  + [abs(r.ci_upper or r.value) for r in rows] + [1e-9])
    domain_max = max_abs * 1.35
    scale = half_plot / domain_max

    svg_rows = []
    for i, row in enumerate(rows):
        row_top = top_pad + i * row_h
        bar_y = row_top + (bar_h - 0) / 2 - 2  # center-ish, leaves room for whisker below
        x1 = zero_x + row.value * scale
        color = "var(--series-1)" if row.value >= 0 else "var(--diverging-neg)"
        tooltip_extra = ""
        if row.std_error is not None:
            tooltip_extra = (
                f"SE {fmt_num(row.std_error, 4)} · t {fmt_num(row.t_stat, 2)} · "
                f"p {fmt_pvalue(row.p_value)} · 95% CI [{value_fmt(row.ci_lower)}, {value_fmt(row.ci_upper)}]"
            )
        svg_rows.append(
            f'<g class="viz-mark" tabindex="0" '
            f'data-tt-label="{esc(row.label)}" data-tt-value="{esc(value_fmt(row.value))}" '
            f'data-tt-extra="{esc(tooltip_extra)}">'
            f'<title>{esc(row.label)}: {esc(value_fmt(row.value))}'
            + (f" ({esc(tooltip_extra)})" if tooltip_extra else "")
            + "</title>"
            f'<path d="{_hbar_path(zero_x, x1, bar_y, bar_h, 4)}" fill="{color}" />'
            "</g>"
        )
        # value label, always outside the bar end (never clipped)
        if row.value >= 0:
            svg_rows.append(
                f'<text x="{x1 + 6:.2f}" y="{bar_y + bar_h / 2 + 4:.2f}" font-size="12" '
                f'fill="var(--text-secondary)">{esc(value_fmt(row.value))}</text>'
            )
        else:
            svg_rows.append(
                f'<text x="{x1 - 6:.2f}" y="{bar_y + bar_h / 2 + 4:.2f}" font-size="12" text-anchor="end" '
                f'fill="var(--text-secondary)">{esc(value_fmt(row.value))}</text>'
            )
        # category label
        svg_rows.append(
            f'<text x="{left_w - 12:.2f}" y="{bar_y + bar_h / 2 + 4:.2f}" font-size="12.5" text-anchor="end" '
            f'fill="var(--text-primary)">{esc(row.label)}</text>'
        )
        # CI whisker, drawn below the bar so it's a distinct, visible overlay
        if row.ci_lower is not None and row.ci_upper is not None:
            wy = bar_y + bar_h + 8
            wx0 = zero_x + row.ci_lower * scale
            wx1 = zero_x + row.ci_upper * scale
            svg_rows.append(
                f'<line x1="{wx0:.2f}" y1="{wy:.2f}" x2="{wx1:.2f}" y2="{wy:.2f}" '
                f'stroke="var(--text-secondary)" stroke-width="1.5" />'
                f'<line x1="{wx0:.2f}" y1="{wy - 4:.2f}" x2="{wx0:.2f}" y2="{wy + 4:.2f}" '
                f'stroke="var(--text-secondary)" stroke-width="1.5" />'
                f'<line x1="{wx1:.2f}" y1="{wy - 4:.2f}" x2="{wx1:.2f}" y2="{wy + 4:.2f}" '
                f'stroke="var(--text-secondary)" stroke-width="1.5" />'
            )
            svg_rows.append(
                f'<text x="{left_w - 12:.2f}" y="{wy + 3:.2f}" font-size="10" text-anchor="end" '
                f'fill="var(--text-muted)">95% CI</text>'
            )

    plot_bottom = top_pad + row_h * n
    axis_y = plot_bottom + 14
    tick_lo, tick_hi = -domain_max, domain_max
    ticks_svg = (
        f'<line x1="{zero_x - half_plot:.2f}" y1="{axis_y:.2f}" x2="{zero_x + half_plot:.2f}" y2="{axis_y:.2f}" '
        f'stroke="var(--gridline)" stroke-width="1" />'
        f'<text x="{zero_x - half_plot:.2f}" y="{axis_y + 16:.2f}" font-size="11" fill="var(--text-muted)">'
        f"{esc(value_fmt(tick_lo))}</text>"
        f'<text x="{zero_x:.2f}" y="{axis_y + 16:.2f}" font-size="11" text-anchor="middle" '
        f'fill="var(--text-muted)">0</text>'
        f'<text x="{zero_x + half_plot:.2f}" y="{axis_y + 16:.2f}" font-size="11" text-anchor="end" '
        f'fill="var(--text-muted)">{esc(value_fmt(tick_hi))}</text>'
    )
    baseline = (
        f'<line x1="{zero_x:.2f}" y1="{top_pad:.2f}" x2="{zero_x:.2f}" y2="{plot_bottom:.2f}" '
        f'stroke="var(--baseline)" stroke-width="1" />'
    )

    return (
        f'<div class="viz-chart-wrap"><svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Diverging bar chart">{baseline}{"".join(svg_rows)}{ticks_svg}</svg></div>'
    )


# ---------------------------------------------------------------------------
# Efficient frontier chart
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrontierPointVM:
    volatility: float
    ret: float
    sharpe: float | None = None


def frontier_chart(
    frontier: list[FrontierPointVM],
    current: FrontierPointVM,
    gmv: FrontierPointVM,
    max_sharpe: FrontierPointVM | None,
    *,
    frontier_return_at_current_vol: float | None,
    width: int = 680,
    height: int = 380,
) -> str:
    left, right, top, bottom = 60, 20, 16, 46
    plot_w = width - left - right
    plot_h = height - top - bottom

    all_vols = [p.volatility for p in frontier] + [current.volatility, gmv.volatility]
    all_rets = [p.ret for p in frontier] + [current.ret, gmv.ret]
    if max_sharpe is not None:
        all_vols.append(max_sharpe.volatility)
        all_rets.append(max_sharpe.ret)

    x_max = max(all_vols + [1e-9]) * 1.15
    y_min_raw = min(all_rets + [0.0])
    y_max_raw = max(all_rets + [1e-9])
    pad = max((y_max_raw - y_min_raw) * 0.15, abs(y_max_raw) * 0.1, 1e-6)
    y_min = min(0.0, y_min_raw - pad)
    y_max = y_max_raw + pad

    def px(vol: float) -> float:
        return left + (vol / x_max) * plot_w if x_max > 0 else left

    def py(ret: float) -> float:
        return top + plot_h - ((ret - y_min) / (y_max - y_min)) * plot_h

    # gridlines + ticks
    grid = []
    n_y_ticks = 4
    for i in range(n_y_ticks + 1):
        val = y_min + (y_max - y_min) * i / n_y_ticks
        y = py(val)
        grid.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}" '
            f'stroke="var(--gridline)" stroke-width="1" />'
            f'<text x="{left - 8}" y="{y + 4:.2f}" font-size="11" text-anchor="end" '
            f'fill="var(--text-muted)">{esc(fmt_pct(val, 0))}</text>'
        )
    n_x_ticks = 4
    for i in range(n_x_ticks + 1):
        val = x_max * i / n_x_ticks
        x = px(val)
        grid.append(
            f'<text x="{x:.2f}" y="{top + plot_h + 18:.2f}" font-size="11" text-anchor="middle" '
            f'fill="var(--text-muted)">{esc(fmt_pct(val, 0))}</text>'
        )
    grid.append(
        f'<line x1="{left}" y1="{top + plot_h:.2f}" x2="{left + plot_w}" y2="{top + plot_h:.2f}" '
        f'stroke="var(--baseline)" stroke-width="1" />'
    )

    sorted_frontier = sorted(frontier, key=lambda p: p.volatility)
    poly_points = " ".join(f"{px(p.volatility):.2f},{py(p.ret):.2f}" for p in sorted_frontier)
    frontier_line = (
        f'<polyline points="{poly_points}" fill="none" stroke="var(--series-1)" '
        f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />'
    )
    frontier_dots = []
    for p in sorted_frontier:
        x, y = px(p.volatility), py(p.ret)
        frontier_dots.append(
            f'<g class="viz-mark" tabindex="0" data-tt-label="Modeled frontier point" '
            f'data-tt-value="{esc(fmt_pct(p.ret, 2))} return" '
            f'data-tt-extra="{esc(fmt_pct(p.volatility, 2))} volatility · Sharpe {esc(fmt_ratio(p.sharpe))}">'
            f'<title>Frontier point: {esc(fmt_pct(p.ret, 2))} return, {esc(fmt_pct(p.volatility, 2))} volatility</title>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="12" fill="transparent" />'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="var(--series-1)" '
            f'stroke="var(--surface-1)" stroke-width="1.5" />'
            "</g>"
        )

    def marker_group(point: FrontierPointVM, label: str, color: str, shape: str, r: int, tt_extra: str) -> str:
        x, y = px(point.volatility), py(point.ret)
        if shape == "diamond":
            mark = f'<rect x="{x - r:.2f}" y="{y - r:.2f}" width="{r * 2}" height="{r * 2}" fill="{color}" ' \
                   f'stroke="var(--surface-1)" stroke-width="2" transform="rotate(45 {x:.2f} {y:.2f})" />'
        else:
            mark = f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{color}" stroke="var(--surface-1)" stroke-width="2" />'
        # Flip the direct label to the marker's left when it would overflow the plot's right
        # edge (e.g. a max-Sharpe/frontier point near the highest-volatility end) -- never let
        # it clip. ~6.4px/char at this font-size/weight is a safe overestimate for measuring
        # without a layout engine.
        label_w = len(label) * 6.4
        overflows_right = x + r + 6 + label_w > width - right
        if overflows_right:
            text_x, anchor = x - r - 6, "end"
        else:
            text_x, anchor = x + r + 6, "start"
        return (
            f'<g class="viz-mark" tabindex="0" data-tt-label="{esc(label)}" '
            f'data-tt-value="{esc(fmt_pct(point.ret, 2))} return" data-tt-extra="{esc(tt_extra)}">'
            f'<title>{esc(label)}: {esc(fmt_pct(point.ret, 2))} return, {esc(fmt_pct(point.volatility, 2))} volatility</title>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="18" fill="transparent" />'
            f"{mark}"
            f'<text x="{text_x:.2f}" y="{y + 4:.2f}" font-size="11.5" text-anchor="{anchor}" '
            f'fill="var(--text-primary)" font-weight="600">{esc(label)}</text>'
            "</g>"
        )

    gmv_svg = marker_group(
        gmv, "Global min-variance", "var(--text-muted)", "circle", 5,
        f"volatility {fmt_pct(gmv.volatility, 2)} · Sharpe {fmt_ratio(gmv.sharpe)}",
    )
    ms_svg = ""
    if max_sharpe is not None:
        ms_svg = marker_group(
            max_sharpe, "Max Sharpe (tangency)", "var(--text-muted)", "diamond", 5,
            f"volatility {fmt_pct(max_sharpe.volatility, 2)} · Sharpe {fmt_ratio(max_sharpe.sharpe)}",
        )
    current_svg = marker_group(
        current, "Your portfolio", "var(--series-2)", "circle", 6,
        f"volatility {fmt_pct(current.volatility, 2)} · Sharpe {fmt_ratio(current.sharpe)}",
    )

    connector = ""
    if frontier_return_at_current_vol is not None:
        cx = px(current.volatility)
        cy1, cy2 = py(current.ret), py(frontier_return_at_current_vol)
        gap = frontier_return_at_current_vol - current.ret
        mid_y = (cy1 + cy2) / 2
        gap_text = f"{fmt_pct(gap, 2, signed=True)} more return at matched volatility"
        # No static text label here: with markers/labels placed freely around the plot area,
        # a fixed-offset label risks colliding with whichever marker label happens to land
        # nearby (see decision 0004 / marks-and-anatomy.md on end-label collisions). The exact
        # value is always visible in the "Return gap at matched volatility" stat tile below the
        # chart; this connector is a hoverable mark that supplements it, not the only way to read it.
        connector = (
            f'<g class="viz-mark" tabindex="0" data-tt-label="Return gap at matched volatility" '
            f'data-tt-value="{esc(fmt_pct(gap, 2, signed=True))}" '
            f'data-tt-extra="Frontier return {esc(fmt_pct(frontier_return_at_current_vol, 2))} vs. your {esc(fmt_pct(current.ret, 2))}, both at {esc(fmt_pct(current.volatility, 2))} volatility">'
            f"<title>{esc(gap_text)}</title>"
            f'<line x1="{cx:.2f}" y1="{cy1:.2f}" x2="{cx:.2f}" y2="{cy2:.2f}" '
            f'stroke="var(--text-secondary)" stroke-width="1.5" />'
            f'<line x1="{cx - 4:.2f}" y1="{cy2:.2f}" x2="{cx + 4:.2f}" y2="{cy2:.2f}" '
            f'stroke="var(--text-secondary)" stroke-width="1.5" />'
            f'<circle cx="{cx:.2f}" cy="{mid_y:.2f}" r="10" fill="transparent" />'
            "</g>"
        )

    svg = (
        f'<div class="viz-chart-wrap"><svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Efficient frontier chart">'
        f"{''.join(grid)}{frontier_line}{''.join(frontier_dots)}{connector}{gmv_svg}{ms_svg}{current_svg}"
        f'<text x="{left + plot_w / 2:.2f}" y="{height - 6}" font-size="11.5" text-anchor="middle" '
        f'fill="var(--text-secondary)">Annualized volatility</text>'
        f'<text x="14" y="{top + plot_h / 2:.2f}" font-size="11.5" fill="var(--text-secondary)" '
        f'transform="rotate(-90 14 {top + plot_h / 2:.2f})" text-anchor="middle">Annualized return</text>'
        "</svg></div>"
    )
    return svg


# ---------------------------------------------------------------------------
# Two-part stacked bar (risk attribution: factor-explained vs idiosyncratic)
# ---------------------------------------------------------------------------


def _rounded_rect_path(x: float, w: float, h: float, r: float, *, round_left: bool, round_right: bool) -> str:
    """A horizontal rect path with independently-toggleable rounded corners (used for the split-bar segments)."""
    if w <= 0:
        return ""
    rl = min(r, w / 2, h / 2) if round_left else 0.0
    rr = min(r, w / 2, h / 2) if round_right else 0.0
    top_right = f"Q{x + w:.2f},0 {x + w:.2f},{rr:.2f}" if rr else f"L{x + w:.2f},0"
    bottom_right = f"Q{x + w:.2f},{h:.2f} {x + w - rr:.2f},{h:.2f}" if rr else f"L{x + w:.2f},{h:.2f}"
    bottom_left = f"Q{x:.2f},{h:.2f} {x:.2f},{h - rl:.2f}" if rl else f"L{x:.2f},{h:.2f}"
    top_left = f"Q{x:.2f},0 {x + rl:.2f},0" if rl else f"L{x:.2f},0"
    return (
        f"M{x + rl:.2f},0 H{x + w - rr:.2f} {top_right} "
        f"V{h - rr:.2f} {bottom_right} H{x + rl:.2f} {bottom_left} "
        f"V{rl:.2f} {top_left} Z"
    )


def risk_split_bar(explained_share: float, idiosyncratic_share: float, *, width: int = 680, bar_h: int = 34) -> str:
    seg1_w = max(0.0, min(width, explained_share * width))
    gap = 2 if 0 < seg1_w < width else 0
    seg2_x = seg1_w + gap
    seg2_w = max(0.0, width - seg2_x)
    r = 4.0

    seg1_path = _rounded_rect_path(0, seg1_w, bar_h, r, round_left=True, round_right=seg2_w <= 0)
    seg1 = (
        f'<g class="viz-mark" tabindex="0" data-tt-label="Factor-explained" '
        f'data-tt-value="{esc(fmt_pct(explained_share, 1))}" '
        f'data-tt-extra="Share of return variance explained by the fitted factor model (R²)">'
        f"<title>Factor-explained: {esc(fmt_pct(explained_share, 1))} of return variance</title>"
        f'<path d="{seg1_path}" fill="var(--series-1)" />'
        "</g>"
    )
    seg2 = ""
    if seg2_w > 0:
        seg2_path = _rounded_rect_path(seg2_x, seg2_w, bar_h, r, round_left=True, round_right=True)
        seg2 = (
            f'<g class="viz-mark" tabindex="0" data-tt-label="Idiosyncratic (unexplained)" '
            f'data-tt-value="{esc(fmt_pct(idiosyncratic_share, 1))}" '
            f'data-tt-extra="Share of return variance not explained by the factor model (1 - R²)">'
            f"<title>Idiosyncratic: {esc(fmt_pct(idiosyncratic_share, 1))} of return variance</title>"
            f'<path d="{seg2_path}" fill="var(--text-muted)" />'
            "</g>"
        )

    return (
        f'<div class="viz-chart-wrap"><svg viewBox="0 0 {width} {bar_h}" role="img" '
        f'aria-label="Risk attribution split">{seg1}{seg2}</svg></div>'
    )
