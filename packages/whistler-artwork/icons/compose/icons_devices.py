
from glyphs import orb, rounded_poly, text_lines
from icons_places import gust
from lib import BEIGE, GREEN, Ramp, circ, d, ell, poly, rot, rr
from objects import box3d, crt, disc, drive_box, floppy, keyboard, printer, tower
from registry import icon

GRAPHITE = Ramp("#A9B1BD", "#7C8592", "#59616E", "#3C424C", "#22262D")


@icon("devices", "computer")
def _computer(c):
    tower(c, 27, 6, 40, 41, 5, 4)
    crt(c, 3, 12, 30, 33)


@icon("devices", "video-display")
def _display(c):
    crt(c, 4, 6, 40, 34)


@icon("devices", "drive-harddisk")
def _hdd(c):
    drive_box(c)


@icon("devices", "drive-harddisk-system")
def _hdd_sys(c):
    b = drive_box(c)
    if c.px > 16:
        with c.place(c.sx(6), c.sy(4), 22):
            orb(c, GREEN)
            gust(c)
    else:
        with c.place(c.sx(3), c.sy(3), 24):
            orb(c, GREEN)


@icon("devices", "drive-optical")
def _optical(c):
    b = drive_box(c, x0=9, y0=25, x1=41, y1=37, dx=5, dy=10, label=False)
    lw = c.lw
    if c.px > 16:
        disc(c, 15, 22, 13)
    else:
        disc(c, 15, 21, 14)


@icon("devices", "drive-removable-media")
def _removable(c):
    lw, px = c.lw, c.px
    drive_box(c, x0=11, y0=24, x1=41, y1=37, dx=5, dy=10, label=False)
    # memory card in front
    pts = [(4, 12), (19, 12), (24, 17), (24, 43), (4, 43)]
    if px <= 16:
        pts = [(3, 12), (18, 12), (24, 18), (24, 45), (3, 45)]
    card = rounded_poly(rot(pts, 14, 28, -10), 1.0)
    c.drop(card)
    c.shape(card, c.lin(4, 12, 24, 43, (0, "#7DB3FF"), (0.5, "#2F6FE0"), (1, "#1C45A8")), line="#132F78",
            hl=c.hl_grad(4, 12, 24, 30, 0.6, 0))
    if px > 16:
        for i in range(4):
            x = 6.5 + i * 3.3
            g = poly(rot([(x, 13.5), (x + 2, 13.5), (x + 2, 19), (x, 19)], 14, 28, -10))
            c.path(g, c.lin(0, 13, 0, 19, (0, "#FFF2A8"), (1, "#C99A1C")))
        lab = poly(rot([(7, 26), (21, 26), (21, 40), (7, 40)], 14, 28, -10))
        c.shape(lab, c.lin(0, 26, 0, 40, (0, "#FFFFFF"), (1, "#DCE6F5")), line="#5577B8")
    else:
        lab = poly(rot([(7, 28), (21, 28), (21, 40), (7, 40)], 14, 28, -10))
        c.path(lab, "#FFFFFF", op=0.9)


@icon("devices", "drive-removable-media-usb")
def _usb(c):
    lw, px = c.lw, c.px
    ang = -32
    cx, cy = 24, 25
    body = rr(4, 18, 32, 31, 4)
    conn = rr(31, 19.5, 44, 29.5, 0.6)
    if px <= 16:
        body = rr(3, 17, 32, 32, 3)
        conn = rr(31, 19, 45, 30, 0)
    c.add('<g transform="rotate(%d %d %d)">' % (ang, cx, cy))
    c.drop(body)
    c.drop(conn)
    c.shape(conn, c.lin(0, 19, 0, 30, (0, "#FFFFFF"), (0.5, "#C9D0D9"), (1, "#8C96A4")), line="#535C68")
    if px > 16:
        for x in (35, 39.5):
            c.path(rr(x, 22, x + 2.4, 24.4, 0.2), "#3A414C")
    c.shape(body, c.lin(0, 17, 0, 32, (0, "#8FC2FF"), (0.45, "#2E76E6"), (1, "#173F9E")), line="#122F78",
            hl=c.lin(0, 17, 0, 24, (0, "#FFFFFF", 0.7), (1, "#FFFFFF", 0)))
    if px > 20:
        c.path(rr(7, 21, 27, 23.5, 1.2), "#FFFFFF", op=0.35)
        c.path(circ(9, 27.5, 1.2), "#4BF03C")
        c.path(circ(9, 24.5, 3.0), "none", stroke="#0E2A6E", sw=1.2)
    c.add("</g>")


