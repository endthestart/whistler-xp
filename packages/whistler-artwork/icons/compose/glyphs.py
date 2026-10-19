"""Reusable Whistler glyphs. Each draws into the current 48x48 box of a Ctx."""
import math

from lib import (BLUE, FOLDER, GREEN, PAPER_LINE, TEXT_LINE, YELLOW, arc_pts, circ, d, dk, ell, mix, poly,
                 rot, rr)


def rounded_poly(pts, r):
    """Closed polygon with corners rounded by quadratic curves."""
    n = len(pts)
    rs = r if isinstance(r, (list, tuple)) else [r] * n
    segs = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        l1 = math.hypot(p0[0] - p1[0], p0[1] - p1[1])
        l2 = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        rr_ = min(rs[i], l1 / 2, l2 / 2)
        a = (p1[0] + (p0[0] - p1[0]) / l1 * rr_, p1[1] + (p0[1] - p1[1]) / l1 * rr_)
        b = (p1[0] + (p2[0] - p1[0]) / l2 * rr_, p1[1] + (p2[1] - p1[1]) / l2 * rr_)
        segs.append((a, p1, b))
    out = ["M", segs[0][2][0], segs[0][2][1]]
    for i in range(1, n + 1):
        a, p, b = segs[i % n]
        out += ["L", a[0], a[1], "Q", p[0], p[1], b[0], b[1]]
    out.append("Z")
    return d(*out)


# ------------------------------------------------------------------ folder

FOLDER_BACK = ("#F9DA78", "#F0C14F", "#DE9F2B")
FOLDER_FRONT = ("#FFF4C2", "#FCDF84", "#F0B940")


def folder_shapes(c, open_=False):
    lw, px = c.lw, c.px
    x0, x1 = c.sx(3), c.sx(41)
    ytab, yt = c.sy(6), c.sy(10)
    yb = c.sy(41)
    tabx = c.sx(16)
    r = min(2.0, lw * 0.9)
    if open_:
        yf, lean = c.sy(21), c.sx(8) - c.sx(0)
    else:
        yf, lean = c.sy(16), c.sx(3) - c.sx(0)
    if px <= 16:
        yf = c.sy(18 if not open_ else 21)
        lean = lw if not open_ else 2 * lw
    back = d("M", x0, ytab + r, "A", r, r, 0, 0, 1, x0 + r, ytab, "H", tabx, "L", tabx + (yt - ytab), yt,
             "H", x1 - r, "A", r, r, 0, 0, 1, x1, yt + r, "V", yb, "H", x0, "Z")
    fr = d("M", x0 + lean + r * 0.5, yf, "H", x1 + lean - r, "Q", x1 + lean, yf, x1 + lean - 0.1, yf + r,
           "L", x1 + 0.1, yb - r, "Q", x1, yb, x1 - r, yb, "H", x0, "Z")
    return dict(x0=x0, x1=x1, ytab=ytab, yt=yt, yb=yb, yf=yf, lean=lean, back=back, front=fr)


