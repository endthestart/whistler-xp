import math

from glyphs import (curved_arrow, folder, house, magnifier, orb_arrow, page, plus_poly, rounded_poly, sparkle,
                    text_lines, x_mark, x_poly)
from icons_mime import page_text
from lib import GREEN, PAPER_LINE, RED, TEXT_LINE, Ramp, circ, d, ell, poly, rot, rr
from objects import clock, floppy, printer, tile
from registry import icon


@icon("actions", "go-next")
def _next(c):
    orb_arrow(c, GREEN, 0)


@icon("actions", "go-previous")
def _prev(c):
    orb_arrow(c, GREEN, 180)


@icon("actions", "go-up")
def _up(c):
    orb_arrow(c, GREEN, -90)


@icon("actions", "go-home")
def _home(c):
    house(c, 3, 3, 45, 45)


def glossy_poly(c, dd, ramp, box):
    x0, y0, x1, y1 = box
    c.drop(dd, op=0.25)
    c.shape(dd, c.lin(x0, y0, x1, y1, (0, ramp.light), (0.5, ramp.base), (1, ramp.dark)), line=ramp.line,
            hl=c.lin(0, y0, 0, (y0 + y1) / 2, (0, "#FFFFFF", 0.75), (1, "#FFFFFF", 0.05)))


@icon("actions", "view-refresh")
def _refresh(c):
    px = c.px
    w = 7 if px > 24 else 8 if px > 16 else 9.5
    hw = 16 if px > 16 else 19
    for a0, a1 in ((-160, -25), (20, 155)):
        pts = curved_arrow(23, 23, 15, w, a0, a1, hw, 40 if px > 16 else 46)
        glossy_poly(c, rounded_poly(pts, 0.6), GREEN, (8, 8, 38, 38))


@icon("actions", "edit-find")
def _find(c):
    magnifier(c, 19, 19, 13, 45, 16)


@icon("actions", "edit-delete")
def _delete(c):
    px = c.px
    t = 5.2 if px > 16 else 6.5
    glossy_poly(c, rounded_poly(x_poly(23, 23, 19, t), 1.2), RED, (6, 6, 40, 40))


@icon("actions", "list-add")
def _add(c):
    px = c.px
    t = 5.5 if px > 16 else 6.5
    glossy_poly(c, rounded_poly(plus_poly(23, 23, 18, t), 1.0), GREEN, (6, 6, 40, 40))


@icon("actions", "list-remove")
def _remove(c):
    px = c.px
    t = 5.5 if px > 16 else 6.5
    X0, Y0, X1, Y1 = c.sbox(5, 23 - t, 41, 23 + t)
    glossy_poly(c, rr(X0, Y0, X1, Y1, 1.2), RED, (6, Y0, 40, Y1))


@icon("actions", "edit-copy")
def _copy(c):
    lw, px = c.lw, c.px
    for x0, y0 in ((4, 2), (16, 14)):
        X0, Y0, X1, Y1, fold = page(c, x0, x0 + 26, y0, y0 + 32)
        if px <= 16:
            text_lines(c, X0 + 2 * lw, Y0 + fold + lw, X1 - 2 * lw, Y1 - 2 * lw)
        else:
            text_lines(c, X0 + (3 * lw if px <= 24 else 4), Y0 + fold + (lw if px <= 24 else 2),
                       X1 - (3 * lw if px <= 24 else 4), Y1 - (2 * lw if px <= 24 else 4))


