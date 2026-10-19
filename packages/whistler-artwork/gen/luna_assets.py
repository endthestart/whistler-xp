#!/usr/bin/env python3
"""Draw Whistler's original XP-style ("Luna-like") theme bitmaps with cairo.

usage: luna_assets.py OUTDIR

Writes the asset set that the Whistler GTK/xfwm4/panel themes read through
/usr/share/whistler/assets/current:
  OUTDIR/gtk/*.png        widget images referenced by the GTK 3 stylesheet
  OUTDIR/panel/*.png      taskbar, start button, task buttons, start menu bands
  OUTDIR/xfwm4/*          window frame theme (themerc + parts)
Everything is drawn from scratch here; nothing is copied from other themes.
"""
import math
import os
import sys

try:
    import cairo
except ImportError:  # pragma: no cover - local previews on macOS
    import cairocffi as cairo

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets-out"


# ----------------------------------------------------------------- helpers
def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def surface(w, h):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return s, cairo.Context(s)


def save(s, *parts):
    path = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s.write_to_png(path)


def vgrad(cr, y0, y1, stops):
    g = cairo.LinearGradient(0, y0, 0, y1)
    for pos, col in stops:
        g.add_color_stop_rgba(pos, *(hexc(col) if isinstance(col, str) else col))
    return g


def hgrad(cr, x0, x1, stops):
    g = cairo.LinearGradient(x0, 0, x1, 0)
    for pos, col in stops:
        g.add_color_stop_rgba(pos, *(hexc(col) if isinstance(col, str) else col))
    return g


def rrect(cr, x, y, w, h, r, corners=(True, True, True, True)):
    """Rounded rectangle path; corners = (tl, tr, br, bl)."""
    tl, tr, br, bl = corners
    cr.new_path()
    cr.move_to(x + (r if tl else 0), y)
    if tr:
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    else:
        cr.line_to(x + w, y)
    if br:
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    else:
        cr.line_to(x + w, y + h)
    if bl:
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    else:
        cr.line_to(x, y + h)
    if tl:
        cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    else:
        cr.line_to(x, y)
    cr.close_path()


def fill(cr, src):
    if isinstance(src, str):
        cr.set_source_rgba(*hexc(src))
    elif isinstance(src, tuple):
        cr.set_source_rgba(*src)
    else:
        cr.set_source(src)


# ----------------------------------------------------- check boxes / radios
STATES = {
    # state: (border, top, bottom, hover_glow)
    "normal": ("#1C5180", "#DCDCD7", "#FFFFFF", None),
    "hover": ("#1C5180", "#DCDCD7", "#FFFFFF", ("#FFF0CF", "#F8B33A")),
    "active": ("#1C5180", "#B0B0A7", "#E3E2DA", None),
    "insensitive": ("#CAC8BB", "#FFFFFF", "#FFFFFF", None),
}
CHECK_GREEN = "#21A121"


def draw_box(cr, x, y, size, state, round_=False):
    border, top, bottom, glow = STATES[state]
    r = size / 2 if round_ else 0.5
    rrect(cr, x + 0.5, y + 0.5, size - 1, size - 1, r - 0.5 if round_ else 0.5)
    fill(cr, vgrad(cr, y, y + size, [(0, top), (1, bottom)]))
    cr.fill_preserve()
    fill(cr, border)
    cr.set_line_width(1)
    cr.stroke()
    if glow:
        inner, outer = glow
        rrect(cr, x + 2, y + 2, size - 4, size - 4, (size - 4) / 2 if round_ else 0.5)
        fill(cr, hexc(outer, 0.9))
        cr.set_line_width(2)
        cr.stroke()


def draw_check(cr, x, y, size, color):
    cr.save()
    fill(cr, color)
    cr.set_line_width(2.1)
    cr.set_line_cap(cairo.LINE_CAP_SQUARE)
    cr.move_to(x + size * 0.27, y + size * 0.48)
    cr.line_to(x + size * 0.43, y + size * 0.66)
    cr.line_to(x + size * 0.74, y + size * 0.30)
    cr.stroke()
    cr.restore()


