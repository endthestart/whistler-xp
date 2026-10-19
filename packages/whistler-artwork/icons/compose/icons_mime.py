from glyphs import e_film, e_note, e_picture, globe, page, page_with, text_lines
from lib import TEXT_LINE, d, ell, poly, rr
from objects import cardboard, window
from registry import icon


def page_text(c, X0, Y0, X1, Y1, fold, col=TEXT_LINE, bottom=None):
    lw, px = c.lw, c.px
    yb = Y1 - (2 * lw if px <= 24 else 5) if bottom is None else bottom
    if px <= 16:
        text_lines(c, X0 + 2 * lw, Y0 + 2 * lw, X1 - fold - lw, Y0 + 3 * lw, col=col, widths=(1,))
        text_lines(c, X0 + 2 * lw, Y0 + fold + lw, X1 - 2 * lw, yb, col=col)
    elif px <= 24:
        text_lines(c, X0 + 3 * lw, Y0 + 3 * lw, X1 - fold - 2 * lw, Y0 + fold, col=col, widths=(1, 0.7))
        text_lines(c, X0 + 3 * lw, Y0 + fold + 2 * lw, X1 - 3 * lw, yb, col=col)
    else:
        text_lines(c, X0 + 5, Y0 + 6, X1 - fold - 4, Y0 + fold, col=col, widths=(1, 0.7))
        text_lines(c, X0 + 5, Y0 + fold + 4, X1 - 5, yb, col=col)


@icon("mimetypes", "text-x-generic")
def _text(c):
    X0, Y0, X1, Y1, fold = page(c)
    page_text(c, X0, Y0, X1, Y1, fold)


@icon("mimetypes", "text-html")
def _html(c):
    X0, Y0, X1, Y1, fold = page(c, 5, 35, 3, 45)
    lw, px = c.lw, c.px
    page_text(c, X0, Y0, X1, Y1, fold, bottom=Y1 - (16 if px > 24 else 7 * lw))
    if px <= 16:
        with c.place(c.sx(18), c.sy(18), 30):
            globe(c, 24, 24, 20)
    else:
        with c.place(18, 18, 30):
            globe(c, 24, 24, 19)


@icon("mimetypes", "image-x-generic")
def _image(c):
    page_with(c, lambda c: e_picture(c, 3, 7, 45, 41), lines=True)


@icon("mimetypes", "audio-x-generic")
def _audio(c):
    page_with(c, e_note)


@icon("mimetypes", "video-x-generic")
def _video(c):
    page_with(c, e_film)


@icon("mimetypes", "package-x-generic")
def _package(c):
    cardboard(c, 3, 21, 33, 43, 10, 9)


def box_emblem(c):
    cardboard(c, 4, 20, 32, 43, 10, 9, label=False)


@icon("mimetypes", "application-x-msi")
def _msi(c):
    X0, Y0, X1, Y1, fold = page(c)
    page_text(c, X0, Y0, X1, Y1, fold, bottom=Y0 + fold + (4 * c.lw if c.px <= 24 else 8))
    with c.place(c.sx(8) if c.px > 16 else c.sx(9), c.sy(15), 32):
        box_emblem(c)
    if c.px > 16:
        from glyphs import e_down
        with c.place(24, 8, 18):
            e_down(c)


@icon("mimetypes", "application-x-executable")
def _exe(c):
    lw, px = c.lw, c.px

    def body(c, box):
        X0, Y0, X1, Y1 = box
        c.path(rr(X0, Y0, X1, Y1, 0), "#FFFFFF")
        if px > 20:
            mh = c.sy(Y0 + 2 * lw + (1 if px > 30 else 0))
            c.path(rr(X0, Y0, X1, mh, 0), "#ECE9D8")
            c.path(rr(X0, mh, X1, mh + lw, 0), "#C9C5B0")
    window(c, 3, 6, 45, 40, content=body)


