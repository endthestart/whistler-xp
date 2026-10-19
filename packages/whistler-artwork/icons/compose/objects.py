"""Objects: monitors, cases, drives, windows and other things."""
import math

from glyphs import curved_arrow, rounded_poly, text_lines
from lib import BEIGE, BLUE, GREEN, PAPER_LINE, Ramp, arc_pts, circ, d, dk, ell, lt, poly, rr

METAL = Ramp("#FFFFFF", "#EEF1F5", "#C9D0D9", "#98A2B0", "#5E6774")
SCREEN = ("#7CC8FF", "#2F86E6", "#1F9C8C")
BROWN = Ramp("#FFF0D8", "#EBC48C", "#D29E5A", "#A87436", "#76501F")


def box3d(c, x0, y0, x1, y1, dx, dy, front, top, side, line, shadow=True, hl=True):
    """Oblique box: front face (x0,y0)-(x1,y1), depth receding up-right by (dx, dy)."""
    lw = c.lw
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    DX = max(lw, c.sx(x1 + dx) - X1)
    DY = max(lw, Y0 - c.sy(y0 - dy))
    sil = poly([(X0, Y1), (X0, Y0), (X0 + DX, Y0 - DY), (X1 + DX, Y0 - DY), (X1 + DX, Y1 - DY), (X1, Y1)])
    if shadow:
        c.drop(sil)
    topf = poly([(X0, Y0), (X0 + DX, Y0 - DY), (X1 + DX, Y0 - DY), (X1, Y0)])
    sidef = poly([(X1, Y0), (X1 + DX, Y0 - DY), (X1 + DX, Y1 - DY), (X1, Y1)])
    frontf = rr(X0, Y0, X1, Y1, 0)
    c.path(topf, top)
    c.path(sidef, side)
    c.path(frontf, front)
    if hl:
        c.path(rr(X0, Y0, X1, Y0 + lw, 0), line, op=0.45)
        c.path(rr(X0 + lw, Y0 + lw, X1, Y0 + 2 * lw, 0), "#FFFFFF", op=0.7)
        c.path(rr(X1 - lw, Y0, X1, Y1, 0), line, op=0.35)
    c.outline(sil, line)
    return dict(X0=X0, Y0=Y0, X1=X1, Y1=Y1, DX=DX, DY=DY, sil=sil, top=topf, side=sidef, front=frontf)


# ----------------------------------------------------------------- monitor

def screen_fill(c, x0, y0, x1, y1, cols=SCREEN):
    return c.lin(x0, y0, x1 * 0.4 + x0 * 0.6, y1, (0, cols[0]), (0.55, cols[1]), (1, cols[2]))


def crt(c, x0, y0, x1, y1, screen=None, stand=True, ramp=BEIGE, depth=None, led=True, shadow=True,
        screen_cols=SCREEN):
    """Beige CRT monitor; screen(c, box) draws the picture. Returns the screen box."""
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    w, h = X1 - X0, Y1 - Y0
    if depth is None:
        depth = w * 0.13
    D = max(lw, c.sx(X1 + depth) - X1)
    cx = c.sx((X0 + X1) / 2)
    parts = []
    side = poly([(X1 - lw, Y0 + 2 * lw), (X1 + D, Y0 + max(lw, h * 0.18)), (X1 + D, Y1 - max(lw, h * 0.22)),
                 (X1 - lw, Y1 - 2 * lw)])
    if stand:
        nh = max(lw, c.sy(h * 0.1) - c.sy(0))
        fh = max(lw, c.sy(h * 0.1) - c.sy(0))
        ny1 = Y1 + nh
        neck = rr(c.sx(cx - w * 0.14), Y1 - lw, c.sx(cx + w * 0.14), ny1, 0)
        foot = rounded_poly([(c.sx(cx - w * 0.36), ny1 + fh), (c.sx(cx - w * 0.28), ny1),
                             (c.sx(cx + w * 0.3), ny1), (c.sx(cx + w * 0.4), ny1 + fh)], 0.6 * lw)
        parts += [neck, foot]
    bezel = rr(X0, Y0, X1, Y1, min(2.0, 0.9 * lw) if px > 16 else 0.5 * lw)
    if shadow:
        for p in parts + [side, bezel]:
            c.drop(p)
    if stand:
        c.shape(foot, c.lin(0, ny1, 0, ny1 + fh, (0, ramp.light), (1, ramp.dark)), line=ramp.line)
        c.shape(neck, c.lin(X0, 0, X1, 0, (0, ramp.base), (1, ramp.dark)), line=ramp.line)
    c.shape(side, c.lin(X1, 0, X1 + D, 0, (0, ramp.dark), (1, dk(ramp.dark, 0.15))), line=ramp.line)
    c.shape(bezel, c.lin(X0, Y0, X1, Y1, (0, ramp.hi), (0.4, ramp.light), (1, ramp.base)), line=ramp.line,
            hl=c.hl_grad(X0, Y0, X0 + w * 0.5, Y0 + h * 0.5, 0.9, 0.2))
    if px * w / 48 <= 12:
        m, mb = lw, lw
    elif px * w / 48 <= 20:
        m, mb = 2 * lw, 2 * lw
    else:
        m = c.sx(X0 + max(2 * lw, w * 0.08)) - X0
        mb = c.sy(Y1) - c.sy(Y1 - max(3 * lw, h * 0.15))
    sx0, sy0, sx1, sy1 = X0 + m, Y0 + m, X1 - m, Y1 - mb
    scr = rr(sx0, sy0, sx1, sy1, 0.5 * lw if px * w / 48 > 20 else 0)
    c.shape(scr, screen_fill(c, sx0, sy0, sx1, sy1, screen_cols), line=dk(ramp.line, 0.25))
    if screen:
        with c.clipped(rr(sx0 + lw, sy0 + lw, sx1 - lw, sy1 - lw, 0)):
            screen(c, (sx0 + lw, sy0 + lw, sx1 - lw, sy1 - lw))
    if px * w / 48 > 12:
        with c.clipped(scr):
            c.path(poly([(sx0, sy0), (sx0 + (sx1 - sx0) * 0.7, sy0), (sx0, sy0 + (sy1 - sy0) * 0.75)]),
                   c.lin(sx0, sy0, sx0 + (sx1 - sx0) * 0.35, sy0 + (sy1 - sy0) * 0.4, (0, "#FFFFFF", 0.38),
                         (1, "#FFFFFF", 0.04)))
    if led and px * w / 48 > 18:
        lx, ly = c.sx(X1 - max(2 * lw, w * 0.1)), c.sy(Y1 - mb / 2 - lw / 2)
        c.path(rr(lx, ly, lx + lw * (1 if px * w / 48 < 30 else 2), ly + lw, 0), "#3BD12A")
    return (sx0, sy0, sx1, sy1)


