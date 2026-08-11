"""Pure-function unit tests for the Phase 10g interaction/motion markup hooks
(`app/dashboard/viz.py`, `app/dashboard/diagrams.py`) -- no network/live data
needed. These assert on the *hooks* the client-side motion layer
(`app/dashboard/motion.py`) needs to exist with the right structure/data
attributes, per decision 0015's own testing note: assert on
`data-count-target`/final markup, never on mid-tween DOM state (there is no
JS execution in these tests at all).
"""
from __future__ import annotations

import re

from app.dashboard import diagrams
from app.dashboard.viz import (
    DivergingBarRow,
    FrontierPointVM,
    diverging_bar_chart,
    frontier_chart,
    risk_split_bar,
    stat_tile,
    stat_tile_num,
    stat_tile_pct,
    stat_tile_ratio,
)


def test_stat_tile_pct_emits_count_attributes_matching_displayed_value():
    html = stat_tile_pct("CAPM alpha (annualized)", -0.0164, 2, signed=True)
    assert 'data-count-target="-1.640000"' in html
    assert 'data-count-decimals="2"' in html
    assert 'data-count-suffix="%"' in html
    assert 'data-count-signed="true"' in html
    assert ">-1.64%<" in html


def test_stat_tile_num_emits_count_attributes():
    html = stat_tile_num("CAPM beta vs ^GSPC", 1.2345, 2)
    assert 'data-count-target="1.234500"' in html
    assert 'data-count-suffix=""' in html
    assert 'data-count-signed="false"' in html


def test_stat_tile_ratio_emits_count_attributes():
    html = stat_tile_ratio("Your Sharpe ratio", 0.876)
    assert 'data-count-target="0.876000"' in html


def test_stat_tile_omits_count_attributes_when_value_is_none():
    """A missing figure ("—") must not carry a count-up hook -- there's nothing to animate to."""
    html = stat_tile_pct("Return gap at matched volatility", None, 2, signed=True)
    assert "data-count-target" not in html
    assert ">—<" in html


def test_stat_tile_plain_call_has_no_count_attributes_by_default():
    html = stat_tile("A label", "some text")
    assert "data-count-target" not in html


def test_diverging_bar_chart_bars_and_whiskers_carry_matching_reveal_order():
    rows = [
        DivergingBarRow(name="mkt_rf", label="Market", value=1.05, std_error=0.1, t_stat=10.5, p_value=0.001, ci_lower=0.85, ci_upper=1.25),
        DivergingBarRow(name="smb", label="Size", value=-0.3, std_error=0.05, t_stat=-6.0, p_value=0.001, ci_lower=-0.4, ci_upper=-0.2),
    ]
    svg = diverging_bar_chart("test-chart", rows, value_fmt=lambda v: f"{v:.2f}")
    bar_orders = re.findall(r'class="viz-bar-reveal" data-reveal-order="(\d+)"', svg)
    whisker_orders = re.findall(r'class="viz-whisker-reveal" data-reveal-order="(\d+)"', svg)
    assert bar_orders == ["0", "1"]
    assert whisker_orders == ["0", "1"]
    # Every reveal group carries an inline zero-baseline transform-origin, not a bare bounding-box
    # percentage (which would anchor off-center for a negative bar).
    assert svg.count("transform-origin:") == 2


def test_diverging_bar_chart_without_ci_has_no_whisker_reveal_groups():
    rows = [DivergingBarRow(name="alpha", label="Alpha contribution", value=0.0012)]
    svg = diverging_bar_chart("test-chart", rows, value_fmt=lambda v: f"{v:.4f}")
    assert "viz-bar-reveal" in svg
    assert "viz-whisker-reveal" not in svg


def test_frontier_chart_polyline_and_markers_carry_reveal_hooks():
    frontier = [
        FrontierPointVM(volatility=0.10, ret=0.05, sharpe=0.4),
        FrontierPointVM(volatility=0.20, ret=0.10, sharpe=0.5),
    ]
    current = FrontierPointVM(volatility=0.22, ret=0.11, sharpe=0.5)
    gmv = FrontierPointVM(volatility=0.10, ret=0.05, sharpe=0.3)
    max_sharpe = FrontierPointVM(volatility=0.30, ret=0.16, sharpe=0.55)
    svg = frontier_chart(frontier, current, gmv, max_sharpe, frontier_return_at_current_vol=0.01)

    assert '<polyline class="viz-frontier-polyline"' in svg
    marker_orders = re.findall(r'class="viz-marker-pop" data-marker-order="(\d+)"', svg)
    # GMV, max-Sharpe, current-portfolio, in that DOM order (decision 0015 S4).
    assert marker_orders == ["0", "1", "2"]
    # The halo travels inside the current-portfolio marker's own group (last), not emitted
    # as a separate top-level element.
    current_marker_group = svg.split('data-marker-order="2"')[1].split("</g>", 1)[0]
    assert 'fill="var(--series-2)" opacity="0.16"' in current_marker_group


def test_frontier_chart_degenerate_single_point_still_has_marker_reveal_hooks():
    """No polyline points (degenerate/single-asset case) must not break marker reveal wrapping."""
    p = FrontierPointVM(volatility=0.20, ret=0.10, sharpe=0.5)
    svg = frontier_chart([], current=p, gmv=p, max_sharpe=None, frontier_return_at_current_vol=None)
    assert '<polyline class="viz-frontier-polyline" points=""' in svg
    marker_orders = re.findall(r'class="viz-marker-pop" data-marker-order="(\d+)"', svg)
    assert marker_orders == ["0", "1"]


def test_risk_split_bar_segments_carry_reveal_hooks_anchored_at_own_left_edge():
    svg = risk_split_bar(0.7, 0.3)
    orders = re.findall(r'class="viz-bar-reveal" data-reveal-order="(\d+)"', svg)
    assert orders == ["0", "1"]
    assert "transform-origin:0px" in svg  # segment 1 anchored at the bar's own left edge (x=0)


def test_risk_split_bar_full_explained_share_has_no_second_segment():
    svg = risk_split_bar(1.0, 0.0)
    orders = re.findall(r'class="viz-bar-reveal" data-reveal-order="(\d+)"', svg)
    assert orders == ["0"]


def test_capm_diagram_has_four_ordered_reveal_items_and_diagram_id():
    svg = diagrams.capm_decomposition_diagram()
    assert 'data-diagram="capm"' in svg
    orders = re.findall(r'class="diag-reveal-item" data-order="(\d+)"', svg)
    assert orders == ["0", "1", "2", "3"]


def test_ci_diagram_has_reveal_classes_per_row_and_diagram_id():
    svg = diagrams.factor_loading_ci_diagram()
    assert 'data-diagram="ci"' in svg
    assert svg.count('class="diag-ci-bar"') == 2
    assert svg.count('class="diag-ci-whisker"') == 2
    assert svg.count('class="diag-ci-whisker-line"') == 2
    assert svg.count('class="diag-ci-verdict"') == 2


def test_frontier_position_diagram_has_reveal_classes_and_diagram_id():
    svg = diagrams.frontier_position_diagram()
    assert 'data-diagram="frontier"' in svg
    assert 'class="diag-frontier-curve"' in svg
    assert 'class="diag-frontier-current"' in svg
    arrow_orders = re.findall(r'class="diag-frontier-arrow" data-arrow-order="(\d+)"', svg)
    assert arrow_orders == ["0", "1"]
