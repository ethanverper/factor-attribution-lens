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
  --surface-1:      #ffffff;
  --surface-2:      #e7ebf2;
  --page-plane:     #eef1f6;
  --text-primary:   #0d1117;
  --text-secondary: #4b5468;
  --text-muted:     #838da0;
  --gridline:       #e1e5ee;
  --baseline:       #c7cee0;
  --border:         rgba(13,17,23,0.10);
  --series-1:       #2461ea;   /* blue: frontier line, factor-explained, positive */
  --series-2:       #a64d09;   /* amber/bronze: current-portfolio emphasis, site signal */
  --diverging-neg:  #dc2626;   /* red: negative loadings/contributions */
  --status-warning: #b45309;
  --status-good:    #15803d;
  --tooltip-bg:     #0d1117;
  --tooltip-fg:     #ffffff;
  --shadow-card:    0 1px 2px rgba(13,17,23,0.05), 0 1px 1px rgba(13,17,23,0.03);
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --surface-1:      #12161f;
    --surface-2:      #171c27;
    --page-plane:     #0a0d13;
    --text-primary:   #eef1f6;
    --text-secondary: #9aa3b5;
    --text-muted:     #5f6779;
    --gridline:       #1b202b;
    --baseline:       #2a3040;
    --border:         rgba(255,255,255,0.08);
    --series-1:       #4c93f0;
    --series-2:       #f0a63e;
    --diverging-neg:  #ef6b6b;
    --status-warning: #e6b23c;
    --status-good:    #22c55e;
    --tooltip-bg:     #eef1f6;
    --tooltip-fg:     #0a0d13;
    --shadow-card:    0 1px 0 rgba(255,255,255,0.02), 0 4px 16px rgba(0,0,0,0.28);
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --surface-1:      #12161f;
  --surface-2:      #171c27;
  --page-plane:     #0a0d13;
  --text-primary:   #eef1f6;
  --text-secondary: #9aa3b5;
  --text-muted:     #5f6779;
  --gridline:       #1b202b;
  --baseline:       #2a3040;
  --border:         rgba(255,255,255,0.08);
  --series-1:       #4c93f0;
  --series-2:       #f0a63e;
  --diverging-neg:  #ef6b6b;
  --status-warning: #e6b23c;
  --status-good:    #22c55e;
  --tooltip-bg:     #eef1f6;
  --tooltip-fg:     #0a0d13;
  --shadow-card:    0 1px 0 rgba(255,255,255,0.02), 0 4px 16px rgba(0,0,0,0.28);
}

.viz-root { background: var(--page-plane); color: var(--text-primary);
  font-family: var(--font-body, 'Inter', system-ui, -apple-system, "Segoe UI", sans-serif); }
.viz-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  box-shadow: var(--shadow-card); padding: 20px 22px; margin-bottom: 20px; }
.viz-card h2 { font-family: var(--font-display, inherit); font-size: 17px; margin: 0 0 2px; font-weight: 500; }
.viz-card .viz-subtitle { font-size: 13px; color: var(--text-secondary); margin: 0 0 14px; }
.viz-chart-wrap { overflow-x: auto; }
.viz-chart-wrap svg { width: 100%; height: auto; display: block; min-width: 480px; }
/* Every chart's SVG text is a *reading* (an axis tick, a bar value, a category/asset name,
   an annotation) -- route it through the mono readout face so it reads as instrumentation,
   matching the rest of the app's aggressive mono-for-data convention (decision 0008), rather
   than inheriting the plain body sans it fell back to pre-Phase-9d. */
.viz-chart-wrap svg text { font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace);
  font-variant-numeric: tabular-nums; }
.viz-mark { cursor: pointer; }
.viz-legend { display: flex; flex-wrap: wrap; gap: 16px; margin: 4px 0 14px; font-size: 12.5px;
  font-family: var(--font-mono, ui-monospace); color: var(--text-secondary); }
