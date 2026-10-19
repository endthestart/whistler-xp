"""Tiny SVG composition kit for the Whistler icon theme.

Every icon is drawn on a 48x48 design grid. A Ctx renders one variant for a
target pixel size v (48, 32, 24, 22, 16): the viewBox stays 0 0 48 48, but
outlines are exactly one output pixel wide (ctx.lw) and ctx.sx/ctx.sy snap
coordinates to the output pixel grid, so each size comes out crisp.
Glyphs can be placed inside other glyphs with ctx.place(); lw/px follow.
"""
import colorsys
import math
from contextlib import contextmanager


# ----------------------------------------------------------------- numbers

def f(v):
    if isinstance(v, str):
        return v
    s = ("%.3f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def d(*parts):
    out = []
    for p in parts:
        if isinstance(p, (tuple, list)):
            out.extend(f(x) for x in p)
        else:
            out.append(f(p))
    return " ".join(out)


def poly(pts, close=True):
    s = "M" + " L".join("%s %s" % (f(x), f(y)) for x, y in pts)
    return s + (" Z" if close else "")


def rr(x0, y0, x1, y1, r):
    r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    if r <= 0.01:
        return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    return d("M", x0 + r, y0, "H", x1 - r, "A", r, r, 0, 0, 1, x1, y0 + r, "V", y1 - r,
             "A", r, r, 0, 0, 1, x1 - r, y1, "H", x0 + r, "A", r, r, 0, 0, 1, x0, y1 - r,
             "V", y0 + r, "A", r, r, 0, 0, 1, x0 + r, y0, "Z")


def circ(cx, cy, r):
    return d("M", cx - r, cy, "A", r, r, 0, 1, 0, cx + r, cy, "A", r, r, 0, 1, 0, cx - r, cy, "Z")


def ell(cx, cy, rx, ry):
    return d("M", cx - rx, cy, "A", rx, ry, 0, 1, 0, cx + rx, cy, "A", rx, ry, 0, 1, 0, cx - rx, cy, "Z")


def rot(pts, cx, cy, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def arc_pts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# ------------------------------------------------------------------ colour

def _rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _hex(t):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v * 255)))) for v in t)


def mix(a, b, t):
    A, B = _rgb(a), _rgb(b)
    return _hex([A[i] + (B[i] - A[i]) * t for i in range(3)])


def lt(c, t):
    return mix(c, "#FFFFFF", t)


def dk(c, t):
    """Darker shade that keeps (and slightly raises) saturation."""
    h, s, v = colorsys.rgb_to_hsv(*_rgb(c))
    return _hex(colorsys.hsv_to_rgb(h, min(1.0, s * (1 + 0.35 * t) + 0.04 * t), v * (1 - t)))


class Ramp:
    """Colour ramp for a material: hi (specular) .. line (outline)."""

    def __init__(self, hi, light, base, dark, line):
        self.hi, self.light, self.base, self.dark, self.line = hi, light, base, dark, line


GREEN = Ramp("#D9FFC6", "#86DD62", "#3DAA2B", "#25821A", "#1C6314")
BLUE = Ramp("#DDEEFF", "#7AB4FA", "#2F74E0", "#1B4FB8", "#173F8C")
RED = Ramp("#FFE0D6", "#FF8A66", "#E5432A", "#B32213", "#86190E")
ORANGE = Ramp("#FFF0D0", "#FFC060", "#F68B1F", "#CC5F0B", "#93450B")
YELLOW = Ramp("#FFFBE0", "#FFE77A", "#FFCC33", "#E8A511", "#A87808")
TEAL = Ramp("#E0FFFA", "#7FE3D2", "#26B39E", "#16806F", "#0F5E52")
PURPLE = Ramp("#F2E6FF", "#C29BF2", "#8A55D6", "#6534AE", "#4B2683")
GREY = Ramp("#FFFFFF", "#F0F2F5", "#D5DAE1", "#A8B0BC", "#6E7784")
BEIGE = Ramp("#FFFFFA", "#F6F1E1", "#E6DDC4", "#C9BC98", "#8C8064")
FOLDER = Ramp("#FFF8D8", "#FCE49A", "#F3C85A", "#E2A632", "#B47E1C")
PAPER_LINE = "#8D9AB0"
TEXT_LINE = "#A9B6C9"
SHADOW = "#000000"


