#!/usr/bin/env python3
"""Draw Whistler's original XP-era style cursor theme and assemble it with xcursorgen.

usage: build_cursors.py OUT_DIR                  -> OUT_DIR/<theme>/cursors + index.theme
       build_cursors.py --frames-only DIR        -> PNG frames + xcursorgen configs only
       build_cursors.py --preview OUT.png        -> contact sheet
       --name NAME   theme directory/name (default whistler-lookalike-cursors)
"""
import math
import os
import shutil
import subprocess
import sys

try:
    import cairo
except ImportError:  # local previews on macOS
    import cairocffi as cairo

SIZES = (24, 32, 48)
BASE = 32.0  # design grid


def ctx(size):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    cr = cairo.Context(s)
    cr.scale(size / BASE, size / BASE)
    return s, cr


def outline_fill(cr, path_fn, fill=(1, 1, 1), stroke=(0, 0, 0), width=1.0, shadow=True):
    if shadow:
        for i, a in ((2.2, 0.10), (1.6, 0.14), (1.0, 0.18)):
            cr.save()
            cr.translate(i, i)
            path_fn(cr)
            cr.set_source_rgba(0, 0, 0, a)
            cr.fill()
            cr.restore()
    path_fn(cr)
    cr.set_source_rgb(*fill)
    cr.fill_preserve()
    cr.set_source_rgb(*stroke)
    cr.set_line_width(width)
    cr.set_line_join(cairo.LINE_JOIN_MITER)
    cr.stroke()


# ----------------------------------------------------------------- shapes
def arrow_path(cr, x=1.5, y=1.5, s=1.0):
    pts = [(0, 0), (0, 17.5), (4.2, 13.6), (7.2, 20.2), (9.6, 19.1), (6.7, 12.6), (12.3, 12.6)]
    cr.new_path()
    cr.move_to(x + pts[0][0] * s, y + pts[0][1] * s)
    for px, py in pts[1:]:
        cr.line_to(x + px * s, y + py * s)
    cr.close_path()


def draw_arrow(cr, s=1.0, x=1.5, y=1.5):
    outline_fill(cr, lambda c: arrow_path(c, x, y, s))


def hourglass(cr, cx, cy, h, phase, small=False):
    """Hourglass centred at cx,cy, height h; phase 0..1 = sand fallen; >1 flipping."""
    w = h * 0.62
    flip = 0.0
    if phase > 1.0:
        flip = (phase - 1.0) * math.pi
        phase = 1.0
    cr.save()
    cr.translate(cx, cy)
    cr.rotate(flip)
    t = h / 2
    # shadow
    if not small:
        cr.rectangle(-w / 2 + 1.2, -t + 1.2, w, h)
        cr.set_source_rgba(0, 0, 0, 0.15)
        cr.fill()
    # glass
    cr.new_path()
    cr.move_to(-w / 2 + 1, -t + 1.5)
    cr.line_to(w / 2 - 1, -t + 1.5)
    cr.curve_to(w / 2 - 1, -t * 0.25, 1.2, -0.8, 1.2, 0)
    cr.curve_to(1.2, 0.8, w / 2 - 1, t * 0.25, w / 2 - 1, t - 1.5)
    cr.line_to(-w / 2 + 1, t - 1.5)
    cr.curve_to(-w / 2 + 1, t * 0.25, -1.2, 0.8, -1.2, 0)
    cr.curve_to(-1.2, -0.8, -w / 2 + 1, -t * 0.25, -w / 2 + 1, -t + 1.5)
    cr.close_path()
    cr.set_source_rgba(0.92, 0.96, 1.0, 0.95)
    cr.fill_preserve()
    cr.save()
    cr.clip()
    sand = (0.93, 0.76, 0.32)
    top_level = -t + 1.5 + (t - 2) * phase           # top sand surface sinks
    cr.rectangle(-w, top_level, 2 * w, -top_level)
    cr.set_source_rgb(*sand)
    cr.fill()
    bottom_h = (t - 2) * phase
    cr.new_path()
    cr.move_to(-w / 2, t - 1.5)
    cr.line_to(w / 2, t - 1.5)
    cr.line_to(w / 2, t - 1.5 - bottom_h * 0.6)
    cr.line_to(0, t - 1.5 - bottom_h)
    cr.line_to(-w / 2, t - 1.5 - bottom_h * 0.6)
    cr.close_path()
    cr.fill()
    if 0.02 < phase < 0.98:
        cr.rectangle(-0.35, -0.5, 0.7, t - 1.5 - bottom_h * 0.9)
        cr.fill()
    cr.restore()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.8)
    cr.stroke()
    # wooden caps
    for yy in (-t, t - 2):
        cr.rectangle(-w / 2, yy, w, 2)
        g = cairo.LinearGradient(0, yy, 0, yy + 2)
        g.add_color_stop_rgb(0, 0.75, 0.5, 0.25)
        g.add_color_stop_rgb(1, 0.45, 0.27, 0.1)
        cr.set_source(g)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(0.6)
        cr.stroke()
    cr.restore()


