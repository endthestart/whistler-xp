
from glyphs import (e_picture, folder, globe, magnifier, orb, orb_arrow, page, person, rounded_poly, sym_q,
                    text_lines, white_mark)
from icons_places import mini_desktop
from lib import BLUE, GREEN, ORANGE, PAPER_LINE, PURPLE, RED, YELLOW, circ, d, dk, ell, lt, poly, rot, rr
from objects import BROWN, calculator, clock, crt, disc, envelope, speaker, waves, window
from registry import icon


def check(c, cx, cy, s=1.0, ramp=GREEN):
    pts = [(-11, 0), (-6, -5), (-2, -1), (8, -11), (13, -6), (-2, 9)]
    p = rounded_poly([(cx + x * s, cy + y * s) for x, y in pts], 1.2 * s)
    c.drop(p, op=0.25)
    c.shape(p, c.lin(cx - 10 * s, cy - 10 * s, cx + 10 * s, cy + 10 * s, (0, ramp.light), (0.5, ramp.base),
                     (1, ramp.dark)), line=ramp.line)


@icon("apps", "preferences-system")
def _control_panel(c):
    lw, px = c.lw, c.px

    def sliders(c, box):
        X0, Y0, X1, Y1 = box
        w, h = X1 - X0, Y1 - Y0
        c.path(rr(X0, Y0, X1, Y1, 0), c.lin(0, Y0, 0, Y1, (0, "#F4F8FF"), (1, "#C7D9F2")))
        cols = (RED, GREEN, BLUE)
        pos = (0.35, 0.65, 0.45)
        for i in range(3):
            tx = c.sx(X0 + w * (0.22 + i * 0.28))
            t0, t1 = c.sy(Y0 + h * 0.12), c.sy(Y1 - h * 0.12)
            c.path(rr(tx - lw / 2 if px <= 24 else tx - lw, t0, tx + lw / 2 if px <= 24 else tx + lw, t1, 0),
                   "#5B6B82")
            ky = c.sy(Y0 + h * pos[i])
            kw = max(lw * 1.5, w * 0.1)
            kh = max(lw * 1.5 if px > 16 else lw * 2, h * 0.14)
            k = rr(tx - kw, ky - kh / 2, tx + kw, ky + kh / 2, 0.4 * lw if px > 24 else 0)
            c.shape(k, c.lin(0, ky - kh / 2, 0, ky + kh / 2, (0, cols[i].light), (1, cols[i].dark)),
                    line=cols[i].line if px > 16 else None)

    crt(c, 3, 5, 41, 35, screen=sliders)


@icon("apps", "system-search")
def _search(c):
    X0, Y0, X1, Y1, fold = page(c, 4, 32, 2, 40)
    lw = c.lw
    if c.px > 16:
        text_lines(c, X0 + 3 * lw if c.px <= 24 else X0 + 4, Y0 + fold + lw, X1 - 4, Y1 - 4)
    magnifier(c, 28, 27, 10, 45, 12)


@icon("apps", "system-run")
def _run(c):
    window(c, 2, 4, 42, 36)
    with c.place(c.sx(20), c.sy(20), 28):
        orb_arrow(c, GREEN, 0)


