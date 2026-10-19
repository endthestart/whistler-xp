"""Full-screen "welcome" shown while the desktop starts, like XP after logon."""
import os
import subprocess
import sys
import time

from gi.repository import Gdk, GLib, Gtk, Pango, PangoCairo

from . import welcomebg
from .common import SHARE

MIN_SECONDS = 2.0
MAX_SECONDS = 12.0
SOUNDS = "/usr/share/whistler/assets/current/sounds"
BOOT_MARK = "/tmp/.whistler-bootup-sound-played"


def startup_sound():
    """The big startup sound once per boot (like XP), the log-on sound after that."""
    if not os.path.exists(BOOT_MARK):
        try:
            open(BOOT_MARK, "w").close()
            os.chmod(BOOT_MARK, 0o666)
        except OSError:
            pass
        return os.path.join(SOUNDS, "system-bootup.wav")
    return os.path.join(SOUNDS, "desktop-login.wav")


def desktop_ready():
    try:
        out = subprocess.run(["xprop", "-root", "_NET_CLIENT_LIST"], capture_output=True,
                             text=True, timeout=2).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    if "window id" not in out:
        return False
    try:
        procs = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "xfce4-panel"],
                               capture_output=True, timeout=2).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        procs = False
    return procs


class Splash(Gtk.Window):
    def __init__(self, text):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.text = text
        screen = Gdk.Screen.get_default()
        self.w, self.h = screen.get_width(), screen.get_height()
        self.set_default_size(self.w, self.h)
        self.move(0, 0)
        self.set_app_paintable(True)
        visual = screen.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)
        self.connect("draw", self.on_draw)
        self.connect("destroy", Gtk.main_quit)
        self.started = time.monotonic()
        self.opacity = 1.0
        self.show_all()
        GLib.timeout_add(150, self.tick)

    def on_draw(self, w, cr):
        cr.push_group()
        welcomebg.paint(cr, self.w, self.h)
        layout = PangoCairo.create_layout(cr)
        size = max(28, int(self.h * 0.075))
        layout.set_font_description(Pango.FontDescription(
            "Trebuchet MS Bold Italic %dpx" % size))
        layout.set_text(self.text, -1)
        tw, th = layout.get_pixel_size()
        x, y = self.w * 0.5 - tw * 0.62, self.h * 0.5 - th * 0.62
        cr.set_source_rgba(0, 0, 0, 0.35)
        cr.move_to(x + 2, y + 2)
        PangoCairo.show_layout(cr, layout)
        cr.set_source_rgb(1, 1, 1)
        cr.move_to(x, y)
        PangoCairo.show_layout(cr, layout)
        cr.pop_group_to_source()
        cr.paint_with_alpha(self.opacity)
        return True

    def tick(self):
        gdkwin = self.get_window()
        if gdkwin is not None:
            gdkwin.raise_()
        elapsed = time.monotonic() - self.started
        if elapsed > MAX_SECONDS or (elapsed > MIN_SECONDS and desktop_ready()):
            GLib.timeout_add(600, self.begin_fade)
            return False
        return True

    def begin_fade(self):
        sound = startup_sound()
        if os.path.exists(sound):
            subprocess.Popen(["paplay", sound], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        GLib.timeout_add(30, self.fade)
        return False

    def fade(self):
        if not self.get_screen().is_composited():
            self.destroy()
            return False
        self.opacity -= 0.08
        if self.opacity <= 0:
            self.destroy()
            return False
        self.queue_draw()
        return True


def main():
    text = "welcome"
    if "--text" in sys.argv:
        text = sys.argv[sys.argv.index("--text") + 1]
    Splash(text)
    Gtk.main()
    return 0