# --------------------------------------------------------------------- ctx

class Ctx:
    def __init__(self, v):
        self.v = v
        self.u = 48.0 / v
        self.tx, self.ty, self.k = 0.0, 0.0, 1.0
        self.stack = []
        self.defs = []
        self.body = []
        self.n = 0

    # metrics -------------------------------------------------------------
    @property
    def lw(self):
        """One output pixel, in local units."""
        return self.u / self.k

    @property
    def px(self):
        """Output pixel size of the current 48x48 box."""
        return 48.0 * self.k / self.u

    def sx(self, x, half=False):
        rx = self.tx + x * self.k
        if half:
            rx = (math.floor(rx / self.u) + 0.5) * self.u
        else:
            rx = round(rx / self.u) * self.u
        return (rx - self.tx) / self.k

    def sy(self, y, half=False):
        ry = self.ty + y * self.k
        if half:
            ry = (math.floor(ry / self.u) + 0.5) * self.u
        else:
            ry = round(ry / self.u) * self.u
        return (ry - self.ty) / self.k

    def sbox(self, x0, y0, x1, y1, minpx=1):
        a, b, c, e = self.sx(x0), self.sy(y0), self.sx(x1), self.sy(y1)
        if c - a < minpx * self.lw:
            c = a + minpx * self.lw
        if e - b < minpx * self.lw:
            e = b + minpx * self.lw
        return a, b, c, e

    # plumbing ------------------------------------------------------------
    def uid(self, p):
        self.n += 1
        return "%s%d" % (p, self.n)

    def add(self, s):
        self.body.append(s)

    @contextmanager
    def place(self, x, y, size):
        """Draw a 48x48 glyph scaled into the square (x, y, size)."""
        k = size / 48.0
        self.add('<g transform="translate(%s %s) scale(%s)">' % (f(x), f(y), f(k)))
        self.stack.append((self.tx, self.ty, self.k))
        self.tx += x * self.k
        self.ty += y * self.k
        self.k *= k
        try:
            yield
        finally:
            self.add("</g>")
            self.tx, self.ty, self.k = self.stack.pop()

    @contextmanager
    def group(self, opacity=None, transform=None, clip=None):
        attrs = ""
        if opacity is not None:
            attrs += ' opacity="%s"' % f(opacity)
        if transform:
            attrs += ' transform="%s"' % transform
        if clip:
            attrs += ' clip-path="url(#%s)"' % self.clip(clip)
        self.add("<g%s>" % attrs)
        try:
            yield
        finally:
            self.add("</g>")

    def clipped(self, dd, rule=None):
        if rule:
            cid = self.clip(dd, rule)
            self.add('<g clip-path="url(#%s)">' % cid)
            return self._close_group()
        return self.group(clip=dd)

    @contextmanager
    def _close_group(self):
        try:
            yield
        finally:
            self.add("</g>")

    def clip(self, dd, rule=None):
        cid = self.uid("c")
        r = ' clip-rule="%s"' % rule if rule else ""
        self.defs.append('<clipPath id="%s"><path d="%s"%s/></clipPath>' % (cid, dd, r))
        return cid

    def outline(self, dd, col, w=1.0, rule=None):
        cid = self.clip(dd, rule)
        self.add('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" '
                 'clip-path="url(#%s)"/>' % (dd, col, f(2 * w * self.lw), cid))

    # paint servers -------------------------------------------------------
    @staticmethod
    def _stops(stops):
        out = []
        for st in stops:
            off, col = st[0], st[1]
            op = st[2] if len(st) > 2 else 1
            o = "" if op >= 1 else ' stop-opacity="%s"' % f(op)
            out.append('<stop offset="%s" stop-color="%s"%s/>' % (f(off), col, o))
        return "".join(out)

    def lin(self, x1, y1, x2, y2, *stops):
        gid = self.uid("l")
        self.defs.append('<linearGradient id="%s" gradientUnits="userSpaceOnUse" x1="%s" y1="%s" '
                         'x2="%s" y2="%s">%s</linearGradient>'
                         % (gid, f(x1), f(y1), f(x2), f(y2), self._stops(stops)))
        return "url(#%s)" % gid

    def rad(self, cx, cy, r, *stops, fx=None, fy=None, sx=1.0, sy=1.0):
        gid = self.uid("r")
        extra = ""
        if fx is not None:
            extra += ' fx="%s" fy="%s"' % (f(fx), f(fy))
        if sx != 1.0 or sy != 1.0:
            extra += ' gradientTransform="translate(%s %s) scale(%s %s) translate(%s %s)"' % (
                f(cx), f(cy), f(sx), f(sy), f(-cx), f(-cy))
        self.defs.append('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%s" cy="%s" r="%s"%s>'
                         '%s</radialGradient>' % (gid, f(cx), f(cy), f(r), extra, self._stops(stops)))
        return "url(#%s)" % gid

    # drawing -------------------------------------------------------------
    def path(self, dd, fill="none", stroke=None, sw=None, op=None, cap=None, join=None,
             fop=None, sop=None, dash=None, rule=None):
        a = ['d="%s"' % dd, 'fill="%s"' % fill]
        if stroke:
            a.append('stroke="%s"' % stroke)
            a.append('stroke-width="%s"' % f(sw if sw is not None else self.lw))
            if cap:
                a.append('stroke-linecap="%s"' % cap)
            if join:
                a.append('stroke-linejoin="%s"' % join)
            if sop is not None:
                a.append('stroke-opacity="%s"' % f(sop))
            if dash:
                a.append('stroke-dasharray="%s"' % dash)
        if op is not None:
            a.append('opacity="%s"' % f(op))
        if fop is not None:
            a.append('fill-opacity="%s"' % f(fop))
        if rule:
            a.append('fill-rule="%s"' % rule)
        self.add("<path %s/>" % " ".join(a))

    def shape(self, dd, fill, line=None, hl=None, op=None, w=1.0, hlw=1.0):
        """Filled shape with a crisp inside outline (w px) and optional inner
        highlight band (hlw px) just inside the outline."""
        if op is not None:
            self.add('<g opacity="%s">' % f(op))
        self.path(dd, fill)
        if line or hl:
            cid = self.clip(dd)
            if hl:
                self.add('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" '
                         'clip-path="url(#%s)"/>' % (dd, hl, f(2 * (w + hlw) * self.lw), cid))
            if line:
                self.add('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" '
                         'clip-path="url(#%s)"/>' % (dd, line, f(2 * w * self.lw), cid))
        if op is not None:
            self.add("</g>")

    def oshape(self, dd, fill, line, w=1.0, op=None, join="round"):
        """Filled shape with a centred outline (for thin or pointy shapes)."""
        self.path(dd, fill, stroke=line, sw=w * self.lw, join=join, op=op)

    def line(self, pts, col, w=1.0, cap="round", join="round", op=None, dash=None):
        self.path(poly(pts, close=False), "none", stroke=col, sw=w * self.lw, cap=cap, join=join,
                  op=op, dash=dash)

    def hl_grad(self, x0, y0, x1, y1, a=0.9, b=0.0, col="#FFFFFF"):
        return self.lin(x0, y0, x1, y1, (0, col, a), (1, col, b))

    # shadows -------------------------------------------------------------
    def drop(self, dd, dx=None, dy=None, op=0.22):
        """Soft drop shadow of a path toward the bottom right."""
        lw = self.lw
        if dx is None:
            dx = lw * (1 if self.px <= 24 else 1.5)
        if dy is None:
            dy = dx
        self.add('<g transform="translate(%s %s)">' % (f(dx), f(dy)))
        if self.px > 24:
            self.path(dd, "none", stroke=SHADOW, sw=3.2 * lw, sop=op * 0.18, join="round")
            self.path(dd, "none", stroke=SHADOW, sw=1.6 * lw, sop=op * 0.35, join="round")
        self.path(dd, SHADOW, fop=op)
        self.add("</g>")

    # output --------------------------------------------------------------
    def svg(self):
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 48 48">\n'
                "<!-- Whistler icon theme - original artwork -->\n"
                "<defs>%s</defs>\n%s\n</svg>\n") % (self.v, self.v, "\n".join(self.defs), "\n".join(self.body))