@icon("apps", "help-browser")
def _help(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(9, 4, 41, 44)
    # page block visible at the right and bottom
    pages = rr(X0 + 2 * lw, Y0 + 2 * lw, X1, Y1, 1)
    c.drop(pages)
    c.shape(pages, c.lin(0, Y0, 0, Y1, (0, "#FFFFFF"), (1, "#D9DFE8")), line="#7D8899")
    cover = rr(X0, Y0, X1 - 2 * lw, Y1 - 2 * lw, 1.5 if px > 16 else 0.5 * lw)
    c.shape(cover, c.lin(X0, Y0, X1, Y1, (0, "#6FA8FF"), (0.5, "#2A62D8"), (1, "#183C9E")), line="#122E7C",
            hl=c.hl_grad(X0, Y0, X1, Y1, 0.6, 0.0))
    sp = c.sx(X0 + max(2 * lw, 5))
    c.path(rr(X0 + lw, Y0 + lw, sp, Y1 - 3 * lw, 0), "#0F2A70", op=0.45)
    cx = (sp + X1 - 2 * lw) / 2
    sym_q(c, cx, (Y0 + Y1) / 2 - lw, s=0.95 if px > 16 else 1.05, col="#FFFFFF")


@icon("apps", "system-users")
def _users(c):
    person(c, 31, 12, 0.95, GREEN, hair="#3E2A1A")
    person(c, 18, 20, 1.15, BLUE)


@icon("apps", "utilities-terminal")
def _terminal(c):
    lw, px = c.lw, c.px

    def prompt(c, box):
        X0, Y0, X1, Y1 = box
        c.path(rr(X0, Y0, X1, Y1, 0), "#0C0C0C")
        if px <= 16:
            x, y = X0 + lw, Y0 + lw
            c.path(poly([(x, y), (x + lw, y), (x + 2 * lw, y + lw), (x + lw, y + 2 * lw), (x, y + 2 * lw),
                         (x + lw, y + lw)]), "#E8E8E8")
            c.path(rr(x + 3 * lw, y + 2 * lw, x + 5 * lw, y + 3 * lw, 0), "#E8E8E8")
            return
        s = 1 if px > 24 else 0.8
        x, y = c.sx(X0 + 3 * lw), c.sy(Y0 + 3 * lw)
        c.line([(x, y), (x + 5 * s, y + 4 * s), (x, y + 8 * s)], "#E8E8E8", w=1.6 if px > 24 else 1.2,
               cap="square", join="miter")
        cy_ = c.sy(y + 8 * s)
        c.path(rr(c.sx(x + 8 * s), cy_ - lw, c.sx(x + 15 * s), cy_ + (lw if px > 24 else 0), 0), "#E8E8E8")
        if px > 30:
            for i, wdt in enumerate((0.7, 0.45)):
                yy = c.sy(y + 13 + i * 4)
                c.path(rr(x, yy, x + (X1 - X0 - 8) * wdt, yy + lw, 0), "#9A9A9A")

    window(c, 2, 5, 44, 41, content=prompt)


@icon("apps", "accessories-text-editor")
def _editor(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(6, 4, 36, 45)
    pad = rr(X0, Y0, X1, Y1, 0.5 * lw)
    c.drop(pad)
    c.shape(pad, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (1, "#DDE5EF")), line=PAPER_LINE)
    with c.clipped(pad):
        lx = c.sx(X0 + (3 if px <= 16 else 4) * lw)
        if px > 16:
            c.path(rr(lx, Y0, lx + lw, Y1, 0), "#F08A8A", op=0.8)
        y = c.sy(Y0 + (5 if px <= 16 else 4) * lw if px <= 24 else Y0 + 11)
        gap = 2 * lw if px <= 24 else 4
        while y < Y1 - lw:
            c.path(rr(X0, y, X1, y + lw, 0), "#9CC3EE", op=0.9)
            y += gap
    bh = max(2 * lw, c.sy(Y0 + 6) - Y0) if px > 16 else 2 * lw
    band = rr(X0, Y0, X1, Y0 + bh, 0.5 * lw)
    c.shape(band, c.lin(0, Y0, 0, Y0 + bh, (0, "#6FA8FF"), (1, "#1F50C0")), line="#163A8C")
    # pencil
    a = -50
    cx, cy = 33, 29
    L, W = 30 if px > 16 else 32, 6 if px > 16 else 7.5
    body = [(cx - L / 2 + 7, cy - W / 2), (cx + L / 2 - 4, cy - W / 2), (cx + L / 2, cy - W / 2),
            (cx + L / 2, cy + W / 2), (cx - L / 2 + 7, cy + W / 2)]
    tip = [(cx - L / 2 + 7, cy - W / 2), (cx - L / 2, cy), (cx - L / 2 + 7, cy + W / 2)]
    lead = [(cx - L / 2 + 2.6, cy - W * 0.19), (cx - L / 2, cy), (cx - L / 2 + 2.6, cy + W * 0.19)]
    eraser = [(cx + L / 2 - 5, cy - W / 2), (cx + L / 2, cy - W / 2), (cx + L / 2, cy + W / 2),
              (cx + L / 2 - 5, cy + W / 2)]
    R = lambda pts: rot(pts, cx, cy, a)  # noqa: E731
    c.drop(poly(R(body + tip[1:2])))
    c.oshape(poly(R(tip)), "#F3D9A8", "#8A6A3A", w=0.8)
    if px > 16:
        c.path(poly(R(lead)), "#3A3A3A")
    c.oshape(poly(R(body)), c.lin(*R([(0, cy - W / 2)])[0], *R([(0, cy + W / 2)])[0], (0, "#FFE680"),
                                  (0.5, "#FFC21A"), (1, "#D68A00")), "#8A5A00", w=0.8)
    c.oshape(poly(R(eraser)), c.lin(*R([(0, cy - W / 2)])[0], *R([(0, cy + W / 2)])[0], (0, "#FFB4B4"),
                                    (1, "#D9534F")), "#8A2A2A", w=0.8)


@icon("apps", "accessories-calculator")
def _calc(c):
    calculator(c)


def letter_a(c, cx, base, h, fill, line):
    s = h / 30.0
    outer = [(cx - 15 * s, base), (cx - 3.4 * s, base - 30 * s), (cx + 3.4 * s, base - 30 * s), (cx + 15 * s, base),
             (cx + 8.2 * s, base), (cx + 5.4 * s, base - 8 * s), (cx - 5.4 * s, base - 8 * s), (cx - 8.2 * s, base)]
    inner = [(cx - 3.6 * s, base - 13.5 * s), (cx, base - 23.5 * s), (cx + 3.6 * s, base - 13.5 * s)]
    dd = poly(outer) + " " + poly(inner)
    c.path(dd, fill, stroke=line, sw=c.lw, join="round", rule="evenodd")


@icon("apps", "accessories-character-map")
def _charmap(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(3, 5, 41, 43)
    card = rr(X0, Y0, X1, Y1, 1 if px > 16 else 0)
    c.drop(card)
    c.shape(card, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (1, "#DCE3EC")), line="#7A8696")
    n = 4 if px > 16 else 3
    for i in range(1, n):
        x = c.sx(X0 + (X1 - X0) * i / n)
        y = c.sy(Y0 + (Y1 - Y0) * i / n)
        c.path(rr(x, Y0, x + lw, Y1, 0), "#B5C0CF")
        c.path(rr(X0, y, X1, y + lw, 0), "#B5C0CF")
    if px > 24:
        cw = (X1 - X0) / n
        for (i, j) in ((0, 0), (2, 0), (3, 1), (0, 2), (1, 3), (3, 3)):
            gx, gy = X0 + cw * (i + 0.5), Y0 + cw * (j + 0.5)
            c.path(circ(gx, gy, 1.6), "#5B6B82") if (i + j) % 2 else c.path(rr(gx - 1.5, gy - 2, gx + 1.5, gy + 2, 0.5), "#5B6B82")
    # magnified cell
    bx0, by0, bx1, by1 = c.sbox(15, 13, 45, 45)
    pop = rr(bx0, by0, bx1, by1, 1.5 if px > 16 else 0)
    c.drop(pop)
    c.shape(pop, c.lin(bx0, by0, bx1, by1, (0, "#FFFFFF"), (1, "#E6EEF9")), line="#2E5FB8",
            w=1 if px <= 24 else 1.4)
    letter_a(c, (bx0 + bx1) / 2, by1 - (bx1 - bx0) * 0.18, (by1 - by0) * 0.64,
             c.lin(0, by0, 0, by1, (0, "#5C9BFF"), (1, "#1A44B0")), "#102C78")


@icon("apps", "preferences-desktop-theme")
def _theme(c):
    lw, px = c.lw, c.px
    pal = d("M", 22, 9, "C", 35, 9, 43, 16, 42, 25, "C", 41.5, 30, 36, 30, 33, 29, "C", 29, 28, 27, 32, 29, 35,
            "C", 31, 38, 29, 43, 21, 43, "C", 10, 43, 3, 36, 3, 26, "C", 3, 16, 11, 9, 22, 9, "Z")
    hole = ell(13, 33, 3.2, 2.6)
    shape = pal + " " + hole
    c.drop(pal)
    c.path(shape, c.lin(3, 9, 42, 43, (0, "#F7DDB0"), (0.5, "#DDAE6A"), (1, "#B07A3A")), rule="evenodd")
    c.outline(shape, "#7A5228", rule="evenodd")
    dots = [((12, 19), RED), ((21, 14.5), YELLOW), ((31, 16), GREEN), ((36, 23), BLUE), ((10, 26), PURPLE)]
    rad = 3.6 if px > 24 else 4.4
    for (x, y), r_ in dots:
        if px <= 16 and r_ is PURPLE:
            continue
        c.shape(circ(x, y, rad), c.rad(x - 1, y - 1, rad * 1.3, (0, r_.light), (1, r_.dark)),
                line=r_.line if px > 16 else None)
    # brush
    a = -55
    cx, cy = 33, 33
    hnd = rot([(cx - 2, cy - 2.2), (cx + 16, cy - 1.6), (cx + 16, cy + 1.6), (cx - 2, cy + 2.2)], cx, cy, a)
    fer = rot([(cx - 6, cy - 2.6), (cx - 1, cy - 2.4), (cx - 1, cy + 2.4), (cx - 6, cy + 2.6)], cx, cy, a)
    tip = rot([(cx - 6, cy - 2.6), (cx - 11, cy - 1.6), (cx - 14, cy), (cx - 11, cy + 1.6), (cx - 6, cy + 2.6)],
              cx, cy, a)
    c.drop(poly(hnd))
    c.oshape(poly(hnd), c.lin(*hnd[0], *hnd[3], (0, "#E86A4A"), (1, "#9A2A14")), "#5E1A0C", w=0.8)
    c.oshape(poly(fer), c.lin(*fer[0], *fer[3], (0, "#FFFFFF"), (1, "#8C96A4")), "#4E5662", w=0.8)
    c.oshape(rounded_poly(tip, 1.0), c.lin(*tip[0], *tip[2], (0, "#3A2A1A"), (1, "#2F74E0")), "#1A1208", w=0.8)


@icon("apps", "preferences-desktop-display")
def _display(c):
    def scr(c, box):
        X0, Y0, X1, Y1 = box
        mini_desktop(c, X0, Y0, X1, Y1)
        if c.px > 20:
            w, h = X1 - X0, Y1 - Y0
            window(c, X0 + w * 0.35, Y0 + h * 0.14, X0 + w * 0.88, Y0 + h * 0.66, shadow=True)
    crt(c, 3, 5, 41, 35, screen=scr)


@icon("apps", "preferences-desktop-wallpaper")
def _wallpaper(c):
    from glyphs import landscape
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(4, 7, 44, 41)
    fr = rr(X0, Y0, X1, Y1, 0.5 * lw)
    c.drop(fr)
    c.shape(fr, c.lin(X0, Y0, X1, Y1, (0, "#E8B66C"), (0.5, "#B87A30"), (1, "#7E4C16")), line="#5A3410",
            hl=c.hl_grad(X0, Y0, X1, Y1, 0.6, 0))
    m = (2 if px <= 24 else 3) * lw if px <= 32 else 4
    inner = rr(X0 + m, Y0 + m, X1 - m, Y1 - m, 0)
    with c.clipped(inner):
        landscape(c, X0 + m, Y0 + m, X1 - m, Y1 - m)
    c.outline(inner, "#5A3410", w=0.8)


@icon("apps", "preferences-desktop-default-applications")
def _defaults(c):
    window(c, 2, 4, 40, 38)
    lw = c.lw
    if c.px > 16:
        with c.place(18, 18, 30):
            check(c, 24, 26, 1.35)
    else:
        with c.place(c.sx(16), c.sy(15), 33):
            check(c, 24, 26, 1.5)


@icon("apps", "preferences-desktop-font")
def _font(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1, fold = page(c, 6, 38, 3, 45)
    g = c.lin(0, 10, 0, 40, (0, "#6FA8FF"), (0.5, "#2A62D8"), (1, "#183C9E"))
    if px <= 16:
        letter_a(c, 22, c.sy(42), 30, g, "#102C78")
    else:
        letter_a(c, 22, 40, 28, g, "#102C78")


@icon("apps", "preferences-system-time")
def _time(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(3, 5, 33, 39)
    cal = rr(X0, Y0, X1, Y1, 1 if px > 16 else 0)
    c.drop(cal)
    c.shape(cal, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (1, "#D9E0EA")), line="#6E7A8C")
    hh = c.sy(Y0 + (Y1 - Y0) * 0.28)
    head = d("M", X0, Y0 + (1 if px > 16 else 0), "Q", X0, Y0, X0 + 1, Y0, "H", X1 - 1, "Q", X1, Y0, X1,
             Y0 + 1, "V", hh, "H", X0, "Z")
    c.shape(head, c.lin(0, Y0, 0, hh, (0, "#FF8A66"), (0.5, "#E5432A"), (1, "#B32213")), line="#86190E")
    if px > 16:
        for x in (X0 + (X1 - X0) * 0.28, X0 + (X1 - X0) * 0.72):
            c.shape(rr(x - 1.2, Y0 - 2.5, x + 1.2, Y0 + 3, 1.2), c.lin(x - 1.2, 0, x + 1.2, 0, (0, "#FFFFFF"),
                                                                       (1, "#7C8592")), line="#4E5662")
        gx0, gy0 = X0 + 3 * lw, hh + 3 * lw
        cw, ch = (X1 - X0 - 6 * lw) / 5, (Y1 - hh - 6 * lw) / 4
        for j in range(4):
            for i in range(5):
                x, y = gx0 + i * cw, gy0 + j * ch
                col = "#E5432A" if (i, j) == (3, 1) else "#8C9AB0"
                c.path(rr(x, y, x + cw * 0.6, y + ch * 0.55, 0), col, op=0.9 if col != "#8C9AB0" else 0.6)
    else:
        for j in range(2):
            y = c.sy(hh + 2 * lw + j * 2 * lw)
            c.path(rr(X0 + 2 * lw, y, X1 - 2 * lw, y + lw, 0), "#8C9AB0")
    clock(c, 32, 31, 13 if px > 16 else 14)


@icon("apps", "preferences-desktop-accessibility")
def _a11y(c):
    orb(c, BLUE)
    lw, px = c.lw, c.px
    w = 3.4 if px > 24 else 4.2 if px > 16 else 5.0
    col = "#FFFFFF"
    c.path(circ(23, 11.5, 3.6 if px > 16 else 4.4), col)
    c.line([(12, 18), (23, 20), (34, 18)], col, w=w / c.lw, cap="round")
    c.line([(23, 20), (23, 27)], col, w=w / c.lw, cap="round")
    c.line([(16, 36), (23, 27), (30, 36)], col, w=w / c.lw, cap="round")


@icon("apps", "preferences-desktop-locale")
def _locale(c):
    lw, px = c.lw, c.px
    globe(c, 19, 27, 17)
    X0, Y0, X1, Y1 = c.sbox(24, 3, 45, 21)
    tail = [(X0 + 4, Y1), (X0 + 1, Y1 + 6), (X0 + 10, Y1)]
    bub = d("M", X0 + 2, Y0, "H", X1 - 2, "Q", X1, Y0, X1, Y0 + 2, "V", Y1 - 2, "Q", X1, Y1, X1 - 2, Y1,
            "H", tail[2][0], "L", tail[1][0], tail[1][1], "L", tail[0][0], Y1, "H", X0 + 2, "Q", X0, Y1, X0, Y1 - 2,
            "V", Y0 + 2, "Q", X0, Y0, X0 + 2, Y0, "Z")
    c.drop(bub)
    c.shape(bub, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (1, "#DCE6F2")), line="#5B6B82")
    letter_a(c, (X0 + X1) / 2, Y1 - 3 if px > 16 else Y1 - lw, (Y1 - Y0) * (0.62 if px > 16 else 0.75),
             c.lin(0, Y0, 0, Y1, (0, "#FF8A66"), (1, "#B32213")), "#86190E")


@icon("apps", "system-software-install")
def _install(c):
    lw, px = c.lw, c.px
    x0, y0, x1, y1, dx, dy = 5, 24, 33, 44, 9, 8
    X0, Y0, X1, Y1 = c.sbox(x0, y0, x1, y1)
    DX, DY = c.sx(x1 + dx) - X1, Y0 - c.sy(y0 - dy)
    sil = poly([(X0, Y1), (X0, Y0), (X0 + DX, Y0 - DY), (X1 + DX, Y0 - DY), (X1 + DX, Y1 - DY), (X1, Y1)])
    c.drop(sil)
    fl = 8 if px > 16 else 7
    back = poly([(X0 + DX, Y0 - DY), (X1 + DX, Y0 - DY), (X1 + DX + 2, Y0 - DY - fl), (X0 + DX + 2, Y0 - DY - fl)])
    left = poly([(X0, Y0), (X0 + DX, Y0 - DY), (X0 + DX - fl, Y0 - DY - fl * 0.5), (X0 - fl, Y0 - fl * 0.5)])
    c.shape(back, c.lin(0, Y0 - DY - fl, 0, Y0 - DY, (0, BROWN.light), (1, BROWN.base)), line=BROWN.line)
    c.shape(left, c.lin(X0 - fl, 0, X0 + DX, 0, (0, BROWN.light), (1, BROWN.dark)), line=BROWN.line)
    top = poly([(X0, Y0), (X0 + DX, Y0 - DY), (X1 + DX, Y0 - DY), (X1, Y0)])
    c.path(top, c.lin(0, Y0 - DY, 0, Y0, (0, "#4A2E10"), (1, "#8A6030")))
    # disc going in
    with c.clipped(d("M", 0, 0, "H", 48, "V", Y0 - lw * 0.5, "H", 0, "Z") + " " + top):
        disc(c, 23, 15, 11 if px > 16 else 12, shadow=False)
    side = poly([(X1, Y0), (X1 + DX, Y0 - DY), (X1 + DX, Y1 - DY), (X1, Y1)])
    c.path(side, c.lin(X1, 0, X1 + DX, 0, (0, BROWN.dark), (1, dk(BROWN.dark, 0.15))))
    c.path(rr(X0, Y0, X1, Y1, 0), c.lin(X0, Y0, X1, Y1, (0, BROWN.light), (1, BROWN.base)))
    c.outline(sil, BROWN.line)
    right = poly([(X1, Y0), (X1 + DX, Y0 - DY), (X1 + DX + fl, Y0 - DY + 1), (X1 + fl, Y0 + 1)])
    c.shape(right, c.lin(X1, 0, X1 + DX + fl, 0, (0, BROWN.base), (1, BROWN.light)), line=BROWN.line)
    front = poly([(X0, Y0), (X1, Y0), (X1 - 1, Y0 + fl * 0.9), (X0 - 1, Y0 + fl * 0.9)])
    c.shape(front, c.lin(0, Y0, 0, Y0 + fl, (0, lt(BROWN.light, 0.3)), (1, BROWN.light)), line=BROWN.line)
    # green arrow
    if px > 16:
        with c.place(26, 26, 22):
            from glyphs import e_down
            e_down(c)


@icon("apps", "utilities-system-monitor")
def _sysmon(c):
    lw, px = c.lw, c.px

    def graph(c, box):
        X0, Y0, X1, Y1 = box
        w, h = X1 - X0, Y1 - Y0
        c.path(rr(X0, Y0, X1, Y1, 0), "#06140A")
        if px > 16:
            n = 4
            for i in range(1, n):
                x = c.sx(X0 + w * i / n)
                y = c.sy(Y0 + h * i / n)
                c.path(rr(x, Y0, x + lw, Y1, 0), "#1E5A2A", op=0.8)
                c.path(rr(X0, y, X1, y + lw, 0), "#1E5A2A", op=0.8)
        vals = [0.7, 0.55, 0.62, 0.3, 0.45, 0.2, 0.38, 0.25, 0.5, 0.35]
        pts = [(X0 + w * i / (len(vals) - 1), Y0 + h * v) for i, v in enumerate(vals)]
        c.path(poly(pts + [(X1, Y1), (X0, Y1)]), "#38E04A", op=0.25)
        c.line(pts, "#5CFF6A", w=1.2 if px > 16 else 1.0)

    crt(c, 3, 5, 41, 35, screen=graph, screen_cols=("#123A1C", "#06140A", "#06140A"))


@icon("apps", "multimedia-volume-control")
def _volctl(c):
    lw, px = c.lw, c.px
    speaker(c, 18, 25, 0.9 if px > 16 else 0.95)
    if px > 16:
        waves(c, 20, 25, 2, s=0.85)
    tx = c.sx(40)
    t0, t1 = c.sy(5), c.sy(45)
    gw = lw if px <= 24 else 1.5 * lw
    c.path(rr(tx - gw, t0, tx + gw, t1, gw), "#3C4350")
    c.path(rr(tx, t0 + lw, tx + gw, t1 - lw, 0), "#FFFFFF", op=0.5)
    kh = (2 if px <= 16 else 3) * lw if px <= 24 else 6
    ky = c.sy(18)
    k = rr(c.sx(34), ky, c.sx(46), ky + kh, 0.6 * lw if px > 16 else 0)
    c.drop(k)
    c.shape(k, c.lin(0, ky, 0, ky + kh, (0, "#E6F2FF"), (1, "#6E9BD8")), line="#1F3F7A",
            hl=c.hl_grad(0, ky, 0, ky + kh, 0.8, 0) if px > 24 else None)


@icon("apps", "multimedia-player")
def _player(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(3, 5, 41, 35)
    tv = rr(X0, Y0, X1, Y1, 3 if px > 16 else lw)
    c.drop(tv)
    c.shape(tv, c.lin(X0, Y0, X1, Y1, (0, "#6A7C9A"), (0.5, "#2C3A55"), (1, "#151D2E")), line="#0C1220",
            hl=c.hl_grad(X0, Y0, X1, Y1, 0.6, 0))
    m = 2 * lw if px <= 24 else 3
    scr = rr(X0 + m, Y0 + m, X1 - m, Y1 - m, 1 if px > 16 else 0)
    c.path(scr, c.lin(X0, Y0, X1, Y1, (0, "#2A6ED8"), (0.6, "#123C8C"), (1, "#0A1E4C")))
    if px > 16:
        with c.clipped(scr):
            c.path(ell(X0 + 6, Y0 + 2, 26, 12), "#FFFFFF", op=0.12)
            eq_bars(c, X0 + m + 3, Y1 - m - 12, X0 + 20, Y1 - m - 2)
    with c.place(c.sx(19), c.sy(19), 29):
        orb(c, ORANGE)
        tri = rounded_poly([(17, 12), (34, 23), (17, 34)], 2)
        white_mark(c, tri, ORANGE)


def eq_bars(c, x0, y0, x1, y1):
    n = 5
    bw = (x1 - x0) / n
    for i, v in enumerate((0.5, 0.8, 0.35, 0.95, 0.6)):
        c.path(rr(x0 + i * bw, y1 - (y1 - y0) * v, x0 + (i + 0.7) * bw, y1, 0),
               c.lin(0, y0, 0, y1, (0, "#B8FF9A"), (1, "#2FBF3A")), op=0.9)


@icon("apps", "image-viewer")
def _imgview(c):
    e_picture(c, 2, 4, 38, 34)
    magnifier(c, 31, 30, 8.5, 45, 9)


@icon("apps", "internet-web-browser")
def _browser(c):
    lw, px = c.lw, c.px
    cx, cy, r = 23, 25, 17
    ring = ell(0, 0, 22, 8.5)
    rw = 3.0 if px > 24 else 3.6 if px > 16 else 4.6
    tf = 'translate(%s %s) rotate(-28)' % (cx, cy)

    def ring_part(clip_top):
        c.add('<g transform="%s">' % tf)
        with c.clipped(rr(-30, -14 if clip_top else 0, 30, 0 if clip_top else 14, 0)):
            c.path(ring, "none", stroke="#8A3A06", sw=rw + 2 * lw)
            c.path(ring, "none", stroke=c.lin(-22, -8, 22, 8, (0, "#FFE08A"), (0.5, "#FF9A1E"), (1, "#D9600A")),
                   sw=rw)
        c.add("</g>")
    ring_part(True)
    globe(c, cx, cy, r)
    ring_part(False)


@icon("apps", "mail-client")
def _mail(c):
    if c.px > 16:
        c.add('<g transform="rotate(-9 24 20)">')
        envelope(c, 7, 6, 41, 28)
        c.add("</g>")
        envelope(c, 3, 17, 45, 43, stamp=True)
    else:
        envelope(c, 3, 11, 45, 39, stamp=True)


@icon("apps", "accessories-screenshot")
def _screenshot(c):
    lw, px = c.lw, c.px

    def sel(c, box):
        X0, Y0, X1, Y1 = box
        w, h = X1 - X0, Y1 - Y0
        c.path(rr(X0, Y0, X1, Y1, 0), "#FFFFFF")
        a0, b0 = c.sx(X0 + w * 0.15) + lw / 2, c.sy(Y0 + h * 0.18) + lw / 2
        a1, b1 = c.sx(X0 + w * 0.8) - lw / 2, c.sy(Y0 + h * 0.8) - lw / 2
        c.path(rr(a0, b0, a1, b1, 0), "#D7E7FF", stroke="#2F6FE0", sw=lw,
               dash="%g %g" % (2 * lw, 1.5 * lw) if px > 16 else "%g %g" % (lw, lw))

    window(c, 2, 3, 40, 35, content=sel)
    with c.place(c.sx(19), c.sy(21), 28):
        camera_small(c)


def camera_small(c):
    lw = c.lw
    body = rr(4, 14, 44, 40, 4)
    c.drop(body)
    c.shape(rr(10, 9, 22, 16, 1.5), c.lin(0, 9, 0, 16, (0, "#E6EAF0"), (1, "#8E98A6")), line="#3E4552")
    c.shape(body, c.lin(0, 14, 0, 40, (0, "#F5F7FA"), (0.5, "#B3BCC8"), (1, "#7C8796")), line="#3E4552")
    c.shape(circ(24, 27, 10), c.lin(14, 17, 34, 37, (0, "#FFFFFF"), (1, "#5E6774")), line="#3E4552")
    c.path(circ(24, 27, 7), c.rad(22, 25, 8, (0, "#7FB2FF"), (0.5, "#1F3C7A"), (1, "#0B0E14")))
    c.path(ell(22, 24.5, 2.2, 1.4), "#FFFFFF", op=0.8)


@icon("apps", "system-file-manager")
def _fileman(c):
    folder(c)
    lw = c.lw
    if c.px > 16:
        magnifier(c, 30, 28, 8, 45, 8)
    else:
        magnifier(c, 30, 27, 9, 45, 9)
