#!/usr/bin/env python3
"""Render a set of XP-style account pictures (emoji on soft gradients).

usage: userpics.py OUTDIR
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from drawing import find_font, radial  # noqa: E402

PICS = [
    ("chess", "♟️", (250, 250, 250), (150, 160, 180)),
    ("duck", "\U0001f986", (190, 230, 255), (60, 140, 210)),
    ("dog", "\U0001f436", (255, 240, 200), (220, 170, 90)),
    ("flower", "\U0001f33c", (200, 240, 170), (70, 160, 60)),
    ("guitar", "\U0001f3b8", (255, 220, 200), (200, 90, 60)),
    ("soccer", "⚽", (200, 255, 200), (40, 150, 60)),
    ("cat", "\U0001f431", (255, 230, 240), (210, 120, 160)),
    ("rocket", "\U0001f680", (200, 210, 255), (40, 50, 130)),
    ("butterfly", "\U0001f98b", (220, 245, 255), (90, 160, 220)),
    ("car", "\U0001f3ce️", (255, 245, 210), (230, 150, 40)),
    ("fish", "\U0001f420", (190, 240, 255), (20, 120, 190)),
    ("snowflake", "❄️", (235, 245, 255), (120, 160, 220)),
    ("palm", "\U0001f334", (255, 240, 190), (60, 170, 200)),
    ("frog", "\U0001f438", (220, 255, 200), (90, 170, 60)),
    ("horse", "\U0001f40e", (245, 230, 210), (150, 110, 70)),
    ("airplane", "✈️", (215, 235, 255), (70, 130, 220)),
]


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    emoji = ImageFont.truetype(find_font("NotoColorEmoji.ttf"), 109)
    for name, ch, light, dark in PICS:
        S = 128
        img = radial(S, S, S * 0.35, S * 0.3, S * 1.0, light, dark)
        glyph = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(glyph).text((80, 80), ch, font=emoji, embedded_color=True, anchor="mm")
        bbox = glyph.getbbox()
        if bbox:
            glyph = glyph.crop(bbox)
        g = 92
        glyph.thumbnail((g, g), Image.LANCZOS)
        img.alpha_composite(glyph, ((S - glyph.width) // 2, (S - glyph.height) // 2))
        img.convert("RGB").save(os.path.join(out, name + ".png"))


if __name__ == "__main__":
    main()