@icon("actions", "edit-cut")
def _cut(c):
    lw, px = c.lw, c.px
    cx, cy = 24, 21
    for sgn in (-1, 1):
        blade = [(cx, cy + 4), (cx + sgn * 2.2, cy - 2), (cx + sgn * 9.5, cy - 20), (cx + sgn * 7.5, cy - 20.5),
                 (cx - sgn * 1.5, cy - 3), (cx - sgn * 2, cy + 3)]
        blade = rot(blade, cx, cy, sgn * 0)
        c.drop(poly(blade), op=0.2)
        c.oshape(rounded_poly(blade, 0.5), c.lin(cx - 8, cy - 20, cx + 8, cy, (0, "#FFFFFF"), (0.5, "#C2C9D3"),
                                                 (1, "#7E8896")), "#4E5662", w=0.9)
    for sgn, ramp in ((-1, RED), (1, RED)):
        hx, hy = cx + sgn * 9.5, cy + 14
        r_o, r_i = (7.5, 4.0) if px > 16 else (8.0, 3.6)
        arm = poly([(cx - sgn * 1.5, cy + 2), (cx + sgn * 2.5, cy + 3), (hx + sgn * 0.5 - sgn * 4, hy - 5.5),
                    (hx - sgn * 6, hy - 3)])
        c.oshape(arm, c.lin(0, cy, 0, hy, (0, ramp.light), (1, ramp.dark)), ramp.line, w=0.9)
        ring = circ(hx, hy, r_o) + " " + circ(hx, hy, r_i)
        c.drop(circ(hx, hy, r_o), op=0.25)
        c.path(ring, c.lin(hx - r_o, hy - r_o, hx + r_o, hy + r_o, (0, ramp.light), (0.5, ramp.base),
                           (1, ramp.dark)), rule="evenodd")
        c.outline(ring, ramp.line, rule="evenodd")
    c.shape(circ(cx, cy + 2.5, 2.0 if px > 16 else 2.8), c.lin(cx - 2, cy, cx + 2, cy + 4, (0, "#FFFFFF"),
                                                                 (1, "#6E7784")), line="#3E4652")


def clipboard(c, x0=6, y0=5, x1=38, y1=45):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    board = rr(X0, Y0, X1, Y1, 2 if px > 16 else 0.5 * lw)
    c.drop(board)
    c.shape(board, c.lin(X0, Y0, X1, Y1, (0, "#E7A762"), (0.5, "#C07A35"), (1, "#8A5220")), line="#5E3410",
            hl=c.hl_grad(X0, Y0, X1, Y1, 0.6, 0))
    m = 2 * lw if px <= 24 else 4
    pX0, pY0, pX1, pY1 = c.sbox(X0 + m, Y0 + (3 * lw if px <= 24 else 6), X1 - m, Y1 - m)
    sheet = rr(pX0, pY0, pX1, pY1, 0)
    c.shape(sheet, c.lin(pX0, pY0, pX1, pY1, (0, "#FFFFFF"), (1, "#DCE3EC")), line=PAPER_LINE)
    if px > 16:
        text_lines(c, pX0 + (2 * lw if px <= 24 else 4), pY0 + (3 * lw if px <= 24 else 7), pX1 - (2 * lw if px <= 24 else 4),
                   pY1 - (2 * lw if px <= 24 else 4))
    else:
        text_lines(c, pX0 + lw, pY0 + 2 * lw, pX1 - lw, pY1 - lw)
    cx = (X0 + X1) / 2
    cw = (X1 - X0) * 0.25
    clip = rr(c.sx(cx - cw), c.sy(Y0 - (2 if px > 16 else 0)), c.sx(cx + cw), c.sy(Y0 + (5 if px > 16 else 2 * lw)), 1.2 if px > 16 else 0)
    c.shape(clip, c.lin(0, Y0 - 2, 0, Y0 + 5, (0, "#FFFFFF"), (0.5, "#BFC7D2"), (1, "#7C8592")), line="#4C5463")
    return (pX0, pY0, pX1, pY1)


@icon("actions", "edit-paste")
def _paste(c):
    clipboard(c, 4, 5, 36, 45)
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1, fold = page(c, 20, 44, 18, 46)
    if px > 16:
        text_lines(c, X0 + (3 * lw if px <= 24 else 4), Y0 + fold + lw, X1 - (3 * lw if px <= 24 else 4),
                   Y1 - (2 * lw if px <= 24 else 4))