def folder(c, open_=False, emblem=None, paper=None, emblem_box=None):
    """XP-style manila folder. emblem(c) is drawn on the front flap."""
    lw, px = c.lw, c.px
    g = folder_shapes(c, open_)
    x0, x1, ytab, yt, yb, yf = g["x0"], g["x1"], g["ytab"], g["yt"], g["yb"], g["yf"]
    c.drop(g["back"])
    c.drop(g["front"])
    c.shape(g["back"], c.lin(0, ytab, 0, yb, (0, FOLDER_BACK[0]), (0.45, FOLDER_BACK[1]), (1, FOLDER_BACK[2])),
            line=FOLDER.line, hl=c.hl_grad(0, ytab, 0, yt + 6, 0.8, 0.0))
    if open_:
        c.path(poly([(x0 + lw, yt + 2 * lw), (x1 - lw, yt + 2 * lw), (x1 - lw, yb), (x0 + lw, yb)]),
               c.lin(0, yt, 0, yf, (0, "#C98A1C", 0.0), (1, "#B87710", 0.5)))
    if paper is None:
        paper = open_
    if paper and px > 16:
        pg = poly(rot([(x0 + 5, yt + 2), (x1 - 7, yt + 2), (x1 - 7, yb), (x0 + 5, yb)], 23, 25, -3))
        c.shape(pg, c.lin(0, yt, 0, yf, (0, "#FFFFFF"), (1, "#E9EEF4")), line=PAPER_LINE)
        pg2 = poly(rot([(x0 + 8, yt + 4), (x1 - 3, yt + 4), (x1 - 3, yb), (x0 + 8, yb)], 25, 25, 4))
        c.shape(pg2, c.lin(0, yt, 0, yf, (0, "#FFFFFF"), (1, "#EEF2F7")), line=PAPER_LINE)
    elif paper:
        pg = poly([(x0 + 2 * lw, yt + lw), (x1 - 2 * lw, yt + lw), (x1 - 2 * lw, yb), (x0 + 2 * lw, yb)])
        c.shape(pg, "#FFFFFF", line=PAPER_LINE)
    ff = c.lin(x0, yf, x1, yb, (0, FOLDER_FRONT[0]), (0.45, FOLDER_FRONT[1]), (1, FOLDER_FRONT[2]))
    c.shape(g["front"], ff, line=FOLDER.line,
            hl=c.lin(0, yf, 0, yf + 4 * lw, (0, "#FFFFFF", 0.95), (1, "#FFFFFF", 0.0)))
    if px > 24:
        c.path(poly([(x0 + 2, yb - 3), (x1 - 2, yb - 3)], close=False), "none", stroke="#FFFFFF",
               sw=lw, sop=0.35)
    if emblem is not None:
        if emblem_box:
            ex, ey, sz = emblem_box
        elif px <= 16:
            ex, ey, sz = c.sx(17), c.sy(15), 33
        elif px <= 24:
            ex, ey, sz = c.sx(16), c.sy(13), 32
        else:
            ex, ey, sz = 15, 12, 31
        with c.place(ex, ey, sz):
            emblem(c)
    return g


# -------------------------------------------------------------------- page

def page_geom(c, x0=8, x1=38, y0=3, y1=45):
    X0, X1, Y0, Y1 = c.sx(x0), c.sx(x1), c.sy(y0), c.sy(y1)
    wpx = (X1 - X0) / c.lw
    fold = max(2, round(wpx * 0.38)) * c.lw
    return X0, Y0, X1, Y1, fold


def page(c, x0=8, x1=38, y0=3, y1=45, tint=None, shadow=True, line=PAPER_LINE):
    """White document with a dog-ear. Returns (x0, y0, x1, y1, fold)."""
    X0, Y0, X1, Y1, fold = page_geom(c, x0, x1, y0, y1)
    body = poly([(X0, Y0), (X1 - fold, Y0), (X1, Y0 + fold), (X1, Y1), (X0, Y1)])
    if shadow:
        c.drop(body)
    top = tint or "#FFFFFF"
    c.shape(body, c.lin(X0, Y0, X1, Y1, (0, top), (0.55, mix(top, "#F2F5F9", 0.6)), (1, "#DCE3EC")),
            line=line)
    ear = poly([(X1 - fold, Y0), (X1 - fold, Y0 + fold), (X1, Y0 + fold)])
    c.shape(ear, c.lin(X1 - fold, Y0 + fold, X1 - fold * 0.5, Y0 + fold * 0.5,
                       (0, "#C4CFDD"), (1, "#FFFFFF")), line=line)
    return X0, Y0, X1, Y1, fold


def text_lines(c, x0, y0, x1, y1, col=TEXT_LINE, gap=None, widths=(1, 0.85, 0.95, 0.7, 1, 0.9, 0.6),
               thick=None):
    lw = c.lw
    if gap is None:
        gap = (2 if c.px <= 24 else 3 if c.px <= 32 else 4) * lw
    if thick is None:
        thick = lw if c.px <= 32 else 2 * lw
    y = c.sy(y0)
    i = 0
    while y + thick <= y1 + 0.01:
        w = widths[i % len(widths)]
        xe = max(c.sx(x0) + lw, c.sx(x0 + (x1 - x0) * w))
        c.path(rr(c.sx(x0), y, xe, y + thick, 0), col)
        y += gap
        i += 1