def hand_path(cr):
    cr.new_path()
    # index finger pointing up, other fingers curled, thumb at the left
    cr.move_to(9.5, 1.5)
    cr.curve_to(10.8, 1.0, 12.0, 1.8, 12.0, 3.2)
    cr.line_to(12.0, 10.5)
    cr.curve_to(12.4, 9.6, 14.6, 9.6, 15.0, 10.8)
    cr.curve_to(15.6, 10.0, 17.8, 10.2, 18.0, 11.6)
    cr.curve_to(18.6, 11.0, 20.8, 11.2, 21.0, 12.8)
    cr.line_to(21.0, 18.0)
    cr.curve_to(21.0, 21.0, 19.5, 23.0, 18.5, 24.5)
    cr.line_to(18.5, 26.5)
    cr.line_to(9.5, 26.5)
    cr.line_to(9.5, 24.8)
    cr.curve_to(8.0, 23.0, 5.2, 19.5, 4.2, 17.2)
    cr.curve_to(3.5, 15.6, 5.6, 14.4, 6.8, 15.6)
    cr.line_to(7.5, 16.6)
    cr.line_to(7.5, 3.2)
    cr.curve_to(7.5, 1.9, 8.4, 1.4, 9.5, 1.5)
    cr.close_path()


def draw_hand(cr, closed=False, open_=False):
    if open_ or closed:
        def path(c):
            c.new_path()
            top = 9.0 if closed else 3.0
            fingers = [(7.0, top + 3), (10.2, top + 1), (13.4, top), (16.6, top + 1.5)]
            c.move_to(5.5, 16)
            for fx, fy in fingers:
                c.line_to(fx - 1.2, fy + 2)
                c.curve_to(fx - 1.2, fy, fx + 1.4, fy, fx + 1.4, fy + 2)
            c.line_to(19.5, 12)
            c.curve_to(21.5, 11.2, 22.5, 13.5, 21.0, 15.0)
            c.line_to(18.5, 20.5)
            c.line_to(18.5, 25.5)
            c.line_to(8.5, 25.5)
            c.line_to(8.5, 22.5)
            c.curve_to(6.0, 21.0, 5.0, 19.0, 5.5, 16)
            c.close_path()
        outline_fill(cr, path)
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(0.6)
        for fx in (8.6, 11.8, 15.0):
            cr.move_to(fx, (12.5 if closed else 8) + 2)
            cr.line_to(fx, 16)
        cr.stroke()
        return
    outline_fill(cr, hand_path)
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.6)
    for fx, y0 in ((15.0, 11.2), (18.0, 12.2)):
        cr.move_to(fx, y0)
        cr.line_to(fx, 15.5)
    cr.stroke()


