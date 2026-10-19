"""LightDM greeter that recreates the Windows XP Welcome screen."""
import os
import subprocess
import sys

import gi

gi.require_version("LightDM", "1")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, LightDM, Pango, PangoCairo  # noqa: E402

from . import welcomebg  # noqa: E402
from .common import css_class, icon_pixbuf, load_css  # noqa: E402

LOGO = "/usr/share/whistler/logos/wordmark.png"
GREETER = "/usr/share/whistler/assets/current/greeter"


def greeter_image(name):
    path = os.path.join(GREETER, name + ".png")
    if os.path.exists(path):
        try:
            return GdkPixbuf.Pixbuf.new_from_file(path)
        except GLib.Error:
            return None
    return None
USERPICS = "/usr/share/whistler/assets/current/userpics"


def user_pixbuf(user, size):
    for path in (user.get_image(), os.path.join(user.get_home_directory() or "/nonexistent", ".face"),
                 os.path.join("/var/lib/AccountsService/icons", user.get_name())):
        if path and os.path.isfile(path):
            try:
                return GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, False)
            except GLib.Error:
                pass
    pics = sorted(f for f in os.listdir(USERPICS) if f.endswith(".png")) if os.path.isdir(USERPICS) else []
    if pics:
        pick = pics[sum(map(ord, user.get_name())) % len(pics)]
        return GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(USERPICS, pick), size, size, False)
    return icon_pixbuf("avatar-default", size)


class UserTile(Gtk.EventBox):
    """Picture + name; expands to a password box when selected."""

    def __init__(self, greeter, user):
        super().__init__()
        self.greeter = greeter
        self.user = user
        self.set_visible_window(False)
        css_class(self, "xp-user-tile")
        self.box = Gtk.Box(spacing=12)
        css_class(self.box, "xp-user-box")
        self.add(self.box)

        frame = Gtk.Box()
        css_class(frame, "xp-user-picture")
        frame.add(Gtk.Image.new_from_pixbuf(user_pixbuf(user, 48)))
        frame.set_valign(Gtk.Align.START)
        self.box.pack_start(frame, False, False, 0)

        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        col.set_valign(Gtk.Align.CENTER)
        name = Gtk.Label(label=user.get_display_name() or user.get_name(), xalign=0)
        css_class(name, "xp-user-name")
        col.pack_start(name, False, False, 0)
        self.status = Gtk.Label(xalign=0)
        css_class(self.status, "xp-user-status")
        col.pack_start(self.status, False, False, 0)

        self.pw_row = Gtk.Box(spacing=6)
        self.prompt = Gtk.Label(label="Type your password", xalign=0)
        css_class(self.prompt, "xp-user-prompt")
        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        self.entry.set_width_chars(18)
        css_class(self.entry, "xp-password")
        self.entry.connect("activate", lambda *_: greeter.submit(self))
        go = Gtk.Button()
        go.set_relief(Gtk.ReliefStyle.NONE)
        css_class(go, "xp-go")
        go.add(Gtk.Image.new_from_pixbuf(icon_pixbuf("whistler-go", 22)))
        go.connect("clicked", lambda *_: greeter.submit(self))
        hint = Gtk.Button()
        hint.set_relief(Gtk.ReliefStyle.NONE)
        css_class(hint, "xp-go")
        theme = Gtk.IconTheme.get_default()
        hint.add(Gtk.Image.new_from_pixbuf(icon_pixbuf(
            "whistler-help-tile" if theme.has_icon("whistler-help-tile") else "whistler-help", 22)))
        hint.connect("clicked", lambda *_: self.show_hint())
        self.pw_row.pack_start(self.entry, False, False, 0)
        self.pw_row.pack_start(go, False, False, 0)
        self.pw_row.pack_start(hint, False, False, 0)
        self.pw_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.pw_box.pack_start(self.prompt, False, False, 0)
        self.pw_box.pack_start(self.pw_row, False, False, 0)
        self.pw_box.set_no_show_all(True)
        col.pack_start(self.pw_box, False, False, 0)
        self.box.pack_start(col, True, True, 0)

        self.connect("button-press-event", lambda *_: greeter.select(self))
        self.connect("enter-notify-event", self.on_enter)
        self.connect("leave-notify-event", self.on_leave)

    def on_enter(self, *_):
        self.box.get_style_context().add_class("hover")

    def on_leave(self, w, ev):
        if ev.detail != Gdk.NotifyType.INFERIOR:
            self.box.get_style_context().remove_class("hover")

    def set_selected(self, selected):
        ctx = self.box.get_style_context()
        (ctx.add_class if selected else ctx.remove_class)("selected")
        if not selected:
            self.pw_box.hide()
            self.status.set_text("")

    def ask_password(self, text):
        if not text or text.strip().lower().rstrip(":") == "password":
            text = "Type your password"
        self.prompt.set_text(text.rstrip(": "))
        self.pw_box.set_no_show_all(False)
        self.pw_box.show_all()
        self.entry.set_text("")
        self.entry.set_sensitive(True)
        self.entry.grab_focus()

    def show_hint(self):
        self.status.set_text("Ask your administrator if you forgot your password.")


