"""Phase 9e: hand-authored inline SVG diagrams for the Learning section.

These are deliberately distinct from `app/dashboard/viz.py`'s Results charts:
`viz.py` renders *this run's* live numbers (your actual beta, your actual
frontier); everything in this module is a static, illustrative diagram that
teaches a *mechanism* -- how a CAPM return decomposes, what a confidence-
interval whisker actually tells you, what "moving along the efficient
frontier" means -- using generic example values, never the current request's
data. Built per `docs/project-standards.md` rule 5 (explanations need real
visual elements, not text walls alone) and the `artifact-diagramming` skill's
inline-SVG method (content-sized `viewBox`, labeled arrows, a
`<figure>/<figcaption>` wrapper carrying the one claim each picture makes).

Reuses the shared design-system tokens Phase 9c/9d established
(`app/dashboard/viz.py::CHART_STYLE`, `app/dashboard/shell.py::SHELL_STYLE`)
unchanged -- `--signal`, `--series-1`, `--diverging-neg`, `--status-good`,
`--status-warning`, `--font-mono`, etc. -- so these diagrams read as the same
"quant terminal" system as the Results charts, not a bolt-on with its own
palette. No new colors are introduced here.
"""
from __future__ import annotations

import math

DIAGRAM_STYLE = """
.learn-diagram { margin: 16px 0 2px; }
.learn-diagram .viz-chart-wrap { overflow-x: auto; }
.learn-diagram .viz-chart-wrap svg { width: 100%; height: auto; display: block; min-width: 440px; }
.learn-diagram svg text { font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace);
  font-variant-numeric: tabular-nums; }
.learn-diagram figcaption { font-size: 12px; color: var(--text-muted); margin-top: 10px; line-height: 1.6;
  max-width: 66ch; }
"""


def _figure(*, aria_label: str, caption: str, body: str, view_box: str) -> str:
    return f"""
<figure class="learn-diagram">
  <div class="viz-chart-wrap">
    <svg viewBox="{view_box}" role="img" aria-label="{aria_label}">{body}</svg>
  </div>
  <figcaption>{caption}</figcaption>
</figure>
"""


# ---------------------------------------------------------------------------
# (a) CAPM decomposition: Rp = Rf + beta*(Rm - Rf) + alpha, as three blocks
#     that sum exactly to the total.
# ---------------------------------------------------------------------------


def capm_decomposition_diagram() -> str:
    width, height = 800, 165
    bar_y, bar_h = 70, 46
    token_y, plain_y = 54, 134
    gap = 28

    # Widths sized generously against each block's own short plain-language label (checked
    # against JetBrains Mono's ~0.6em advance width at these font sizes) so nothing overflows
    # its own block or spills into its neighbor -- a real bug caught in this phase's own
    # verification (see decision 0010), not a hypothetical.
    seg1_x, seg1_w = 0.0, 86.0
    seg2_x, seg2_w = seg1_x + seg1_w + gap, 330.0
    seg3_x, seg3_w = seg2_x + seg2_w + gap, 140.0
    total_x, total_w = seg3_x + seg3_w + gap, 150.0

    def block(x: float, w: float, fill: str, token: str, plain: str) -> str:
        cx = x + w / 2
        return (
            f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" rx="4" fill="{fill}" />'
            f'<text x="{cx:.1f}" y="{token_y}" font-size="11.5" text-anchor="middle" '
            f'fill="var(--text-muted)">{token}</text>'
            f'<text x="{cx:.1f}" y="{plain_y}" font-size="11" text-anchor="middle" '
            f'fill="var(--text-secondary)">{plain}</text>'
        )

    def joiner(x_after: float, glyph: str) -> str:
        return (
            f'<text x="{x_after + gap / 2:.1f}" y="99" font-size="20" text-anchor="middle" '
            f'fill="var(--text-muted)">{glyph}</text>'
        )

    body = (
        f'<text x="{width / 2:.1f}" y="18" font-size="12.5" text-anchor="middle" '
        f'fill="var(--text-muted)">Rp &minus; Rf = &alpha; + &beta;&middot;(Rm &minus; Rf)</text>'
        + block(seg1_x, seg1_w, "var(--baseline)", "Rf", "Risk-free")
        + joiner(seg1_x + seg1_w, "+")
        + block(seg2_x, seg2_w, "var(--series-1)", "&beta;&middot;(Rm&minus;Rf)", "Market exposure (&beta;-scaled)")
        + joiner(seg2_x + seg2_w, "+")
        + block(seg3_x, seg3_w, "var(--signal)", "&alpha;", "Alpha")
        + joiner(seg3_x + seg3_w, "=")
        + f'<rect x="{total_x:.1f}" y="{bar_y}" width="{total_w:.1f}" height="{bar_h}" rx="4" '
        f'fill="var(--page-plane)" stroke="var(--text-primary)" stroke-width="1.5" />'
        + f'<text x="{total_x + total_w / 2:.1f}" y="99" font-size="15" font-weight="700" text-anchor="middle" '
        f'fill="var(--text-primary)">Rp</text>'
        + f'<text x="{total_x + total_w / 2:.1f}" y="{plain_y}" font-size="11" text-anchor="middle" '
        f'fill="var(--text-secondary)">Total return</text>'
    )
    return _figure(
        aria_label=(
            "Diagram: a portfolio's return decomposed into a risk-free baseline, market exposure "
            "scaled by beta, and alpha, summing exactly to the total return"
        ),
        caption=(
            "How a CAPM return actually adds up: a risk-free floor, plus the market's move scaled by your "
            "beta, plus whatever's left over. The three blocks sum exactly to your realized return &mdash; "
            "alpha isn't a bonus sitting on top of the other two, it's literally &ldquo;whatever the first "
            "two blocks didn't already explain.&rdquo; Widths here are illustrative, not your portfolio's "
            "actual proportions &mdash; see Results for those."
        ),
        body=body,
        view_box=f"0 0 {width} {height}",
    )