def page_with(c, emblem, lines=True, box=None, tint=None):
    """Document page with an emblem in its lower part."""
    X0, Y0, X1, Y1, fold = page(c, tint=tint)
    lw, px = c.lw, c.px
    if lines:
        if px <= 16:
            text_lines(c, X0 + 2 * lw, Y0 + 2 * lw, X1 - fold - lw, Y0 + 3 * lw, widths=(1,))
        else:
            text_lines(c, X0 + 4, Y0 + 5, X1 - fold - 3, Y0 + 12, widths=(1, 0.8))
    if box is None:
        if px <= 16:
            box = (c.sx(9), c.sy(15), 33)
        elif px <= 24:
            box = (c.sx(8), c.sy(15), 30)
        else:
            box = (8, 15, 30)
    with c.place(*box):
        emblem(c)


# --------------------------------------------------------------------- orb

def orb(c, ramp, cx=23, cy=23, r=19, shadow=True):
    """Glossy XP button ball."""
    if shadow:
        c.drop(circ(cx, cy, r), op=0.25)
    body = c.rad(cx - 0.1 * r, cy + 0.45 * r, 1.35 * r, (0, ramp.light), (0.45, ramp.base), (1, ramp.dark))
    c.shape(circ(cx, cy, r), body, line=ramp.line)
    hl = c.lin(0, cy - r, 0, cy + 0.05 * r, (0, "#FFFFFF", 0.92 if c.px > 16 else 0.7), (1, "#FFFFFF", 0.05))
    c.path(ell(cx, cy - 0.43 * r, 0.74 * r, 0.5 * r), hl)


def arrow_poly(cx, cy, length, shaft, head_w, head_len, deg=0):
    """Right-pointing block arrow centred on (cx, cy), rotated by deg."""
    x0, x1 = cx - length / 2, cx + length / 2
    xh = x1 - head_len
    pts = [(x0, cy - shaft / 2), (xh, cy - shaft / 2), (xh, cy - head_w / 2), (x1, cy),
           (xh, cy + head_w / 2), (xh, cy + shaft / 2), (x0, cy + shaft / 2)]
    return rot(pts, cx, cy, deg)


def white_mark(c, dd, ramp, w=None):
    """White symbol on a coloured ball, with a soft coloured edge."""
    px = c.px
    fill = c.lin(0, 10, 0, 36, (0, "#FFFFFF"), (1, mix("#FFFFFF", ramp.light, 0.25)))
    if px <= 16:
        c.oshape(dd, fill, ramp.dark, w=w or 0.7)
        return
    c.oshape(dd, fill, dk(ramp.line, 0.1), w=w or (1.0 if px > 24 else 0.8))


def x_mark(c, ramp, cx=23, cy=23, L=12, t=3.6):
    """White X on a coloured ball or tile."""
    if c.px <= 16:
        Ls, w = 7.6, 5.4
        for a, b in (((cx - Ls, cy - Ls), (cx + Ls, cy + Ls)), ((cx + Ls, cy - Ls), (cx - Ls, cy + Ls))):
            c.path(poly([a, b], close=False), "none", stroke="#FFFFFF", sw=w, cap="round")
        return
    white_mark(c, rounded_poly(x_poly(cx, cy, L, t), 0.8), ramp)


def orb_arrow(c, ramp, deg, cx=23, cy=23):
    orb(c, ramp, cx, cy)
    px = c.px
    if px <= 16:
        pts = arrow_poly(cx, cy, 27, 9, 22, 12, deg)
    elif px <= 24:
        pts = arrow_poly(cx, cy, 26, 8, 21, 11, deg)
    else:
        pts = arrow_poly(cx, cy, 24, 7.5, 20, 11, deg)
    white_mark(c, rounded_poly(pts, 0.8), ramp)


# --------------------------------------------------------------- symbols

def sym_i(c, cx=23, cy=23, s=1.0, col="#FFFFFF", line=None):
    px = c.px
    if px <= 16:
        dot = rr(c.sx(cx - 3.5 * s), c.sy(cy - 13 * s), c.sx(cx + 3.5 * s), c.sy(cy - 7 * s), 1.5)
        stem = rr(c.sx(cx - 3.5 * s), c.sy(cy - 4 * s), c.sx(cx + 3.5 * s), c.sy(cy + 12 * s), 0.8)
    else:
        dot = circ(cx, cy - 10 * s, 3.3 * s)
        stem = rr(cx - 3.1 * s, cy - 4.5 * s, cx + 3.1 * s, cy + 12 * s, 1.4 * s)
    for p in (dot, stem):
        if line:
            c.oshape(p, col, line, w=0.8)
        else:
            c.path(p, col)