def checkboxes():
    for state, suffix in (("normal", ""), ("hover", "-hover"), ("active", "-active"),
                          ("insensitive", "-insensitive")):
        for kind in ("unchecked", "checked", "mixed"):
            s, cr = surface(16, 16)
            draw_box(cr, 1, 1, 13, state)
            col = "#CAC8BB" if state == "insensitive" else CHECK_GREEN
            if kind == "checked":
                draw_check(cr, 1, 1, 13, col)
            elif kind == "mixed":
                cr.rectangle(4, 4, 7, 7)
                fill(cr, vgrad(cr, 4, 11, [(0, "#4FC24F"), (1, col)]) if state != "insensitive" else col)
                cr.fill()
            save(s, "gtk", "checkbox-%s%s.png" % (kind, suffix))
            # radio
            s, cr = surface(16, 16)
            draw_box(cr, 1, 1, 13, state, round_=True)
            if kind == "checked":
                g = cairo.RadialGradient(6.7, 6.7, 0.3, 7.5, 7.5, 3.4)
                g.add_color_stop_rgba(0, *hexc("#A6E89C"))
                g.add_color_stop_rgba(0.5, *hexc("#3EB03E"))
                g.add_color_stop_rgba(1, *hexc("#1E7F1E"))
                cr.arc(7.5, 7.5, 3, 0, 2 * math.pi)
                fill(cr, g if state != "insensitive" else "#CAC8BB")
                cr.fill()
            elif kind == "mixed":
                cr.rectangle(4.5, 6.5, 6, 2)
                fill(cr, col)
                cr.fill()
            save(s, "gtk", "radio-%s%s.png" % (kind, suffix))
    # large "selection mode" checks used by content views
    for name, checked, hover, active in (("checkbox-selectionmode", False, False, False),
                                         ("checkbox-hover-selectionmode", False, True, False),
                                         ("checkbox-active-selectionmode", False, False, True),
                                         ("checkbox-checked-selectionmode", True, False, False),
                                         ("checkbox-checked-hover-selectionmode", True, True, False),
                                         ("checkbox-checked-active-selectionmode", True, False, True)):
        s, cr = surface(41, 41)
        cr.scale(41 / 16, 41 / 16)
        draw_box(cr, 1, 1, 13, "hover" if hover else ("active" if active else "normal"))
        if checked:
            draw_check(cr, 1, 1, 13, CHECK_GREEN)
        save(s, "gtk", name + ".png")
    # menu check/radio marks (black glyphs, white when hovered)
    for kind in ("check", "radio"):
        for mixed in (False, True):
            for suffix, col in (("", "#000000"), ("-hover", "#FFFFFF"), ("-insensitive", "#ACA899")):
                s, cr = surface(18, 18)
                fill(cr, col)
                if mixed:
                    cr.rectangle(5, 8, 8, 2)
                    cr.fill()
                elif kind == "check":
                    cr.set_line_width(2)
                    cr.move_to(5, 9)
                    cr.line_to(8, 12)
                    cr.line_to(13, 6)
                    cr.stroke()
                else:
                    cr.arc(9, 9, 3, 0, 2 * math.pi)
                    cr.fill()
                save(s, "gtk", "menu-%s-%s%s.png" % (kind, "mixed" if mixed else "checked", suffix))


# ---------------------------------------------------------------- scrollbars
SB = {
    "": ("#C8D6FB", "#B7CBF8", "#A3BBF2", "#FFFFFF", "#7F9DB9"),
    "-hover": ("#D9E5FF", "#CADBFF", "#B5CDFF", "#FFFFFF", "#7F9DB9"),
    "-active": ("#A9BEF0", "#9AB3EE", "#8AA5E8", "#E4EAF8", "#5F7EAE"),
}


def stepper(direction, suffix):
    top, mid, bot, hi, border = SB[suffix]
    s, cr = surface(17, 17)
    fill(cr, "#FDFDFA")
    cr.paint()
    rrect(cr, 0.5, 0.5, 16, 16, 2.5)
    fill(cr, vgrad(cr, 0, 17, [(0, top), (0.5, mid), (1, bot)]) if direction in ("up", "down")
         else hgrad(cr, 0, 17, [(0, top), (0.5, mid), (1, bot)]))
    cr.fill_preserve()
    fill(cr, hexc(border, 0.9))
    cr.set_line_width(1)
    cr.stroke()
    rrect(cr, 1.5, 1.5, 14, 14, 1.8)
    fill(cr, hexc(hi, 0.7))
    cr.stroke()
    # arrow glyph
    fill(cr, "#4D6185")
    cr.save()
    cr.translate(8.5, 8.5)
    cr.rotate({"up": 0, "right": math.pi / 2, "down": math.pi, "left": -math.pi / 2}[direction])
    cr.set_line_width(2)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.move_to(-3.5, 1.8)
    cr.line_to(0, -1.7)
    cr.line_to(3.5, 1.8)
    cr.stroke()
    cr.restore()
    return s