.viz-legend-item { display: inline-flex; align-items: center; gap: 6px; }
.viz-legend-swatch-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.viz-legend-swatch-line { width: 14px; height: 2px; display: inline-block; border-radius: 1px; }
.viz-legend-swatch-diamond { width: 9px; height: 9px; display: inline-block; transform: rotate(45deg); }
.viz-tooltip { position: fixed; pointer-events: none; background: var(--tooltip-bg); color: var(--tooltip-fg);
  font-family: var(--font-mono, ui-monospace); font-size: 12px; padding: 6px 9px; border-radius: 6px; z-index: 1000;
  opacity: 0; transition: opacity 0.08s; max-width: 260px; line-height: 1.45; }
.viz-tooltip.is-visible { opacity: 0.97; }
.viz-tooltip .tt-value { font-weight: 700; }
.viz-table-twin { margin-top: 10px; }
.viz-table-twin summary { cursor: pointer; font-size: 12.5px; color: var(--text-secondary); font-family: var(--font-mono, ui-monospace); }
.viz-table-twin table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12.5px; }
.viz-table-twin th, .viz-table-twin td { text-align: right; padding: 5px 8px; border-bottom: 1px solid var(--gridline); }
.viz-table-twin th { font-family: var(--font-mono, ui-monospace); font-size: 10.5px; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--text-muted); font-weight: 500; }
.viz-table-twin th:first-child, .viz-table-twin td:first-child { text-align: left; }
.viz-table-twin td { font-variant-numeric: tabular-nums; font-family: var(--font-mono, ui-monospace); }
.viz-note { font-size: 12.5px; color: var(--text-secondary); margin-top: 8px; }
.viz-warn-banner { display: flex; align-items: flex-start; gap: 8px; background: color-mix(in srgb, var(--status-warning) 14%, var(--surface-1));
  border: 1px solid color-mix(in srgb, var(--status-warning) 45%, var(--border)); border-radius: 8px;
  padding: 10px 12px; font-size: 12.5px; color: var(--text-primary); margin-bottom: 14px; }
.viz-info-banner { display: flex; align-items: flex-start; gap: 8px; background: color-mix(in srgb, var(--series-1) 12%, var(--surface-1));
  border: 1px solid color-mix(in srgb, var(--series-1) 40%, var(--border)); border-radius: 8px;
  padding: 10px 12px; font-size: 12.5px; color: var(--text-primary); margin-bottom: 14px; }
.viz-stat-row { display: flex; flex-wrap: wrap; gap: 12px; }
/* Neutral top border, not `--signal` (decision 0012 #4's amber audit): a Results page can
   have 8-10 of these tiles at once (CAPM, Fama-French, frontier stats), and giving every
   one an amber cap diluted the one-accent-per-view discipline to nothing -- amber now
   reads only where it's actually the single most important mark on a view (the frontier
   chart's "current portfolio" iris, the primary CTA, the active nav item). */
.viz-stat-tile { flex: 1 1 150px; min-width: 140px; background: var(--page-plane); border: 1px solid var(--border);
  border-radius: 8px; padding: 12px 14px 11px; border-top: 2px solid var(--border); }
.viz-stat-tile .stat-label { font-size: 10.5px; color: var(--text-secondary); text-transform: uppercase;
  letter-spacing: 0.05em; margin-bottom: 6px; font-family: var(--font-mono, ui-monospace); }
.viz-stat-tile .stat-value { font-size: 27px; font-weight: 600; line-height: 1.1; font-variant-numeric: tabular-nums;
  font-family: var(--font-mono, ui-monospace); }
.viz-stat-tile .stat-sub { font-size: 11.5px; color: var(--text-muted); margin-top: 5px; line-height: 1.4; }

@media print {
  .viz-tooltip { display: none !important; }
  .viz-mark { cursor: default; }
}
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