def ibeam(cr):
    def path(c):
        c.new_path()
        c.move_to(12.5, 4)
        c.line_to(15, 4)
        c.curve_to(15.6, 4, 16, 4.6, 16, 5.2)
        c.curve_to(16, 4.6, 16.4, 4, 17, 4)
        c.line_to(19.5, 4)
        c.line_to(19.5, 5.2)
        c.line_to(17.4, 5.2)
        c.line_to(16.6, 6)
        c.line_to(16.6, 26)
        c.line_to(17.4, 26.8)
        c.line_to(19.5, 26.8)
        c.line_to(19.5, 28)
        c.line_to(17, 28)
        c.curve_to(16.4, 28, 16, 27.4, 16, 26.8)
        c.curve_to(16, 27.4, 15.6, 28, 15, 28)
        c.line_to(12.5, 28)
        c.line_to(12.5, 26.8)
        c.line_to(14.6, 26.8)
        c.line_to(15.4, 26)
        c.line_to(15.4, 6)
        c.line_to(14.6, 5.2)
        c.line_to(12.5, 5.2)
        c.close_path()
    path(cr)
    cr.set_source_rgb(1, 1, 1)
    cr.set_line_width(2.0)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.stroke_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.fill()


def double_arrow(cr, angle, length=22.0):
    """Black double-headed sizing arrow with white outline, centred."""
    def path(c):
        c.new_path()
        L, head, hw, sw = length / 2, 5.5, 4.6, 1.0
        pts = [(-L, 0), (-L + head, -hw), (-L + head, -sw), (L - head, -sw), (L - head, -hw), (L, 0),
               (L - head, hw), (L - head, sw), (-L + head, sw), (-L + head, hw)]
        c.save()
        c.translate(16, 16)
        c.rotate(angle)
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        c.close_path()
        c.restore()
    outline_fill(cr, path, fill=(0, 0, 0), stroke=(1, 1, 1), width=1.1, shadow=True)


def four_way(cr):
    def path(c):
        c.new_path()
        L, head, hw, sw = 11.5, 5, 4, 1.0
        c.save()
        c.translate(16, 16)
        c.move_to(0, -L)
        for k in range(4):
            c.line_to(hw, -L + head)
            c.line_to(sw, -L + head)
            c.line_to(sw, -sw)
            c.line_to(L - head, -sw)
            c.line_to(L - head, -hw)
            c.rotate(math.pi / 2)
            c.line_to(0, -L)
        c.close_path()
        c.restore()
    outline_fill(cr, path, fill=(0, 0, 0), stroke=(1, 1, 1), width=1.1)


def crosshair(cr):
    for col, w in (((1, 1, 1), 3.4), ((0, 0, 0), 1.4)):
        cr.set_source_rgb(*col)
        cr.set_line_width(w)
        cr.move_to(16, 4)
        cr.line_to(16, 13.5)
        cr.move_to(16, 18.5)
        cr.line_to(16, 28)
        cr.move_to(4, 16)
        cr.line_to(13.5, 16)
        cr.move_to(18.5, 16)
        cr.line_to(28, 16)
        cr.stroke()


def badge_plus(cr, x, y):
    cr.rectangle(x, y, 8, 8)
    cr.set_source_rgb(1, 1, 1)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.8)
    cr.stroke()
    cr.rectangle(x + 1.8, y + 3.5, 4.4, 1)
    cr.rectangle(x + 3.5, y + 1.8, 1, 4.4)
    cr.fill()


def badge_link(cr, x, y):
    cr.rectangle(x, y, 8, 8)
    cr.set_source_rgb(1, 1, 1)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.8)
    cr.stroke()
    cr.move_to(x + 2, y + 6.5)
    cr.curve_to(x + 2, y + 3.5, x + 3.5, y + 2.6, x + 6, y + 2.6)
    cr.stroke()
    cr.move_to(x + 6.6, y + 2.6)
    cr.line_to(x + 4.8, y + 1.2)
    cr.line_to(x + 4.8, y + 4.0)
    cr.close_path()
    cr.fill()


def no_sign(cr, cx, cy, r):
    cr.arc(cx, cy, r, 0, 2 * math.pi)
    cr.set_source_rgb(1, 1, 1)
    cr.set_line_width(r * 0.55)
    cr.stroke()
    cr.arc(cx, cy, r, 0, 2 * math.pi)
    cr.set_source_rgb(0.85, 0.1, 0.1)
    cr.set_line_width(r * 0.32)
    cr.stroke()
    cr.move_to(cx - r * 0.7, cy - r * 0.7)
    cr.line_to(cx + r * 0.7, cy + r * 0.7)
    cr.stroke()