def sym_q(c, cx=23, cy=23, s=1.0, col="#FFFFFF", line=None):
    w = 5.6 * s if c.px > 16 else 6.5 * s
    p = d("M", cx - 6.8 * s, cy - 6 * s, "C", cx - 6.8 * s, cy - 15 * s, cx + 7 * s, cy - 15 * s,
          cx + 7 * s, cy - 6.8 * s, "C", cx + 7 * s, cy - 1.5 * s, cx, cy - 1.5 * s, cx, cy + 4.5 * s)
    if line:
        c.path(p, "none", stroke=line, sw=w + 1.6 * c.lw, cap="round", join="round")
        c.path(circ(cx, cy + 11.5 * s, 3.4 * s + 0.8 * c.lw), line)
    c.path(p, "none", stroke=col, sw=w, cap="round", join="round")
    c.path(circ(cx, cy + 11.5 * s, 3.4 * s), col)


def sym_excl(c, cx=24, cy=24, s=1.0, col="#FFFFFF"):
    bar = rounded_poly([(cx - 3.4 * s, cy - 13 * s), (cx + 3.4 * s, cy - 13 * s), (cx + 2.2 * s, cy + 5 * s),
                        (cx - 2.2 * s, cy + 5 * s)], 1.6 * s)
    c.path(bar, col)
    c.path(circ(cx, cy + 10.5 * s, 3.1 * s), col)


def x_poly(cx, cy, L, t, deg=45):
    pts = [(t, L), (t, t), (L, t), (L, -t), (t, -t), (t, -L), (-t, -L), (-t, -t), (-L, -t), (-L, t),
           (-t, t), (-t, L)]
    return rot([(cx + x, cy + y) for x, y in pts], cx, cy, deg)


def plus_poly(cx, cy, L, t):
    return x_poly(cx, cy, L, t, 0)


def sparkle(c, cx, cy, r, col=YELLOW):
    """Four-point 'new' sparkle."""
    k = 0.28
    pts = []
    for i in range(8):
        a = math.radians(-90 + i * 45)
        rad = r if i % 2 == 0 else r * k
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    c.oshape(poly(pts), c.rad(cx, cy, r, (0, "#FFFFFF"), (0.35, col.light), (1, col.dark)), col.line, w=0.9)


# ------------------------------------------------------------------ emblems

def e_doc(c):
    X0, Y0, X1, Y1, fold = page(c, 10, 38, 4, 44)
    lw = c.lw
    if c.px >= 14:
        text_lines(c, X0 + 3 * lw, Y0 + fold + lw, X1 - 3 * lw, Y1 - 3 * lw)
    else:
        text_lines(c, X0 + 2 * lw, Y0 + fold, X1 - 2 * lw, Y1 - 2 * lw, gap=2 * lw)


def landscape(c, X0, Y0, X1, Y1, sun=True):
    """Sky, sun and hills filling the box (call inside a clip)."""
    lw = c.lw
    h, w = Y1 - Y0, X1 - X0
    c.path(rr(X0, Y0, X1, Y1, 0), c.lin(0, Y0, 0, Y1, (0, "#2E7FE0"), (0.6, "#8CC8FF"), (1, "#D6EEFF")))
    if sun:
        sr = max(w * 0.11, 0.9 * lw)
        c.path(circ(X1 - w * 0.25, Y0 + h * 0.3, sr), c.rad(X1 - w * 0.27, Y0 + h * 0.27, sr * 1.2,
                                                            (0, "#FFFFE0"), (1, "#FFC926")))
    c.path(d("M", X0, Y0 + h * 0.72, "C", X0 + w * 0.25, Y0 + h * 0.42, X0 + w * 0.45, Y0 + h * 0.45,
             X0 + w * 0.6, Y0 + h * 0.62, "C", X0 + w * 0.75, Y0 + h * 0.5, X0 + w * 0.9, Y0 + h * 0.52,
             X1, Y0 + h * 0.6, "V", Y1, "H", X0, "Z"),
           c.lin(0, Y0 + h * 0.45, 0, Y1, (0, "#7DD34F"), (1, "#2F8F22")))
    c.path(d("M", X0, Y0 + h * 0.9, "C", X0 + w * 0.3, Y0 + h * 0.7, X0 + w * 0.7, Y0 + h * 0.78,
             X1, Y0 + h * 0.82, "V", Y1, "H", X0, "Z"), "#2A7A1E", op=0.55)