def tower(c, x0, y0, x1, y1, dx, dy, ramp=BEIGE, server=False, shadow=True):
    lw, px = c.lw, c.px
    b = box3d(c, x0, y0, x1, y1, dx, dy,
              c.lin(x0, y0, x1, y1, (0, ramp.hi), (0.5, ramp.light), (1, ramp.base)),
              c.lin(x0, y0 - dy, x1 + dx, y0, (0, ramp.hi), (1, ramp.light)),
              c.lin(x1, 0, x1 + dx, 0, (0, ramp.dark), (1, dk(ramp.dark, 0.12))), ramp.line, shadow=shadow)
    X0, Y0, X1, Y1 = b["X0"], b["Y0"], b["X1"], b["Y1"]
    w, h = X1 - X0, Y1 - Y0
    pw = px * w / 48
    if pw < 4:
        bx0, bx1 = X0 + lw, X1 - lw
    else:
        bx0, bx1 = c.sx(X0 + max(lw, w * 0.15)), c.sx(X1 - max(lw, w * 0.15))
    nb = 4 if server else 2
    y = c.sy(Y0 + max(2 * lw, h * 0.1))
    bay_h = max(lw, c.sy(h * 0.09) - c.sy(0)) if pw >= 8 else lw
    for i in range(nb):
        if pw >= 8:
            c.shape(rr(bx0, y, bx1, y + bay_h, 0), c.lin(0, y, 0, y + bay_h, (0, ramp.light), (1, ramp.dark)),
                    line=dk(ramp.line, 0.05))
            if server:
                c.path(rr(bx1 - 2 * lw, y + bay_h / 2 - lw / 2, bx1 - lw, y + bay_h / 2 + lw / 2, 0), "#46E03A")
        else:
            c.path(rr(bx0, y, bx1, y + lw, 0), ramp.line, op=0.7)
        y += bay_h + (lw if pw >= 8 else lw)
    if pw >= 8 and not server:
        fy = c.sy(Y0 + h * 0.42)
        c.path(rr(c.sx(X0 + w * 0.3), fy, c.sx(X1 - w * 0.3), fy + lw, 0), dk(ramp.line, 0.2), op=0.8)
    # power button + led
    pyy = c.sy(Y1 - max(2 * lw, h * 0.16))
    if pw >= 8:
        c.shape(circ((X0 + X1) / 2, pyy, max(lw, w * 0.11)), c.lin(0, pyy - 2, 0, pyy + 2, (0, ramp.hi),
                                                                     (1, ramp.dark)), line=ramp.line)
        c.path(rr(c.sx(X1 - w * 0.25), c.sy(pyy + w * 0.15), c.sx(X1 - w * 0.25) + lw,
                  c.sy(pyy + w * 0.15) + lw, 0), "#3BD12A")
    else:
        c.path(rr(c.sx((X0 + X1) / 2), pyy, c.sx((X0 + X1) / 2) + lw, pyy + lw, 0), "#3BD12A")
    return b


# ------------------------------------------------------------------ window