def scrollbars():
    names = {"up": "top-stepper", "down": "bottom-stepper", "left": "left-stepper", "right": "right-stepper"}
    for d, base in names.items():
        for suffix in ("", "-hover", "-active"):
            save(stepper(d, suffix), "gtk", base + suffix + ".png")
    for suffix in ("", "-hover", "-active"):
        top, mid, bot, hi, border = SB[suffix]
        # vertical slider frame (border-image, 5px slices)
        for orient, (w, h) in (("vert", (17, 22)), ("horz", (22, 17))):
            s, cr = surface(w, h)
            rrect(cr, 0.5, 0.5, w - 1, h - 1, 2.5)
            g = (hgrad(cr, 0, w, [(0, top), (0.55, mid), (1, bot)]) if orient == "vert"
                 else vgrad(cr, 0, h, [(0, top), (0.55, mid), (1, bot)]))
            fill(cr, g)
            cr.fill_preserve()
            fill(cr, hexc(border, 0.9))
            cr.stroke()
            rrect(cr, 1.5, 1.5, w - 3, h - 3, 1.8)
            fill(cr, hexc(hi, 0.75))
            cr.stroke()
            save(s, "gtk", "scrollbar-slider-%s%s.png" % (orient, suffix))
            # fill used behind the grip
            bw, bh = (7, 12) if orient == "vert" else (12, 7)
            s, cr = surface(bw, bh)
            g = (hgrad(cr, -5, bw + 5, [(0, top), (0.55, mid), (1, bot)]) if orient == "vert"
                 else vgrad(cr, -5, bh + 5, [(0, top), (0.55, mid), (1, bot)]))
            fill(cr, g)
            cr.paint()
            save(s, "gtk", "slider-bg-%s%s.png" % (orient, suffix))
        # grips: four short raised lines
        for orient, (w, h) in (("vert", (9, 10)), ("horz", (10, 9))):
            s, cr = surface(w, h)
            for i in range(4):
                if orient == "vert":
                    y = 1.5 + i * 2.2
                    cr.move_to(1, y)
                    cr.line_to(8, y)
                    fill(cr, "#EEF4FE")
                    cr.stroke()
                    cr.move_to(2, y + 1)
                    cr.line_to(9, y + 1)
                    fill(cr, hexc("#8CB0F8"))
                    cr.stroke()
                else:
                    x = 1.5 + i * 2.2
                    cr.move_to(x, 1)
                    cr.line_to(x, 8)
                    fill(cr, "#EEF4FE")
                    cr.stroke()
                    cr.move_to(x + 1, 2)
                    cr.line_to(x + 1, 9)
                    fill(cr, hexc("#8CB0F8"))
                    cr.stroke()
            save(s, "gtk", "handle-%s%s.png" % (orient, suffix))
    for orient, (w, h) in (("vert", (17, 1)), ("horz", (1, 17))):
        s, cr = surface(w, h)
        g = (hgrad(cr, 0, w, [(0, "#EEEDE5"), (0.15, "#F7F7F4"), (1, "#FEFEFB")]) if orient == "vert"
             else vgrad(cr, 0, h, [(0, "#EEEDE5"), (0.15, "#F7F7F4"), (1, "#FEFEFB")]))
        fill(cr, g)
        cr.paint()
        save(s, "gtk", "trough-scrollbar-%s.png" % orient)