def e_picture(c, x0=5, y0=8, x1=43, y1=40):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    frame = rr(X0, Y0, X1, Y1, 0.5 * lw)
    c.drop(frame, op=0.25)
    c.shape(frame, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (1, "#DDE3EA")), line="#7A8696")
    m = (1 if px < 16 else 2) * lw if px < 30 else 3.5
    ix0, iy0, ix1, iy1 = c.sx(X0 + m), c.sy(Y0 + m), c.sx(X1 - m), c.sy(Y1 - m)
    inner = rr(ix0, iy0, ix1, iy1, 0)
    with c.clipped(inner):
        landscape(c, ix0, iy0, ix1, iy1, sun=px >= 12)
    c.path(inner, "none", stroke="#5C6B7E", sw=0.6 * lw, sop=0.6)


def e_note(c, ramp=None):
    col1, col2, line = "#6E9CF7", "#1E40B0", "#132B7A"
    g = c.lin(8, 6, 40, 42, (0, col1), (1, col2))
    lw = c.lw
    if c.px < 16:
        head = ell(17, 35, 8, 6)
        stem = rr(21.5, 7, 26.5, 35, 0)
        flag = d("M", 26, 7, "C", 32, 10, 38, 14, 36, 25, "C", 34, 19, 30, 17, 26, 17, "Z")
        for p in (stem, flag):
            c.oshape(p, g, line, w=0.7)
        c.oshape(head, g, line, w=0.7)
        return
    h1 = ell(0, 0, 6.3, 4.6)
    for cx, cy in ((14, 37), (33, 33)):
        c.add('<g transform="translate(%s %s) rotate(-22)">' % (cx, cy))
        c.oshape(h1, g, line, w=0.9)
        c.add("</g>")
    c.oshape(rr(17.6, 9, 21, 36, 0), g, line, w=0.9)
    c.oshape(rr(36.6, 5, 40, 32, 0), g, line, w=0.9)
    beam = poly([(17.6, 9), (40, 4), (40, 10.5), (17.6, 15.5)])
    c.oshape(beam, g, line, w=0.9)
    c.path(ell(12.5, 35.5, 2.4, 1.3), "#FFFFFF", op=0.7)
    c.path(ell(31.5, 31.5, 2.4, 1.3), "#FFFFFF", op=0.7)