# ---------------------------------------------------------------------------
# (b) What a factor-loading confidence interval actually shows -- a generic,
#     labeled example distinct from the live Results chart.
# ---------------------------------------------------------------------------


def factor_loading_ci_diagram() -> str:
    width, height = 720, 210
    left_w, right_w = 168, 150
    plot_w = width - left_w - right_w
    half_plot = plot_w / 2.0
    zero_x = left_w + half_plot
    domain_max = 1.0
    scale = half_plot / domain_max

    def x_of(v: float) -> float:
        return zero_x + v * scale

    bar_h = 22
    row1_top, row2_top = 26.0, 118.0
    axis_y = row2_top + bar_h + 14 + 24

    def row(top: float, label: str, value: float, ci_lo: float, ci_hi: float, verdict: str, color: str) -> str:
        cy = top + bar_h / 2 + 4
        wy = top + bar_h + 14
        bar_x0, bar_x1 = zero_x, x_of(value)
        wx0, wx1 = x_of(ci_lo), x_of(ci_hi)
        return (
            f'<text x="{left_w - 12}" y="{cy:.1f}" font-size="12" text-anchor="end" '
            f'fill="var(--text-primary)">{label}</text>'
            f'<rect x="{min(bar_x0, bar_x1):.1f}" y="{top}" width="{abs(bar_x1 - bar_x0):.1f}" '
            f'height="{bar_h}" rx="4" fill="var(--series-1)" />'
            f'<text x="{bar_x1 + 8:.1f}" y="{cy:.1f}" font-size="10.5" fill="var(--text-secondary)">point estimate</text>'
            f'<line x1="{wx0:.1f}" y1="{wy:.1f}" x2="{wx1:.1f}" y2="{wy:.1f}" '
            f'stroke="var(--text-secondary)" stroke-width="1.5" />'
            f'<line x1="{wx0:.1f}" y1="{wy - 4:.1f}" x2="{wx0:.1f}" y2="{wy + 4:.1f}" '
            f'stroke="var(--text-secondary)" stroke-width="1.5" />'
            f'<line x1="{wx1:.1f}" y1="{wy - 4:.1f}" x2="{wx1:.1f}" y2="{wy + 4:.1f}" '
            f'stroke="var(--text-secondary)" stroke-width="1.5" />'
            f'<text x="{left_w - 12}" y="{wy + 3:.1f}" font-size="10" text-anchor="end" '
            f'fill="var(--text-muted)">95% CI</text>'
            f'<text x="{wx1 + 10:.1f}" y="{wy + 3:.1f}" font-size="11" fill="{color}">{verdict}</text>'
        )

    zero_line = (
        f'<line x1="{zero_x:.1f}" y1="10" x2="{zero_x:.1f}" y2="{axis_y - 8:.1f}" '
        f'stroke="var(--baseline)" stroke-width="1.5" stroke-dasharray="3 3" />'
        f'<text x="{zero_x:.1f}" y="{axis_y + 14:.1f}" font-size="11" text-anchor="middle" '
        f'fill="var(--text-muted)">0</text>'
        f'<line x1="{left_w}" y1="{axis_y:.1f}" x2="{width - right_w + 30}" y2="{axis_y:.1f}" '
        f'stroke="var(--gridline)" stroke-width="1" />'
        f'<text x="{left_w}" y="{axis_y + 30:.1f}" font-size="10.5" fill="var(--text-muted)">&larr; negative loading</text>'
        f'<text x="{width - right_w + 30}" y="{axis_y + 30:.1f}" font-size="10.5" text-anchor="end" '
        f'fill="var(--text-muted)">positive loading &rarr;</text>'
    )

    body = (
        zero_line
        + row(row1_top, "Example factor A", 0.55, 0.30, 0.80, "&#10003; real exposure", "var(--status-good)")
        + row(row2_top, "Example factor B", 0.15, -0.20, 0.50, "&asymp; inconclusive", "var(--status-warning)")
    )
    return _figure(
        aria_label=(
            "Diagram: two illustrative factor loadings with 95% confidence interval whiskers, one whose "
            "interval excludes zero (a real exposure) and one whose interval includes zero (inconclusive)"
        ),
        caption=(
            "Illustrative example, not your data (see Results for your actual loadings and whiskers). A "
            "factor loading is only worth reading as a real exposure when its whisker &mdash; the 95% "
            "confidence interval around the point estimate &mdash; stays entirely on one side of zero, like "
            "Example A. When the whisker crosses the zero line, like Example B, the data can't distinguish "
            "that loading from &ldquo;no exposure at all&rdquo; at 95% confidence, even though the point "
            "estimate itself is a nonzero number."
        ),
        body=body,
        view_box=f"0 0 {width} {height}",
    )


