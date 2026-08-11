"""Unit tests for the aperture/focus-ring brand mark (`app/dashboard/mark.py`,
decision 0012). Pure function tests, no network/live data needed.
"""
from __future__ import annotations

import re

from app.dashboard.mark import aperture_svg, favicon_data_uri


def test_aperture_svg_is_three_concentric_circles():
    svg = aperture_svg(size=34, ring_color="var(--signal)", core_color="var(--signal)", stroke_width=2.3)
    circles = re.findall(r"<circle[^>]*/>", svg)
    assert len(circles) == 3
    # Two rings (stroked, unfilled) and one solid core.
    rings = [c for c in circles if 'fill="none"' in c]
    core = [c for c in circles if 'fill="none"' not in c]
    assert len(rings) == 2
    assert len(core) == 1
    # All three share the same center.
    centers = {tuple(re.findall(r'c[xy]="([\d.]+)"', c)) for c in circles}
    assert len(centers) == 1


def test_aperture_svg_uses_currentcolor_by_default_for_theme_inheritance():
    svg = aperture_svg()
    assert "currentColor" in svg


def test_favicon_data_uri_is_a_valid_svg_data_uri_with_no_leftover_text_glyph():
    uri = favicon_data_uri()
    assert uri.startswith("data:image/svg+xml,")
    from urllib.parse import unquote

    svg = unquote(uri[len("data:image/svg+xml,"):])
    assert "<svg" in svg
    assert svg.count("<circle") == 3
    # The old "FL" text-monogram favicon must be fully gone, not just supplemented.
    assert "<text" not in svg