def question(cr, x, y):
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(12)
    cr.move_to(x, y)
    cr.text_path("?")
    cr.set_source_rgb(1, 1, 1)
    cr.set_line_width(2)
    cr.stroke_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.fill()


def magnifier(cr, sign):
    def path(c):
        c.new_path()
        c.arc(13, 13, 7.5, 0, 2 * math.pi)
    cr.save()
    path(cr)
    cr.set_source_rgba(0.85, 0.93, 1.0, 0.9)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(1.6)
    cr.stroke()
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_width(3.5)
    cr.move_to(18.6, 18.6)
    cr.line_to(25, 25)
    cr.stroke()
    cr.set_line_width(1.6)
    cr.move_to(9.5, 13)
    cr.line_to(16.5, 13)
    if sign == "+":
        cr.move_to(13, 9.5)
        cr.line_to(13, 16.5)
    cr.stroke()
    cr.restore()


def pencil(cr):
    def path(c):
        c.new_path()
        c.move_to(4, 28)
        c.line_to(6, 21)
        c.line_to(22, 5)
        c.line_to(27, 10)
        c.line_to(11, 26)
        c.close_path()
    outline_fill(cr, path, fill=(1.0, 0.85, 0.3))
    cr.move_to(4, 28)
    cr.line_to(6, 21)
    cr.line_to(11, 26)
    cr.close_path()
    cr.set_source_rgb(0.95, 0.85, 0.7)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.8)
    cr.stroke()


def plus_cell(cr):
    def path(c):
        c.new_path()
        for (x, y, w, h) in ((13, 5, 6, 22), (5, 13, 22, 6)):
            c.rectangle(x, y, w, h)
    cr.save()
    for i, a in ((1.5, 0.15), (1.0, 0.18)):
        cr.save()
        cr.translate(i, i)
        path(cr)
        cr.set_source_rgba(0, 0, 0, a)
        cr.fill()
        cr.restore()
    cr.new_path()
    cr.move_to(13, 5)
    for x, y in ((19, 5), (19, 13), (27, 13), (27, 19), (19, 19), (19, 27), (13, 27), (13, 19), (5, 19), (5, 13),
                 (13, 13)):
        cr.line_to(x, y)
    cr.close_path()
    cr.set_source_rgb(1, 1, 1)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(1)
    cr.stroke()
    cr.restore()


# ------------------------------------------------------------- cursor table
def frames_static(fn):
    return [(fn, 0)]


def cursor_defs():
    """name -> (list of (draw_fn, delay_ms), hotspot in design units)."""
    d = {}
    d["default"] = ([(lambda cr: draw_arrow(cr), 0)], (1.5, 1.5))
    d["pointer"] = ([(lambda cr: draw_hand(cr), 0)], (9.6, 1.6))
    d["grab"] = ([(lambda cr: draw_hand(cr, open_=True), 0)], (13, 10))
    d["grabbing"] = ([(lambda cr: draw_hand(cr, closed=True), 0)], (13, 14))
    d["text"] = ([(ibeam, 0)], (16, 16))
    d["vertical-text"] = ([(lambda cr: (cr.translate(32, 0), cr.rotate(math.pi / 2), ibeam(cr)), 0)], (16, 16))
    d["crosshair"] = ([(crosshair, 0)], (16, 16))
    d["move"] = ([(four_way, 0)], (16, 16))
    d["ew-resize"] = ([(lambda cr: double_arrow(cr, 0), 0)], (16, 16))
    d["ns-resize"] = ([(lambda cr: double_arrow(cr, math.pi / 2), 0)], (16, 16))
    d["nwse-resize"] = ([(lambda cr: double_arrow(cr, math.pi / 4, 20), 0)], (16, 16))
    d["nesw-resize"] = ([(lambda cr: double_arrow(cr, -math.pi / 4, 20), 0)], (16, 16))
    d["col-resize"] = ([(lambda cr: double_arrow(cr, 0, 20), 0)], (16, 16))
    d["row-resize"] = ([(lambda cr: double_arrow(cr, math.pi / 2, 20), 0)], (16, 16))
    d["not-allowed"] = ([(lambda cr: no_sign(cr, 16, 16, 9), 0)], (16, 16))
    d["help"] = ([(lambda cr: (draw_arrow(cr), question(cr, 13.5, 26)), 0)], (1.5, 1.5))
    d["copy"] = ([(lambda cr: (draw_arrow(cr), badge_plus(cr, 13, 17)), 0)], (1.5, 1.5))
    d["alias"] = ([(lambda cr: (draw_arrow(cr), badge_link(cr, 13, 17)), 0)], (1.5, 1.5))
    d["context-menu"] = ([(lambda cr: (draw_arrow(cr), _menu_badge(cr)), 0)], (1.5, 1.5))
    d["cell"] = ([(plus_cell, 0)], (16, 16))
    d["pencil"] = ([(pencil, 0)], (4, 28))
    d["zoom-in"] = ([(lambda cr: magnifier(cr, "+"), 0)], (13, 13))
    d["zoom-out"] = ([(lambda cr: magnifier(cr, "-"), 0)], (13, 13))
    # animated
    steps = 12
    wait_frames = []
    prog_frames = []
    for i in range(steps + 3):
        phase = i / steps if i <= steps else 1.0 + (i - steps) / 3
        wait_frames.append((lambda cr, p=phase: hourglass(cr, 16, 16, 22, p), 110 if i <= steps else 70))
        prog_frames.append((lambda cr, p=phase: (draw_arrow(cr), hourglass(cr, 21.5, 23.5, 11, p, small=True)),
                            110 if i <= steps else 70))
    d["wait"] = (wait_frames, (16, 16))
    d["progress"] = (prog_frames, (1.5, 1.5))
    return d