@icon("devices", "media-floppy")
def _floppy(c):
    floppy(c)


@icon("devices", "media-optical")
def _media_optical(c):
    disc(c, 23, 23, 20)


@icon("devices", "printer")
def _printer(c):
    printer(c)


@icon("devices", "audio-speakers")
def _speakers(c):
    lw, px = c.lw, c.px

    def spk(x0, y0, x1, y1, dx, dy):
        b = box3d(c, x0, y0, x1, y1, dx, dy,
                  c.lin(x0, y0, x1, y1, (0, GRAPHITE.light), (1, GRAPHITE.dark)),
                  c.lin(x0, y0 - dy, x1 + dx, y0, (0, GRAPHITE.hi), (1, GRAPHITE.light)),
                  GRAPHITE.dark, GRAPHITE.line)
        X0, Y0, X1, Y1 = b["X0"], b["Y0"], b["X1"], b["Y1"]
        w, h = X1 - X0, Y1 - Y0
        cx = (X0 + X1) / 2
        rw = w * 0.36
        wy = Y1 - h * 0.3
        c.shape(circ(cx, wy, rw), c.rad(cx - rw * 0.2, wy - rw * 0.2, rw, (0, "#5A6270"), (0.7, "#1C2027"),
                                          (1, "#0C0E12")), line="#B9C1CC" if px > 16 else "#0C0E12")
        if px > 20:
            c.path(circ(cx, wy, rw * 0.3), c.rad(cx - 1, wy - 1, rw * 0.35, (0, "#8A93A0"), (1, "#2A2F38")))
            tr = w * 0.15
            ty = Y0 + h * 0.25
            c.shape(circ(cx, ty, tr), c.rad(cx - 0.5, ty - 0.5, tr, (0, "#6A7280"), (1, "#14171C")),
                    line="#B9C1CC")
    spk(26, 12, 40, 41, 5, 4)
    spk(5, 9, 21, 43, 5, 4)


@icon("devices", "input-keyboard")
def _keyboard(c):
    keyboard(c, 2, 16, 40, 36, 6)


@icon("devices", "input-mouse")
def _mouse(c):
    lw, px = c.lw, c.px
    cable = d("M", 24, 13, "C", 24, 6, 32, 3, 38, 6, "C", 43, 9, 42, 14, 45, 15)
    c.path(cable, "none", stroke="#6E6650", sw=2.2 if px > 24 else 1.4 * lw, cap="round")
    c.path(cable, "none", stroke="#D9D1BA", sw=1.0 if px > 24 else 0.5 * lw, cap="round")
    body = d("M", 24, 12, "C", 34, 12, 37, 20, 37, 29, "C", 37, 39, 31, 45, 24, 45, "C", 17, 45, 11, 39, 11, 29,
             "C", 11, 20, 14, 12, 24, 12, "Z")
    c.drop(body)
    c.shape(body, c.rad(19, 20, 26, (0, BEIGE.hi), (0.5, BEIGE.light), (1, BEIGE.dark)), line=BEIGE.line)
    with c.clipped(body):
        c.line([(10, 26), (38, 26)], BEIGE.line, w=1.0, op=0.8)
        c.line([(24, 10), (24, 26)], BEIGE.line, w=1.0, op=0.8)
        c.path(rr(10, 10, 24, 26, 0), "#FFFFFF", op=0.25)
    if px > 16:
        c.shape(rr(22, 15, 26, 22, 2), c.lin(0, 15, 0, 22, (0, "#8E8E96"), (1, "#3A3A42")), line="#2A2A30")
    else:
        c.path(rr(c.sx(22), c.sy(15), c.sx(25), c.sy(21), 0), "#4A4A52")


