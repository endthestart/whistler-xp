"""Small drawing toolkit (numpy + Pillow) for the generated Whistler artwork."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIRS = ["/usr/share/fonts", os.path.expanduser("~/.fonts"), "/Library/Fonts",
             "/System/Library/Fonts", "/System/Library/Fonts/Supplemental"]


def find_font(*names):
    """Return the first font file found among candidate file names."""
    for name in names:
        for d in FONT_DIRS:
            for root, _dirs, files in os.walk(d):
                for f in files:
                    if f.lower() == name.lower():
                        return os.path.join(root, f)
    raise FileNotFoundError("none of the fonts %s are installed" % (names,))


def font(size, *names):
    return ImageFont.truetype(find_font(*names), size)


# Only openly licensed fonts are used to render artwork (Fira Sans: OFL,
# DejaVu: free license). Arial is a local-preview fallback on macOS only.
def bold_font(size):
    return font(size, "FiraSans-Bold.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf")


def bold_italic_font(size):
    return font(size, "FiraSans-BoldItalic.ttf", "DejaVuSans-BoldOblique.ttf", "Arial Bold Italic.ttf")


def ui_font(size):
    return font(size, "FiraSans-Regular.ttf", "DejaVuSans.ttf", "Arial.ttf")


def ui_bold_font(size):
    return font(size, "FiraSans-SemiBold.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf")


def rgba(c, a=255):
    return (int(c[0]), int(c[1]), int(c[2]), a)


def vgradient(w, h, stops):
    """Vertical gradient image from [(pos, (r,g,b[,a])), ...]."""
    ys = np.linspace(0, 1, h)
    pos = [p for p, _ in stops]
    cols = np.array([list(c) + ([255] if len(c) == 3 else []) for _, c in stops], np.float32)
    out = np.zeros((h, w, 4), np.float32)
    for ch in range(4):
        out[:, :, ch] = np.interp(ys, pos, cols[:, ch])[:, None]
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def radial(w, h, cx, cy, r, inner, outer):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.clip(np.hypot(xs - cx, ys - cy) / r, 0, 1)[..., None]
    a = np.array(list(inner) + ([255] if len(inner) == 3 else []), np.float32)
    b = np.array(list(outer) + ([255] if len(outer) == 3 else []), np.float32)
    return Image.fromarray((a + (b - a) * d).astype(np.uint8), "RGBA")


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    return m


def apply_mask(img, mask):
    out = img.copy()
    a = np.asarray(out.split()[3], np.float32) * (np.asarray(mask, np.float32) / 255)
    out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out


def shadow(img, offset=(2, 2), blur=2, opacity=0.5):
    w, h = img.size
    pad = blur * 3 + max(abs(offset[0]), abs(offset[1]))
    base = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: int(v * opacity))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 255))
    sh.putalpha(a)
    base.paste(sh, (pad + offset[0], pad + offset[1]), sh)
    base = base.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(img, (pad, pad))
    return base, pad


def downsample(img, size):
    return img.resize((size, size), Image.LANCZOS)


def flag(size=512, trail=True):
    """Whistler's mark: a four-colour pinwheel (spinning in the wind) with
    optional motion streaks. Original artwork, drawn with cairo."""
    try:
        import cairo
    except ImportError:
        import cairocffi as cairo
    import math
    S = size
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    cr = cairo.Context(surf)
    cr.scale(S / 100.0, S / 100.0)
    cx, cy = (56, 50) if trail else (50, 50)
    blades = [((241, 90, 41), (255, 160, 110)), ((122, 190, 30), (190, 235, 110)),
              ((24, 120, 220), (110, 185, 255)), ((250, 186, 10), (255, 228, 120))]
    for i, (dark, light) in enumerate(blades):
        cr.save()
        cr.translate(cx, cy)
        cr.rotate(math.radians(-45 + 90 * i))
        # a pinwheel sail: straight leading edge, full curved back
        cr.new_path()
        cr.move_to(0, 0)
        cr.line_to(0, -43)
        cr.curve_to(20, -42, 36, -30, 38, -10)
        cr.curve_to(24, -12, 10, -6, 0, 0)
        cr.close_path()
        g = cairo.LinearGradient(0, -40, 30, -4)
        g.add_color_stop_rgb(0, *(c / 255 for c in light))
        g.add_color_stop_rgb(1, *(c / 255 for c in dark))
        cr.set_source(g)
        cr.fill_preserve()
        cr.set_source_rgba(*(c / 255 * 0.65 for c in dark), 0.95)
        cr.set_line_width(1.1)
        cr.stroke()
        # folded flap along the leading edge
        cr.new_path()
        cr.move_to(0, -2)
        cr.line_to(0, -41)
        cr.curve_to(4, -30, 7, -16, 0, -2)
        cr.close_path()
        cr.set_source_rgba(1, 1, 1, 0.35)
        cr.fill()
        cr.restore()
    # hub
    g = cairo.RadialGradient(cx - 1.5, cy - 1.5, 0.5, cx, cy, 5)
    g.add_color_stop_rgb(0, 1, 1, 1)
    g.add_color_stop_rgb(1, 0.72, 0.74, 0.8)
    cr.arc(cx, cy, 4.2, 0, 2 * math.pi)
    cr.set_source(g)
    cr.fill_preserve()
    cr.set_source_rgba(0.35, 0.38, 0.45, 1)
    cr.set_line_width(0.8)
    cr.stroke()
    if trail:
        # wind streaks to the left
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for y, x0, x1, w, a in ((36, 2, 16, 2.4, 0.55), (50, 0, 11, 2.8, 0.7), (64, 4, 15, 2.2, 0.5)):
            g = cairo.LinearGradient(x0, 0, x1, 0)
            g.add_color_stop_rgba(0, 1, 1, 1, 0)
            g.add_color_stop_rgba(1, 1, 1, 1, a)
            cr.set_source(g)
            cr.set_line_width(w)
            cr.move_to(x0, y)
            cr.line_to(x1, y)
            cr.stroke()
    data = surf.get_data()
    img = Image.frombuffer("RGBA", (S, S), bytes(data), "raw", "BGRA", 0, 1)
    return img