def stat_tile(
    label: str,
    value: str,
    sub: str | None = None,
    *,
    count_target: float | None = None,
    count_decimals: int = 2,
    count_suffix: str = "",
    count_signed: bool = False,
) -> str:
    """A single stat readout. `value` is always the real, already-formatted string --
    server-rendered, correct with no JS at all (progressive enhancement, decision 0015).

    `count_target`/`count_decimals`/`count_suffix`/`count_signed` (Phase 10g) are an
    *additional*, optional data-attribute payload the client-side count-up animation
    reads to tween a raw number and reformat it on every tick -- it never parses
    `value` back apart (fragile). Omit `count_target` (leave `None`) for a tile whose
    value isn't a plain formatted number (e.g. already "—" for a missing figure) --
    the tile still renders correctly, it just doesn't animate.
    """
    sub_html = f'<div class="stat-sub">{esc(sub)}</div>' if sub else ""
    count_attrs = ""
    if count_target is not None:
        count_attrs = (
            f' data-count-target="{count_target:.6f}" data-count-decimals="{count_decimals}"'
            f' data-count-suffix="{esc(count_suffix)}" data-count-signed="{"true" if count_signed else "false"}"'
        )
    return (
        '<div class="viz-stat-tile">'
        f'<div class="stat-label">{esc(label)}</div>'
        f'<div class="stat-value"{count_attrs}>{esc(value)}</div>'
        f"{sub_html}"
        "</div>"
    )


def stat_tile_pct(label: str, value: float | None, decimals: int = 2, *, signed: bool = False, sub: str | None = None) -> str:
    """`stat_tile` for a fraction rendered as a percent (the app's most common case) --
    formats `value` with `fmt_pct` and wires the matching count-up attributes in one call."""
    return stat_tile(
        label,
        fmt_pct(value, decimals, signed=signed),
        sub,
        count_target=(value * 100) if value is not None else None,
        count_decimals=decimals,
        count_suffix="%",
        count_signed=signed,
    )


def stat_tile_num(label: str, value: float | None, decimals: int = 3, *, signed: bool = False, sub: str | None = None) -> str:
    """`stat_tile` for a plain (non-percent) number, e.g. CAPM beta or an F-statistic."""
    return stat_tile(
        label,
        fmt_num(value, decimals, signed=signed),
        sub,
        count_target=value,
        count_decimals=decimals,
        count_suffix="",
        count_signed=signed,
    )