@icon("devices", "camera-photo")
def _camera(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(3, 14, 45, 40)
    top = rounded_poly([(c.sx(9), Y0 + lw), (c.sx(11), c.sy(9)), (c.sx(21), c.sy(9)), (c.sx(23), Y0 + lw)], 1.0)
    body = rr(X0, Y0, X1, Y1, 3 if px > 16 else lw)
    c.drop(body)
    c.drop(top)
    c.shape(top, c.lin(0, 9, 0, 15, (0, "#E6EAF0"), (1, "#8E98A6")), line="#4C5563")
    if px > 16:
        c.shape(rr(c.sx(32), c.sy(10), c.sx(39), Y0 + lw, 0.8), c.lin(0, 10, 0, 14, (0, "#FF8A6A"), (1, "#C42E18")),
                line="#7A1B0E")
    c.shape(body, c.lin(X0, Y0, X0, Y1, (0, "#F5F7FA"), (0.45, "#CED5DE"), (0.5, "#B3BCC8"), (1, "#8994A3")),
            line="#4C5563", hl=c.hl_grad(0, Y0, 0, Y0 + 6, 0.9, 0))
    # grip band
    c.path(rr(X0 + lw, c.sy(31), X1 - lw, Y1 - lw, 0), "#3A414C", op=0.25)
    # flash
    if px > 16:
        fl = rr(c.sx(34), c.sy(17), c.sx(42), c.sy(22), 0.6)
        c.shape(fl, c.lin(0, 17, 0, 22, (0, "#FFFFFF"), (1, "#D5DCE6")), line="#6A7484")
    # lens
    lx, ly, lr = 21, 27, 10.5 if px > 16 else 11
    c.shape(circ(lx, ly, lr), c.lin(lx - lr, ly - lr, lx + lr, ly + lr, (0, "#FFFFFF"), (0.5, "#A6AFBC"),
                                    (1, "#5E6774")), line="#3E4552")
    c.shape(circ(lx, ly, lr * 0.72), c.rad(lx, ly, lr * 0.72, (0, "#2B3445"), (1, "#0B0E14")), line="#0B0E14")
    c.path(circ(lx, ly, lr * 0.45), c.rad(lx - 2, ly - 2, lr * 0.5, (0, "#7FB2FF"), (0.6, "#2A4C9A"),
                                          (1, "#101C3A")))
    c.path(ell(lx - lr * 0.22, ly - lr * 0.25, lr * 0.2, lr * 0.13), "#FFFFFF", op=0.85)


@icon("devices", "phone")
def _phone(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(13, 5, 35, 45)
    ant = rr(c.sx(29), c.sy(1), c.sx(33), Y0 + 2, 1)
    c.drop(ant)
    c.shape(ant, c.lin(c.sx(29), 0, c.sx(33), 0, (0, "#6A7280"), (1, "#2A2F38")), line="#1E2228")
    body = rr(X0, Y0, X1, Y1, 4 if px > 16 else lw)
    c.drop(body)
    c.shape(body, c.lin(X0, Y0, X1, Y1, (0, "#E9EEF5"), (0.5, "#A9B6C8"), (1, "#6C7A90")), line="#3B4658",
            hl=c.hl_grad(X0, Y0, X1, Y1, 0.9, 0.0))
    m = 2 * lw if px <= 24 else 3
    sx0, sy0, sx1 = X0 + m, c.sy(Y0 + (5 if px > 16 else 2 * lw)), X1 - m
    sy1 = c.sy(Y0 + (Y1 - Y0) * 0.42)
    scr = rr(sx0, sy0, sx1, sy1, 0.5 if px > 16 else 0)
    c.shape(scr, c.lin(0, sy0, 0, sy1, (0, "#B9F0E6"), (1, "#3FA8B8")), line="#24364A")
    if px > 20:
        text_lines(c, sx0 + 2 * lw, sy0 + 3 * lw, sx1 - 2 * lw, sy1 - 2 * lw, col="#1F5A68",
                   widths=(0.7, 1, 0.5))
    ky0 = sy1 + (2 * lw if px <= 24 else 3)
    ky1 = Y1 - m
    if px <= 16:
        for r_ in range(3):
            yy = c.sy(ky0 + r_ * 2 * lw)
            if yy + lw <= ky1:
                c.path(rr(sx0, yy, sx1, yy + lw, 0), "#F4F7FB")
        return
    cols, rows = 3, 4
    gx = (sx1 - sx0 + 1.2) / cols
    gy = (ky1 - ky0 + 1.2) / rows
    for r_ in range(rows):
        for q in range(cols):
            k = rr(sx0 + q * gx, ky0 + r_ * gy, sx0 + (q + 1) * gx - 1.2, ky0 + (r_ + 1) * gy - 1.2, 0.8)
            c.shape(k, c.lin(0, ky0 + r_ * gy, 0, ky0 + (r_ + 1) * gy, (0, "#FFFFFF"), (1, "#C9D2DE")),
                    line="#5B6A80")
