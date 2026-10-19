import math

from glyphs import orb, person, rounded_poly, sym_excl, sym_i, sym_q, x_mark
from lib import GREEN, RED, Ramp, circ, d, dk, ell, poly, rr
from objects import battery, crt, speaker, waves
from registry import icon


def bubble_path(cx=24, cy=21, r=18, tip=(6, 45)):
    a1, a2 = math.radians(112), math.radians(150)
    p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    p2 = (cx + r * math.cos(a2), cy + r * math.sin(a2))
    return d("M", p1[0], p1[1], "A", r, r, 0, 1, 0, p2[0], p2[1],
             "Q", p2[0] - 1.0, p2[1] + 8, tip[0], tip[1], "Q", p1[0] - 5, p1[1] + 3, p1[0], p1[1], "Z")


def bubble(c, ramp):
    px = c.px
    if px <= 16:
        cx, cy, r, tip = 24, 21, 19.5, (4.5, 46)
    else:
        cx, cy, r, tip = 24, 21, 18.5, (6, 45)
    p = bubble_path(cx, cy, r, tip)
    c.drop(p, op=0.25)
    body = c.rad(cx - 0.1 * r, cy + 0.45 * r, 1.35 * r, (0, ramp.light), (0.45, ramp.base), (1, ramp.dark))
    c.shape(p, body, line=ramp.line)
    hl = c.lin(0, cy - r, 0, cy + 0.05 * r, (0, "#FFFFFF", 0.92), (1, "#FFFFFF", 0.08))
    c.path(ell(cx, cy - 0.43 * r, 0.74 * r, 0.5 * r), hl)
    return cx, cy


INFO = Ramp("#E6F2FF", "#86C0FF", "#2F74E0", "#1A4CB4", "#123A8C")


@icon("status", "dialog-information")
def _info(c):
    cx, cy = bubble(c, INFO)
    sym_i(c, cx, cy + 1, s=1.0 if c.px > 16 else 1.05, line=dk(INFO.line, 0.1) if c.px > 24 else None)


@icon("status", "dialog-question")
def _question(c):
    cx, cy = bubble(c, INFO)
    sym_q(c, cx, cy - 1, s=1.0 if c.px > 16 else 1.1, line=dk(INFO.line, 0.1) if c.px > 24 else None)


@icon("status", "dialog-error")
def _error(c):
    orb(c, RED)
    px = c.px
    t = 3.6 if px > 24 else 4.4 if px > 16 else 5.6
    x_mark(c, RED, L=12, t=t)


@icon("status", "dialog-warning")
def _warning(c):
    px = c.px
    pts = [(24, 3), (45.5, 41.5), (2.5, 41.5)] if px > 16 else [(24, 2), (47, 43), (1, 43)]
    tri = rounded_poly(pts, 4.5 if px > 16 else 3)
    c.drop(tri, op=0.25)
    c.shape(tri, c.lin(14, 6, 34, 44, (0, "#FFF4B0"), (0.35, "#FFD84A"), (1, "#E9A40E")), line="#A87308",
            hl=c.lin(0, 4, 0, 30, (0, "#FFFFFF", 0.9), (1, "#FFFFFF", 0.1)))
    sym_excl(c, 24, 26.5 if px > 16 else 27.5, s=1.0 if px > 16 else 1.15, col="#1E1A10")


# --------------------------------------------------------------- tray: audio

def vol(c, n, muted=False):
    px = c.px
    s = 0.95 if px > 16 else 1.0
    speaker(c, 18 if px > 16 else 17, 24, s)
    if n:
        waves(c, 21, 24, n, s=0.95 if px > 16 else 1.0,
              r0=8 if px > 16 else 9, gap=7.5 if px > 16 else 9)
    if muted:
        with c.place(c.sx(20), c.sy(20), 28):
            no_sign(c)


def no_sign(c):
    lw = c.lw
    w = 6.5 if c.px > 12 else 9
    ring = circ(24, 24, 17)
    c.drop(ring, op=0.25)
    c.path(ring, "none", stroke=RED.line, sw=w + 2 * lw)
    c.line([(12.5, 12.5), (35.5, 35.5)], RED.line, w=(w + 2 * lw) / lw, cap="butt")
    c.path(ring, "none", stroke=c.lin(0, 6, 0, 42, (0, RED.light), (1, RED.base)), sw=w)
    c.line([(12.5, 12.5), (35.5, 35.5)], RED.base, w=w / lw, cap="butt")


@icon("status", "audio-volume-high")
def _vh(c):
    vol(c, 3)


@icon("status", "audio-volume-medium")
def _vm(c):
    vol(c, 2)


@icon("status", "audio-volume-low")
def _vl(c):
    vol(c, 1)


@icon("status", "audio-volume-muted")
def _vmute(c):
    vol(c, 0, muted=True)


# ------------------------------------------------------------- tray: network