def _menu_badge(cr):
    cr.rectangle(14, 16, 10, 11)
    cr.set_source_rgb(1, 1, 1)
    cr.fill_preserve()
    cr.set_source_rgb(0, 0, 0)
    cr.set_line_width(0.8)
    cr.stroke()
    for y in (19, 21.5, 24):
        cr.rectangle(16, y, 6, 1)
    cr.fill()


ALIASES = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "left-arrow", "right_ptr", "X_cursor", "dnd-none", "draft_large"],
    "pointer": ["hand1", "hand2", "hand", "pointing_hand", "9d800788f1b08800ae810202380a0822",
                "e29285e634086352946a0e7090d73106", "dnd-link"],
    "grab": ["openhand", "fleur-open"],
    "grabbing": ["closedhand", "dnd-move", "4498f0e0c1937ffe01fd06f973665830", "9081237383d90e509aa00f00170e968f"],
    "text": ["xterm", "ibeam"],
    "crosshair": ["cross", "tcross", "cross_reverse", "diamond_cross"],
    "move": ["fleur", "all-scroll", "size_all"],
    "ew-resize": ["sb_h_double_arrow", "h_double_arrow", "size_hor", "e-resize", "w-resize", "left_side",
                  "right_side", "028006030e0e7ebffc7f7070c0600140", "14fef782d02440884392942c11205230", "split_h"],
    "ns-resize": ["sb_v_double_arrow", "v_double_arrow", "size_ver", "n-resize", "s-resize", "top_side",
                  "bottom_side", "00008160000006810000408080010102", "2870a09082c103050810ffdffffe0204", "split_v"],
    "nwse-resize": ["nw-resize", "se-resize", "top_left_corner", "bottom_right_corner", "size_fdiag",
                    "fd_double_arrow", "c7088f0f3e6c8088236ef8e1e3e70000"],
    "nesw-resize": ["ne-resize", "sw-resize", "top_right_corner", "bottom_left_corner", "size_bdiag",
                    "bd_double_arrow", "fcf1c3c7cd4491d801f1e1c78f100000"],
    "col-resize": ["sb_h_double_arrow_col"],
    "row-resize": [],
    "not-allowed": ["no-drop", "forbidden", "crossed_circle", "circle", "pirate", "03b6e0fcb3499374a867c041f52298f0"],
    "help": ["question_arrow", "whats_this", "left_ptr_help", "dnd-ask", "5c6cd98b3f3ebcb1f9c7f1c204630408",
             "d9ce0ab605698f320427677b8f8af0bd"],
    "copy": ["dnd-copy", "1081e37283d90000800003c07f3ef6bf", "6407b0e94181790501fd1e167b474872"],
    "alias": ["link", "3085a0e285430894940527032f8b26df", "640fb0e74195791501fd1e167b474872"],
    "cell": ["plus"],
    "pencil": ["draft"],
    "wait": ["watch"],
    "progress": ["left_ptr_watch", "half-busy", "08e8e1c95fe2fc01f976f1e063a24ccd",
                 "3ecb610c1bf2410f44200f48c40d3599"],
}