def window(c, x0, y0, x1, y1, body="#FFFFFF", content=None, close=True, shadow=True, frame=BLUE):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    w, h = X1 - X0, Y1 - Y0
    pw = px * w / 48
    th = (2 if pw <= 12 else 3 if pw <= 18 else 4 if pw <= 26 else 5) * lw
    if pw > 34:
        th = c.sy(Y0 + max(6, h * 0.2)) - Y0
    r = min(3.0, th * 0.45)
    fw = lw if pw <= 30 else 2 * lw
    outer = d("M", X0, Y0 + r, "A", r, r, 0, 0, 1, X0 + r, Y0, "H", X1 - r, "A", r, r, 0, 0, 1, X1, Y0 + r,
              "V", Y1, "H", X0, "Z")
    if shadow:
        c.drop(outer)
    c.shape(outer, c.lin(0, Y0, 0, Y1, (0, "#2F7CF2"), (1, "#0D4FC8")), line="#0B3C9C")
    tb = d("M", X0, Y0 + r, "A", r, r, 0, 0, 1, X0 + r, Y0, "H", X1 - r, "A", r, r, 0, 0, 1, X1, Y0 + r,
           "V", Y0 + th, "H", X0, "Z")
    c.shape(tb, c.lin(0, Y0, 0, Y0 + th, (0, "#8CC2FF"), (0.18, "#3C8DF8"), (0.55, "#0F5FE6"), (1, "#0B4FD0")),
            line="#0B3C9C")
    bx0, by0, bx1, by1 = X0 + fw, Y0 + th, X1 - fw, Y1 - fw
    c.path(rr(bx0, by0, bx1, by1, 0), body)
    if close and pw > 12:
        cs = th - 2 * lw if pw > 18 else th - lw
        cx1 = X1 - lw - (lw if pw > 26 else 0)
        cy0 = Y0 + (th - cs) / 2
        cl = rr(cx1 - cs, cy0, cx1, cy0 + cs, 0.25 * cs)
        c.shape(cl, c.lin(0, cy0, 0, cy0 + cs, (0, "#FF9C7A"), (0.5, "#E5482A"), (1, "#B8240F")),
                line="#FFFFFF" if pw > 26 else "#8A1A0D")
        if pw > 26:
            m = cs * 0.3
            c.line([(cx1 - cs + m, cy0 + m), (cx1 - m, cy0 + cs - m)], "#FFFFFF", w=1.2)
            c.line([(cx1 - m, cy0 + m), (cx1 - cs + m, cy0 + cs - m)], "#FFFFFF", w=1.2)
    if pw > 30:
        ty = c.sy(Y0 + th / 2 - 0.5)
        c.path(rr(X0 + 3 * lw, ty, X0 + w * 0.42, ty + lw, 0), "#FFFFFF", op=0.85)
    if content:
        with c.clipped(rr(bx0, by0, bx1, by1, 0)):
            content(c, (bx0, by0, bx1, by1))
    return (bx0, by0, bx1, by1)


# ------------------------------------------------------------------ drives

def drive_box(c, x0=3, y0=24, x1=37, y1=37, dx=8, dy=11, ramp=METAL, led=True, slot=True, label=True):
    lw, px = c.lw, c.px
    b = box3d(c, x0, y0, x1, y1, dx, dy,
              c.lin(0, y0, 0, y1, (0, ramp.light), (1, ramp.dark)),
              c.lin(x0, y0 - dy, x1 + dx, y0, (0, ramp.hi), (0.6, ramp.light), (1, ramp.base)),
              c.lin(x1, 0, x1 + dx, 0, (0, ramp.dark), (1, dk(ramp.dark, 0.2))), ramp.line)
    X0, Y0, X1, Y1, DX, DY = b["X0"], b["Y0"], b["X1"], b["Y1"], b["DX"], b["DY"]
    w = X1 - X0
    if label and px > 20:
        P = lambda u, v: (X0 + u * w + v * DX, Y0 - v * DY)  # noqa: E731
        lab = poly([P(0.08, 0.22), P(0.5, 0.22), P(0.5, 0.8), P(0.08, 0.8)])
        c.shape(lab, c.lin(*P(0.08, 0.8), *P(0.5, 0.22), (0, "#FFFFFF"), (1, "#E4E9F0")), line="#8C96A4")
        if px > 30:
            for v in (0.45, 0.62):
                c.line([P(0.14, v), P(0.42, v)], "#7FA8E8", w=1.0, cap="butt")
        for u in (0.62, 0.9):
            c.path(circ(*P(u, 0.5), max(lw * 0.7, 1.0)), ramp.dark)
    if slot:
        sy_ = c.sy((Y0 + Y1) / 2 + lw * 0.5)
        if px > 20:
            c.path(rr(c.sx(X0 + w * 0.08), sy_, c.sx(X0 + w * 0.62), sy_ + lw, 0), dk(ramp.line, 0.3), op=0.8)
            c.path(rr(c.sx(X0 + w * 0.08), sy_ + lw, c.sx(X0 + w * 0.62), sy_ + 2 * lw, 0), "#FFFFFF", op=0.6)
    if led:
        lx = c.sx(X1 - w * 0.14)
        ly = c.sy((Y0 + Y1) / 2)
        sz = lw if px <= 24 else 2 * lw
        if px <= 16:
            lx, ly = X1 - 3 * lw, c.sy((Y0 + Y1) / 2)
        c.path(rr(lx, ly, lx + sz * 1.5 if px > 24 else lx + sz, ly + sz, 0.3 * sz), "#47E23A")
        if px > 24:
            c.path(rr(lx, ly, lx + sz * 1.5, ly + sz * 0.45, 0.2), "#D8FFD0", op=0.8)
    return b


def disc(c, cx, cy, r, shadow=True):
    lw = c.lw
    hole = r * 0.16
    ring = circ(cx, cy, r) + " " + circ(cx, cy, hole)
    if shadow:
        c.drop(circ(cx, cy, r), op=0.25)
    c.path(ring, c.rad(cx - r * 0.3, cy - r * 0.3, r * 1.4, (0, "#FFFFFF"), (0.5, "#DCE1E8"), (1, "#AAB3C0")),
           rule="evenodd")
    with c.clipped(ring, rule="evenodd"):
        for a0, a1, c0, c1 in ((-75, -25, "#7AF0FF", "#F58BFF"), (105, 155, "#FFF27A", "#6BF5A0"),
                               (-160, -130, "#FFB070", "#B48CFF"), (20, 50, "#9CD0FF", "#FF9CC8")):
            pts = [(cx, cy)] + arc_pts(cx, cy, r * 1.05, a0, a1, 8)
            p0, p1 = pts[1], pts[-1]
            c.path(poly(pts), c.lin(p0[0], p0[1], p1[0], p1[1], (0, c0, 0.55), (1, c1, 0.55)))
        c.path(circ(cx, cy, r * 0.36), "#F4F6F9", op=0.85)
        c.path(circ(cx, cy, r * 0.36), "none", stroke="#9AA3AE", sw=lw * 0.8, op=0.8)
        c.path(circ(cx, cy, r * 0.24), "#E3E8EE", op=0.9)
    c.outline(ring, "#6E7784", rule="evenodd")


