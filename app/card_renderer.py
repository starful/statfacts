"""Programmatic insight cards (Option B) — PNG from text + numbers, no AI."""
from __future__ import annotations

import io
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# StatFacts brand colors
BG_TOP = (15, 23, 42)       # #0f172a
BG_BOTTOM = (30, 58, 138)   # #1e3a8a
EFFECT_COLOR = (147, 197, 253)  # #93c5fd
TEXT_COLOR = (248, 250, 252)    # #f8fafc
MUTED_COLOR = (148, 163, 184)   # #94a3b8
ACCENT_BAR = (37, 99, 235)      # #2563eb

OG_SIZE = (1200, 630)
LIST_SIZE = (600, 340)

_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _gradient_bg(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def render_insight_card(
    *,
    effect_label: str,
    hook: str,
    title: str = "",
    category: str = "",
    site_name: str = "StatFacts",
    size: tuple[int, int] = OG_SIZE,
) -> bytes:
    """Return PNG bytes for a programmatic share/list card."""
    w, h = size
    scale = w / OG_SIZE[0]
    img = _gradient_bg(size)
    draw = ImageDraw.Draw(img)

    pad = int(48 * scale)
    bar_h = max(int(6 * scale), 4)
    draw.rectangle([(0, 0), (w, bar_h)], fill=ACCENT_BAR)

    brand_font = _load_font(int(22 * scale))
    draw.text((pad, pad), f"📊 {site_name}", fill=MUTED_COLOR, font=brand_font)

    effect_font = _load_font(int(96 * scale), bold=True)
    effect = effect_label or "—"
    draw.text((pad, int(h * 0.28)), effect, fill=EFFECT_COLOR, font=effect_font)

    hook_text = hook or title or "Conditional benchmark"
    hook_font = _load_font(int(32 * scale))
    max_text_w = w - pad * 2
    lines = _wrap_text(hook_text, hook_font, max_text_w, draw)
    y = int(h * 0.52)
    line_h = int(40 * scale)
    for line in lines[:3]:
        draw.text((pad, y), line, fill=TEXT_COLOR, font=hook_font)
        y += line_h

    if title and title != hook_text:
        title_font = _load_font(int(20 * scale))
        draw.text((pad, h - int(80 * scale)), title[:90], fill=MUTED_COLOR, font=title_font)

    if category:
        cat_font = _load_font(int(18 * scale))
        cat = category.upper()[:24]
        bbox = draw.textbbox((0, 0), cat, font=cat_font)
        tw = bbox[2] - bbox[0] + int(24 * scale)
        th = bbox[3] - bbox[1] + int(14 * scale)
        x = w - pad - tw
        y_cat = h - pad - th
        draw.rounded_rectangle(
            [(x, y_cat), (x + tw, y_cat + th)],
            radius=int(8 * scale),
            fill=(30, 41, 59),
        )
        draw.text((x + int(12 * scale), y_cat + int(4 * scale)), cat, fill=MUTED_COLOR, font=cat_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