@icon("mimetypes", "application-x-ms-dos-executable")
def _dosexe(c):
    lw, px = c.lw, c.px

    def body(c, box):
        X0, Y0, X1, Y1 = box
        c.path(rr(X0, Y0, X1, Y1, 0), "#000000")
        x, y = c.sx(X0 + 2 * lw), c.sy(Y0 + 2 * lw)
        if px <= 16:
            c.path(rr(x, y, x + 2 * lw, y + lw, 0), "#C0C0C0")
            c.path(rr(x + 3 * lw, y, x + 4 * lw, y + lw, 0), "#C0C0C0")
            return
        for i, wd in enumerate((0.55, 0.8, 0.3)):
            yy = c.sy(y + i * (2 * lw if px <= 24 else 4))
            c.path(rr(x, yy, x + (X1 - X0 - 4 * lw) * wd, yy + lw, 0), "#C0C0C0")
    window(c, 3, 6, 45, 40, content=body)


@icon("mimetypes", "x-office-document")
def _doc(c):
    X0, Y0, X1, Y1, fold = page(c)
    lw, px = c.lw, c.px
    if px <= 16:
        c.path(rr(X0 + 2 * lw, Y0 + 2 * lw, X1 - fold - lw, Y0 + 3 * lw, 0), "#2F6FE0")
        c.path(rr(X0 + 2 * lw, Y0 + 6 * lw, X0 + 5 * lw, Y0 + 9 * lw, 0), "#6BB0FF")
        text_lines(c, X0 + 6 * lw, Y0 + 6 * lw, X1 - 2 * lw, Y0 + 9 * lw, widths=(1,))
        text_lines(c, X0 + 2 * lw, Y0 + 10 * lw, X1 - 2 * lw, Y1 - 2 * lw)
        return
    m = 3 * lw if px <= 24 else 5
    hy = c.sy(Y0 + (3 * lw if px <= 24 else 6))
    c.path(rr(X0 + m, hy, X1 - fold - lw, hy + (lw if px <= 32 else 2 * lw), 0), "#2F6FE0")
    iy0 = c.sy(Y0 + fold + (2 * lw if px <= 24 else 4))
    iy1 = c.sy(iy0 + (X1 - X0) * 0.3)
    ix1 = c.sx(X0 + m + (X1 - X0) * 0.38)
    img = rr(X0 + m, iy0, ix1, iy1, 0)
    c.path(img, c.lin(0, iy0, 0, iy1, (0, "#9FD0FF"), (1, "#3F86E0")))
    with c.clipped(img):
        c.path(ell(ix1 - 2, iy1, (ix1 - X0) * 0.6, (iy1 - iy0) * 0.4), "#4FAE3A")
    c.outline(img, "#5B7BAE", w=0.7)
    text_lines(c, ix1 + (lw if px <= 24 else 3), iy0, X1 - m, iy1, widths=(1, 0.8, 0.95))
    text_lines(c, X0 + m, iy1 + (2 * lw if px <= 24 else 3), X1 - m, Y1 - m)


@icon("mimetypes", "x-office-spreadsheet")
def _sheet(c):
    X0, Y0, X1, Y1, fold = page(c)
    lw, px = c.lw, c.px
    m = 2 * lw if px <= 24 else 4
    gx0, gx1 = X0 + m, X1 - m
    gy0, gy1 = c.sy(Y0 + fold + (lw if px <= 24 else 3)), c.sy(Y1 - m)
    cols = 3 if px <= 16 else 4
    rows = 4 if px <= 16 else 6 if px <= 24 else 7
    cw = (gx1 - gx0) / cols
    rh = (gy1 - gy0) / rows
    c.path(rr(gx0, gy0, gx1, c.sy(gy0 + rh), 0), "#58B847")
    c.path(rr(gx0, gy0, c.sx(gx0 + cw * 0.9), gy1, 0), "#DFF3D8")
    c.path(rr(gx0, gy0, c.sx(gx0 + cw * 0.9), c.sy(gy0 + rh), 0), "#3E9A30")
    for i in range(rows + 1):
        y = c.sy(gy0 + i * rh)
        c.path(rr(gx0, y, gx1, y + lw, 0), "#6E9C64", op=0.8)
    for j in range(cols + 1):
        x = c.sx(gx0 + j * cw) if j < cols else gx1 - lw
        c.path(rr(x, gy0, x + lw, gy1 + lw, 0), "#6E9C64", op=0.8)
    if px <= 16:
        return
    text_lines(c, X0 + m, Y0 + m, X1 - fold - lw, Y0 + fold - lw, col="#3E9A30", widths=(0.8,),
               gap=10 * lw)


