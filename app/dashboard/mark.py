"""Factor Lens's brand mark -- Phase 10d, implementing decision 0012.

A circular aperture/focus-ring glyph: an outer focus ring, a mid ring, and a
solid center standing in for the aperture opening -- clean concentric-circle
geometry, no photographic literalism (no blade shapes, no lens-flare). One
construction (`_rings_markup`) feeds every place the mark appears so the
identity reads as one system, not three separate assets:

- the masthead, next to the "Factor Lens" wordmark (`shell.py`)
- the favicon (`favicon_data_uri`, hardcoded colors -- browser chrome can't
  resolve the page's CSS custom properties, so `currentColor` doesn't work
  in a `<link rel="icon">`)
- the frontier chart's "current portfolio" marker, restyled (not rebuilt --
  see `viz.py::_iris_marker_svg`) from a flat dot into this same glyph, so
  the one functional use of the motif is visibly the same mark as the
  wordmark's, not a coincidentally-similar circle.

The loading-state iris (the other functional use decision 0012 calls for)
animates rings built the same way but lives in `viz.py::LOADING_OVERLAY_HTML`
since it needs an SVG `<animate>` sequence, not a static glyph.
"""
from __future__ import annotations

from urllib.parse import quote


def _rings_markup(
    cx: float, cy: float, size: float, ring_color: str, core_color: str, stroke_width: float
) -> str:
    outer_r = size * 0.40
    mid_r = size * 0.255
    core_r = size * 0.105
    return (
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{outer_r:.2f}" fill="none" '
        f'stroke="{ring_color}" stroke-width="{stroke_width:.2f}" />'
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{mid_r:.2f}" fill="none" '
        f'stroke="{ring_color}" stroke-width="{stroke_width * 0.72:.2f}" />'
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{core_r:.2f}" fill="{core_color}" />'
    )


def aperture_svg(
    *,
    size: float = 32,
    ring_color: str = "currentColor",
    core_color: str = "currentColor",
    stroke_width: float = 2.2,
) -> str:
    """The masthead glyph -- sized/colored via CSS (`currentColor`) so it inherits
    `--signal` and responds to theme changes without a second asset."""
    c = size / 2
    return (
        f'<svg viewBox="0 0 {size:g} {size:g}" width="{size:g}" height="{size:g}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Factor Lens" focusable="false">'
        + _rings_markup(c, c, size, ring_color, core_color, stroke_width)
        + "</svg>"
    )


def favicon_data_uri() -> str:
    """Standalone favicon build of the same glyph on a rounded graphite housing --
    fixed dark-mode colors (`--page-plane`/`--signal` from `viz.py::CHART_STYLE`'s
    dark tokens) so the browser tab icon reads correctly regardless of the page's
    own active theme."""
    size = 64.0
    c = size / 2
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size:g} {size:g}">'
        f'<rect width="{size:g}" height="{size:g}" rx="14" fill="#0a0d13"/>'
        + _rings_markup(c, c, size, "#f0a63e", "#f0a63e", 4.4)
        + "</svg>"
    )
    return "data:image/svg+xml," + quote(svg, safe="")
