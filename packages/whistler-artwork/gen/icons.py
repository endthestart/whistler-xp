#!/usr/bin/env python3
"""Generate Whistler's own icons and logos into an output tree.

usage: icons.py OUTDIR
Creates OUTDIR/icons/hicolor/<size>/apps/*.png, OUTDIR/logos/*.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from drawing import (apply_mask, bold_font, bold_italic_font, downsample, flag, font,  # noqa: E402
                     radial, rounded_mask, shadow, ui_font, vgradient)

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
SIZES = [16, 22, 24, 32, 48, 64, 96, 128, 256]


def save_icon(name, big):
    for s in SIZES:
        d = os.path.join(OUT, "icons", "hicolor", "%dx%d" % (s, s), "apps")
        os.makedirs(d, exist_ok=True)
        downsample(big, s).save(os.path.join(d, name + ".png"))


def rounded_tile(S, top, bottom, radius=0.22, border=(255, 255, 255, 230)):
    tile = vgradient(S, S, [(0, top), (1, bottom)])
    gloss = radial(S, S, S * 0.3, S * 0.2, S * 0.9, (255, 255, 255, 110), (255, 255, 255, 0))
    tile.alpha_composite(gloss)
    m = rounded_mask(S, S, int(S * radius))
    tile = apply_mask(tile, m)
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle([1, 1, S - 2, S - 2], radius=int(S * radius), outline=border, width=max(2, S // 40))
    return tile


def power_icon(S=256):
    tile = rounded_tile(S, (240, 110, 60), (190, 45, 15))
    d = ImageDraw.Draw(tile)
    c, r, w = S / 2, S * 0.27, int(S * 0.085)
    d.arc([c - r, c - r + S * 0.04, c + r, c + r + S * 0.04], start=-60, end=240, fill="white", width=w)
    d.rounded_rectangle([c - w / 2, S * 0.18, c + w / 2, S * 0.53], radius=w // 2, fill="white")
    return tile


def key_icon(S=256):
    tile = rounded_tile(S, (255, 200, 70), (225, 130, 15))
    d = ImageDraw.Draw(tile)
    w = int(S * 0.08)
    # key bow (ring) and blade with teeth
    cx, cy, r = S * 0.36, S * 0.40, S * 0.15
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="white", width=w)
    ang = math.radians(45)
    x0, y0 = cx + r * math.cos(ang), cy + r * math.sin(ang)
    x1, y1 = S * 0.78, S * 0.82
    d.line([x0, y0, x1, y1], fill="white", width=w)
    for t in (0.62, 0.78):
        px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        d.line([px, py, px + S * 0.09, py - S * 0.09], fill="white", width=w)
    return tile


def arrow_icon(S=256):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    disc = radial(S, S, S * 0.38, S * 0.3, S * 0.75, (130, 220, 110), (30, 130, 30))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96], fill=255)
    img = apply_mask(disc, m)
    d = ImageDraw.Draw(img)
    d.ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96], outline=(20, 100, 20, 255), width=max(2, S // 50))
    d.polygon([(S * 0.30, S * 0.42), (S * 0.52, S * 0.42), (S * 0.52, S * 0.28), (S * 0.76, S * 0.50),
               (S * 0.52, S * 0.72), (S * 0.52, S * 0.58), (S * 0.30, S * 0.58)], fill="white")
    return img


def go_icon(S=256):
    """Green rounded-square 'go' arrow used on the welcome screen."""
    tile = rounded_tile(S, (110, 205, 90), (35, 140, 35))
    d = ImageDraw.Draw(tile)
    d.polygon([(S * 0.24, S * 0.42), (S * 0.50, S * 0.42), (S * 0.50, S * 0.26), (S * 0.78, S * 0.50),
               (S * 0.50, S * 0.74), (S * 0.50, S * 0.58), (S * 0.24, S * 0.58)], fill="white")
    return tile


def help_icon(S=256):
    tile = rounded_tile(S, (90, 150, 245), (25, 80, 200))
    d = ImageDraw.Draw(tile)
    f = bold_font(int(S * 0.7))
    d.text((S / 2, S / 2 + S * 0.03), "?", font=f, fill="white", anchor="mm")
    return tile


def standby_icon(S=256):
    tile = rounded_tile(S, (255, 210, 80), (220, 140, 10))
    d = ImageDraw.Draw(tile)
    c, r = S / 2, S * 0.24
    d.ellipse([c - r, c - r, c + r, c + r], fill="white")
    d.ellipse([c - r + S * 0.12, c - r - S * 0.06, c + r + S * 0.12, c + r - S * 0.06],
              fill=(240, 175, 40, 255))
    return tile


def restart_icon(S=256):
    tile = rounded_tile(S, (110, 205, 90), (35, 140, 35))
    d = ImageDraw.Draw(tile)
    c, r, w = S / 2, S * 0.25, int(S * 0.085)
    d.arc([c - r, c - r, c + r, c + r], start=-40, end=250, fill="white", width=w)
    a = math.radians(-40)
    tx, ty = c + r * math.cos(a), c + r * math.sin(a)
    d.polygon([(tx - S * 0.13, ty - S * 0.02), (tx + S * 0.07, ty - S * 0.12), (tx + S * 0.06, ty + S * 0.10)],
              fill="white")
    return tile


def switch_user_icon(S=256):
    tile = rounded_tile(S, (110, 205, 90), (35, 140, 35))
    d = ImageDraw.Draw(tile)
    for ox, col in ((-0.12, (255, 255, 255, 170)), (0.08, (255, 255, 255, 255))):
        cx = S * (0.5 + ox)
        d.ellipse([cx - S * 0.11, S * 0.2, cx + S * 0.11, S * 0.42], fill=col)
        d.pieslice([cx - S * 0.2, S * 0.45, cx + S * 0.2, S * 0.95], 180, 360, fill=col)
    return tile


def window_frame(S, body=(255, 255, 255)):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = S * 0.06, S * 0.10, S * 0.94, S * 0.86
    d.rounded_rectangle([x0, y0, x1, y1], radius=S * 0.05, fill=(0, 60, 200, 255))
    bar = vgradient(int(x1 - x0), int(S * 0.16), [(0, (60, 140, 255)), (0.5, (0, 84, 227)), (1, (0, 60, 200))])
    m = rounded_mask(bar.width, bar.height, int(S * 0.05))
    img.alpha_composite(apply_mask(bar, m), (int(x0), int(y0)))
    d.rectangle([x0 + S * 0.03, y0 + S * 0.16, x1 - S * 0.03, y1 - S * 0.03], fill=body + (255,))
    d.rounded_rectangle([x1 - S * 0.14, y0 + S * 0.03, x1 - S * 0.04, y0 + S * 0.13], radius=S * 0.02,
                        fill=(225, 80, 40, 255), outline=(255, 255, 255, 255), width=max(1, S // 128))
    return img


def wine_icon(S=256):
    img = window_frame(S)
    d = ImageDraw.Draw(img)
    # wine glass
    cx = S * 0.56
    bowl = [cx - S * 0.17, S * 0.34, cx + S * 0.17, S * 0.66]
    d.pieslice(bowl, 0, 180, fill=(150, 20, 50, 255))
    d.rectangle([cx - S * 0.17, S * 0.36, cx + S * 0.17, S * 0.50], fill=(150, 20, 50, 255))
    d.arc([cx - S * 0.18, S * 0.20, cx + S * 0.18, S * 0.67], 0, 180, fill=(120, 120, 140, 255), width=max(2, S // 64))
    d.line([cx - S * 0.18, S * 0.30, cx - S * 0.18, S * 0.45], fill=(120, 120, 140, 255), width=max(2, S // 64))
    d.line([cx + S * 0.18, S * 0.30, cx + S * 0.18, S * 0.45], fill=(120, 120, 140, 255), width=max(2, S // 64))
    d.rectangle([cx - S * 0.02, S * 0.66, cx + S * 0.02, S * 0.78], fill=(130, 130, 150, 255))
    d.ellipse([cx - S * 0.12, S * 0.76, cx + S * 0.12, S * 0.82], fill=(130, 130, 150, 255))
    d.ellipse([cx - S * 0.10, S * 0.38, cx - S * 0.04, S * 0.46], fill=(240, 140, 160, 200))
    # small flag in the corner
    fl = flag(int(S * 0.42), trail=False)
    img.alpha_composite(fl, (int(S * 0.02), int(S * 0.56)))
    return img


def mine_icon(S=256):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, r = S / 2, S * 0.26
    w = max(2, S // 22)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        d.line([c + math.cos(rad) * r * 0.5, c + math.sin(rad) * r * 0.5,
                c + math.cos(rad) * r * 1.55, c + math.sin(rad) * r * 1.55], fill=(0, 0, 0, 255), width=w)
    d.ellipse([c - r, c - r, c + r, c + r], fill=(0, 0, 0, 255))
    d.ellipse([c - r * 0.55, c - r * 0.55, c - r * 0.15, c - r * 0.15], fill=(255, 255, 255, 255))
    return img


def card(S, suit, color, rank):
    img = Image.new("RGBA", (int(S * 0.5), int(S * 0.7)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=S * 0.05, fill=(255, 255, 255, 255),
                        outline=(60, 60, 60, 255), width=max(1, S // 100))
    f = bold_font(int(S * 0.16))
    d.text((S * 0.04, S * 0.02), rank, font=f, fill=color)
    sf = font(int(S * 0.3), "DejaVuSans.ttf", "Arial Unicode.ttf", "Apple Symbols.ttf")
    d.text((img.width / 2, img.height * 0.6), suit, font=sf, fill=color, anchor="mm")
    return img


def cards_icon(S, cards):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    n = len(cards)
    for i, (suit, color, rank) in enumerate(cards):
        c = card(S, suit, color, rank).rotate((i - (n - 1) / 2) * -14, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(c, (int(S * 0.5 - c.width / 2 + (i - (n - 1) / 2) * S * 0.14),
                                int(S * 0.5 - c.height / 2)))
    return img


def setup_icon(S=256):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    disc = radial(S, S, S * 0.4, S * 0.35, S * 0.6, (245, 245, 255), (150, 170, 210))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([S * 0.05, S * 0.05, S * 0.85, S * 0.85], fill=255)
    ImageDraw.Draw(m).ellipse([S * 0.38, S * 0.38, S * 0.52, S * 0.52], fill=0)
    img = apply_mask(disc, m)
    d = ImageDraw.Draw(img)
    d.ellipse([S * 0.05, S * 0.05, S * 0.85, S * 0.85], outline=(110, 120, 150, 255), width=max(1, S // 80))
    a = arrow_icon(int(S * 0.5))
    img.alpha_composite(a, (int(S * 0.48), int(S * 0.48)))
    return img


def folder_icon(S=256, inner=None):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    back = vgradient(int(S * 0.84), int(S * 0.62), [(0, (250, 215, 110)), (1, (225, 170, 50))])
    img.alpha_composite(apply_mask(back, rounded_mask(back.width, back.height, int(S * 0.04))),
                        (int(S * 0.08), int(S * 0.22)))
    d.rounded_rectangle([S * 0.08, S * 0.15, S * 0.42, S * 0.3], radius=S * 0.04, fill=(240, 195, 80, 255))
    if inner is not None:
        img.alpha_composite(inner.resize((int(S * 0.5), int(S * 0.5)), Image.LANCZOS), (int(S * 0.26), int(S * 0.24)))
    front = vgradient(int(S * 0.88), int(S * 0.5), [(0, (255, 235, 150)), (1, (240, 190, 70))])
    front = front.transform(front.size, Image.AFFINE, (1, 0.12, 0, 0, 1, 0), Image.BICUBIC)
    img.alpha_composite(apply_mask(front, rounded_mask(front.width, front.height, int(S * 0.04))),
                        (int(S * 0.06), int(S * 0.40)))
    return img


def program_group_icon(S=256):
    win = window_frame(S)
    return folder_icon(S, inner=win)


def start_logo():
    return flag(512, trail=False)


def wordmark(scale=1.0, sub="Linux Edition", top="CachyOS", flag_size=None):
    """"Whistler xp" wordmark next to the pinwheel mark."""
    s = scale
    big = bold_font(int(64 * s))
    xp = bold_italic_font(int(34 * s))
    small = ui_font(int(15 * s))
    fl = flag(int(flag_size or 120 * s), trail=True)
    word = "Whistler"
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    bw = d.textbbox((0, 0), word, font=big)
    xw = d.textbbox((0, 0), "xp", font=xp)
    W = int(fl.width + 10 * s + bw[2] + xw[2] + 12 * s)
    H = int(max(fl.height, bw[3] + 40 * s) + 10 * s)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(fl, (0, int((H - fl.height) / 2)))
    d = ImageDraw.Draw(img)
    tx = fl.width + int(10 * s)
    ty = int(H / 2 - bw[3] / 2)
    d.text((tx + 2, ty - int(16 * s)), top, font=small, fill="white")
    d.text((tx, ty), word, font=big, fill="white")
    d.text((tx + bw[2] + int(4 * s), ty - int(6 * s)), "xp", font=xp, fill=(255, 110, 30, 255))
    if sub:
        sw = d.textbbox((0, 0), sub, font=small)[2]
        d.text((tx + bw[2] + xw[2] - sw, ty + bw[3] + int(2 * s)), sub, font=small, fill="white")
    return img


def boot_assets(dest):
    os.makedirs(dest, exist_ok=True)
    wordmark(1.0).save(os.path.join(dest, "logo.png"))
    # progress box: rounded grey frame on black
    W, H = 124, 16
    box = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, W - 1, H - 1], radius=4, outline=(180, 180, 180, 255), width=2)
    box.save(os.path.join(dest, "progress-box.png"))
    blk = vgradient(8, 8, [(0, (130, 160, 255)), (0.45, (40, 70, 220)), (1, (20, 40, 160))])
    blk.save(os.path.join(dest, "progress-block.png"))
    f = ui_font(13)
    for name, text in (("copyright.png", "Copyright © The Whistler Project"),
                       ("vendor.png", "Built on CachyOS")):
        t = Image.new("RGBA", (300, 20), (0, 0, 0, 0))
        ImageDraw.Draw(t).text((0, 2), text, font=f, fill=(200, 200, 200, 255))
        t = t.crop(t.getbbox())
        t.save(os.path.join(dest, name))
    lock = Image.new("RGBA", (300, 24), (0, 0, 0, 0))
    ImageDraw.Draw(lock).text((0, 2), "Enter passphrase:", font=f, fill="white")
    lock.crop(lock.getbbox()).save(os.path.join(dest, "prompt.png"))
    bullet = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    ImageDraw.Draw(bullet).ellipse([1, 1, 8, 8], fill="white")
    bullet.save(os.path.join(dest, "bullet.png"))
    entry = Image.new("RGBA", (220, 24), (255, 255, 255, 255))
    ImageDraw.Draw(entry).rectangle([0, 0, 219, 23], outline=(127, 157, 185, 255))
    entry.save(os.path.join(dest, "entry.png"))


def main():
    save_icon("whistler-start-logo", start_logo())
    save_icon("whistler-logo", flag(512))
    save_icon("whistler-turnoff", power_icon())
    save_icon("whistler-logoff", key_icon())
    save_icon("whistler-allprograms-arrow", arrow_icon())
    save_icon("whistler-go", go_icon())
    save_icon("whistler-help", help_icon())
    save_icon("whistler-standby", standby_icon())
    save_icon("whistler-restart", restart_icon())
    save_icon("whistler-switchuser", switch_user_icon())
    save_icon("whistler-winecenter", wine_icon())
    save_icon("whistler-minesweeper", mine_icon())
    save_icon("whistler-solitaire", cards_icon(256, [("\u2660", (0, 0, 0, 255), "A"), ("\u2665", (200, 0, 0, 255), "K")]))
    save_icon("whistler-freecell", cards_icon(256, [("\u2663", (0, 0, 0, 255), "Q"), ("\u2666", (200, 0, 0, 255), "J"),
                                                    ("\u2660", (0, 0, 0, 255), "K")]))
    save_icon("whistler-spider", cards_icon(256, [("\u2660", (0, 0, 0, 255), "K"), ("\u2660", (0, 0, 0, 255), "Q")]))
    save_icon("whistler-setup", setup_icon())
    save_icon("whistler-programs-folder", program_group_icon())
    logos = os.path.join(OUT, "logos")
    os.makedirs(logos, exist_ok=True)
    wordmark(1.0).save(os.path.join(logos, "wordmark.png"))
    wordmark(0.75, sub=None).save(os.path.join(logos, "wordmark-small.png"))
    sh, _ = shadow(flag(160), (3, 3), 3, 0.4)
    sh.save(os.path.join(logos, "flag-160.png"))
    boot_assets(os.path.join(OUT, "plymouth"))
    # 640x480 syslinux menu background
    sp = Image.new("RGB", (640, 480), (0, 0, 0))
    wm = wordmark(0.8)
    sp.paste(wm, ((640 - wm.width) // 2, 70), wm)
    sp.save(os.path.join(logos, "syslinux-splash.png"))


if __name__ == "__main__":
    main()