UNDO = Ramp("#EAF6FF", "#A6D6FF", "#4A94F2", "#2563D2", "#143780")


def undo_arrow(c, mirror=False):
    px = c.px
    if px <= 16:
        pts = curved_arrow(27, 30, 13, 10.5, 5, -175, 27, 52)
    elif px <= 24:
        pts = curved_arrow(27, 29, 13, 9, 8, -175, 24, 46)
    else:
        pts = curved_arrow(27, 29, 13.5, 7.5, 10, -175, 21, 42)
    if mirror:
        pts = [(48 - x, y) for x, y in pts]
    glossy_poly(c, rounded_poly(pts, 0.6), UNDO, (6, 10, 40, 40))


@icon("actions", "edit-undo")
def _undo(c):
    undo_arrow(c)


@icon("actions", "edit-redo")
def _redo(c):
    undo_arrow(c, mirror=True)


@icon("actions", "document-new")
def _new(c):
    X0, Y0, X1, Y1, fold = page(c, 10, 40, 3, 45)
    page_text(c, X0, Y0, X1, Y1, fold) if c.px > 24 else None
    sparkle(c, 12 if c.px > 16 else 13, 12 if c.px > 16 else 13, 11 if c.px > 16 else 13)


@icon("actions", "document-open")
def _open(c):
    folder(c, open_=True)


@icon("actions", "document-save")
def _save(c):
    floppy(c)


@icon("actions", "document-properties")
def _props(c):
    X0, Y0, X1, Y1, fold = page(c)
    lw, px = c.lw, c.px
    rows = 3
    if px <= 16:
        for i in range(2):
            y = c.sy(Y0 + fold + 2 * lw + i * 4 * lw)
            c.shape(rr(X0 + 2 * lw, y, X0 + 5 * lw, y + 3 * lw, 0), "#FFFFFF", line="#5B6B82")
            c.path(rr(X0 + 6 * lw, y + lw, X1 - 2 * lw, y + 2 * lw, 0), TEXT_LINE)
            if i == 0:
                c.path(rr(X0 + 3 * lw, y + lw, X0 + 4 * lw, y + 2 * lw, 0), "#2E9E1F")
        return
    bs = 3 * lw if px <= 24 else 7
    y = c.sy(Y0 + fold + (lw if px <= 24 else 3))
    gap = bs + (2 * lw if px <= 24 else 4)
    for i in range(rows):
        bx = c.sx(X0 + (2 * lw if px <= 24 else 4))
        b = rr(bx, y, bx + bs, y + bs, 0.3 * lw)
        c.shape(b, c.lin(bx, y, bx + bs, y + bs, (0, "#FFFFFF"), (1, "#D5DCE6")), line="#5B6B82")
        if i != 1:
            p = [(bx + bs * 0.2, y + bs * 0.5), (bx + bs * 0.45, y + bs * 0.75), (bx + bs * 0.85, y + bs * 0.2)]
            c.line(p, "#2E9E1F", w=1.0 if px <= 24 else 1.6)
        c.path(rr(bx + bs + (lw if px <= 24 else 3), c.sy(y + bs / 2 - lw / 2), X1 - (2 * lw if px <= 24 else 4),
                  c.sy(y + bs / 2 - lw / 2) + lw * (1 if px <= 32 else 2), 0), TEXT_LINE)
        y = c.sy(y + gap)


@icon("actions", "document-print")
def _print(c):
    printer(c)


@icon("actions", "folder-new")
def _folder_new(c):
    folder(c)
    px = c.px
    sparkle(c, 13 if px > 16 else 12, 11 if px > 16 else 11, 11 if px > 16 else 12)


