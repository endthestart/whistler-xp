"""XP "Turn off computer" and "Log Off" dialogs over a fading, desaturating desktop."""
import os
import sys

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

from .common import css_class, icon_pixbuf, load_css, spawn

FADE_STEPS = 12
SOUNDS = "/usr/share/whistler/assets/current/sounds"


def play_and_wait(name, limit=4.0):
    """Play a scheme sound (like XP's logoff/shutdown sounds) before leaving."""
    import subprocess
    path = os.path.join(SOUNDS, name + ".wav")
    if not os.path.exists(path):
        return
    while Gtk.events_pending():
        Gtk.main_iteration()
    try:
        subprocess.run(["paplay", path], timeout=limit, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        pass


class ShutdownScreen(Gtk.Window):
    def __init__(self, mode):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.mode = mode
        screen = Gdk.Screen.get_default()
        root = screen.get_root_window()
        self.w, self.h = root.get_width(), root.get_height()
        self.shot = Gdk.pixbuf_get_from_window(root, 0, 0, self.w, self.h)
        self.current = self.shot.copy() if self.shot else None
        self.step = 0
        self.set_default_size(self.w, self.h)
        self.move(0, 0)
        self.set_app_paintable(True)
        self.connect("draw", self.on_draw)
        self.connect("key-press-event", self.on_key)
        self.connect("destroy", Gtk.main_quit)

        overlay = Gtk.Overlay()
        self.add(overlay)
        bg = Gtk.DrawingArea()
        bg.connect("draw", self.on_draw)
        overlay.add(bg)
        dialog = self.build_dialog()
        dialog.set_halign(Gtk.Align.CENTER)
        dialog.set_valign(Gtk.Align.CENTER)
        overlay.add_overlay(dialog)

        self.grab_tries = 0
        self.connect("map-event", lambda *_: GLib.timeout_add(20, self.grab) and False)
        self.show_all()
        if self.shot is not None:
            GLib.timeout_add(80, self.fade)

    def grab(self):
        seat = Gdk.Display.get_default().get_default_seat()
        status = seat.grab(self.get_window(), Gdk.SeatCapabilities.ALL, True, None, None, None, None)
        self.grab_tries += 1
        return status != Gdk.GrabStatus.SUCCESS and self.grab_tries < 40

    def fade(self):
        self.step += 1
        sat = max(0.0, 1.0 - self.step / FADE_STEPS)
        self.shot.saturate_and_pixelate(self.current, sat, False)
        self.queue_draw()
        return self.step < FADE_STEPS

    def on_draw(self, widget, cr):
        if self.current is not None:
            Gdk.cairo_set_source_pixbuf(cr, self.current, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.paint()
        return False

    def on_key(self, w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    def action_button(self, icon, label, cb):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        css_class(btn, "xp-off-button")
        pb = icon_pixbuf(icon, 33)
        btn.add(Gtk.Image.new_from_pixbuf(pb))
        btn.connect("clicked", lambda *_: cb())
        btn.set_halign(Gtk.Align.CENTER)
        lbl = Gtk.Label(label=label)
        css_class(lbl, "xp-off-label")
        box.pack_start(btn, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        return box

    def build_dialog(self):
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        css_class(frame, "xp-off-dialog")
        frame.set_size_request(313, 198)

        top = Gtk.Box()
        css_class(top, "xp-off-top")
        title = Gtk.Label(label="Turn off computer" if self.mode == "turnoff" else "Log Off Whistler",
                          xalign=0)
        css_class(title, "xp-off-title")
        top.pack_start(title, True, True, 0)
        theme = Gtk.IconTheme.get_default()
        logo = icon_pixbuf("whistler-dialog-logo" if theme.has_icon("whistler-dialog-logo") else "whistler-logo", 32)
        if logo:
            top.pack_end(Gtk.Image.new_from_pixbuf(logo), False, False, 0)
        frame.pack_start(top, False, False, 0)

        mid = Gtk.Box(spacing=0, homogeneous=True)
        css_class(mid, "xp-off-middle")
        if self.mode == "turnoff":
            mid.pack_start(self.action_button("whistler-standby", "Stand By", lambda: self.do("--suspend")),
                           True, True, 0)
            mid.pack_start(self.action_button("whistler-turnoff", "Turn Off", lambda: self.do("--halt")),
                           True, True, 0)
            mid.pack_start(self.action_button("whistler-restart", "Restart", lambda: self.do("--reboot")),
                           True, True, 0)
        else:
            mid.pack_start(self.action_button("whistler-switchuser", "Switch User", self.switch_user),
                           True, True, 0)
            mid.pack_start(self.action_button("whistler-logoff", "Log Off", lambda: self.do("--logout")),
                           True, True, 0)
        frame.pack_start(mid, True, True, 0)

        bottom = Gtk.Box()
        css_class(bottom, "xp-off-bottom")
        cancel = Gtk.Button(label="Cancel")
        cancel.set_size_request(75, 23)
        cancel.connect("clicked", lambda *_: self.destroy())
        bottom.pack_end(cancel, False, False, 0)
        frame.pack_start(bottom, False, False, 0)
        cancel.grab_focus()
        return frame

    def do(self, flag):
        self.hide()
        sound = "system-shutdown" if flag in ("--halt", "--reboot") else "desktop-logout"
        play_and_wait(sound)
        spawn(["/usr/bin/xfce4-session-logout", flag, "--fast"])
        GLib.timeout_add(300, Gtk.main_quit)

    def switch_user(self):
        self.hide()
        spawn(["dm-tool", "switch-to-greeter"])
        GLib.timeout_add(300, Gtk.main_quit)


def single_instance():
    """Only one Turn Off/Log Off screen at a time (it grabs the pointer)."""
    import fcntl
    path = os.path.join(GLib.get_user_runtime_dir(), "whistler-shutdown.lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(0)
    return fd


def main(mode=None):
    _lock = single_instance()
    if mode is None:
        mode = "logoff" if "--logoff" in sys.argv else "turnoff"
    load_css("dialogs.css")
    ShutdownScreen(mode)
    Gtk.main()
    return 0


def main_logoff():
    return main("logoff")
