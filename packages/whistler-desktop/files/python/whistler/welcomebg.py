"""Cairo painter for the XP Welcome screen backdrop (used by greeter and splash)."""
import cairo


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def bands(h):
    top = max(60, int(h * 0.102))
    bottom = max(70, int(h * 0.124))
    return top, bottom


def paint(cr, w, h, divider=False):
    top, bottom = bands(h)
    # middle field with a soft glow in the upper left
    cr.set_source_rgb(*_hex("#5A7EDC"))
    cr.paint()
    glow = cairo.RadialGradient(w * 0.08, h * 0.18, 0, w * 0.08, h * 0.18, max(w, h) * 0.62)
    glow.add_color_stop_rgba(0.0, *_hex("#A6BFF5"), 0.95)
    glow.add_color_stop_rgba(0.35, *_hex("#7C9BEB"), 0.6)
    glow.add_color_stop_rgba(1.0, *_hex("#5A7EDC"), 0.0)
    cr.set_source(glow)
    cr.rectangle(0, top, w, h - top - bottom)
    cr.fill()

    # top band + light rule
    cr.set_source_rgb(*_hex("#00309C"))
    cr.rectangle(0, 0, w, top)
    cr.fill()
    rule = cairo.LinearGradient(0, 0, w, 0)
    rule.add_color_stop_rgba(0.0, 1, 1, 1, 0.0)
    rule.add_color_stop_rgba(0.25, *_hex("#C5D4F7"), 0.9)
    rule.add_color_stop_rgba(0.5, 1, 1, 1, 1.0)
    rule.add_color_stop_rgba(0.75, *_hex("#C5D4F7"), 0.9)
    rule.add_color_stop_rgba(1.0, 1, 1, 1, 0.0)
    cr.set_source(rule)
    cr.rectangle(0, top, w, 2)
    cr.fill()

    # bottom band + orange rule
    cr.set_source_rgb(*_hex("#00309C"))
    cr.rectangle(0, h - bottom, w, bottom)
    cr.fill()
    orange = cairo.LinearGradient(0, 0, w, 0)
    orange.add_color_stop_rgba(0.0, *_hex("#3A5FCD"), 1.0)
    orange.add_color_stop_rgba(0.3, *_hex("#F2A65A"), 1.0)
    orange.add_color_stop_rgba(0.5, *_hex("#FFD99C"), 1.0)
    orange.add_color_stop_rgba(0.7, *_hex("#F2A65A"), 1.0)
    orange.add_color_stop_rgba(1.0, *_hex("#3A5FCD"), 1.0)
    cr.set_source(orange)
    cr.rectangle(0, h - bottom - 2, w, 2)
    cr.fill()

    if divider:
        x = int(w / 2)
        y0, y1 = top + h * 0.08, h - bottom - h * 0.08
        line = cairo.LinearGradient(0, y0, 0, y1)
        line.add_color_stop_rgba(0.0, 1, 1, 1, 0.0)
        line.add_color_stop_rgba(0.5, 1, 1, 1, 0.85)
        line.add_color_stop_rgba(1.0, 1, 1, 1, 0.0)
        cr.set_source(line)
        cr.rectangle(x, y0, 1, y1 - y0)
        cr.fill()