@icon("actions", "process-stop")
def _stop(c):
    px = c.px
    pts = [(23 + 19 * math.cos(math.radians(22.5 + i * 45)), 23 + 19 * math.sin(math.radians(22.5 + i * 45)))
           for i in range(8)]
    oct_ = rounded_poly(pts, 1.6)
    c.drop(oct_, op=0.25)
    c.shape(oct_, c.rad(21, 31, 26, (0, RED.light), (0.45, RED.base), (1, RED.dark)), line=RED.line)
    c.outline(rounded_poly([(23 + (x - 23) * 0.86, 23 + (y - 23) * 0.86) for x, y in pts], 1.2), "#FFFFFF",
              w=1.0 if px <= 32 else 1.5) if px > 16 else None
    with c.clipped(oct_):
        c.path(ell(23, 13, 15, 10), c.lin(0, 3, 0, 23, (0, "#FFFFFF", 0.7), (1, "#FFFFFF", 0.05)))
    t = 3.4 if px > 24 else 4.2 if px > 16 else 5.4
    x_mark(c, RED, L=11.5, t=t)


@icon("actions", "window-close")
def _close(c):
    px = c.px
    tile(c, RED, 4, 4, 42, 42, r=6 if px > 16 else 4)
    t = 3.6 if px > 24 else 4.4 if px > 16 else 4.6
    if px <= 16:
        x_mark(c, RED)
    else:
        c.path(rounded_poly(x_poly(23, 23, 12, t), 0.8), "#FFFFFF")


@icon("actions", "system-shutdown")
def _shutdown(c):
    lw, px = c.lw, c.px
    tile(c, Ramp("#FFE0D0", "#FF9A5C", "#E8541E", "#B8340C", "#7E2208"), 4, 4, 42, 42, r=6 if px > 16 else 4)
    w = 3.6 if px > 24 else 4.4 if px > 16 else 5.4
    arc = poly(arc_pts_deg(23, 24.5, 10.5, -55, 235), close=False)
    c.path(arc, "none", stroke="#FFFFFF", sw=w, cap="round")
    c.line([(23, 10), (23, 22)], "#FFFFFF", w=w / lw)


def arc_pts_deg(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
            for a in [a0 + (a1 - a0) * i / n for i in range(n + 1)]]


@icon("actions", "system-log-out")
def _logout(c):
    lw, px = c.lw, c.px
    # door frame and open door
    X0, Y0, X1, Y1 = c.sbox(6, 3, 30, 45)
    frame = rr(X0, Y0, X1, Y1, 0)
    c.drop(frame)
    c.shape(frame, c.lin(X0, Y0, X1, Y1, (0, "#3A4A6A"), (1, "#141C2E")), line="#0C1220")
    with c.clipped(rr(X0 + lw, Y0 + lw, X1 - lw, Y1, 0)):
        c.path(rr(X0, Y1 - (Y1 - Y0) * 0.35, X1, Y1, 0), c.lin(0, Y1 - 14, 0, Y1, (0, "#FFE8A0", 0.0),
                                                                 (1, "#FFE8A0", 0.5)))
    dw = (X1 - X0) * 0.62
    door = poly([(X0, Y0), (X0 + dw, c.sy(Y0 + 4)), (X0 + dw, c.sy(Y1 - 3)), (X0, Y1)])
    c.shape(door, c.lin(X0, Y0, X0 + dw, Y1, (0, "#E8A866"), (0.5, "#B8722E"), (1, "#7E4614")), line="#4E2A0A")
    if px > 16:
        c.path(circ(X0 + dw - 3, (Y0 + Y1) / 2 + 2, 1.4), "#FFE07A")
    with c.place(c.sx(20), c.sy(12), 28):
        orb_arrow(c, GREEN, 0)


