"""Unit tests for the Phase 10b frontier-chart marker-label collision fix
(`app/dashboard/viz.py::frontier_chart`). Pure function tests, no network/live
data needed -- see docs/decisions/0011-phase10b-frontier-marker-label-collision.md.
"""
from __future__ import annotations

import re

from app.dashboard.viz import FrontierPointVM, frontier_chart

_LABEL_RE = re.compile(
    r'<text x="([\d.]+)" y="([\d.]+)" font-size="11.5" text-anchor="(start|end)"[^>]*font-weight="600">([^<]*)</text>'
)


def _extract_labels(svg: str) -> list[dict]:
    labels = []
    for x, y, anchor, text in _LABEL_RE.findall(svg):
        x, y = float(x), float(y)
        label_w = len(text) * 6.4
        x0 = x - label_w if anchor == "end" else x
        x1 = x if anchor == "end" else x + label_w
        labels.append({"text": text, "x": x, "y": y, "anchor": anchor, "bbox": (x0, y - 10.0, x1, y + 4.0)})
    return labels


def _bbox_overlap(a: tuple, b: tuple) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _assert_no_label_overlaps(labels: list[dict]) -> None:
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            assert not _bbox_overlap(labels[i]["bbox"], labels[j]["bbox"]), (
                f"labels overlap: {labels[i]['text']!r} vs {labels[j]['text']!r}"
            )


def test_degenerate_single_point_merges_all_three_labels_into_one():
    """Single-asset (or fully-identical-holdings) portfolio: GMV == max-Sharpe ==
    current portfolio at the exact same point. Must render one combined label, not
    three stacked, illegible ones."""
    p = FrontierPointVM(volatility=0.20, ret=0.10, sharpe=0.5)
    svg = frontier_chart([], current=p, gmv=p, max_sharpe=p, frontier_return_at_current_vol=None)
    labels = _extract_labels(svg)
    assert len(labels) == 1
    assert labels[0]["text"] == "GMV = Max Sharpe = Your portfolio"


def test_qa_repro_close_but_distinct_markers_merge_only_the_close_pair():
    """QA's exact repro shape: GMV and current portfolio land a fraction of a pixel
    apart (genuinely close to minimum-variance), max-Sharpe sits elsewhere. Must
    combine GMV + current into one label and leave max-Sharpe's label separate."""
    gmv = FrontierPointVM(volatility=0.20, ret=0.10, sharpe=0.5)
    current = FrontierPointVM(volatility=0.2001, ret=0.1000, sharpe=0.5)  # ~sub-pixel apart from gmv
    max_sharpe = FrontierPointVM(volatility=0.35, ret=0.18, sharpe=0.6)
    svg = frontier_chart([], current=current, gmv=gmv, max_sharpe=max_sharpe, frontier_return_at_current_vol=None)
    labels = _extract_labels(svg)
    texts = {label["text"] for label in labels}
    assert texts == {"GMV = Your portfolio", "Max Sharpe"}
    _assert_no_label_overlaps(labels)


def test_close_but_not_coincident_labels_never_overlap():
    """Markers close enough on screen for their default label placements to collide,
    but far enough apart to stay visually distinct (not merged) -- the collision-
    avoidance pass must still separate the two labels."""
    gmv = FrontierPointVM(volatility=0.05, ret=0.02, sharpe=0.2)
    current = FrontierPointVM(volatility=0.30, ret=0.15, sharpe=0.5)
    max_sharpe = FrontierPointVM(volatility=0.30, ret=0.158, sharpe=0.52)
    svg = frontier_chart(
        [], current=current, gmv=gmv, max_sharpe=max_sharpe, frontier_return_at_current_vol=None
    )
    labels = _extract_labels(svg)
    texts = {label["text"] for label in labels}
    assert texts == {"GMV", "Your portfolio", "Max Sharpe"}
    _assert_no_label_overlaps(labels)


def test_no_max_sharpe_still_handles_gmv_and_current_collision():
    """max_sharpe is optional (None when the tangency portfolio doesn't solve) --
    the two-marker case must still merge/collide-avoid correctly."""
    p = FrontierPointVM(volatility=0.15, ret=0.08, sharpe=0.4)
    svg = frontier_chart([], current=p, gmv=p, max_sharpe=None, frontier_return_at_current_vol=None)
    labels = _extract_labels(svg)
    assert len(labels) == 1
    assert labels[0]["text"] == "GMV = Your portfolio"


def test_far_apart_markers_keep_independent_labels_and_right_edge_flip():
    """Baseline (non-colliding) case must still behave as before: three independent
    labels, and a marker near the plot's right edge flips its label leftward instead
    of clipping."""
    gmv = FrontierPointVM(volatility=0.05, ret=0.02, sharpe=0.2)
    current = FrontierPointVM(volatility=0.15, ret=0.09, sharpe=0.45)
    max_sharpe = FrontierPointVM(volatility=0.40, ret=0.20, sharpe=0.55)  # near the right edge
    # A narrower chart width than the default so the highest-volatility marker's
    # label genuinely doesn't fit before the plot's right edge.
    svg = frontier_chart(
        [], current=current, gmv=gmv, max_sharpe=max_sharpe, frontier_return_at_current_vol=None, width=500
    )
    labels = _extract_labels(svg)
    texts = {label["text"] for label in labels}
    assert texts == {"GMV", "Your portfolio", "Max Sharpe"}
    _assert_no_label_overlaps(labels)
    ms_label = next(label for label in labels if label["text"] == "Max Sharpe")
    assert ms_label["anchor"] == "end"  # flipped left, not clipped off the right edge
