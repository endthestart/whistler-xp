#!/usr/bin/env python3
"""Procedurally paint "Serenity", an original rolling-green-hill-under-blue-sky
wallpaper in the spirit of the classic XP default. Deterministic (seeded)."""
import sys
import numpy as np
from PIL import Image, ImageFilter

W, H = 1920, 1200
rng = np.random.default_rng(2001)


def noise(w, h, scale, octaves=5, persistence=0.5, seed=None):
    """Fractal value noise in [0,1] built from upscaled random grids."""
    r = np.random.default_rng(seed) if seed is not None else rng
    acc = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gw, gh = max(2, int(w / s)), max(2, int(h / s))
        grid = (r.random((gh, gw)) * 255).astype(np.uint8)
        layer = np.asarray(Image.fromarray(grid).resize((w, h), Image.BICUBIC), np.float32) / 255
        acc += layer * amp
        total += amp
        amp *= persistence
        s /= 2
    return acc / total


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t[..., None]


ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = xs / W, ys / H

# ---- sky -------------------------------------------------------------------
top = np.array([22, 76, 200], np.float32)
mid = np.array([62, 125, 230], np.float32)
hor = np.array([150, 196, 245], np.float32)
t1 = smoothstep(0.0, 0.42, v)
sky = lerp(top, mid, t1)
sky = lerp(sky, hor, smoothstep(0.30, 0.62, v))

# clouds: soft cumulus band, denser toward the upper left/middle
n = noise(W, H, 300, octaves=6, persistence=0.58, seed=7)
streak = noise(W, H, 900, octaves=3, persistence=0.5, seed=11)
band = np.exp(-((v - 0.22) / 0.16) ** 2) * (0.75 + 0.5 * np.exp(-((u - 0.45) / 0.35) ** 2))
density = smoothstep(0.52, 0.74, n * 0.85 + streak * 0.30 + band * 0.30 - 0.08)
density *= smoothstep(0.62, 0.30, v)  # fade toward horizon
cloud_col = np.array([250, 252, 255], np.float32)
shade = smoothstep(0.0, 1.0, noise(W, H, 160, 4, 0.5, seed=3))
cloud_col = lerp(cloud_col, np.array([205, 220, 242], np.float32), shade * 0.55)
sky = lerp(sky, cloud_col, density * 0.92)
# a few high wispy strands
wisp = noise(W * 1, H, 140, 5, 0.6, seed=21)
wisp = smoothstep(0.62, 0.80, wisp) * np.exp(-((v - 0.10) / 0.10) ** 2) * 0.35
sky = lerp(sky, np.array([240, 246, 255], np.float32), wisp)

# ---- hills -----------------------------------------------------------------
x = u[0]
# distant hazy hill on the right
far = 0.575 - 0.07 * np.exp(-((x - 0.86) / 0.20) ** 2) - 0.012 * np.sin(x * 9)
# main dome: rises from the left, crest left of centre, falls away to the right
main = (0.66 - 0.205 * np.exp(-((x - 0.36) / 0.36) ** 2)
        - 0.03 * np.exp(-((x - 0.05) / 0.10) ** 2)
        + 0.035 * smoothstep(0.62, 1.0, x))
main += 0.004 * np.sin(x * 23 + 1.3)

img = sky.copy()

def paint_hill(img, crest, base_light, base_dark, haze, seed):
    crest_px = crest[None, :] * H
    depth = (ys - crest_px) / H            # >0 below the crest
    mask = smoothstep(-0.0015, 0.0015, depth)
    g = noise(W, H, 260, 6, 0.55, seed=seed)
    fine = noise(W, H, 18, 3, 0.5, seed=seed + 1)
    # sunlit near the crest, deeper green further down, mottled patches
    t = smoothstep(0.0, 0.42, depth + (g - 0.5) * 0.10)
    col = lerp(base_light, base_dark, t)
    patch = smoothstep(0.48, 0.70, g)
    col = lerp(col, base_dark * 0.9, patch * 0.14)
    col *= (0.94 + 0.12 * fine)[..., None]
    # slope lighting: brighter where the crest rises toward the light (left)
    slope = np.gradient(crest)[None, :] * W
    col *= (1.0 - np.clip(slope, -0.6, 0.6)[..., :] * 0.25)[..., None]
    col = lerp(col, np.array([170, 200, 225], np.float32), np.full(depth.shape, haze))
    return lerp(img, col, mask)

img = paint_hill(img, far, np.array([130, 195, 70], np.float32),
                 np.array([60, 135, 45], np.float32), 0.12, 40)
img = paint_hill(img, main, np.array([150, 205, 60], np.float32),
                 np.array([28, 110, 30], np.float32), 0.0, 50)

# subtle rim light along the main crest
crest_px = main[None, :] * H
rim = np.exp(-((ys - crest_px - 3) / 5.0) ** 2)
img = lerp(img, np.array([200, 235, 120], np.float32), rim * 0.35)

out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
out = out.filter(ImageFilter.GaussianBlur(0.6))

dest = sys.argv[1] if len(sys.argv) > 1 else "serenity.jpg"
out.save(dest, quality=93)