def floppy(c, x0=5, y0=5, x1=43, y1=43, ramp=None):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    w, h = X1 - X0, Y1 - Y0
    ch = max(2 * lw, c.sx(w * 0.1) - c.sx(0))
    body = rounded_poly([(X0, Y0), (X1 - ch, Y0), (X1, Y0 + ch), (X1, Y1), (X0, Y1)], [lw * 0.8] * 5)
    c.drop(body)
    c.shape(body, c.lin(X0, Y0, X1, Y1, (0, "#5C7CF0"), (0.5, "#2C47B8"), (1, "#1B2C86")), line="#121E5E",
            hl=c.hl_grad(X0, Y0, X0 + w * 0.6, Y0 + h * 0.6, 0.5, 0.0))
    # shutter
    sx0, sx1 = c.sx(X0 + w * 0.22), c.sx(X0 + w * 0.74)
    sy1 = c.sy(Y0 + h * 0.36)
    sh = rr(sx0, Y0, sx1, sy1, 0)
    c.shape(sh, c.lin(sx0, Y0, sx1, sy1, (0, "#FFFFFF"), (0.5, "#C7CED8"), (1, "#8E98A6")), line="#5E6774")
    wx0 = c.sx(sx0 + (sx1 - sx0) * 0.58)
    wx1 = max(wx0 + lw, c.sx(sx0 + (sx1 - sx0) * 0.82))
    c.path(rr(wx0, Y0 + (2 * lw if px <= 24 else 3), wx1, sy1 - (lw if px <= 24 else 3), 0), "#2C3442")
    # label
    lx0, lx1 = c.sx(X0 + w * 0.12), c.sx(X1 - w * 0.12)
    ly0 = c.sy(Y0 + h * 0.5)
    lab = rr(lx0, ly0, lx1, Y1, 0.5 * lw if px > 24 else 0)
    c.shape(lab, c.lin(0, ly0, 0, Y1, (0, "#FFFFFF"), (1, "#E2E7EE")), line="#8A96A8")
    if px > 20:
        text_lines(c, lx0 + 2 * lw, ly0 + 3 * lw if px > 30 else ly0 + 2 * lw, lx1 - 2 * lw, Y1 - 2 * lw,
                   col="#8FA9D8", widths=(1, 0.7, 0.85))
    if px > 24:
        c.path(rr(c.sx(X0 + w * 0.04), c.sy(Y1 - h * 0.1), c.sx(X0 + w * 0.04) + 2 * lw, c.sy(Y1 - h * 0.1) + 2 * lw,
                  0), "#0E1648")


# ----------------------------------------------------------------- misc

def tile(c, ramp, x0, y0, x1, y1, r=5, border="#FFFFFF"):
    """Glossy rounded square button (XP caption-button style)."""
    lw = c.lw
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    p = rr(X0, Y0, X1, Y1, r)
    c.drop(p)
    c.shape(p, c.rad((X0 + X1) / 2, Y1, (Y1 - Y0) * 1.1, (0, ramp.light), (0.5, ramp.base), (1, ramp.dark), sx=1.2),
            line=ramp.line)
    if border and c.px > 16:
        inner = rr(X0 + lw, Y0 + lw, X1 - lw, Y1 - lw, max(0.0, r - lw))
        c.outline(inner, border, w=1.0 if c.px <= 32 else 1.4)
    with c.clipped(p):
        c.path(ell((X0 + X1) / 2, Y0 + (Y1 - Y0) * 0.12, (X1 - X0) * 0.55, (Y1 - Y0) * 0.36),
               c.lin(0, Y0, 0, Y0 + (Y1 - Y0) * 0.48, (0, "#FFFFFF", 0.75), (1, "#FFFFFF", 0.05)))
    return X0, Y0, X1, Y1


def speaker_shape(cx=0, cy=0, s=1.0):
    """Tray speaker silhouette in a 48 box centred at (cx, cy) with scale s."""
    pts = [(-17, -6), (-9, -6), (2, -16), (4, -16), (4, 16), (2, 16), (-9, 6), (-17, 6)]
    return [(cx + x * s, cy + y * s) for x, y in pts]


def speaker(c, x=16, y=24, s=1.0):
    lw = c.lw
    pts = speaker_shape(x, y, s)
    dd = rounded_poly(pts, [1.2 * s, 0.5, 1.2 * s, 1.2 * s, 1.2 * s, 1.2 * s, 0.5, 1.2 * s])
    c.drop(dd)
    c.shape(dd, c.lin(x - 17 * s, y - 16 * s, x + 4 * s, y + 16 * s, (0, "#FFFFFF"), (0.55, "#DCE2EA"),
                      (1, "#9AA5B4")), line="#39414E")
    if c.px * s > 20:
        c.path(rr(x - 9 * s - lw, y - 6 * s + lw, x - 9 * s, y + 6 * s - lw, 0), "#39414E", op=0.5)


def waves(c, cx, cy, n, s=1.0, col=("#F0FAFF", "#62BEFF"), line="#0E3A8A", r0=None, gap=None):
    lw = c.lw
    w = max(lw * 1.6, 3.2 * s) if c.px > 16 else 2 * lw
    r0 = r0 if r0 is not None else 8 * s
    gap = gap if gap is not None else 7.5 * s
    for i in range(n):
        R = r0 + i * gap
        a = 48 - i * 4
        pts = arc_pts(cx, cy, R, -a, a, 16)
        dd = poly(pts, close=False)
        c.path(dd, "none", stroke=line, sw=w + 2 * lw * (0.8 if c.px > 16 else 0.6), cap="round")
        c.path(dd, "none", stroke=c.lin(0, cy - R, 0, cy + R, (0, col[0]), (1, col[1])), sw=w, cap="round")