# -------------------------------------------------------------- scale (trackbar)
def scales():
    for orient, (w, h) in (("horz", (5, 4)), ("vert", (4, 5))):
        s, cr = surface(w, h)
        fill(cr, "#9D9C99")
        cr.rectangle(0, 0, w, h)
        cr.fill()
        fill(cr, "#FFFFFF")
        if orient == "horz":
            cr.rectangle(1, 1, w - 2, h - 1)
        else:
            cr.rectangle(1, 1, w - 1, h - 2)
        cr.fill()
        fill(cr, "#E5E3DA")
        if orient == "horz":
            cr.rectangle(1, 1, w - 2, 1)
        else:
            cr.rectangle(1, 1, 1, h - 2)
        cr.fill()
        save(s, "gtk", "trough-%s.png" % orient)
    looks = {"": ("#FFFFFF", "#ECEBE6", "#1C5180", "#21A121"),
             "-hover": ("#FFFFFF", "#F1F0EA", "#1C5180", "#F8B33A"),
             "-active": ("#F1F0EA", "#DAD8CC", "#1C5180", "#21A121"),
             "-insensitive": ("#F7F7F4", "#EEEDE5", "#BDBAA2", "#D4D0C8")}
    for suffix, (top, bot, border, accent) in looks.items():
        for variant in ("", "-scale-has-marks-above", "-scale-has-marks-below"):
            for orient in ("horz", "vert"):
                if orient == "horz":
                    w, h = (11, 22) if not variant else (11, 21)
                else:
                    w, h = (22, 11) if not variant else (21, 11)
                s, cr = surface(w, h)
                cr.save()
                if orient == "vert":
                    cr.translate(0, h)
                    cr.rotate(-math.pi / 2)
                    W, H = h, w
                else:
                    W, H = w, h
                if "below" in variant:
                    pts = [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 5), (W / 2, H - 0.5), (0.5, H - 5)]
                elif "above" in variant:
                    pts = [(W / 2, 0.5), (W - 0.5, 5), (W - 0.5, H - 0.5), (0.5, H - 0.5), (0.5, 5)]
                else:
                    pts = [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]
                cr.new_path()
                cr.move_to(*pts[0])
                for p in pts[1:]:
                    cr.line_to(*p)
                cr.close_path()
                fill(cr, vgrad(cr, 0, H, [(0, top), (1, bot)]))
                cr.fill_preserve()
                fill(cr, border)
                cr.set_line_width(1)
                cr.stroke()
                # coloured accent strip near the end, XP-style
                cr.rectangle(1.5, H - (7 if "below" in variant else 3.5), W - 3, 2)
                fill(cr, accent)
                cr.fill()
                cr.restore()
                save(s, "gtk", "slider-%s%s%s.png" % (orient, variant, suffix))