def e_film(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(4, 11, 44, 37)
    strip = rr(X0, Y0, X1, Y1, 0.5 * lw)
    c.drop(strip, op=0.25)
    c.shape(strip, c.lin(0, Y0, 0, Y1, (0, "#4A5160"), (1, "#20242C")), line="#14161B")
    if px >= 14:
        hole = max(lw, 2.4)
        n = 7
        for i in range(n):
            hx = c.sx(X0 + 3 + i * (X1 - X0 - 6) / n + 0.5)
            for hy in (c.sy(Y0 + 1.6 * lw if px < 30 else Y0 + 2), c.sy(Y1 - 1.6 * lw - hole if px < 30 else Y1 - 2 - hole)):
                c.path(rr(hx, hy, hx + hole, hy + hole, 0.3), "#E8ECF2")
        fy0, fy1 = c.sy(Y0 + (3 * lw if px < 30 else 6)), c.sy(Y1 - (3 * lw if px < 30 else 6))
    else:
        fy0, fy1 = Y0 + lw, Y1 - lw
    mid = c.sx((X0 + X1) / 2)
    for a, b in ((c.sx(X0 + 2 * lw), mid - lw * 0.5), (mid + lw * 0.5, c.sx(X1 - 2 * lw))):
        fr = rr(a, fy0, b, fy1, 0)
        c.path(fr, c.lin(0, fy0, 0, fy1, (0, "#9FD4FF"), (0.6, "#4D96E8"), (1, "#3C7C36")))
        if px >= 20:
            with c.clipped(fr):
                c.path(ell((a + b) / 2, fy1, (b - a) * 0.6, (fy1 - fy0) * 0.35), "#5BB443")


def e_down(c):
    pts = arrow_poly(24, 24, 36, 13, 30, 16, 90)
    dd = rounded_poly(pts, 1.2)
    c.drop(dd, op=0.25)
    c.shape(dd, c.lin(10, 6, 36, 42, (0, GREEN.light), (0.5, GREEN.base), (1, GREEN.dark)), line=GREEN.line,
            hl=c.lin(0, 6, 0, 40, (0, "#FFFFFF", 0.7), (1, "#FFFFFF", 0.1)))


def person(c, cx, cy, s, shirt, skin=("#FFE3C4", "#E9A777"), hair="#6B4A2E"):
    """Bust of a person; (cx, cy) is the head centre, s the scale (1 = 48px bust)."""
    lw = c.lw
    body = d("M", cx - 13 * s, cy + 22 * s, "C", cx - 13 * s, cy + 12 * s, cx - 8 * s, cy + 9 * s, cx, cy + 9 * s,
             "C", cx + 8 * s, cy + 9 * s, cx + 13 * s, cy + 12 * s, cx + 13 * s, cy + 22 * s, "Z")
    c.shape(body, c.lin(cx - 10 * s, cy + 8 * s, cx + 10 * s, cy + 22 * s, (0, shirt.light), (0.5, shirt.base),
                        (1, shirt.dark)), line=shirt.line,
            hl=c.lin(0, cy + 9 * s, 0, cy + 16 * s, (0, "#FFFFFF", 0.5), (1, "#FFFFFF", 0)))
    head = circ(cx, cy, 7.2 * s)
    c.shape(head, c.rad(cx - 2.5 * s, cy - 2.5 * s, 9 * s, (0, skin[0]), (1, skin[1])), line=dk(skin[1], 0.35))
    if c.px * s > 20:
        c.path(d("M", cx - 7.2 * s, cy - 0.5 * s, "C", cx - 8 * s, cy - 9 * s, cx + 8 * s, cy - 9.5 * s,
                 cx + 7.2 * s, cy - 0.5 * s, "C", cx + 4 * s, cy - 4.5 * s, cx - 3 * s, cy - 5 * s,
                 cx - 7.2 * s, cy - 0.5 * s, "Z"), hair)


def e_people(c, ramp_back=GREEN, ramp_front=BLUE):
    person(c, 30, 13, 0.85, ramp_back, hair="#3E2A1A")
    person(c, 18, 19, 1.0, ramp_front)


def globe(c, cx=24, cy=24, r=18, shadow=True):
    lw = c.lw
    disc = circ(cx, cy, r)
    if shadow:
        c.drop(disc, op=0.25)
    c.shape(disc, c.rad(cx - 0.35 * r, cy - 0.4 * r, 1.5 * r, (0, "#C9EEFF"), (0.35, "#5DB0F2"),
                        (0.8, "#2167CC"), (1, "#173F95")))
    with c.clipped(disc):
        land = c.lin(cx - r, cy - r, cx + r, cy + r, (0, "#9BE36B"), (0.6, "#46A830"), (1, "#2C7A1F"))
        s = r / 18.0
        blobs = [
            [(-14, -9), (-8, -14), (-1, -13), (2, -9), (-2, -5), (-6, -4), (-5, 1), (-9, 3), (-13, 0), (-16, -4)],
            [(-4, 4), (2, 2), (6, 6), (5, 12), (1, 17), (-3, 13), (-5, 8)],
            [(6, -14), (12, -12), (17, -6), (15, -1), (10, -2), (8, -6), (4, -8)],
            [(10, 4), (16, 3), (17, 8), (13, 10)],
        ]
        for b in blobs:
            pts = [(cx + x * s, cy + y * s) for x, y in b]
            c.path(rounded_poly(pts, 2.2 * s), land)
        if c.px * r / 24 > 9:
            c.path(circ(cx, cy, r), "none", stroke="#FFFFFF", sw=lw * 0.6, sop=0.0)
    c.shape(disc, "none", line="#17418F")
    c.path(ell(cx - 0.18 * r, cy - 0.5 * r, 0.62 * r, 0.38 * r),
           c.lin(0, cy - 0.9 * r, 0, cy - 0.1 * r, (0, "#FFFFFF", 0.85), (1, "#FFFFFF", 0.0)))


def e_globe(c):
    globe(c, 24, 24, 19)


def house(c, x0=6, y0=6, x1=42, y1=42):
    """Little house with red roof (front-left lit)."""
    lw = c.lw
    w, h = x1 - x0, y1 - y0
    X = lambda t: x0 + w * t  # noqa: E731
    Y = lambda t: y0 + h * t  # noqa: E731
    shadow = poly([(X(0.12), Y(0.45)), (X(0.5), Y(0.08)), (X(0.88), Y(0.45)), (X(0.88), Y(1)), (X(0.12), Y(1))])
    c.drop(shadow)
    walls = poly([(X(0.16), Y(0.45)), (X(0.84), Y(0.45)), (X(0.84), Y(1)), (X(0.16), Y(1))])
    c.shape(walls, c.lin(X(0.16), Y(0.45), X(0.84), Y(1), (0, "#FFFBEF"), (1, "#E3D3B0")), line="#8C7552")
    # chimney
    ch = poly([(X(0.66), Y(0.12)), (X(0.77), Y(0.12)), (X(0.77), Y(0.36)), (X(0.66), Y(0.3))])
    c.shape(ch, c.lin(X(0.66), 0, X(0.77), 0, (0, "#D8653F"), (1, "#9C3A22")), line="#6E2412")
    roof = rounded_poly([(X(0.5), Y(0.04)), (X(1.0), Y(0.5)), (X(0.9), Y(0.56)), (X(0.5), Y(0.2)),
                         (X(0.1), Y(0.56)), (X(0.0), Y(0.5))], 1.2 * lw)
    c.shape(roof, c.lin(X(0.2), Y(0.05), X(0.8), Y(0.55), (0, "#FF8A5C"), (0.5, "#E5432A"), (1, "#A92212")),
            line="#7A1B0E", hl=c.lin(0, Y(0), 0, Y(0.3), (0, "#FFFFFF", 0.6), (1, "#FFFFFF", 0)))
    # door
    dx0, dx1 = c.sx(X(0.42)), c.sx(X(0.6))
    door = rr(dx0, c.sy(Y(0.66)), dx1, c.sy(Y(1)) - lw * 0.5, 0)
    c.shape(door, c.lin(dx0, 0, dx1, 0, (0, "#4E8FE8"), (1, "#1D4FB0")), line="#173F8C")
    if c.px * w / 48 > 14:
        win = rr(c.sx(X(0.22)), c.sy(Y(0.58)), c.sx(X(0.36)), c.sy(Y(0.74)), 0)
        c.shape(win, c.lin(0, Y(0.58), 0, Y(0.74), (0, "#E9F6FF"), (1, "#7CB9F2")), line="#5A6B80")
        win2 = rr(c.sx(X(0.66)), c.sy(Y(0.58)), c.sx(X(0.8)), c.sy(Y(0.74)), 0)
        c.shape(win2, c.lin(0, Y(0.58), 0, Y(0.74), (0, "#E9F6FF"), (1, "#7CB9F2")), line="#5A6B80")


def e_house(c):
    house(c, 4, 4, 44, 44)


def e_template(c):
    X0, Y0, X1, Y1, fold = page(c, 10, 38, 4, 44)
    lw, px = c.lw, c.px
    if px < 16:
        c.shape(rr(c.sx(X0 + 2 * lw), c.sy(Y0 + fold), c.sx(X1 - 2 * lw), c.sy(Y1 - 2 * lw), 0), "#CFE2FF",
                line="#3E7BE0")
        return
    bx0, by0, bx1, by1 = c.sbox(X0 + 4, Y0 + fold + 2, X1 - 4, Y0 + fold + 12)
    if px >= 30:
        c.path(rr(bx0 + lw / 2, by0 + lw / 2, bx1 - lw / 2, by1 - lw / 2, 0), "#DCEAFF", stroke="#3E7BE0",
               sw=lw, dash="%s %s" % (f2(2 * lw), f2(1.5 * lw)))
    else:
        c.shape(rr(bx0, by0, bx1, by1, 0), "#CFE2FF", line="#3E7BE0")
    text_lines(c, X0 + 4, by1 + 3, X1 - 4, Y1 - 3, col="#7FA8E8")


def f2(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def magnifier(c, cx=19, cy=19, r=12, angle=45, hlen=17, shadow=True):
    lw = c.lw
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    hw = max(r * 0.36, 1.6 * lw)
    sx, sy = cx + ux * (r + 0.5), cy + uy * (r + 0.5)
    ex, ey = cx + ux * (r + hlen), cy + uy * (r + hlen)
    nx, ny = -uy, ux
    handle = rounded_poly([(sx + nx * hw * 0.8, sy + ny * hw * 0.8), (ex + nx * hw, ey + ny * hw),
                           (ex - nx * hw, ey - ny * hw), (sx - nx * hw * 0.8, sy - ny * hw * 0.8)], hw * 0.9)
    ring_w = max(r * 0.2, 1.5 * lw)
    outer = circ(cx, cy, r + ring_w)
    if shadow:
        c.drop(handle, op=0.25)
        c.drop(outer, op=0.25)
    c.shape(handle, c.lin(sx + nx * hw, sy + ny * hw, sx - nx * hw, sy - ny * hw, (0, "#6E6E78"), (0.4, "#3A3A44"),
                          (1, "#16161C")), line="#0E0E12")
    # collar
    cx2, cy2 = cx + ux * (r + ring_w + 1.0), cy + uy * (r + ring_w + 1.0)
    coll = rounded_poly([(cx2 + nx * hw * 1.05 - ux * 2, cy2 + ny * hw * 1.05 - uy * 2),
                         (cx2 + nx * hw * 1.05 + ux * 2.5, cy2 + ny * hw * 1.05 + uy * 2.5),
                         (cx2 - nx * hw * 1.05 + ux * 2.5, cy2 - ny * hw * 1.05 + uy * 2.5),
                         (cx2 - nx * hw * 1.05 - ux * 2, cy2 - ny * hw * 1.05 - uy * 2)], 0.6)
    if c.px > 20:
        c.shape(coll, c.lin(cx2 + nx * hw, cy2 + ny * hw, cx2 - nx * hw, cy2 - ny * hw, (0, "#F2F4F7"), (1, "#8D95A1")),
                line="#5C636E")
    c.shape(outer, c.lin(cx - r, cy - r, cx + r, cy + r, (0, "#FFFFFF"), (0.5, "#C3CAD4"), (1, "#7C8592")),
            line="#4F5662")
    lens = circ(cx, cy, r)
    c.shape(lens, c.rad(cx - r * 0.3, cy - r * 0.35, r * 1.4, (0, "#F2FAFF"), (0.45, "#9DD2FF"), (1, "#3A86E0")),
            line="#5C6B80")
    if c.px * r / 48 > 4:
        c.path(d("M", cx - r * 0.7, cy + r * 0.05, "A", r * 0.7, r * 0.7, 0, 0, 1, cx + r * 0.05, cy - r * 0.7),
               "none", stroke="#FFFFFF", sw=max(lw, r * 0.16), cap="round", op=0.9)


def curved_arrow(cx, cy, R, w, a0, a1, head_w, head_deg, n=28):
    """Arc band from angle a0 to a1 (degrees) with an arrowhead at a1."""
    sgn = 1 if a1 > a0 else -1
    outer = arc_pts(cx, cy, R + w / 2, a0, a1, n)
    inner = arc_pts(cx, cy, R - w / 2, a1, a0, n)
    ah = math.radians(a1)
    tip_a = math.radians(a1 + sgn * head_deg)
    hb_o = (cx + (R + head_w / 2) * math.cos(ah), cy + (R + head_w / 2) * math.sin(ah))
    hb_i = (cx + (R - head_w / 2) * math.cos(ah), cy + (R - head_w / 2) * math.sin(ah))
    tip = (cx + R * math.cos(tip_a), cy + R * math.sin(tip_a))
    return outer + [hb_o, tip, hb_i] + inner