def battery(c, level=1.0, ramp=GREEN, x0=3, y0=13, x1=40, y1=35):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    nub = rr(X1 - lw, c.sy(Y0 + (Y1 - Y0) * 0.28), c.sx(X1 + max(2 * lw, 4)), c.sy(Y1 - (Y1 - Y0) * 0.28), 0.6 * lw)
    body = rr(X0, Y0, X1, Y1, min(3, 1.2 * lw))
    c.drop(body)
    c.shape(nub, c.lin(0, Y0, 0, Y1, (0, "#F4F6F8"), (1, "#8F98A5")), line="#3E4652")
    c.shape(body, c.lin(0, Y0, 0, Y1, (0, "#FFFFFF"), (0.5, "#D9DEE5"), (1, "#A9B2BF")), line="#3E4652")
    m = 2 * lw if px <= 24 else 3
    ix0, iy0, ix1, iy1 = X0 + m, Y0 + m, X1 - m, Y1 - m
    c.path(rr(ix0, iy0, ix1, iy1, 0), "#4A5260", op=0.35)
    lx1 = c.sx(ix0 + (ix1 - ix0) * level)
    if lx1 - ix0 < lw:
        lx1 = ix0 + lw
    lev = rr(ix0, iy0, lx1, iy1, 0)
    c.path(lev, c.lin(0, iy0, 0, iy1, (0, ramp.light), (0.5, ramp.base), (1, ramp.dark)))
    c.path(rr(ix0, iy0, lx1, iy0 + (iy1 - iy0) * 0.4, 0), "#FFFFFF", op=0.35)
    with c.clipped(body):
        c.path(rr(X0, Y0, X1, Y0 + (Y1 - Y0) * 0.35, 0), "#FFFFFF", op=0.25)


def recycle(c, cx, cy, r, ramp=GREEN):
    lw = c.lw
    w = max(r * 0.42, 1.4 * lw)
    for a in (-90, 30, 150):
        pts = curved_arrow(cx, cy, r, w, a - 40, a + 22, w * 2.0, 34, n=10)
        c.oshape(poly(pts), c.lin(cx - r, cy - r, cx + r, cy + r, (0, ramp.light), (1, ramp.dark)),
                 ramp.line, w=0.8)