# --------------------------------------------------------- title bar buttons
def title_button(kind, state, active=True, size=21):
    """kind: close|minimize|maximize|restore|help|menu|shade|stick; state: normal|hover|pressed."""
    s, cr = surface(size, size)
    if kind == "close":
        base = {"normal": ("#E7774E", "#D05930", "#C0401C"),
                "hover": ("#F59A76", "#E46C47", "#D4542E"),
                "pressed": ("#C0401C", "#A8361A", "#982C12")}[state]
    else:
        base = {"normal": ("#5B97FF", "#2C6CF6", "#1D55E6"),
                "hover": ("#83B2FF", "#4F8CFF", "#346FF9"),
                "pressed": ("#1A4DCC", "#1543B8", "#0E3AA8")}[state]
    if not active:
        base = tuple(_desaturate(c, 0.35) for c in base)
    rrect(cr, 0.5, 0.5, size - 1, size - 1, 3)
    fill(cr, vgrad(cr, 0, size, [(0, base[0]), (0.45, base[1]), (1, base[2])]))
    cr.fill_preserve()
    fill(cr, hexc("#FFFFFF", 0.95 if active else 0.75))
    cr.set_line_width(1)
    cr.stroke()
    # glossy top
    rrect(cr, 2, 1.5, size - 4, size * 0.45, 2.5)
    fill(cr, vgrad(cr, 1, size * 0.5, [(0, hexc("#FFFFFF", 0.35)), (1, hexc("#FFFFFF", 0.0))]))
    cr.fill()
    glyph = hexc("#FFFFFF", 1.0 if active else 0.85)
    c = size / 2
    cr.set_source_rgba(*glyph)
    cr.set_line_cap(cairo.LINE_CAP_SQUARE)
    if kind == "close":
        cr.set_line_width(2.2)
        d = size * 0.19
        cr.move_to(c - d, c - d)
        cr.line_to(c + d, c + d)
        cr.move_to(c + d, c - d)
        cr.line_to(c - d, c + d)
        cr.stroke()
    elif kind == "minimize":
        cr.rectangle(size * 0.28, size * 0.62, size * 0.33, 2.6)
        cr.fill()
    elif kind == "maximize":
        x0, y0, w = size * 0.27, size * 0.26, size * 0.46
        cr.set_line_width(1)
        cr.rectangle(x0 + 0.5, y0 + 0.5, w, w)
        cr.stroke()
        cr.rectangle(x0, y0, w + 1, 2.5)
        cr.fill()
    elif kind == "restore":
        cr.set_line_width(1)
        x0, y0, w = size * 0.36, size * 0.22, size * 0.36
        cr.rectangle(x0 + 0.5, y0 + 0.5, w, w)
        cr.stroke()
        cr.rectangle(x0, y0, w + 1, 2)
        cr.fill()
        x1, y1 = size * 0.24, size * 0.38
        fill(cr, vgrad(cr, 0, size, [(0, base[0]), (0.45, base[1]), (1, base[2])]))
        cr.rectangle(x1, y1, w + 1, w + 1)
        cr.fill()
        cr.set_source_rgba(*glyph)
        cr.rectangle(x1 + 0.5, y1 + 0.5, w, w)
        cr.stroke()
        cr.rectangle(x1, y1, w + 1, 2)
        cr.fill()
    elif kind == "help":
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(size * 0.7)
        ext = cr.text_extents("?")
        cr.move_to(c - ext.width / 2 - ext.x_bearing, c + ext.height / 2)
        cr.show_text("?")
    elif kind in ("menu", "shade", "stick"):
        cr.set_line_width(2)
        if kind == "shade":
            cr.move_to(c - 4, c + 2)
            cr.line_to(c, c - 2)
            cr.line_to(c + 4, c + 2)
            cr.stroke()
        elif kind == "stick":
            cr.arc(c, c, 3, 0, 2 * math.pi)
            cr.fill()
        else:
            cr.rectangle(c - 4, c - 1, 8, 2)
            cr.fill()
    return s


def _desaturate(hexcol, amount):
    r, g, b, _ = hexc(hexcol)
    grey = 0.3 * r + 0.59 * g + 0.11 * b
    r, g, b = (v + (grey - v) * amount for v in (r, g, b))
    # lighten for the inactive XP look
    r, g, b = (v + (1 - v) * 0.35 for v in (r, g, b))
    return "#%02X%02X%02X" % (int(r * 255), int(g * 255), int(b * 255))


def csd_buttons():
    for kind in ("close", "minimize", "maximize", "restore"):
        for name, state, active in (("normal", "normal", True), ("hover", "hover", True), ("active", "pressed", True),
                                    ("backdrop", "normal", False), ("backdrop-hover", "hover", False)):
            save(title_button(kind, state, active), "gtk", "%s-%s.png" % (kind, name))


# ------------------------------------------------------------ title bar body
TITLE_ACTIVE = [(0.00, "#0A5DEA"), (0.04, "#3C8EFF"), (0.10, "#2A78F8"), (0.20, "#0F62EF"),
                (0.50, "#0055E5"), (0.80, "#0052E0"), (0.92, "#0360EC"), (1.00, "#0040C8")]
TITLE_INACTIVE = [(0.00, "#7895E0"), (0.04, "#B8CCF5"), (0.12, "#A2BBF0"), (0.50, "#93AEEA"),
                  (0.90, "#9CB5EC"), (1.00, "#7F9AE0")]
FRAME_ACTIVE = ["#0019CF", "#0831D9", "#166AEE", "#0055EA"]      # outermost -> innermost
FRAME_INACTIVE = ["#6F8CDC", "#7F9ADF", "#A6BCF0", "#9DB5EC"]
TITLE_H = 29


def titlebar_strip(w, h, active):
    s, cr = surface(w, h)
    fill(cr, vgrad(cr, 0, h, TITLE_ACTIVE if active else TITLE_INACTIVE))
    cr.paint()
    return s


def csd_titlebar():
    for active, name in ((True, "focused"), (False, "unfocused")):
        save(titlebar_strip(1, TITLE_H, active), "gtk", "titlebar-%s-middle.png" % name)