@icon("actions", "view-list")
def _list(c):
    lw, px = c.lw, c.px
    rows = 4 if px > 16 else 3
    X0, Y0, X1, Y1 = c.sbox(4, 5, 44, 43)
    sheet = rr(X0, Y0, X1, Y1, 1 if px > 16 else 0)
    c.drop(sheet)
    c.shape(sheet, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (1, "#DCE3EC")), line=PAPER_LINE)
    m = 2 * lw if px <= 24 else 4
    gap = ((Y1 - Y0) - 2 * m) / rows
    for i in range(rows):
        y = c.sy(Y0 + m + i * gap)
        s = c.sy(y + gap * 0.7) - y
        if px <= 16:
            s = 2 * lw
        ib = rr(X0 + m, y, X0 + m + s, y + s, 0.3 * lw)
        c.shape(ib, c.lin(0, y, 0, y + s, (0, "#8CC0FF"), (1, "#2257C8")), line="#163A8C" if px > 16 else None)
        ly = c.sy(y + s / 2 - lw / 2)
        c.path(rr(X0 + m + s + (lw if px <= 24 else 3), ly, X1 - m - (i % 2) * (X1 - X0) * 0.15,
                  ly + (lw if px <= 32 else 2 * lw), 0), "#5B6B82")


@icon("actions", "view-grid")
def _grid(c):
    lw, px = c.lw, c.px
    n = 2
    X0, Y0, X1, Y1 = c.sbox(4, 4, 42, 42)
    g = (lw * 2 if px <= 24 else 4)
    cw = (X1 - X0 - g) / 2
    for j in range(n):
        for i in range(n):
            a0, b0 = c.sx(X0 + i * (cw + g)), c.sy(Y0 + j * (cw + g))
            a1, b1 = c.sx(a0 + cw), c.sy(b0 + cw)
            t = rr(a0, b0, a1, b1, 2 if px > 16 else 0.5 * lw)
            c.drop(t)
            c.shape(t, c.lin(a0, b0, a1, b1, (0, "#9CCBFF"), (0.5, "#3C7FE8"), (1, "#1C4FB0")), line="#173F8C",
                    hl=c.hl_grad(a0, b0, a1, b1, 0.7, 0.0))


@icon("actions", "document-open-recent")
def _recent(c):
    X0, Y0, X1, Y1, fold = page(c, 4, 34, 2, 42)
    page_text(c, X0, Y0, X1, Y1, fold, bottom=Y1 - (16 if c.px > 24 else 6 * c.lw))
    clock(c, 32, 32, 13 if c.px > 16 else 14)


# ------------------------------------------------------------ extra names

@icon("actions", "go-down")
def _down(c):
    orb_arrow(c, GREEN, 90)


def zoom(c, plus):
    magnifier(c, 19, 19, 13, 45, 16)
    px = c.px
    t = 2.0 if px > 24 else 2.6 if px > 16 else 3.4
    L = 7.0 if px > 16 else 8.5
    sym = plus_poly(19, 19, L, t) if plus else [(19 - L, 19 - t), (19 + L, 19 - t), (19 + L, 19 + t), (19 - L, 19 + t)]
    c.oshape(poly(sym), "#1B4FB8", "#FFFFFF", w=0.7 if px > 16 else 0.5)


@icon("actions", "zoom-in")
def _zoom_in(c):
    zoom(c, True)


@icon("actions", "zoom-out")
def _zoom_out(c):
    zoom(c, False)


@icon("actions", "system-reboot")
def _reboot(c):
    px = c.px
    tile(c, GREEN, 4, 4, 42, 42, r=6 if px > 16 else 4)
    w = 4.2 if px > 24 else 5.0 if px > 16 else 6.2
    pts = curved_arrow(23, 24, 10.5, w, 150, -100 + 360 - 360 + 390 - 360, 12 if px > 16 else 14, 50)
    c.path(rounded_poly(pts, 0.5), "#FFFFFF")


@icon("actions", "system-suspend")
def _suspend(c):
    px = c.px
    tile(c, Ramp("#FFF6D0", "#FFD964", "#F2B21C", "#C98A0A", "#8A5E06"), 4, 4, 42, 42, r=6 if px > 16 else 4)
    moon = d("M", 27, 11, "A", 12.5, 12.5, 0, 1, 0, 34, 31, "A", 10, 10, 0, 1, 1, 27, 11, "Z")
    c.path(moon, "#FFFFFF")