def trash_bin(c, full=False):
    lw, px = c.lw, c.px
    cx = 23
    top_y, bot_y = (c.sy(13), c.sy(44)) if full else (c.sy(11), c.sy(43))
    if full and px <= 16:
        top_y, bot_y = c.sy(17), c.sy(45)
    rx_t, ry_t = 16, 4.5 if px > 16 else 3
    rx_b, ry_b = 11.5, 2.5 if px > 16 else 1.5
    if px <= 16:
        rx_t = c.sx(cx + 15) - cx
        rx_b = c.sx(cx + 11) - cx
    body = d("M", cx - rx_t, top_y, "L", cx - rx_b, bot_y - ry_b, "A", rx_b, ry_b, 0, 0, 0, cx + rx_b, bot_y - ry_b,
             "L", cx + rx_t, top_y, "A", rx_t, ry_t, 0, 0, 1, cx - rx_t, top_y, "Z")
    c.drop(body)
    # inside (back wall)
    opening = ell(cx, top_y, rx_t, ry_t)
    c.path(opening, c.lin(0, top_y - ry_t, 0, top_y + ry_t, (0, "#5F7B98"), (1, "#9DB4CB")))
    rim_w = 1.6 if px > 24 else lw
    rim_o = rim_w + 2 * lw if px > 16 else rim_w + lw
    back_rim = d("M", cx - rx_t, top_y, "A", rx_t, ry_t, 0, 0, 1, cx + rx_t, top_y)
    front_rim = d("M", cx - rx_t, top_y, "A", rx_t, ry_t, 0, 0, 0, cx + rx_t, top_y)
    rim_grad = c.lin(0, top_y - ry_t, 0, top_y + ry_t, (0, "#FFFFFF"), (1, "#C4D4E4"))
    c.path(back_rim, "none", stroke="#4E6683", sw=rim_o)
    c.path(back_rim, "none", stroke=rim_grad, sw=rim_w)
    if full:
        if px <= 16:
            crumple = [[(-14, 2), (-13, -7), (-6, -13), (0, -10), (5, -14), (11, -11), (14, -5), (14, 2)]]
        elif px <= 24:
            crumple = [[(-14, 2), (-13, -5), (-7, -10), (-1, -7), (4, -11), (10, -8), (14, -4), (14, 2)]]
        else:
            crumple = [
                [(-12, 2), (-14, -5), (-9, -9), (-3, -8), (-1, -3), (-4, 3)],
                [(-3, 2), (-4, -7), (2, -11), (8, -10), (10, -4), (7, 2)],
                [(5, 2), (6, -5), (11, -8), (15, -4), (14, 2)],
            ]
        for i, b in enumerate(crumple):
            pts = [(cx + x, top_y + y) for x, y in b]
            p = rounded_poly(pts, 2.0)
            c.shape(p, c.lin(cx - 10, top_y - 12, cx + 10, top_y + 2, (0, "#FFFFFF"), (1, "#D5DDE7")),
                    line="#7D8899")
            if px > 24:
                mid = pts[len(pts) // 2]
                c.line([pts[1], ((mid[0] + pts[1][0]) / 2 + 1, (mid[1] + pts[1][1]) / 2 + 2)], "#B6C0CE", w=0.8)
        # paper visible through the mesh
        c.path(rr(cx - 10, top_y + 3, cx + 8, top_y + 18, 3), "#FFFFFF", op=0.65)
    front = d("M", cx - rx_t, top_y, "L", cx - rx_b, bot_y - ry_b, "A", rx_b, ry_b, 0, 0, 0, cx + rx_b,
              bot_y - ry_b, "L", cx + rx_t, top_y, "A", rx_t, ry_t, 0, 0, 0, cx - rx_t, top_y, "Z")
    c.path(front, c.lin(cx - rx_t, 0, cx + rx_t, 0, (0, "#DCEBF7", 0.92), (0.35, "#C2D7EA", 0.88),
                        (1, "#7E9AB8", 0.95)))
    with c.clipped(front):
        if px > 16:
            n = 9 if px > 24 else 6
            for i in range(1, n):
                t = i / n
                xt = cx - rx_t + 2 * rx_t * t
                xb = cx - rx_b + 2 * rx_b * t
                c.line([(xt, top_y), (xb, bot_y)], "#FFFFFF", w=1.0, op=0.5)
                c.line([(xt + lw, top_y), (xb + lw, bot_y)], "#6D88A6", w=0.8, op=0.35)
        c.path(rr(cx - rx_t, top_y, cx - rx_t + 2 * rx_t * 0.3, bot_y, 0),
               c.lin(cx - rx_t, 0, cx - rx_t + 2 * rx_t * 0.3, 0, (0, "#FFFFFF", 0.0), (1, "#FFFFFF", 0.35)))
    c.outline(body, "#4E6683")
    # front half of the rim
    c.path(front_rim, "none", stroke="#4E6683", sw=rim_o, cap="round")
    c.path(front_rim, "none", stroke=rim_grad, sw=rim_w, cap="round")
    # recycle mark
    if px > 16:
        recycle(c, cx, c.sy(29), 6.5 if px > 24 else 7.5)
    else:
        c.path(circ(cx, 29, 6), "none", stroke=GREEN.base, sw=2 * lw)


def cardboard(c, x0=5, y0=21, x1=33, y1=43, dx=10, dy=9, label=True):
    lw, px = c.lw, c.px
    b = box3d(c, x0, y0, x1, y1, dx, dy,
              c.lin(x0, y0, x1, y1, (0, BROWN.light), (1, BROWN.base)),
              c.lin(x0, y0 - dy, x1 + dx, y0, (0, lt(BROWN.light, 0.3)), (1, BROWN.light)),
              c.lin(x1, 0, x1 + dx, 0, (0, BROWN.dark), (1, dk(BROWN.dark, 0.15))), BROWN.line)
    X0, Y0, X1, Y1, DX, DY = b["X0"], b["Y0"], b["X1"], b["Y1"], b["DX"], b["DY"]
    # tape across the top and down the front
    tw = max(lw, (X1 - X0) * 0.18)
    mx = (X0 + X1) / 2
    tape = poly([(mx - tw / 2, Y0), (mx - tw / 2 + DX, Y0 - DY), (mx + tw / 2 + DX, Y0 - DY), (mx + tw / 2, Y0)])
    c.path(tape, "#F7E6C4", op=0.9)
    c.path(rr(c.sx(mx - tw / 2), Y0, c.sx(mx + tw / 2), c.sy(Y0 + (Y1 - Y0) * 0.35), 0), "#F7E6C4", op=0.9)
    if label and px > 20:
        lx0, ly0 = c.sx(X0 + (X1 - X0) * 0.12), c.sy(Y0 + (Y1 - Y0) * 0.55)
        lab = rr(lx0, ly0, c.sx(X0 + (X1 - X0) * 0.55), c.sy(Y1 - (Y1 - Y0) * 0.12), 0)
        c.shape(lab, "#FFFFFF", line="#9A7A4A")
    c.outline(b["sil"], BROWN.line)
    return b


def clock(c, cx, cy, r, ramp=BLUE, hands=(300, 60)):
    lw, px = c.lw, c.px
    c.drop(circ(cx, cy, r))
    c.shape(circ(cx, cy, r), c.lin(cx - r, cy - r, cx + r, cy + r, (0, ramp.light), (0.5, ramp.base),
                                   (1, ramp.dark)), line=ramp.line)
    fr = r * (0.8 if px * r / 24 > 8 else 0.72)
    c.shape(circ(cx, cy, fr), c.rad(cx - fr * 0.3, cy - fr * 0.3, fr * 1.4, (0, "#FFFFFF"), (0.7, "#F2F4F7"),
                                    (1, "#C8D0DA")), line=dk(ramp.line, 0.1))
    if px * r / 24 > 10:
        for i in range(12):
            a = math.radians(i * 30)
            l0 = fr * (0.78 if i % 3 else 0.68)
            c.line([(cx + math.cos(a) * l0, cy + math.sin(a) * l0),
                    (cx + math.cos(a) * fr * 0.9, cy + math.sin(a) * fr * 0.9)], "#4A5568",
                   w=0.8 if i % 3 else 1.2, cap="butt")
    ha, ma = hands
    for ang, ln, wd in ((ha, 0.5, 1.6), (ma, 0.75, 1.2)):
        a = math.radians(ang - 90)
        c.line([(cx, cy), (cx + math.cos(a) * fr * ln, cy + math.sin(a) * fr * ln)], "#1E2A3C",
               w=wd if px * r / 24 > 10 else 1.0)
    if px * r / 24 > 12:
        a = math.radians(200 - 90)
        c.line([(cx - math.cos(a) * fr * 0.15, cy - math.sin(a) * fr * 0.15),
                (cx + math.cos(a) * fr * 0.8, cy + math.sin(a) * fr * 0.8)], "#E5302A", w=0.7)
        c.path(circ(cx, cy, max(lw, fr * 0.08)), "#1E2A3C")


def envelope(c, x0=4, y0=12, x1=44, y1=38, stamp=False):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    w, h = X1 - X0, Y1 - Y0
    body = rr(X0, Y0, X1, Y1, min(1.5, lw))
    c.drop(body)
    c.shape(body, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (0.6, "#F3EFE3"), (1, "#DCD4BC")), line="#857B5E")
    cx = (X0 + X1) / 2
    with c.clipped(body):
        c.path(poly([(X0, Y1), (cx, Y0 + h * 0.48), (X1, Y1)]), "none", stroke="#B9AF92", sw=lw)
        flap = poly([(X0, Y0), (cx, Y0 + h * 0.62), (X1, Y0)])
        c.path(flap, c.lin(0, Y0, 0, Y0 + h * 0.62, (0, "#FFFFFF"), (1, "#E8E2CF")))
        c.path(flap, "none", stroke="#857B5E", sw=1.4 * lw, join="round")
    if stamp and px <= 20:
        sx0, sy0 = c.sx(X1 - 4 * lw), c.sy(Y0 + 1 * lw)
        c.path(rr(sx0, sy0, sx0 + 2 * lw, sy0 + 2 * lw, 0), "#D9381E")
    elif stamp:
        sx0, sy0 = c.sx(X1 - w * 0.24), c.sy(Y0 + h * 0.1)
        st = rr(sx0, sy0, c.sx(X1 - w * 0.06), c.sy(Y0 + h * 0.42), 0)
        c.shape(st, c.lin(sx0, sy0, X1, Y0 + h * 0.4, (0, "#FF8F6E"), (1, "#C8321C")), line="#FFFFFF")