IDLE = ("#5FA6E8", "#1F64B8", "#17508E")
ACTIVE = ("#F2FFFF", "#8FE4FF", "#3FB3F0")
OFF = ("#8A94A2", "#5C6672", "#4A525C")


def two_monitors(c, back, front):
    px = c.px
    if px <= 16:
        crt(c, 0, 3, 27, 27, stand=True, screen_cols=back, depth=3)
        crt(c, 18, 15, 45, 39, stand=True, screen_cols=front, depth=3)
    else:
        crt(c, 2, 3, 28, 26, screen_cols=back)
        crt(c, 18, 16, 44, 39, screen_cols=front)


@icon("status", "network-idle")
def _nidle(c):
    two_monitors(c, IDLE, IDLE)


@icon("status", "network-wired")
def _nwired(c):
    two_monitors(c, IDLE, IDLE)


@icon("status", "network-transmit-receive")
def _ntr(c):
    two_monitors(c, ACTIVE, ACTIVE)


@icon("status", "network-offline")
def _noff(c):
    two_monitors(c, OFF, OFF)
    with c.place(c.sx(22), c.sy(22), 26):
        orb(c, RED, 23, 23, 20)
        x_mark(c, RED, L=11.5, t=4.5)


@icon("status", "network-wireless")
def _nwifi(c):
    px = c.px
    crt(c, 2, 16, 30, 40, screen_cols=IDLE) if px > 16 else crt(c, 0, 15, 30, 40, screen_cols=IDLE, depth=3)
    waves_g = ("#C8FFB0", "#3DAA2B")
    with c.place(c.sx(18), c.sy(0), 30):
        lw = c.lw
        cx, cy = 10, 38
        for i, R in enumerate((12, 23, 34)):
            pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
                   for a in range(-88, -1, 4)]
            w = 5.5 if c.px > 16 else 7.5
            c.path(poly(pts, close=False), "none", stroke="#1C6314", sw=w + 2 * lw * 0.8, cap="round")
            c.path(poly(pts, close=False), "none", stroke=c.lin(0, cy - R, 0, cy, (0, waves_g[0]), (1, waves_g[1])),
                   sw=w, cap="round")


# ---------------------------------------------------------------- battery

@icon("status", "battery-full")
def _bfull(c):
    battery(c, 1.0, GREEN)


@icon("status", "battery-low")
def _blow(c):
    battery(c, 0.18, RED)


# ------------------------------------------------------------------ misc

@icon("status", "avatar-default")
def _avatar(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(3, 3, 45, 45)
    fr = rr(X0, Y0, X1, Y1, 5 if px > 16 else 2 * lw)
    c.drop(fr)
    c.shape(fr, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (1, "#D5DCE6")), line="#5B6B82")
    m = 2 * lw if px <= 24 else 3
    inner = rr(X0 + m, Y0 + m, X1 - m, Y1 - m, max(0, (5 if px > 16 else 2 * lw) - m))
    with c.clipped(inner):
        c.path(rr(X0, Y0, X1, Y1, 0), c.lin(0, Y0, 0, Y1, (0, "#3C86E8"), (0.6, "#8CC8FF"), (1, "#D8F0FF")))
        person(c, 24, 21, 1.45, Ramp("#FFF0D0", "#FFC060", "#F68B1F", "#CC5F0B", "#93450B"))
    c.outline(inner, "#4E6A94", w=0.8)


@icon("status", "image-missing")
def _missing(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(3, 6, 41, 38)
    frame = rr(X0, Y0, X1, Y1, 0.5 * lw)
    c.drop(frame)
    c.shape(frame, c.lin(X0, Y0, X1, Y1, (0, "#FFFFFF"), (1, "#DDE3EA")), line="#7A8696")
    m = 2 * lw if px <= 24 else 3.5
    inner = rr(X0 + m, Y0 + m, X1 - m, Y1 - m, 0)
    c.path(inner, c.lin(0, Y0, 0, Y1, (0, "#D9DEE5"), (1, "#AEB6C2")))
    with c.clipped(inner):
        c.path(d("M", X0, Y1 - 6, "L", X0 + 12, Y1 - 16, "L", X0 + 20, Y1 - 9, "L", X0 + 27, Y1 - 14, "L", X1,
                 Y1 - 6, "V", Y1, "H", X0, "Z"), "#8D97A5")
    c.outline(inner, "#7A8696", w=0.7)
    with c.place(c.sx(20), c.sy(20), 28):
        orb(c, RED, 23, 23, 20)
        x_mark(c, RED, L=11.5, t=4.5)


@icon("status", "battery-good")
def _bgood(c):
    battery(c, 0.6, GREEN)


@icon("status", "battery-caution")
def _bcaution(c):
    battery(c, 0.32, Ramp("#FFF0D0", "#FFC060", "#F68B1F", "#CC5F0B", "#93450B"))
