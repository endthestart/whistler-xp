from glyphs import (e_doc, e_down, e_film, e_globe, e_house, e_note, e_people, e_picture, e_template, folder,
                    globe, orb)
from lib import BEIGE, GREEN, Ramp, d, dk, rr
from objects import crt, tower, trash_bin
from registry import icon


@icon("places", "folder")
def _folder(c):
    folder(c)


@icon("places", "folder-open")
def _folder_open(c):
    folder(c, open_=True)


@icon("places", "folder-documents")
def _docs(c):
    folder(c, emblem=e_doc)


@icon("places", "folder-pictures")
def _pics(c):
    folder(c, emblem=e_picture)


@icon("places", "folder-music")
def _music(c):
    folder(c, emblem=e_note)


@icon("places", "folder-videos")
def _videos(c):
    folder(c, emblem=e_film)


@icon("places", "folder-download")
def _download(c):
    folder(c, emblem=e_down)


@icon("places", "folder-publicshare")
def _public(c):
    folder(c, emblem=e_people)


@icon("places", "folder-remote")
def _remote(c):
    folder(c, emblem=e_globe)


@icon("places", "folder-templates")
def _templates(c):
    folder(c, emblem=e_template)


@icon("places", "user-home")
def _home(c):
    folder(c, emblem=e_house)


def mini_desktop(c, X0, Y0, X1, Y1):
    """A tiny desktop: sky wallpaper, icons and a taskbar (inside a clip)."""
    lw, px = c.lw, c.px
    w, h = X1 - X0, Y1 - Y0
    c.path(rr(X0, Y0, X1, Y1, 0), c.lin(0, Y0, 0, Y1, (0, "#2B6FD8"), (0.55, "#6BB2F5"), (1, "#B7E0FF")))
    c.path(d("M", X0, Y0 + h * 0.78, "C", X0 + w * 0.3, Y0 + h * 0.6, X0 + w * 0.65, Y0 + h * 0.62, X1,
             Y0 + h * 0.74, "V", Y1, "H", X0, "Z"), c.lin(0, Y0 + h * 0.6, 0, Y1, (0, "#6CC24A"), (1, "#2F8A2A")))
    tb = max(lw, c.sy(Y1) - c.sy(Y1 - h * 0.14))
    c.path(rr(X0, Y1 - tb, X1, Y1, 0), c.lin(0, Y1 - tb, 0, Y1, (0, "#4A90F5"), (1, "#1A4FC8")))
    sw = max(2 * lw, c.sx(X0 + w * 0.22) - X0)
    c.path(rr(X0, Y1 - tb, X0 + sw, Y1, min(tb / 2, 2)), c.lin(0, Y1 - tb, 0, Y1, (0, "#7FD46A"), (1, "#2F9628")))
    if px * w / 48 > 14:
        ix = c.sx(X0 + w * 0.08)
        isz = max(2 * lw, c.sx(w * 0.12) - c.sx(0))
        for i, col in enumerate(("#F6CF5C", "#FFFFFF", "#7FC4FF")):
            iy = c.sy(Y0 + h * 0.1 + i * (isz + 2 * lw))
            if iy + isz < Y1 - tb - lw:
                c.path(rr(ix, iy, ix + isz, iy + isz, 0.4 * lw), col, stroke=dk(col, 0.4), sw=0.7 * lw)


@icon("places", "user-desktop")
def _desktop(c):
    lw, px = c.lw, c.px
    X0, Y0, X1, Y1 = c.sbox(3, 8, 45, 40)
    if px <= 16:
        X0, Y0, X1, Y1 = c.sbox(3, 9, 45, 39)
    frame = rr(X0, Y0, X1, Y1, 1.5 if px > 24 else 0.5 * lw)
    c.drop(frame)
    c.shape(frame, c.lin(X0, Y0, X1, Y1, (0, "#F2F4F8"), (1, "#9EA9B8")), line="#4C5668")
    m = lw if px <= 24 else 2 * lw
    with c.clipped(rr(X0 + m, Y0 + m, X1 - m, Y1 - m, 0)):
        mini_desktop(c, X0 + m, Y0 + m, X1 - m, Y1 - m)
    if px > 16:
        c.outline(rr(X0 + m, Y0 + m, X1 - m, Y1 - m, 0), "#3A4658", w=0.6)


@icon("places", "network-workgroup")
def _workgroup(c):
    px = c.px
    lw = c.lw
    # cable
    cable = d("M", 12, 27, "C", 11, 40, 22, 45, 32, 40)
    c.path(cable, "none", stroke="#2F3742", sw=(2.6 if px > 24 else 2.0) * lw if px <= 24 else 2.6, cap="round")
    c.path(cable, "none", stroke="#8A94A3", sw=0.9 * lw if px > 24 else 0.7 * lw, cap="round")
    crt(c, 1, 4, 25, 23, ramp=BEIGE)
    crt(c, 20, 17, 44, 36, ramp=BEIGE)


@icon("places", "network-server")
def _server(c):
    srv = Ramp("#F4F7FB", "#DCE2EA", "#B5BFCC", "#8793A4", "#4F5A6A")
    tower(c, 14, 8, 34, 44, 7, 5, ramp=srv, server=True)
    with c.place(0, 22, 26):
        globe(c, 24, 24, 19)


@icon("places", "user-trash")
def _trash(c):
    trash_bin(c, full=False)


@icon("places", "user-trash-full")
def _trash_full(c):
    trash_bin(c, full=True)


def gust(c, cx=23, cy=23):
    """White wind-gust swirl for start-here."""
    lw, px = c.lw, c.px
    w = 3.6 if px > 24 else 4.2 if px > 16 else 5.0
    if px <= 16:
        paths = [d("M", 9, 18, "H", 27, "C", 33, 18, 33, 10, 28, 10),
                 d("M", 9, 29, "H", 31, "C", 37, 29, 37, 37, 32, 37)]
        for p in paths:
            c.path(p, "none", stroke="#FFFFFF", sw=w, cap="round", join="round")
        return
    paths = [
        d("M", 9, 19, "H", 26, "C", 32, 19, 33, 11, 27.5, 10.5, "C", 24, 10.2, 23, 13.5, 25, 15),
        d("M", 9, 27, "H", 31, "C", 38, 27, 39, 36, 32.5, 36.5, "C", 29, 36.8, 28, 33.5, 30, 32),
    ]
    if px > 24:
        paths.append(d("M", 13, 23, "H", 35))
    for p in paths:
        c.path(p, "none", stroke="#1C6314", sw=w + 1.6 * lw, cap="round", join="round", op=0.55)
        c.path(p, "none", stroke="#FFFFFF", sw=w, cap="round", join="round")


@icon("places", "start-here")
def _start(c):
    orb(c, GREEN)
    gust(c)