def printer(c, paper_lines=True):
    lw, px = c.lw, c.px
    # paper standing at the back
    pX0, pX1 = c.sx(14), c.sx(34)
    pY0 = c.sy(4)
    if px <= 16:
        pX0, pX1, pY0 = c.sx(15), c.sx(33), c.sy(6)
    back_paper = poly([(pX0, c.sy(22)), (pX0 + 3, pY0), (pX1 + 3, pY0), (pX1, c.sy(22))])
    if px <= 16:
        back_paper = rr(pX0, pY0, pX1, c.sy(22), 0)
    c.drop(back_paper)
    c.shape(back_paper, c.lin(0, pY0, 0, 22, (0, "#FFFFFF"), (1, "#DCE3EC")), line=PAPER_LINE)
    if px > 24 and paper_lines:
        for i in range(3):
            y = 9 + i * 3.5
            c.line([(pX0 + 3 + 3 * (1 - (y - pY0) / 18), y), (pX1 - 2, y)], "#A9B6C9", w=1.2, cap="butt")
    b = box3d(c, 3, 26, 39, 39, 6, 7,
              c.lin(0, 26, 0, 39, (0, "#F3F1EC"), (1, "#B9B4A6")),
              c.lin(3, 19, 45, 26, (0, "#FFFFFF"), (1, "#DEDAD0")),
              c.lin(39, 0, 45, 0, (0, "#A9A497"), (1, "#8A8577")), "#6E6858")
    X0, Y0, X1, Y1, DX, DY = b["X0"], b["Y0"], b["X1"], b["Y1"], b["DX"], b["DY"]
    # output slot on the front and paper coming out
    sy_ = c.sy(Y0 + (Y1 - Y0) * 0.35)
    sx0, sx1 = c.sx(X0 + (X1 - X0) * 0.18), c.sx(X1 - (X1 - X0) * 0.18)
    c.path(rr(sx0, sy_, sx1, sy_ + lw, 0), "#3E3A30", op=0.9)
    out = poly([(sx0 + lw, sy_ + lw), (sx1 - lw, sy_ + lw), (sx1 + lw, c.sy(44)), (sx0 - lw, c.sy(44))])
    if px <= 16:
        out = rr(sx0 + lw, sy_ + lw, sx1 - lw, c.sy(45), 0)
    c.shape(out, c.lin(0, sy_, 0, 44, (0, "#E7ECF2"), (1, "#FFFFFF")), line=PAPER_LINE)
    if px > 24:
        for i in range(2):
            y = sy_ + 4 + i * 3
            c.line([(sx0 + 3, y), (sx1 - 4 - i * 4, y)], "#A9B6C9", w=1.0, cap="butt")
    # led + button
    lx = c.sx(X1 - (X1 - X0) * 0.09)
    ly = c.sy(Y0 + (Y1 - Y0) * 0.3)
    if px > 16:
        c.path(rr(lx - lw, ly, lx + (lw if px <= 24 else 1.5 * lw), ly + lw, 0), "#3BD12A")