def xfwm4():
    d = "xfwm4"
    for active, st in ((True, "active"), (False, "inactive")):
        frame = FRAME_ACTIVE if active else FRAME_INACTIVE
        title = TITLE_ACTIVE if active else TITLE_INACTIVE
        # title pieces 1..5 (all the same gradient; 1 and 5 next to the corners)
        for i in range(1, 6):
            save(titlebar_strip(8, TITLE_H, active), d, "title-%d-%s.png" % (i, st))
        # rounded top corners (8x29): outer frame line + gradient, transparent outside
        for side in ("left", "right"):
            s, cr = surface(8, TITLE_H)
            cr.save()
            if side == "right":
                cr.translate(8, 0)
                cr.scale(-1, 1)
            rrect(cr, 0, 0, 16, TITLE_H + 8, 7, (True, True, False, False))
            cr.clip()
            fill(cr, vgrad(cr, 0, TITLE_H, title))
            cr.paint()
            # light inner edge on the left
            cr.rectangle(1, 3, 1, TITLE_H - 3)
            fill(cr, hexc("#FFFFFF", 0.18 if active else 0.25))
            cr.fill()
            cr.restore()
            cr.save()
            if side == "right":
                cr.translate(8, 0)
                cr.scale(-1, 1)
            rrect(cr, 0.5, 0.5, 16, TITLE_H + 8, 7, (True, True, False, False))
            fill(cr, frame[0])
            cr.set_line_width(1)
            cr.stroke()
            cr.restore()
            save(s, d, "top-%s-%s.png" % (side, st))
        # side and bottom borders (4px)
        for side in ("left", "right"):
            s, cr = surface(4, 8)
            cols = frame if side == "left" else list(reversed(frame))
            for i, c in enumerate(cols):
                cr.rectangle(i, 0, 1, 8)
                fill(cr, c)
                cr.fill()
            save(s, d, "%s-%s.png" % (side, st))
        s, cr = surface(8, 4)
        for i, c in enumerate(reversed(frame)):
            cr.rectangle(0, i, 8, 1)
            fill(cr, c)
            cr.fill()
        save(s, d, "bottom-%s.png" % st)
        for side in ("left", "right"):
            s, cr = surface(4, 4)
            for y in range(4):
                for x in range(4):
                    # distance to the outer edge decides the colour band
                    dx = x if side == "left" else 3 - x
                    dy = 3 - y
                    band = min(dx, dy)
                    cr.rectangle(x, y, 1, 1)
                    fill(cr, frame[band])
                    cr.fill()
            save(s, d, "bottom-%s-%s.png" % (side, st))
        # buttons
        mapping = {"close": "close", "hide": "minimize", "maximize": "maximize",
                   "maximize-toggled": "restore", "menu": "menu", "shade": "shade",
                   "shade-toggled": "shade", "stick": "stick", "stick-toggled": "stick"}
        for fname, kind in mapping.items():
            for bst, state in (("active", "normal"), ("inactive", "normal"), ("prelight", "hover"),
                               ("pressed", "pressed")):
                is_active = bst != "inactive"
                if not active:
                    # xfwm4 uses <name>-inactive for unfocused windows only; prelight/pressed shared
                    pass
                save(title_button(kind, state, is_active), d, "%s-%s.png" % (fname, bst))
    with open(os.path.join(OUT, d, "themerc"), "w") as f:
        f.write("""# Whistler window frame (original artwork)
active_text_color=#FFFFFF
active_text_shadow_color=#0A1A64
title_shadow_active=true
inactive_text_color=#D8E4F8
inactive_text_shadow_color=#5A73C8
title_shadow_inactive=false
full_width_title=true
title_vertical_offset_active=1
title_vertical_offset_inactive=1
title_horizontal_offset=3
button_offset=4
button_spacing=2
show_app_icon=true
maximized_offset=4
shadow_delta_height=2
shadow_delta_width=0
shadow_delta_x=0
shadow_delta_y=-5
shadow_opacity=40
""")


# ----------------------------------------------------------------- taskbar
TASKBAR = [(0.00, "#1F4CBE"), (0.03, "#4D8EF1"), (0.08, "#3F7FEC"), (0.18, "#2E66DE"),
           (0.55, "#245DDA"), (0.86, "#2257D3"), (0.96, "#1C4BC0"), (1.00, "#163C9E")]