def pdf_letters(c, x0, y0, x1, y1, col="#FFFFFF"):
    """'PDF' in simple strokes inside the box."""
    w = (x1 - x0) / 3.0
    h = y1 - y0
    s = min(w * 0.75, h)
    sw = s * 0.2
    t = y0 + (h - s) / 2
    b = t + s
    pts = []
    x = x0 + w * 0.15
    c.path(d("M", x, b, "V", t, "H", x + s * 0.35, "A", s * 0.25, s * 0.25, 0, 0, 1, x + s * 0.35, t + s * 0.5,
             "H", x), "none", stroke=col, sw=sw, join="round", cap="round")
    x += w
    c.path(d("M", x, b, "V", t, "H", x + s * 0.2, "A", s * 0.42, s * 0.5, 0, 0, 1, x + s * 0.2, b, "Z"), "none",
           stroke=col, sw=sw, join="round")
    x += w
    c.path(d("M", x + s * 0.55, t, "H", x, "V", b, "M", x, t + s * 0.48, "H", x + s * 0.42), "none", stroke=col,
           sw=sw, cap="round", join="round")


@icon("mimetypes", "application-pdf")
def _pdf(c):
    X0, Y0, X1, Y1, fold = page(c)
    lw, px = c.lw, c.px
    by0 = c.sy(Y1 - (Y1 - Y0) * (0.36 if px > 16 else 0.38))
    page_text(c, X0, Y0, X1, Y1, fold, bottom=by0 - (2 * lw if px <= 24 else 4))
    bx0, bx1 = c.sx(X0 - (2 if px > 24 else 1) * lw), c.sx(X1 + (2 if px > 24 else 1) * lw)
    by1 = c.sy(Y1 - (2 * lw if px <= 24 else 4))
    band = rr(bx0, by0, bx1, by1, 1.2 if px > 16 else 0)
    c.drop(band, op=0.3)
    c.shape(band, c.lin(0, by0, 0, by1, (0, "#FF7A5C"), (0.5, "#E02D17"), (1, "#A8180A")), line="#7E1208",
            hl=c.lin(0, by0, 0, by1, (0, "#FFFFFF", 0.6), (1, "#FFFFFF", 0)))
    if px > 36:
        m = (by1 - by0) * 0.22
        pdf_letters(c, bx0 + (bx1 - bx0) * 0.12, by0 + m, bx1 - (bx1 - bx0) * 0.12, by1 - m)


@icon("mimetypes", "application-x-desktop")
def _desktop_file(c):
    X0, Y0, X1, Y1, fold = page(c)
    lw, px = c.lw, c.px
    page_text(c, X0, Y0, X1, Y1, fold, bottom=Y0 + fold + (2 * lw if px <= 24 else 4))
    with c.place(c.sx(9), c.sy(17), 30):
        window(c, 4, 8, 44, 40)
    # shortcut badge
    bx0, by0 = c.sx(5 if px > 16 else 3), c.sy(30 if px > 16 else 27)
    sz = c.sx(bx0 + (13 if px > 16 else 18)) - bx0
    badge = rr(bx0, by0, bx0 + sz, by0 + sz, 0.5 * lw)
    c.shape(badge, "#FFFFFF", line="#5B6B82")
    p = d("M", bx0 + sz * 0.28, by0 + sz * 0.8, "C", bx0 + sz * 0.28, by0 + sz * 0.45, bx0 + sz * 0.45,
          by0 + sz * 0.38, bx0 + sz * 0.62, by0 + sz * 0.38)
    c.path(p, "none", stroke="#1F50C0", sw=max(lw, sz * 0.16), cap="round")
    c.path(poly([(bx0 + sz * 0.55, by0 + sz * 0.16), (bx0 + sz * 0.86, by0 + sz * 0.38),
                 (bx0 + sz * 0.55, by0 + sz * 0.62)]), "#1F50C0")