def calculator(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(9, 3, 39, 45)
    body = rr(X0, Y0, X1, Y1, 3 if px > 24 else lw)
    c.drop(body)
    c.shape(body, c.lin(X0, Y0, X1, Y1, (0, "#F1F3F6"), (0.5, "#C9CFD8"), (1, "#8E97A5")), line="#4C5463",
            hl=c.hl_grad(X0, Y0, X1, Y1, 0.9, 0.0))
    m = (2 if px <= 24 else 3) * lw if px <= 32 else 4
    lx0, ly0, lx1 = X0 + m, Y0 + m, X1 - m
    ly1 = c.sy(Y0 + (Y1 - Y0) * 0.27)
    lcd = rr(lx0, ly0, lx1, ly1, 0)
    c.shape(lcd, c.lin(0, ly0, 0, ly1, (0, "#D9E8C4"), (1, "#9FB98A")), line="#4E5A44")
    if px > 20:
        dy0, dy1 = ly0 + 2 * lw, ly1 - 2 * lw
        x = lx1 - 2 * lw
        for i in range(3):
            c.path(rr(x - 2.6 * lw if px <= 24 else x - 4, dy0, x, dy1, 0), "#2F3A26", op=0.8)
            x -= (4 * lw if px <= 24 else 6)
    cols, rows = 4, 4
    kx0, kx1, ky0, ky1 = lx0, lx1, ly1 + (lw if px <= 16 else 2 * lw), Y1 - m
    gx = (kx1 - kx0 + (lw if px <= 24 else 1.5)) / cols
    gy = (ky1 - ky0 + (lw if px <= 24 else 1.5)) / rows
    for r_ in range(rows):
        for q in range(cols):
            a0, b0 = c.sx(kx0 + q * gx), c.sy(ky0 + r_ * gy)
            a1, b1 = c.sx(kx0 + (q + 1) * gx) - (lw if px <= 24 else 1.5), c.sy(ky0 + (r_ + 1) * gy) - (lw if px <= 24 else 1.5)
            if a1 - a0 < lw:
                a1 = a0 + lw
            if b1 - b0 < lw:
                b1 = b0 + lw
            if q == 3:
                col = ("#FF9E80", "#D9431F") if r_ == 0 else ("#9CC8FF", "#2F6FD6")
            else:
                col = ("#FFFFFF", "#C7CDD6")
            k = rr(a0, b0, a1, b1, 0.4 * lw if px > 24 else 0)
            if px <= 16:
                c.path(k, col[1] if q == 3 else "#FFFFFF")
            else:
                c.shape(k, c.lin(0, b0, 0, b1, (0, col[0]), (1, col[1])), line=dk(col[1], 0.35))


def keyboard(c, x0=2, y0=22, x1=40, y1=36, skew=6):
    lw, px = c.lw, c.px
    X0, X1 = c.sx(x0), c.sx(x1)
    Yt, Yb = c.sy(y0), c.sy(y1)
    S = c.sx(skew) - c.sx(0)
    fh = (lw if px <= 24 else 3)
    top = poly([(X0, Yb), (X0 + S, Yt), (X1 + S, Yt), (X1, Yb)])
    front = poly([(X0, Yb), (X1, Yb), (X1, Yb + fh), (X0, Yb + fh)])
    side = poly([(X1, Yb), (X1 + S, Yt), (X1 + S, Yt + fh), (X1, Yb + fh)])
    sil = poly([(X0, Yb + fh), (X0, Yb), (X0 + S, Yt), (X1 + S, Yt), (X1 + S, Yt + fh), (X1, Yb + fh)])
    c.drop(sil)
    c.path(front, c.lin(0, Yb, 0, Yb + fh, (0, BEIGE.base), (1, BEIGE.dark)))
    c.path(side, BEIGE.dark)
    c.path(top, c.lin(X0, Yt, X1, Yb, (0, BEIGE.hi), (1, BEIGE.base)))
    c.outline(sil, BEIGE.line)
    m = 2 * lw if px <= 24 else 2.5
    rows = 4 if px > 24 else max(2, int((Yb - Yt - 2 * m) / (2 * lw)) + 1)
    inner_t, inner_b = Yt + m, Yb - m
    rh = (inner_b - inner_t) / rows
    for r_ in range(rows):
        ya, yb = inner_t + r_ * rh, inner_t + (r_ + 1) * rh - (lw if px <= 24 else 0.9)
        if px <= 24:
            ya = inner_t + r_ * 2 * lw
            yb = ya + lw
        ta = 1 - (ya - Yt) / (Yb - Yt)
        tb = 1 - (yb - Yt) / (Yb - Yt)
        xa0, xb0 = X0 + S * ta + m, X0 + S * tb + m
        xa1, xb1 = X1 + S * ta - m - (4 if r_ == 0 and px > 24 else 0), X1 + S * tb - m - (4 if r_ == 0 and px > 24 else 0)
        if px <= 24:
            n = int((xa1 - xa0) / (2 * lw))
            for k in range(n):
                kx = c.sx(xa0 + k * 2 * lw)
                c.path(rr(kx, c.sy(ya), kx + lw, c.sy(ya) + lw, 0), "#7A6E52", op=0.8)
            continue
        nk = 10 - (1 if r_ % 2 else 0)
        kw = (xa1 - xa0) / nk
        for k in range(nk):
            if r_ == rows - 1 and 2 < k < nk - 3:
                if k == 3:
                    a0, a1 = xa0 + 3 * kw, xa0 + (nk - 3) * kw - 0.8
                    b0, b1 = xb0 + 3 * kw, xb0 + (nk - 3) * kw - 0.8
                else:
                    continue
            else:
                a0, a1 = xa0 + k * kw, xa0 + (k + 1) * kw - 0.8
                b0, b1 = xb0 + k * kw, xb0 + (k + 1) * kw - 0.8
            key = poly([(b0, yb), (a0, ya), (a1, ya), (b1, yb)])
            c.path(key, c.lin(0, ya, 0, yb, (0, "#FFFFFF"), (1, "#DCD3BC")), stroke="#9C9073", sw=0.6, join="round")