def panel():
    s, cr = surface(20, 30)
    fill(cr, vgrad(cr, 0, 30, TASKBAR))
    cr.paint()
    save(s, "panel", "taskbar.png")
    # notification area
    s, cr = surface(20, 30)
    fill(cr, vgrad(cr, 0, 30, [(0, "#0C59B9"), (0.06, "#139EE9"), (0.10, "#18B5F2"), (0.16, "#139BEB"),
                               (0.6, "#0D8DEA"), (0.85, "#0D9FF1"), (0.95, "#137ED7"), (1, "#095BC9")]))
    cr.paint()
    save(s, "panel", "tray.png")
    # start button: green pill, flat left edge, round right end
    for st, (hi, top, mid, bot) in (("normal", ("#7ACC6E", "#4CAF4C", "#3A9C3A", "#2E862E")),
                                    ("hover", ("#93DA86", "#5CC05C", "#47AE47", "#389838")),
                                    ("pressed", ("#4E9A44", "#2E8B2E", "#287D28", "#226E22"))):
        W, H = 104, 30
        s, cr = surface(W, H)
        rrect(cr, -12, 0, W + 11, H, 14, (False, True, True, False))
        fill(cr, vgrad(cr, 0, H, [(0, hi), (0.12, top), (0.55, mid), (1, bot)]))
        cr.fill()
        # glossy highlight
        rrect(cr, 0, 2, W - 10, 9, 5, (False, True, True, False))
        fill(cr, vgrad(cr, 2, 12, [(0, hexc("#FFFFFF", 0.35)), (1, hexc("#FFFFFF", 0.0))]))
        cr.fill()
        # darker right rim + shadow
        rrect(cr, -12, 0.5, W + 10.5, H - 1, 14, (False, True, True, False))
        fill(cr, hexc("#1F5F1F", 0.8))
        cr.set_line_width(1)
        cr.stroke()
        save(s, "panel", "start-%s.png" % st)
    # task buttons (used as a 4px border-image)
    for st, (edge, top, bot, hl) in (("normal", ("#1A49B5", "#3F8CF3", "#2F6FE4", 0.30)),
                                     ("hover", ("#2156C7", "#5BA2FF", "#428AF7", 0.35)),
                                     ("active", ("#0F327F", "#1D4BAE", "#1E52B7", 0.0)),
                                     ("active-hover", ("#123A90", "#2557C0", "#2A61CA", 0.0))):
        W, H = 32, 24
        s, cr = surface(W, H)
        rrect(cr, 0.5, 0.5, W - 1, H - 1, 3)
        fill(cr, vgrad(cr, 0, H, [(0, top), (1, bot)]))
        cr.fill_preserve()
        fill(cr, edge)
        cr.set_line_width(1)
        cr.stroke()
        if hl:
            rrect(cr, 1.5, 1.5, W - 3, H - 3, 2)
            fill(cr, hexc("#FFFFFF", hl))
            cr.stroke()
        else:
            # pressed: inner shadow at the top-left
            cr.move_to(2, H - 2)
            cr.line_to(2, 2)
            cr.line_to(W - 2, 2)
            fill(cr, hexc("#000000", 0.35))
            cr.stroke()
        save(s, "panel", "task-%s.png" % st)
    # start menu header and footer bands
    W = 380
    s, cr = surface(W, 60)
    rrect(cr, 0, 0, W, 66, 7, (True, True, False, False))
    fill(cr, vgrad(cr, 0, 60, [(0, "#1767D9"), (0.08, "#5C9BF0"), (0.18, "#2A73E0"),
                               (0.75, "#1458CF"), (1, "#0E4CC4")]))
    cr.fill()
    save(s, "panel", "startmenu-top.png")
    s, cr = surface(W, 40)
    fill(cr, vgrad(cr, 0, 40, [(0, "#3A7BE4"), (0.1, "#2864D8"), (0.6, "#1E58CC"), (1, "#123FA8")]))
    cr.paint()
    save(s, "panel", "startmenu-bottom.png")


def main():
    checkboxes()
    scrollbars()
    scales()
    csd_buttons()
    csd_titlebar()
    xfwm4()
    panel()


if __name__ == "__main__":
    main()