class Greeter(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.ldm = LightDM.Greeter()
        self.ldm.connect("show-prompt", self.on_prompt)
        self.ldm.connect("show-message", self.on_message)
        self.ldm.connect("authentication-complete", self.on_auth_complete)
        try:
            self.ldm.connect_to_daemon_sync()
        except GLib.Error as e:
            print("whistler-greeter: cannot reach LightDM: %s" % e, file=sys.stderr)
        self.selected = None
        self.state = "users"
        self.banner = ""

        screen = Gdk.Screen.get_default()
        self.w, self.h = screen.get_width(), screen.get_height()
        self.set_default_size(self.w, self.h)
        self.move(0, 0)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.connect("draw", self.on_draw)
        self.connect("destroy", Gtk.main_quit)
        root = screen.get_root_window()
        root.set_cursor(Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.LEFT_PTR))

        top, bottom = welcomebg.bands(self.h)
        self.layout = Gtk.Fixed()
        self.add(self.layout)

        # right half: scrolling list of accounts
        self.users_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        css_class(self.users_box, "xp-users")
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.add(self.users_box)
        css_class(scroller, "xp-users-scroller")
        list_h = self.h - top - bottom - 40
        scroller.set_size_request(int(self.w * 0.42), list_h)
        self.layout.put(scroller, int(self.w / 2) + 10, top + 20)
        self.scroller = scroller

        users = LightDM.UserList.get_instance().get_users()
        self.tiles = []
        for u in users:
            tile = UserTile(self, u)
            self.tiles.append(tile)
            self.users_box.pack_start(tile, False, False, 0)
        GLib.idle_add(self.center_users, list_h)

        # bottom left: turn off computer
        off = Gtk.Button()
        off.set_relief(Gtk.ReliefStyle.NONE)
        css_class(off, "xp-turnoff")
        ob = Gtk.Box(spacing=8)
        ob.pack_start(Gtk.Image.new_from_pixbuf(icon_pixbuf("whistler-turnoff", 24)), False, False, 0)
        ob.pack_start(Gtk.Label(label="Turn off computer"), False, False, 0)
        off.add(ob)
        off.connect("clicked", self.on_turnoff)
        self.layout.put(off, int(self.w * 0.03), self.h - bottom + int(bottom / 2) - 16)

        # bottom right: hint
        hint = Gtk.Label(label="After you log on, you can add or change accounts.\n"
                               "Just go to Control Panel and click User Accounts.", xalign=0)
        css_class(hint, "xp-bottom-hint")
        self.layout.put(hint, int(self.w * 0.60), self.h - bottom + int(bottom / 2) - 14)

        self.logo = greeter_image("logo")
        if self.logo is None:
            try:
                self.logo = GdkPixbuf.Pixbuf.new_from_file(LOGO)
            except GLib.Error:
                self.logo = None
        self.art = {n: greeter_image(n) for n in ("glow", "line-top", "line-bottom", "divider")}
        self.show_all()
        hint_user = self.ldm.get_select_user_hint()
        for t in self.tiles:
            if hint_user and t.user.get_name() == hint_user:
                self.select(t)

    def center_users(self, list_h):
        nat = self.users_box.get_preferred_height()[1]
        pad = max(0, (list_h - nat) // 2)
        self.users_box.set_margin_top(pad)
        return False

    # -------------------------------------------------------------- drawing
    def blit(self, cr, pb, x, y, w=None, h=None):
        cr.save()
        cr.translate(x, y)
        if w or h:
            cr.scale((w or pb.get_width()) / pb.get_width(), (h or pb.get_height()) / pb.get_height())
        Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
        cr.paint()
        cr.restore()

    def on_draw(self, w, cr):
        imported = any(self.art.values())
        welcomebg.paint(cr, self.w, self.h, divider=(self.state == "users" and not self.art.get("divider")))
        top, bottom = welcomebg.bands(self.h)
        if imported:
            if self.art.get("glow"):
                g = self.art["glow"]
                px = g.get_pixels()
                off = (g.get_height() - 1) * g.get_rowstride() + (g.get_width() - 1) * g.get_n_channels()
                cr.set_source_rgb(px[off] / 255, px[off + 1] / 255, px[off + 2] / 255)
                cr.rectangle(0, top, self.w, self.h - top - bottom)
                cr.fill()
                self.blit(cr, g, 0, top)
            if self.art.get("line-top"):
                self.blit(cr, self.art["line-top"], 0, top, w=self.w)
            if self.art.get("line-bottom"):
                lb = self.art["line-bottom"]
                self.blit(cr, lb, 0, self.h - bottom - lb.get_height(), w=self.w)
            if self.art.get("divider") and self.state == "users":
                dv = self.art["divider"]
                span = self.h - top - bottom - 2 * int(self.h * 0.06)
                self.blit(cr, dv, self.w / 2, top + int(self.h * 0.06), h=span)
        if self.state == "users":
            cx = self.w / 2
            if self.logo is not None:
                lw = self.logo.get_width()
                lh = self.logo.get_height()
                scale = min(1.0, (self.w * 0.40) / lw)
                cr.save()
                cr.translate(cx - lw * scale - self.w * 0.03, self.h / 2 - lh * scale - 10)
                cr.scale(scale, scale)
                Gdk.cairo_set_source_pixbuf(cr, self.logo, 0, 0)
                cr.paint()
                cr.restore()
            layout = PangoCairo.create_layout(cr)
            layout.set_font_description(Pango.FontDescription("Tahoma %dpx" % max(14, int(self.h * 0.024))))
            layout.set_text("To begin, click your user name", -1)
            tw, th = layout.get_pixel_size()
            cr.set_source_rgb(1, 1, 1)
            cr.move_to(cx - tw - self.w * 0.04, self.h / 2 + 12)
            PangoCairo.show_layout(cr, layout)
        else:
            layout = PangoCairo.create_layout(cr)
            layout.set_font_description(Pango.FontDescription(
                "Trebuchet MS Bold Italic %dpx" % max(28, int(self.h * 0.075))))
            layout.set_text(self.banner, -1)
            tw, th = layout.get_pixel_size()
            x, y = self.w * 0.5 - tw * 0.62, self.h * 0.5 - th * 0.62
            cr.set_source_rgba(0, 0, 0, 0.35)
            cr.move_to(x + 2, y + 2)
            PangoCairo.show_layout(cr, layout)
            cr.set_source_rgb(1, 1, 1)
            cr.move_to(x, y)
            PangoCairo.show_layout(cr, layout)
        return False

    # -------------------------------------------------------- authentication
    def select(self, tile):
        if self.selected is tile and tile.pw_box.get_visible():
            return
        for t in self.tiles:
            t.set_selected(t is tile)
        self.selected = tile
        if self.ldm.get_in_authentication():
            self.ldm.cancel_authentication()
        self.ldm.authenticate(tile.user.get_name())

    def on_prompt(self, ldm, text, prompt_type):
        if self.selected is None:
            return
        if prompt_type == LightDM.PromptType.SECRET:
            self.selected.ask_password(text)
        else:
            self.selected.ask_password(text)
            self.selected.entry.set_visibility(True)

    def on_message(self, ldm, text, mtype):
        if self.selected is not None:
            self.selected.status.set_text(text)

    def submit(self, tile):
        if tile is not self.selected:
            return
        tile.entry.set_sensitive(False)
        self.ldm.respond(tile.entry.get_text())

    def on_auth_complete(self, ldm):
        tile = self.selected
        if self.ldm.get_is_authenticated():
            self.show_banner("welcome")
            GLib.timeout_add(700, self.start_session)
        else:
            if tile is not None:
                tile.status.set_text("Did you forget your password? Please type your password again.\n"
                                     "Be sure to use the correct uppercase and lowercase letters.")
            if tile is not None:
                self.ldm.authenticate(tile.user.get_name())

    def show_banner(self, text):
        self.state = "banner"
        self.banner = text
        self.scroller.hide()
        self.queue_draw()

    def start_session(self):
        session = None
        if self.selected is not None:
            session = self.selected.user.get_session()
        session = session or self.ldm.get_default_session_hint() or "whistler"
        try:
            self.ldm.start_session_sync(session)
        except GLib.Error as e:
            print("whistler-greeter: cannot start session %s: %s" % (session, e), file=sys.stderr)
            try:
                self.ldm.start_session_sync(None)
            except GLib.Error:
                self.state = "users"
                self.scroller.show()
                self.queue_draw()
        return False

    def on_turnoff(self, *_):
        dlg = Gtk.Dialog(title="Turn off computer", transient_for=self, modal=True)
        dlg.add_buttons("Stand By", 1, "Turn Off", 2, "Restart", 3, "Cancel", Gtk.ResponseType.CANCEL)
        r = dlg.run()
        dlg.destroy()
        if r == 1 and LightDM.get_can_suspend():
            LightDM.suspend()
        elif r == 2 and LightDM.get_can_shutdown():
            LightDM.shutdown()
        elif r == 3 and LightDM.get_can_restart():
            LightDM.restart()


def main():
    subprocess.Popen(["xsetroot", "-cursor_name", "left_ptr"], stderr=subprocess.DEVNULL)
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-theme-name", "Whistler")
    settings.set_property("gtk-icon-theme-name", "Whistler")
    settings.set_property("gtk-cursor-theme-name", "Whistler")
    settings.set_property("gtk-font-name", "Tahoma 8")
    load_css("greeter.css")
    Greeter()
    Gtk.main()
    return 0
