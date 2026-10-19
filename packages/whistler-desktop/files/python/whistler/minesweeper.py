"""Minesweeper, faithful to the Windows XP version."""
import json
import math
import os
import random

import cairo
from gi.repository import Gdk, GLib, Gtk

from .common import DATA_HOME, css_class, load_css

CELL = 16
LEVELS = {"beginner": (9, 9, 10), "intermediate": (16, 16, 40), "expert": (30, 16, 99)}
SAVE = os.path.join(DATA_HOME, "minesweeper.json")
NUM_COLORS = {1: (0, 0, 1), 2: (0, 0.5, 0), 3: (1, 0, 0), 4: (0, 0, 0.5), 5: (0.5, 0, 0),
              6: (0, 0.5, 0.5), 7: (0, 0, 0), 8: (0.5, 0.5, 0.5)}

# seven-segment layout: a b c d e f g
DIGITS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
          "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g"}


def load_state():
    try:
        with open(SAVE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    os.makedirs(DATA_HOME, exist_ok=True)
    with open(SAVE, "w") as f:
        json.dump(state, f)


def bevel(cr, x, y, w, h, raised=True, width=2):
    light, dark = (1, 1, 1), (0.5, 0.5, 0.5)
    tl, br = (light, dark) if raised else (dark, light)
    cr.set_source_rgb(0.753, 0.753, 0.753)
    cr.rectangle(x, y, w, h)
    cr.fill()
    for i in range(width):
        cr.set_source_rgb(*tl)
        cr.rectangle(x, y + i, w - i, 1)
        cr.rectangle(x + i, y, 1, h - i)
        cr.fill()
        cr.set_source_rgb(*br)
        cr.rectangle(x + i + 1, y + h - 1 - i, w - i - 1, 1)
        cr.rectangle(x + w - 1 - i, y + i + 1, 1, h - i - 1)
        cr.fill()


class LED(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.value = 0
        self.set_size_request(41, 25)
        self.connect("draw", self.on_draw)

    def set(self, v):
        self.value = v
        self.queue_draw()

    def on_draw(self, w, cr):
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.rectangle(0, 0, 41, 25)
        cr.fill()
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(1, 1, 40, 24)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(1, 1, 39, 23)
        cr.fill()
        v = max(-99, min(999, self.value))
        text = ("-%02d" % -v) if v < 0 else "%03d" % v
        for i, ch in enumerate(text):
            self.digit(cr, 2 + i * 13, 2, ch)
        return True

    def digit(self, cr, x, y, ch):
        on = DIGITS.get(ch, "")
        segs = {"a": (x + 2, y + 1, 7, 2, True), "g": (x + 2, y + 10, 7, 2, True), "d": (x + 2, y + 19, 7, 2, True),
                "f": (x + 1, y + 2, 2, 8, False), "b": (x + 9, y + 2, 2, 8, False),
                "e": (x + 1, y + 11, 2, 8, False), "c": (x + 9, y + 11, 2, 8, False)}
        for name, (sx, sy, sw, sh, _h) in segs.items():
            cr.set_source_rgb(1, 0, 0) if name in on else cr.set_source_rgb(0.35, 0, 0)
            cr.rectangle(sx, sy, sw, sh)
            cr.fill()


class Face(Gtk.Button):
    def __init__(self):
        super().__init__()
        self.mood = "smile"
        css_class(self, "mine-face")
        self.area = Gtk.DrawingArea()
        self.area.set_size_request(24, 24)
        self.area.connect("draw", self.on_draw)
        self.add(self.area)

    def set_mood(self, mood):
        self.mood = mood
        self.area.queue_draw()

    def on_draw(self, w, cr):
        cx, cy, r = 12, 12, 8.5
        cr.arc(cx, cy, r, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 0)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1)
        cr.stroke()
        if self.mood == "dead":
            for ex in (cx - 3.5, cx + 3.5):
                cr.move_to(ex - 1.5, cy - 4.5)
                cr.line_to(ex + 1.5, cy - 1.5)
                cr.move_to(ex + 1.5, cy - 4.5)
                cr.line_to(ex - 1.5, cy - 1.5)
            cr.stroke()
            cr.arc(cx, cy + 6, 3.5, math.pi * 1.15, math.pi * 1.85)
            cr.stroke()
        elif self.mood == "cool":
            cr.rectangle(cx - 6, cy - 4, 5, 3)
            cr.rectangle(cx + 1, cy - 4, 5, 3)
            cr.fill()
            cr.move_to(cx - 8, cy - 4)
            cr.line_to(cx + 8, cy - 4)
            cr.stroke()
            cr.arc(cx, cy + 0.5, 4, math.pi * 0.2, math.pi * 0.8)
            cr.stroke()
        else:
            for ex in (cx - 3, cx + 3):
                cr.rectangle(ex - 1, cy - 3.5, 2, 2)
            cr.fill()
            if self.mood == "oh":
                cr.arc(cx, cy + 3.5, 2.2, 0, 2 * math.pi)
                cr.stroke()
            else:
                cr.arc(cx, cy + 0.5, 4, math.pi * 0.2, math.pi * 0.8)
                cr.stroke()
        return True


class Field(Gtk.DrawingArea):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", game.on_press)
        self.connect("button-release-event", game.on_release)
        self.connect("motion-notify-event", game.on_motion)

    def draw_mine(self, cr, x, y):
        cx, cy = x + 8, y + 8
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1)
        for a in range(0, 360, 45):
            r = 6.5 if a % 90 == 0 else 5
            cr.move_to(cx, cy)
            cr.line_to(cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r)
        cr.stroke()
        cr.arc(cx, cy, 4, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(cx - 2, cy - 2, 2, 2)
        cr.fill()

    def draw_flag(self, cr, x, y):
        cr.set_source_rgb(1, 0, 0)
        cr.move_to(x + 9, y + 3)
        cr.line_to(x + 9, y + 9)
        cr.line_to(x + 4, y + 6)
        cr.close_path()
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(x + 8.5, y + 9, 1.5, 3)
        cr.rectangle(x + 6, y + 11, 6, 1.5)
        cr.rectangle(x + 4, y + 12.5, 10, 1.5)
        cr.fill()

    def on_draw(self, w, cr):
        g = self.game
        cr.select_font_face("Tahoma", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(12)
        for yy in range(g.h):
            for xx in range(g.w):
                x, y = xx * CELL, yy * CELL
                state = g.state[yy][xx]
                pressed = (xx, yy) in g.pressed_cells
                if state == "open" or pressed and state == "hidden":
                    cr.set_source_rgb(0.753, 0.753, 0.753)
                    cr.rectangle(x, y, CELL, CELL)
                    cr.fill()
                    if (xx, yy) == g.exploded:
                        cr.set_source_rgb(1, 0, 0)
                        cr.rectangle(x + 1, y + 1, CELL - 1, CELL - 1)
                        cr.fill()
                    cr.set_source_rgb(0.5, 0.5, 0.5)
                    cr.rectangle(x, y, CELL, 1)
                    cr.rectangle(x, y, 1, CELL)
                    cr.fill()
                    if state == "open":
                        if g.mines[yy][xx]:
                            self.draw_mine(cr, x, y)
                        else:
                            n = g.count(xx, yy)
                            if n:
                                cr.set_source_rgb(*NUM_COLORS[n])
                                ext = cr.text_extents(str(n))
                                cr.move_to(x + 8.5 - ext.width / 2 - ext.x_bearing, y + 13)
                                cr.show_text(str(n))
                else:
                    bevel(cr, x, y, CELL, CELL, True)
                    if state == "flag":
                        if g.over and not g.mines[yy][xx]:
                            self.draw_mine(cr, x, y)
                            cr.set_source_rgb(1, 0, 0)
                            cr.set_line_width(1.5)
                            cr.move_to(x + 3, y + 3)
                            cr.line_to(x + 13, y + 13)
                            cr.move_to(x + 13, y + 3)
                            cr.line_to(x + 3, y + 13)
                            cr.stroke()
                        else:
                            self.draw_flag(cr, x, y)
                    elif state == "mark":
                        cr.set_source_rgb(0, 0, 0)
                        cr.move_to(x + 4.5, y + 13)
                        cr.show_text("?")
                    elif g.over and g.mines[yy][xx] and not g.won:
                        self.draw_mine(cr, x, y)
        return True


class Minesweeper(Gtk.Window):
    def __init__(self):
        super().__init__(title="Minesweeper")
        self.set_icon_name("whistler-minesweeper")
        self.set_resizable(False)
        self.connect("destroy", Gtk.main_quit)
        self.settings = load_state()
        self.level = self.settings.get("level", "beginner")
        self.marks = self.settings.get("marks", True)
        self.timer_id = 0

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)
        vbox.pack_start(self.build_menu(), False, False, 0)
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        css_class(frame, "mine-frame")
        vbox.pack_start(frame, True, True, 0)
        header = Gtk.Box()
        css_class(header, "mine-header")
        self.counter = LED()
        self.face = Face()
        self.face.connect("clicked", lambda *_: self.new_game())
        self.clock = LED()
        header.pack_start(self.counter, False, False, 0)
        header.set_center_widget(self.face)
        header.pack_end(self.clock, False, False, 0)
        frame.pack_start(header, False, False, 0)
        holder = Gtk.Box()
        css_class(holder, "mine-field")
        self.field = Field(self)
        holder.pack_start(self.field, False, False, 0)
        frame.pack_start(holder, False, False, 0)
        self.connect("key-press-event", self.on_key)
        self.new_game()
        self.show_all()

    def build_menu(self):
        mb = Gtk.MenuBar()
        game = Gtk.MenuItem.new_with_mnemonic("_Game")
        m = Gtk.Menu()
        new = Gtk.MenuItem.new_with_mnemonic("_New\tF2")
        new.connect("activate", lambda *_: self.new_game())
        m.append(new)
        m.append(Gtk.SeparatorMenuItem())
        group = None
        for key, label in (("beginner", "_Beginner"), ("intermediate", "_Intermediate"), ("expert", "_Expert"),
                           ("custom", "_Custom...")):
            item = Gtk.RadioMenuItem.new_with_mnemonic_from_widget(group, label)
            group = group or item
            item.set_active(self.level == key)
            item.connect("activate", self.on_level, key)
            m.append(item)
        m.append(Gtk.SeparatorMenuItem())
        marks = Gtk.CheckMenuItem.new_with_mnemonic("_Marks (?)")
        marks.set_active(self.marks)
        marks.connect("toggled", self.on_marks)
        m.append(marks)
        m.append(Gtk.SeparatorMenuItem())
        best = Gtk.MenuItem.new_with_mnemonic("Best _Times...")
        best.connect("activate", lambda *_: self.best_times())
        m.append(best)
        m.append(Gtk.SeparatorMenuItem())
        ex = Gtk.MenuItem.new_with_mnemonic("E_xit")
        ex.connect("activate", lambda *_: self.destroy())
        m.append(ex)
        game.set_submenu(m)
        mb.append(game)
        helpm = Gtk.MenuItem.new_with_mnemonic("_Help")
        hm = Gtk.Menu()
        about = Gtk.MenuItem.new_with_mnemonic("_About Minesweeper...")
        about.connect("activate", lambda *_: self.about())
        hm.append(about)
        helpm.set_submenu(hm)
        mb.append(helpm)
        return mb

    # ------------------------------------------------------------- game
    def dims(self):
        if self.level == "custom":
            c = self.settings.get("custom", [9, 9, 10])
            return c[0], c[1], c[2]
        return LEVELS[self.level]

    def new_game(self):
        self.w, self.h, self.n = self.dims()
        self.mines = [[False] * self.w for _ in range(self.h)]
        self.state = [["hidden"] * self.w for _ in range(self.h)]
        self.placed = False
        self.over = self.won = False
        self.exploded = None
        self.pressed_cells = set()
        self.buttons = set()
        self.seconds = 0
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = 0
        self.field.set_size_request(self.w * CELL, self.h * CELL)
        self.counter.set(self.n)
        self.clock.set(0)
        self.face.set_mood("smile")
        self.field.queue_draw()
        self.resize(1, 1)

    def place(self, sx, sy):
        cells = [(x, y) for y in range(self.h) for x in range(self.w) if (x, y) != (sx, sy)]
        for x, y in random.sample(cells, min(self.n, len(cells))):
            self.mines[y][x] = True
        self.placed = True
        self.timer_id = GLib.timeout_add(1000, self.tick)
        self.seconds = 1
        self.clock.set(1)

    def tick(self):
        if self.over:
            return False
        self.seconds = min(999, self.seconds + 1)
        self.clock.set(self.seconds)
        return True

    def neighbors(self, x, y):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (dx or dy) and 0 <= nx < self.w and 0 <= ny < self.h:
                    yield nx, ny

    def count(self, x, y):
        return sum(1 for nx, ny in self.neighbors(x, y) if self.mines[ny][nx])

    def reveal(self, x, y):
        if self.state[y][x] != "hidden" and self.state[y][x] != "mark":
            return
        if not self.placed:
            self.place(x, y)
        if self.mines[y][x]:
            self.state[y][x] = "open"
            self.exploded = (x, y)
            self.lose()
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if self.state[cy][cx] in ("open", "flag"):
                continue
            self.state[cy][cx] = "open"
            if self.count(cx, cy) == 0:
                stack.extend(self.neighbors(cx, cy))
        self.check_win()

    def chord(self, x, y):
        if self.state[y][x] != "open":
            return
        flags = sum(1 for nx, ny in self.neighbors(x, y) if self.state[ny][nx] == "flag")
        if flags == self.count(x, y):
            for nx, ny in self.neighbors(x, y):
                if self.state[ny][nx] in ("hidden", "mark") and not self.over:
                    self.reveal(nx, ny)

    def lose(self):
        self.over = True
        self.face.set_mood("dead")
        for y in range(self.h):
            for x in range(self.w):
                if self.mines[y][x] and self.state[y][x] == "hidden":
                    self.state[y][x] = "open" if (x, y) == self.exploded else "hidden"

    def check_win(self):
        hidden = sum(1 for y in range(self.h) for x in range(self.w)
                     if self.state[y][x] != "open")
        if hidden == self.n and not self.over:
            self.over = self.won = True
            for y in range(self.h):
                for x in range(self.w):
                    if self.mines[y][x]:
                        self.state[y][x] = "flag"
            self.counter.set(0)
            self.face.set_mood("cool")
            GLib.idle_add(self.record_time)

    def flags_left(self):
        return self.n - sum(row.count("flag") for row in self.state)

    # ---------------------------------------------------------- mouse
    def cell_at(self, ev):
        x, y = int(ev.x // CELL), int(ev.y // CELL)
        if 0 <= x < self.w and 0 <= y < self.h:
            return x, y
        return None

    def update_pressed(self, ev):
        self.pressed_cells = set()
        c = self.cell_at(ev)
        if c is None or self.over:
            return
        if (1 in self.buttons and 3 in self.buttons) or 2 in self.buttons:
            self.pressed_cells = {c} | set(self.neighbors(*c))
        elif 1 in self.buttons:
            self.pressed_cells = {c}
        self.pressed_cells = {p for p in self.pressed_cells if self.state[p[1]][p[0]] == "hidden"}

    def on_press(self, w, ev):
        if self.over or ev.type != Gdk.EventType.BUTTON_PRESS:
            return True
        self.buttons.add(ev.button)
        c = self.cell_at(ev)
        if ev.button == 3 and 1 not in self.buttons and c:
            x, y = c
            s = self.state[y][x]
            if s == "hidden":
                self.state[y][x] = "flag"
            elif s == "flag":
                self.state[y][x] = "mark" if self.marks else "hidden"
            elif s == "mark":
                self.state[y][x] = "hidden"
            self.counter.set(self.flags_left())
        if 1 in self.buttons or 2 in self.buttons:
            self.face.set_mood("oh")
        self.update_pressed(ev)
        self.field.queue_draw()
        return True

    def on_motion(self, w, ev):
        if self.buttons:
            self.update_pressed(ev)
            self.field.queue_draw()
        return True

    def on_release(self, w, ev):
        if self.over:
            self.buttons.discard(ev.button)
            return True
        c = self.cell_at(ev)
        both = (1 in self.buttons and 3 in self.buttons) or ev.button == 2
        if c:
            if both:
                self.chord(*c)
            elif ev.button == 1 and 3 not in self.buttons:
                self.reveal(*c)
        self.buttons.discard(ev.button)
        if both:
            self.buttons.clear()
        self.pressed_cells = set()
        if not self.over:
            self.face.set_mood("smile")
        self.field.queue_draw()
        return True

    def on_key(self, w, ev):
        if ev.keyval == Gdk.KEY_F2:
            self.new_game()
            return True
        return False

    # ------------------------------------------------------- menus
    def on_level(self, item, key):
        if not item.get_active():
            return
        if key == "custom" and not self.custom_dialog():
            return
        self.level = key
        self.settings["level"] = key
        save_state(self.settings)
        self.new_game()

    def on_marks(self, item):
        self.marks = item.get_active()
        self.settings["marks"] = self.marks
        save_state(self.settings)

    def custom_dialog(self):
        d = Gtk.Dialog(title="Custom Field", transient_for=self, modal=True)
        d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)
        g = Gtk.Grid(column_spacing=8, row_spacing=6)
        g.set_border_width(12)
        cw, ch, cn = self.settings.get("custom", [9, 9, 10])
        spins = []
        for i, (label, val, lo, hi) in enumerate((("Height:", ch, 9, 24), ("Width:", cw, 9, 30),
                                                   ("Mines:", cn, 10, 667))):
            g.attach(Gtk.Label(label=label, xalign=0), 0, i, 1, 1)
            s = Gtk.SpinButton.new_with_range(lo, hi, 1)
            s.set_value(val)
            g.attach(s, 1, i, 1, 1)
            spins.append(s)
        d.get_content_area().pack_start(g, True, True, 0)
        d.show_all()
        ok = d.run() == Gtk.ResponseType.OK
        if ok:
            h, w, n = (int(s.get_value()) for s in spins)
            self.settings["custom"] = [w, h, min(n, (w - 1) * (h - 1))]
            save_state(self.settings)
        d.destroy()
        return ok

    def record_time(self):
        if self.level == "custom":
            return False
        best = self.settings.setdefault("best", {})
        cur = best.get(self.level, {"time": 999, "name": "Anonymous"})
        if self.seconds < cur["time"]:
            d = Gtk.Dialog(title="", transient_for=self, modal=True)
            d.add_buttons("OK", Gtk.ResponseType.OK)
            box = d.get_content_area()
            box.set_border_width(12)
            box.set_spacing(8)
            lbl = Gtk.Label(label="You have the fastest time\nfor %s level.\nPlease type your name."
                                  % self.level)
            lbl.set_justify(Gtk.Justification.CENTER)
            box.pack_start(lbl, False, False, 0)
            e = Gtk.Entry()
            e.set_text(os.environ.get("USER", "Anonymous"))
            e.set_activates_default(True)
            d.set_default_response(Gtk.ResponseType.OK)
            box.pack_start(e, False, False, 0)
            d.show_all()
            d.run()
            best[self.level] = {"time": self.seconds, "name": e.get_text() or "Anonymous"}
            d.destroy()
            save_state(self.settings)
            self.best_times()
        return False

    def best_times(self):
        best = self.settings.get("best", {})
        d = Gtk.Dialog(title="Fastest Mine Sweepers", transient_for=self, modal=True)
        reset = d.add_button("Reset Scores", 1)
        d.add_button("OK", Gtk.ResponseType.OK)
        g = Gtk.Grid(column_spacing=18, row_spacing=6)
        g.set_border_width(14)
        for i, lvl in enumerate(("beginner", "intermediate", "expert")):
            b = best.get(lvl, {"time": 999, "name": "Anonymous"})
            g.attach(Gtk.Label(label=lvl.capitalize() + ":", xalign=0), 0, i, 1, 1)
            g.attach(Gtk.Label(label="%d seconds" % b["time"], xalign=0), 1, i, 1, 1)
            g.attach(Gtk.Label(label=b["name"], xalign=0), 2, i, 1, 1)
        d.get_content_area().pack_start(g, True, True, 0)
        d.show_all()
        if d.run() == 1:
            self.settings["best"] = {}
            save_state(self.settings)
        d.destroy()

    def about(self):
        dlg = Gtk.AboutDialog(transient_for=self, modal=True)
        dlg.set_program_name("Minesweeper")
        dlg.set_logo_icon_name("whistler-minesweeper")
        dlg.set_comments("Find all the mines without setting one off.\nPart of Whistler XP.")
        dlg.set_license_type(Gtk.License.GPL_3_0)
        dlg.run()
        dlg.destroy()


def main():
    load_css("whistler.css")
    Minesweeper()
    Gtk.main()
    return 0