def stat_tile_ratio(label: str, value: float | None, decimals: int = 2, *, sub: str | None = None) -> str:
    """`stat_tile` for a ratio (Sharpe), which is never signed with an explicit "+"."""
    return stat_tile(
        label,
        fmt_ratio(value, decimals),
        sub,
        count_target=value,
        count_decimals=decimals,
        count_suffix="",
        count_signed=False,
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


def info_banner(text: str) -> str:
    return f'<div class="viz-info-banner"><strong>ⓘ</strong><span>{esc(text)}</span></div>'


def _bbox_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    """Axis-aligned bounding-box overlap test; boxes are (x0, y0, x1, y1)."""
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


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
            # `viz-bar-reveal`/`data-reveal-order` (Phase 10g, decision 0015 §4): the client
            # scales this group from `scaleX: 0` at the zero baseline up to its real SSR'd
            # width -- the bar's own geometry (the `<path>` below) never changes, only a CSS
            # transform wraps it. `transform-origin` is pinned to the zero baseline in *chart*
            # pixel coordinates (not a `%` of the group's own bounding box, which would anchor
            # off-center for a negative bar) so both positive and negative bars grow outward
            # from zero, matching where the bar visually starts.
            f'<g class="viz-bar-reveal" data-reveal-order="{i}" '
            f'style="transform-origin:{zero_x:.2f}px {bar_y + bar_h / 2:.2f}px">'
            f'<path d="{_hbar_path(zero_x, x1, bar_y, bar_h, 4)}" fill="{color}" />'
            "</g>"
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
            # `viz-whisker-reveal` (Phase 10g, decision 0015 §4): fades in ~100ms after this
            # row's own bar finishes growing (a whisker appearing before its bar exists reads
            # as meaningless) -- matched to the bar above by the same `data-reveal-order`.
            svg_rows.append(
                f'<g class="viz-whisker-reveal" data-reveal-order="{i}">'
                f'<line x1="{wx0:.2f}" y1="{wy:.2f}" x2="{wx1:.2f}" y2="{wy:.2f}" '
                f'stroke="var(--text-secondary)" stroke-width="1.5" />'
                f'<line x1="{wx0:.2f}" y1="{wy - 4:.2f}" x2="{wx0:.2f}" y2="{wy + 4:.2f}" '
                f'stroke="var(--text-secondary)" stroke-width="1.5" />'
                f'<line x1="{wx1:.2f}" y1="{wy - 4:.2f}" x2="{wx1:.2f}" y2="{wy + 4:.2f}" '
                f'stroke="var(--text-secondary)" stroke-width="1.5" />'
                "</g>"
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
        # Vertical gridline completing the panel (horizontal-only gridlines read as a bar
        # chart's baseline grid, not a scatter/instrument readout) -- same hairline spec as
        # the horizontal ticks above, skipped at the plot's own left/right frame edges.
        if 0 < i < n_x_ticks:
            grid.append(
                f'<line x1="{x:.2f}" y1="{top:.2f}" x2="{x:.2f}" y2="{top + plot_h:.2f}" '
                f'stroke="var(--gridline)" stroke-width="1" />'
            )
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
    # `viz-frontier-polyline` (Phase 10g, decision 0015 §4): the client measures this path's
    # own length (`getTotalLength()`) and draws it in via `stroke-dashoffset` -- no server
    # change needed for the technique itself, only this hook class.
    frontier_line = (
        f'<polyline class="viz-frontier-polyline" points="{poly_points}" fill="none" '
        f'stroke="var(--series-1)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />'
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

    # GMV / max-Sharpe / current-portfolio markers and their labels.
    #
    # Marks are placed independently (each at its own data point), but labels need
    # shared awareness of where *sibling* labels land -- three markers placed close
    # together (or, for a degenerate single-asset portfolio, literally the same
    # point by construction) previously produced three independently right-edge-
    # avoiding labels with no idea they'd collide with each other. Two passes fix
    # that; see docs/decisions/0011-phase10b-frontier-marker-label-collision.md:
    #   1. Cluster markers whose *pixel* positions land within COINCIDENT_PX of
    #      each other (visually the same point, e.g. QA's ~0.5px-apart repro or
    #      the exact-equality degenerate case) and give the whole cluster one
    #      combined label ("GMV = Your portfolio") instead of stacking separate,
    #      illegible ones on top of each other.
    #   2. For labels that remain close but distinct, resolve any residual
    #      bounding-box overlap by nudging the lower one further down until clear.
    COINCIDENT_PX = 6.0
    LABEL_GAP_PX = 4.0

    def marker_shape_svg(point: FrontierPointVM, color: str, shape: str, r: int) -> str:
        x, y = px(point.volatility), py(point.ret)
        if shape == "diamond":
            return (
                f'<rect x="{x - r:.2f}" y="{y - r:.2f}" width="{r * 2}" height="{r * 2}" fill="{color}" '
                f'stroke="var(--surface-1)" stroke-width="2" transform="rotate(45 {x:.2f} {y:.2f})" />'
            )
        if shape == "iris":
            # The functional aperture/focus-ring mark (decision 0012 #3): same concentric-ring
            # proportions as the masthead glyph and favicon (`mark.py::_rings_markup`), scaled
            # for chart use and reproduced directly in SVG-attribute terms here rather than
            # imported, since this chart's marks are plotted in chart pixel space (`x`/`y`
            # already resolved from the data), not the fixed local viewBox `mark.py` assumes.
            # `r` is the marker's full visual (outer-ring) radius, matching how GMV/max-Sharpe's
            # `r` is used for label-offset/hover-target sizing elsewhere in this function.
            outer_r, mid_r, core_r = r, r * 0.64, r * 0.27
            return (
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{outer_r:.2f}" fill="none" stroke="{color}" '
                f'stroke-width="1.6" />'
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{mid_r:.2f}" fill="none" stroke="{color}" '
                f'stroke-width="1.3" />'
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{core_r:.2f}" fill="{color}" '
                f'stroke="var(--surface-1)" stroke-width="1.5" />'
            )
        return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{color}" stroke="var(--surface-1)" stroke-width="2" />'

    def marker_hover_svg(point: FrontierPointVM, full_label: str, tt_extra: str) -> str:
        x, y = px(point.volatility), py(point.ret)
        return (
            f'<g class="viz-mark" tabindex="0" data-tt-label="{esc(full_label)}" '
            f'data-tt-value="{esc(fmt_pct(point.ret, 2))} return" data-tt-extra="{esc(tt_extra)}">'
            f'<title>{esc(full_label)}: {esc(fmt_pct(point.ret, 2))} return, {esc(fmt_pct(point.volatility, 2))} volatility</title>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="18" fill="transparent" />'
            "</g>"
        )

    marker_specs = [
        {
            "point": gmv, "short": "GMV", "full": "Global min-variance",
            "color": "var(--text-muted)", "shape": "circle", "r": 5,
            "tt_extra": f"volatility {fmt_pct(gmv.volatility, 2)} · Sharpe {fmt_ratio(gmv.sharpe)}",
        }
    ]
    if max_sharpe is not None:
        marker_specs.append({
            "point": max_sharpe, "short": "Max Sharpe", "full": "Max Sharpe (tangency)",
            "color": "var(--text-muted)", "shape": "diamond", "r": 5,
            "tt_extra": f"volatility {fmt_pct(max_sharpe.volatility, 2)} · Sharpe {fmt_ratio(max_sharpe.sharpe)}",
        })
    marker_specs.append({
        "point": current, "short": "Your portfolio", "full": "Your portfolio",
        "color": "var(--series-2)", "shape": "iris", "r": 9,
        "tt_extra": f"volatility {fmt_pct(current.volatility, 2)} · Sharpe {fmt_ratio(current.sharpe)}",
    })
    for spec in marker_specs:
        spec["x"], spec["y"] = px(spec["point"].volatility), py(spec["point"].ret)

    # A soft amber halo behind "Your portfolio"'s point -- the one location on this
    # chart the site's single signal accent should draw the eye to first, echoing
    # the same armed/active glow already used on buttons and focus rings (decision
    # 0008). Drawn beneath every marker shape so it still reads correctly when
    # "Your portfolio" is coincident with GMV/max-Sharpe.
    current_halo = (
        f'<circle cx="{px(current.volatility):.2f}" cy="{py(current.ret):.2f}" r="15" '
        f'fill="var(--series-2)" opacity="0.16" />'
    )
    # `viz-marker-pop` (Phase 10g, decision 0015 §4): GMV -> max-Sharpe -> current-portfolio
    # pop in, in that DOM/marker order, once the frontier curve above finishes drawing --
    # `data-marker-order` is redundant with DOM order here (kept for the client's stagger
    # bookkeeping) but not load-bearing for placement itself. The halo travels inside the
    # current-portfolio marker's own group so it pops in together with the iris, not before it.
    marks_svg = [
        (
            f'<g class="viz-marker-pop" data-marker-order="{idx}">'
            f'{current_halo if s is marker_specs[-1] else ""}'
            f'{marker_shape_svg(s["point"], s["color"], s["shape"], s["r"])}'
            "</g>"
        )
        for idx, s in enumerate(marker_specs)
    ]
    hovers_svg = [marker_hover_svg(s["point"], s["full"], s["tt_extra"]) for s in marker_specs]

    # Union-find clustering of markers within COINCIDENT_PX of each other in
    # screen space (only ever up to 3 markers, so an O(n^2) pairwise pass is fine).
    n_markers = len(marker_specs)
    parent = list(range(n_markers))

    def _find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def _union(i: int, j: int) -> None:
        ri, rj = _find(i), _find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n_markers):
        for j in range(i + 1, n_markers):
            dist = (
                (marker_specs[i]["x"] - marker_specs[j]["x"]) ** 2
                + (marker_specs[i]["y"] - marker_specs[j]["y"]) ** 2
            ) ** 0.5
            if dist <= COINCIDENT_PX:
                _union(i, j)
    clusters: dict[int, list[int]] = {}
    for i in range(n_markers):
        clusters.setdefault(_find(i), []).append(i)

    label_candidates = []
    for indices in clusters.values():
        members = [marker_specs[i] for i in indices]
        # Coincident members share ~the same pixel position by construction of the
        # distance test above -- anchor the combined label on the first member's point.
        ax, ay = members[0]["x"], members[0]["y"]
        max_r = max(m["r"] for m in members)
        label_text = " = ".join(m["short"] for m in members)
        # ~6.4px/char at this font-size/weight is a safe overestimate for measuring
        # without a layout engine -- same right-edge overflow avoidance as before,
        # now applied once per cluster rather than once per marker.
        label_w = len(label_text) * 6.4
        overflows_right = ax + max_r + 6 + label_w > width - right
        if overflows_right:
            text_x, anchor = ax - max_r - 6, "end"
        else:
            text_x, anchor = ax + max_r + 6, "start"
        x0 = text_x - label_w if anchor == "end" else text_x
        x1 = text_x if anchor == "end" else text_x + label_w
        label_candidates.append({
            "text": label_text, "text_x": text_x, "anchor": anchor, "y": ay,
            "bbox": (x0, ay - 10.0, x1, ay + 4.0),
        })

    # Resolve any residual label-vs-label overlap (clusters close but not close
    # enough to merge) by nudging the lower one down until its bounding box clears
    # every label already placed above it.
    label_candidates.sort(key=lambda c: c["y"])
    placed_labels: list[dict] = []
    for cand in label_candidates:
        guard = 0
        while guard < 10:
            blocker = next((p for p in placed_labels if _bbox_overlap(cand["bbox"], p["bbox"])), None)
            if blocker is None:
                break
            shift = blocker["bbox"][3] - cand["bbox"][1] + LABEL_GAP_PX
            cand["y"] += shift
            x0, y0, x1, y1 = cand["bbox"]
            cand["bbox"] = (x0, y0 + shift, x1, y1 + shift)
            guard += 1
        placed_labels.append(cand)

    labels_svg = [
        f'<text x="{c["text_x"]:.2f}" y="{c["y"] + 4:.2f}" font-size="11.5" text-anchor="{c["anchor"]}" '
        f'fill="var(--text-primary)" font-weight="600">{esc(c["text"])}</text>'
        for c in placed_labels
    ]

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
        f"{''.join(grid)}{frontier_line}{''.join(frontier_dots)}{connector}"
        f"{''.join(marks_svg)}{''.join(hovers_svg)}{''.join(labels_svg)}"
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
        # Reuses `viz-bar-reveal` from the diverging-bar chart (Phase 10g, decision 0015 §4) --
        # same scaleX-from-origin technique, anchored at this segment's own left edge (0) since
        # a stacked split-bar has no shared zero baseline the way the diverging charts do.
        f'<g class="viz-bar-reveal" data-reveal-order="0" style="transform-origin:0px {bar_h / 2:.2f}px">'
        f'<path d="{seg1_path}" fill="var(--series-1)" />'
        "</g>"
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
            f'<g class="viz-bar-reveal" data-reveal-order="1" style="transform-origin:{seg2_x:.2f}px {bar_h / 2:.2f}px">'
            f'<path d="{seg2_path}" fill="var(--text-muted)" />'
            "</g>"
            "</g>"
        )

    return (
        f'<div class="viz-chart-wrap"><svg viewBox="0 0 {width} {bar_h}" role="img" '
        f'aria-label="Risk attribution split">{seg1}{seg2}</svg></div>'
    )