def render_frames(outdir):
    os.makedirs(outdir, exist_ok=True)
    configs = {}
    for name, (frames, (hx, hy)) in cursor_defs().items():
        lines = []
        for fi, (fn, delay) in enumerate(frames):
            for size in SIZES:
                s, cr = ctx(size)
                fn(cr)
                fname = "%s-%d-%02d.png" % (name, size, fi)
                s.write_to_png(os.path.join(outdir, fname))
                hot_x = int(round(hx * size / BASE))
                hot_y = int(round(hy * size / BASE))
                line = "%d %d %d %s" % (size, hot_x, hot_y, fname)
                if len(frames) > 1:
                    line += " %d" % delay
                lines.append(line)
        cfg = os.path.join(outdir, name + ".cfg")
        with open(cfg, "w") as f:
            f.write("\n".join(lines) + "\n")
        configs[name] = cfg
    return configs


def build(out, theme):
    frames = os.path.abspath(os.path.join(out, ".frames"))
    configs = render_frames(frames)
    cdir = os.path.join(out, theme, "cursors")
    os.makedirs(cdir, exist_ok=True)
    for name, cfg in configs.items():
        subprocess.run(["xcursorgen", cfg, os.path.join(os.path.abspath(cdir), name)], cwd=frames, check=True)
    for target, names in ALIASES.items():
        for n in names:
            p = os.path.join(cdir, n)
            if not os.path.lexists(p) and n not in configs:
                os.symlink(target, p)
    with open(os.path.join(out, theme, "index.theme"), "w") as f:
        f.write("[Icon Theme]\nName=%s\nComment=Whistler XP style pointers (original artwork)\n"
                "Directories=cursors\n\n[cursors]\nSize=32\nType=Fixed\n" % theme)
    shutil.rmtree(frames)


def preview(path):
    from PIL import Image, ImageDraw
    defs = cursor_defs()
    cell = 70
    rows = []
    for name, (frames, _) in defs.items():
        n = len(frames) if name in ("wait", "progress") else 1
        rows.append((name, frames[:n]))
    width = cell * 16
    height = cell * (len(rows) // 2 + 2) * 2
    sheet = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    d = ImageDraw.Draw(sheet)
    y = 0
    for idx, (name, frames) in enumerate(rows):
        x = 0
        for bg in ((255, 255, 255), (58, 110, 165)):
            for fn, _ in frames if len(frames) > 1 else frames:
                for size in (32, 48):
                    s, cr = ctx(size)
                    fn(cr)
                    im = Image.frombuffer("RGBA", (size, size), bytes(s.get_data()), "raw", "BGRA", 0, 1)
                    box = Image.new("RGBA", (size + 4, size + 4), bg + (255,))
                    box.alpha_composite(im, (2, 2))
                    sheet.paste(box, (x, y + 12))
                    x += size + 8
                    if x > width - 60:
                        break
                if len(frames) > 1 and bg == (58, 110, 165):
                    break
        d.text((2, y), name, fill=(0, 0, 0))
        y += 66
    sheet = sheet.crop((0, 0, width, y))
    sheet.save(path)


def main(argv):
    theme = "whistler-lookalike-cursors"
    if "--name" in argv:
        i = argv.index("--name")
        theme = argv[i + 1]
        del argv[i:i + 2]
    if argv and argv[0] == "--preview":
        preview(argv[1])
    elif argv and argv[0] == "--frames-only":
        render_frames(argv[1])
    else:
        build(argv[0] if argv else "cursors-out", theme)


if __name__ == "__main__":
    main(sys.argv[1:])