# ---------------------------------------------------------------------------
# (c) Where a portfolio sits relative to the efficient frontier, and what
#     "moving along it" means -- conceptual, not this run's frontier.
# ---------------------------------------------------------------------------


def frontier_position_diagram() -> str:
    width, height = 680, 300
    left, right, top, bottom = 56, 24, 34, 50
    plot_w, plot_h = width - left - right, height - top - bottom

    def px(fx: float) -> float:
        return left + fx * plot_w

    def py(fy: float) -> float:
        return top + (1 - fy) * plot_h

    def frontier_fy(fx: float) -> float:
        t = max(0.0, min(1.0, (fx - 0.08) / 0.86))
        return 0.10 + 0.72 * math.sqrt(t)

    def frontier_fx_for_fy(fy: float) -> float:
        t = max(0.0, ((fy - 0.10) / 0.72)) ** 2
        return 0.08 + 0.86 * min(1.0, t)

    n = 24
    curve_pts = [(px(0.08 + 0.86 * (i / n)), py(frontier_fy(0.08 + 0.86 * (i / n)))) for i in range(n + 1)]
    curve = " ".join(f"{x:.1f},{y:.1f}" for x, y in curve_pts)

    cur_fx = 0.44
    cur_fy = frontier_fy(cur_fx) - 0.20
    up_fx, up_fy = cur_fx, frontier_fy(cur_fx)
    left_fy = cur_fy
    left_fx = frontier_fx_for_fy(left_fy)

    cur_x, cur_y = px(cur_fx), py(cur_fy)
    up_x, up_y = px(up_fx), py(up_fy)
    lft_x, lft_y = px(left_fx), py(left_fy)

    defs = (
        '<defs><marker id="fp-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 Z" fill="var(--text-secondary)" /></marker></defs>'
    )
    axes = (
        f'<line x1="{left}" y1="{top + plot_h:.1f}" x2="{left + plot_w:.1f}" y2="{top + plot_h:.1f}" '
        f'stroke="var(--baseline)" stroke-width="1" />'
        f'<line x1="{left}" y1="{top:.1f}" x2="{left}" y2="{top + plot_h:.1f}" '
        f'stroke="var(--baseline)" stroke-width="1" />'
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 10}" font-size="11.5" text-anchor="middle" '
        f'fill="var(--text-secondary)">Risk (volatility) &rarr;</text>'
        f'<text x="16" y="{top + plot_h / 2:.1f}" font-size="11.5" fill="var(--text-secondary)" '
        f'text-anchor="middle" transform="rotate(-90 16 {top + plot_h / 2:.1f})">Return &rarr;</text>'
    )
    curve_line = f'<polyline points="{curve}" fill="none" stroke="var(--series-1)" stroke-width="2" stroke-linejoin="round" />'
    curve_label = (
        f'<text x="{curve_pts[-1][0] - 6:.1f}" y="{curve_pts[-1][1] - 10:.1f}" font-size="11" text-anchor="end" '
        f'fill="var(--series-1)">Efficient frontier</text>'
    )

    up_connector = (
        f'<line x1="{cur_x:.1f}" y1="{cur_y:.1f}" x2="{up_x:.1f}" y2="{up_y + 9:.1f}" '
        f'stroke="var(--text-secondary)" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#fp-arrow)" />'
    )
    left_connector = (
        f'<line x1="{cur_x:.1f}" y1="{cur_y:.1f}" x2="{lft_x + 9:.1f}" y2="{lft_y:.1f}" '
        f'stroke="var(--text-secondary)" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#fp-arrow)" />'
    )

    up_dot = (
        f'<circle cx="{up_x:.1f}" cy="{up_y:.1f}" r="5" fill="var(--series-1)" stroke="var(--surface-1)" stroke-width="1.5" />'
        f'<text x="{up_x + 10:.1f}" y="{up_y - 8:.1f}" font-size="11" fill="var(--text-secondary)">More return,</text>'
        f'<text x="{up_x + 10:.1f}" y="{up_y + 6:.1f}" font-size="11" fill="var(--text-secondary)">same risk</text>'
    )
    left_dot = (
        f'<circle cx="{lft_x:.1f}" cy="{lft_y:.1f}" r="5" fill="var(--series-1)" stroke="var(--surface-1)" stroke-width="1.5" />'
        f'<text x="{lft_x:.1f}" y="{lft_y - 14:.1f}" font-size="11" text-anchor="middle" fill="var(--text-secondary)">Same return,</text>'
        f'<text x="{lft_x:.1f}" y="{lft_y - 2:.1f}" font-size="11" text-anchor="middle" fill="var(--text-secondary)">less risk</text>'
    )
    # Same concentric-ring aperture marker as the real frontier chart's "current portfolio"
    # point (`viz.py::frontier_chart`'s `shape == "iris"` case) -- this diagram is meant to
    # teach how to read that exact chart, so its own current-position mark should look like
    # the thing it's teaching, not a plain dot the real chart no longer uses.
    current_halo = f'<circle cx="{cur_x:.1f}" cy="{cur_y:.1f}" r="15" fill="var(--signal)" opacity="0.16" />'
    current_dot = (
        f'<circle cx="{cur_x:.1f}" cy="{cur_y:.1f}" r="9" fill="none" stroke="var(--signal)" stroke-width="1.6" />'
        f'<circle cx="{cur_x:.1f}" cy="{cur_y:.1f}" r="5.8" fill="none" stroke="var(--signal)" stroke-width="1.3" />'
        f'<circle cx="{cur_x:.1f}" cy="{cur_y:.1f}" r="2.4" fill="var(--signal)" stroke="var(--surface-1)" stroke-width="1.5" />'
        f'<text x="{cur_x + 15:.1f}" y="{cur_y + 20:.1f}" font-size="11.5" font-weight="700" '
        f'fill="var(--text-primary)">Your portfolio</text>'
    )

    body = (
        defs + axes + curve_line + curve_label + up_connector + left_connector + up_dot + left_dot + current_halo + current_dot
    )
    return _figure(
        aria_label=(
            "Diagram: a portfolio positioned below a conceptual efficient frontier curve, with two dashed "
            "arrows showing the two equivalent ways to read the gap -- more return at the same risk, or the "
            "same return at less risk"
        ),
        caption=(
            "Conceptual illustration, not your actual frontier or holdings (see Results for those). If your "
            "dot sits below the curve, there are two equivalent ways to describe the same gap: a different "
            "weighting of your exact holdings could historically have earned more return at your current "
            "risk level, or the same return at less risk. Both arrows point at the same underlying gap, just "
            "read along a different axis &mdash; neither is a suggestion to hold different stocks."
        ),
        body=body,
        view_box=f"0 0 {width} {height}",
    )
