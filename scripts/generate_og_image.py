"""One-off generator for Factor Lens's social-preview (Open Graph) image.

Not part of the app's runtime dependencies -- Pillow is only needed to run
this script once, not to serve the app. Run it with:

    uv run --with pillow python scripts/generate_og_image.py

It downloads the three brand fonts (Space Grotesk, JetBrains Mono, Inter --
the same faces `app/dashboard/shell.py`'s `FONT_LINKS` loads for the live
site) from Google's public `google/fonts` GitHub mirror into a local cache,
then renders a 1200x630 PNG to `app/static/og-image.png` matching Phase 9c's
design tokens: graphite-navy background, amber signal accent, and a
diverging-bar motif echoing the Results tab's factor-loadings chart. See
`docs/decisions/0008-phase9c-visual-redesign-and-standard-features.md`.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
FONT_CACHE = REPO_ROOT / ".og-font-cache"
OUT_PATH = REPO_ROOT / "app" / "static" / "og-image.png"

FONT_URLS = {
    "SpaceGrotesk.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf",
    "JetBrainsMono.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
    "Inter.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
}

W, H = 1200, 630
BG = (10, 13, 19)
GRID = (19, 24, 34)
BORDER = (42, 48, 64)
TEXT_PRIMARY = (238, 241, 246)
TEXT_SECONDARY = (154, 163, 181)
TEXT_MUTED = (95, 103, 121)
AMBER = (240, 166, 62)
BLUE = (76, 147, 240)
RED = (239, 107, 107)


def _ensure_fonts() -> None:
    FONT_CACHE.mkdir(exist_ok=True)
    for name, url in FONT_URLS.items():
        path = FONT_CACHE / name
        if not path.exists():
            urllib.request.urlretrieve(url, path)  # noqa: S310 -- fixed, trusted Google Fonts URLs


def _load(name: str, size: int, instance: str | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_CACHE / name), size)
    if instance is not None:
        try:
            font.set_variation_by_name(instance)
        except Exception:
            pass
    return font


def main() -> None:
    _ensure_fonts()

    sg_bold = _load("SpaceGrotesk.ttf", 66, "Bold")
    inter_reg = _load("Inter.ttf", 24)
    mono = _load("JetBrainsMono.ttf", 26)
    mono_sm = _load("JetBrainsMono.ttf", 17)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    step = 40
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=GRID, width=1)

    d.rectangle([0, 0, W, 5], fill=AMBER)

    mark_box = (72, 72, 72 + 64, 72 + 64)
    d.rounded_rectangle(mark_box, radius=10, outline=AMBER, width=2)
    bbox = d.textbbox((0, 0), "FL", font=mono)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(
        (mark_box[0] + (64 - tw) / 2 - bbox[0], mark_box[1] + (64 - th) / 2 - bbox[1]),
        "FL",
        font=mono,
        fill=TEXT_PRIMARY,
    )

    d.text((72, 168), "Factor Lens", font=sg_bold, fill=TEXT_PRIMARY)
    d.text((74, 250), "Portfolio factor attribution, computed live", font=inter_reg, fill=TEXT_SECONDARY)

    tags = ["CAPM", "FAMA-FRENCH", "MARKOWITZ"]
    tx, ty = 74, 300
    for t in tags:
        bbox = d.textbbox((0, 0), t, font=mono_sm)
        tw = bbox[2] - bbox[0]
        pad = 12
        d.rounded_rectangle([tx, ty, tx + tw + pad * 2, ty + 34], radius=6, outline=BORDER, width=1)
        d.text((tx + pad, ty + 7), t, font=mono_sm, fill=AMBER)
        tx += tw + pad * 2 + 12

    bars = [("Mkt-RF", 0.62, BLUE), ("SMB", -0.18, RED), ("HML", 0.31, BLUE), ("RMW", -0.09, RED), ("CMA", 0.14, BLUE)]
    mid_x = 720 + 40
    max_half = 140
    bar_h, bar_gap, start_y = 26, 20, 190
    d.line([(mid_x, start_y - 20), (mid_x, start_y + (bar_h + bar_gap) * len(bars))], fill=BORDER, width=1)
    for i, (label, val, color) in enumerate(bars):
        y0 = start_y + i * (bar_h + bar_gap)
        y1 = y0 + bar_h
        length = int(abs(val) * max_half)
        if val >= 0:
            d.rounded_rectangle([mid_x, y0, mid_x + length, y1], radius=4, fill=color)
        else:
            d.rounded_rectangle([mid_x - length, y0, mid_x, y1], radius=4, fill=color)
        bbox = d.textbbox((0, 0), label, font=mono_sm)
        d.text((mid_x - max_half - 20 - (bbox[2] - bbox[0]), y0 + 3), label, font=mono_sm, fill=TEXT_MUTED)

    d.line([(72, 552), (1128, 552)], fill=BORDER, width=1)
    d.text(
        (72, 574),
        "Live OpenBB + Kenneth French factor data  ·  github.com/ethanverper/factor-lens",
        font=mono_sm,
        fill=TEXT_MUTED,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PATH)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
