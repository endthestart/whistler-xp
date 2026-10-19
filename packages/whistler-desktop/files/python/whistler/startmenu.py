"""The two-column XP-style start menu."""
import os
import subprocess
import sys
import time

from gi.repository import Gdk, Gio, GLib, Gtk, Pango

from . import apps
from .common import (css_class, display_name, gicon_pixbuf, icon_pixbuf, image,
                     launch_app, load_css, open_uri, spawn, user_dir, user_picture)

MENU_WIDTH = 380


def panel_event(visible):
    """Tell the taskbar start button whether to look pressed."""
    app = Gio.Application.get_default()
    conn = app.get_dbus_connection() if app else None
    if conn is None:
        return
    try:
        conn.emit_signal(None, "/org/whistler/StartMenu", "org.whistler.StartMenu", "VisibilityChanged",
                         GLib.Variant("(b)", (visible,)))
    except GLib.Error:
        pass


def ellipsize(label, chars):
    label.set_ellipsize(Pango.EllipsizeMode.END)
    label.set_max_width_chars(chars)
    return label


class Item(Gtk.Button):
    """A start menu row: icon, bold or normal title, optional grey subtitle."""

    def __init__(self, icon, title, subtitle=None, size=32, bold=False, arrow=False, pixbuf=None):
        super().__init__()
        self.set_relief(Gtk.ReliefStyle.NONE)
        css_class(self, "sm-item")
        box = Gtk.Box(spacing=6)
        img = Gtk.Image.new_from_pixbuf(pixbuf) if pixbuf else image(icon, size)
        img.set_size_request(size, size)
        box.pack_start(img, False, False, 0)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        texts.set_valign(Gtk.Align.CENTER)
        t = ellipsize(Gtk.Label(label=title, xalign=0), 26 if size == 32 else 34)
        css_class(t, "sm-title")
        if bold:
            css_class(t, "bold")
        texts.pack_start(t, False, False, 0)
        if subtitle:
            s = ellipsize(Gtk.Label(label=subtitle, xalign=0), 28)
            css_class(s, "sm-subtitle")
            texts.pack_start(s, False, False, 0)
        box.pack_start(texts, True, True, 0)
        if arrow:
            a = Gtk.Label(label="▸")
            css_class(a, "sm-arrow")
            box.pack_end(a, False, False, 0)
        self.add(box)


class StartMenu(Gtk.Window):
    def __init__(self, app):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.app = app
        self.set_application(app)
        self.set_title("Start Menu")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        self.stick()
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)
        css_class(self, "whistler-startmenu-window")

        self.mfu = apps.MFU()
        self.grabbed = False
        self.hidden_at = 0.0
        self.programs_menu = None
        self.submenu = None
        self.hover_source = 0

        self.connect("key-press-event", self.on_key)
        self.connect("button-press-event", self.on_button)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("delete-event", lambda *a: self.hide_menu() or True)
        self.connect("grab-broken-event", self.on_grab_broken)

        self.monitor = Gio.AppInfoMonitor.get()
        self.monitor.connect("changed", lambda *_: setattr(self, "programs_menu", None))
        self.build()

    # ------------------------------------------------------------------ build
    def build(self):
        child = self.get_child()
        if child:
            child.destroy()
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_name("startmenu")
        outer.set_size_request(MENU_WIDTH, -1)

        # header
        header = Gtk.Box(spacing=8)
        header.set_name("sm-header")
        pic = user_picture()
        frame = Gtk.Box()
        frame.set_name("sm-userpic")
        pb = icon_pixbuf(pic, 48) if pic else icon_pixbuf("avatar-default", 48)
        frame.add(Gtk.Image.new_from_pixbuf(pb))
        header.pack_start(frame, False, False, 0)
        name = Gtk.Label(label=display_name(), xalign=0)
        name.set_name("sm-username")
        header.pack_start(name, True, True, 0)
        outer.pack_start(header, False, False, 0)
        line = Gtk.Box()
        line.set_name("sm-orange-line")
        outer.pack_start(line, False, False, 0)

        body = Gtk.Box()
        body.set_name("sm-body")
        outer.pack_start(body, True, True, 0)

        # left column
        self.left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left.set_name("sm-left")
        body.pack_start(self.left, True, True, 0)
        self.pinned_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left.pack_start(self.pinned_box, False, False, 0)
        sep = Gtk.Box()
        css_class(sep, "sm-sep-left")
        self.left.pack_start(sep, False, False, 0)
        self.mfu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left.pack_start(self.mfu_box, True, True, 0)
        sep = Gtk.Box()
        css_class(sep, "sm-sep-left")
        self.left.pack_start(sep, False, False, 0)
        allp = Gtk.Button()
        allp.set_relief(Gtk.ReliefStyle.NONE)
        allp.set_name("sm-allprograms")
        ab = Gtk.Box(spacing=8)
        ab.set_halign(Gtk.Align.CENTER)
        al = Gtk.Label(label="All Programs")
        css_class(al, "bold")
        ab.pack_start(al, False, False, 0)
        ab.pack_start(image("whistler-allprograms-arrow", 20), False, False, 0)
        allp.add(ab)
        allp.connect("clicked", lambda b: self.show_programs(b))
        allp.connect("enter-notify-event", lambda b, e: self.hover_open(b, self.show_programs))
        allp.connect("leave-notify-event", lambda *_: self.cancel_hover())
        self.allp = allp
        self.left.pack_start(allp, False, False, 0)

        # right column
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right.set_name("sm-right")
        body.pack_start(right, True, True, 0)

        def ritem(icon, title, cb, bold=False, arrow=False):
            it = Item(icon, title, size=24, bold=bold, arrow=arrow)
            css_class(it, "sm-right-item")
            if arrow:
                it.connect("clicked", lambda w: cb(w))
                it.connect("enter-notify-event", lambda w, e: self.hover_open(w, cb))
                it.connect("leave-notify-event", lambda *_: self.cancel_hover())
            else:
                it.connect("clicked", lambda w: self.activate(cb))
                it.connect("enter-notify-event", lambda *_: self.close_submenu())
            right.pack_start(it, False, False, 0)

        def rsep():
            s = Gtk.Box()
            css_class(s, "sm-sep-right")
            right.pack_start(s, False, False, 0)

        docs = user_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS, "~/My Documents")
        ritem("folder-documents", "My Documents", lambda: open_uri(docs), bold=True)
        ritem("document-open-recent", "My Recent Documents", self.show_recent, bold=True, arrow=True)
        ritem("folder-pictures", "My Pictures",
              lambda: open_uri(user_dir(GLib.UserDirectory.DIRECTORY_PICTURES, "~/Pictures")), bold=True)
        ritem("folder-music", "My Music",
              lambda: open_uri(user_dir(GLib.UserDirectory.DIRECTORY_MUSIC, "~/Music")), bold=True)
        ritem("computer", "My Computer", lambda: spawn(["whistler-mycomputer"]), bold=True)
        rsep()
        ritem("preferences-system", "Control Panel", lambda: spawn(["whistler-control"]))
        ritem("preferences-desktop-default-applications", "Set Program Access and Defaults",
              lambda: spawn(["xfce4-mime-settings"]))
        ritem("network-workgroup", "Connect To", self.show_connect, arrow=True)
        ritem("printer", "Printers and Faxes", lambda: spawn(["system-config-printer"]))
        rsep()
        ritem("help-browser", "Help and Support", lambda: spawn(["whistler-help"]))
        ritem("system-search", "Search", lambda: spawn(["catfish"]))
        ritem("system-run", "Run...", lambda: spawn(["whistler-run"]))
        right.pack_start(Gtk.Box(), True, True, 0)

        # footer
        footer = Gtk.Box(spacing=4)
        footer.set_name("sm-footer")
        footer.pack_start(Gtk.Box(), True, True, 0)
        for icon, text, cmd in (("whistler-logoff", "Log Off", "whistler-logoff"),
                                ("whistler-turnoff", "Turn Off Computer", "whistler-shutdown")):
            b = Gtk.Button()
            b.set_relief(Gtk.ReliefStyle.NONE)
            css_class(b, "sm-footer-button")
            bb = Gtk.Box(spacing=4)
            bb.pack_start(image(icon, 24), False, False, 0)
            bb.pack_start(Gtk.Label(label=text), False, False, 0)
            b.add(bb)
            b.connect("clicked", lambda w, c=cmd: self.activate(lambda: spawn([c])))
            footer.pack_start(b, False, False, 0)
        outer.pack_start(footer, False, False, 0)

        self.add(outer)
        outer.show_all()

    def refresh_left(self):
        for box in (self.pinned_box, self.mfu_box):
            for c in box.get_children():
                c.destroy()
        pinned_ids = set()
        for app_id, title, sub in apps.PINNED:
            info = apps.lookup(app_id)
            if info is None:
                continue
            pinned_ids.add(app_id)
            it = Item(None, title, subtitle=sub, size=32, bold=True,
                      pixbuf=gicon_pixbuf(info.get_icon(), 32))
            it.connect("clicked", lambda w, i=info: self.launch(i))
            it.connect("enter-notify-event", lambda *_: self.close_submenu())
            self.pinned_box.pack_start(it, False, False, 0)
        for info in self.mfu.top(6, exclude=pinned_ids):
            it = Item(None, info.get_display_name() or info.get_name(), size=32,
                      pixbuf=gicon_pixbuf(info.get_icon(), 32))
            it.set_tooltip_text(info.get_description() or None)
            it.connect("clicked", lambda w, i=info: self.launch(i))
            it.connect("enter-notify-event", lambda *_: self.close_submenu())
            self.mfu_box.pack_start(it, False, False, 0)
        self.pinned_box.show_all()
        self.mfu_box.show_all()

    # -------------------------------------------------------------- show/hide
    def toggle(self):
        if self.get_visible():
            self.hide_menu()
        elif time.monotonic() - self.hidden_at > 0.3:
            self.show_menu()
        else:
            panel_event(False)

    def show_menu(self):
        self.refresh_left()
        _, work = self._geometry()
        self.show()
        w, h = self.get_size()
        _, nat = self.get_preferred_size()
        h = max(h, nat.height)
        self.move(work.x, work.y + work.height - h)
        self.present_with_time(Gtk.get_current_event_time() or Gdk.CURRENT_TIME)
        self.set_focus(None)
        panel_event(True)
        self.grab_tries = 0
        GLib.timeout_add(30, self.try_grab)

    def _geometry(self):
        display = Gdk.Display.get_default()
        mon = display.get_primary_monitor() or display.get_monitor(0)
        return mon.get_geometry(), mon.get_workarea()

    def try_grab(self):
        if not self.get_visible():
            return False
        gdkwin = self.get_window()
        seat = Gdk.Display.get_default().get_default_seat()
        status = seat.grab(gdkwin, Gdk.SeatCapabilities.ALL, True, None, None, None, None)
        if status == Gdk.GrabStatus.SUCCESS:
            self.grabbed = True
            return False
        self.grab_tries += 1
        return self.grab_tries < 20

    def ungrab(self):
        if self.grabbed:
            Gdk.Display.get_default().get_default_seat().ungrab()
            self.grabbed = False

    def hide_menu(self):
        self.cancel_hover()
        self.close_submenu()
        self.ungrab()
        if self.get_visible():
            self.hide()
            self.hidden_at = time.monotonic()
        panel_event(False)

    # ----------------------------------------------------------------- events
    def on_key(self, w, ev):
        if ev.keyval in (Gdk.KEY_Escape, Gdk.KEY_Super_L, Gdk.KEY_Super_R):
            self.hide_menu()
            return True
        return False

    def on_button(self, w, ev):
        x, y = self.get_position()
        width, height = self.get_size()
        if not (x <= ev.x_root < x + width and y <= ev.y_root < y + height):
            self.hide_menu()
            return True
        return False

    def on_focus_out(self, w, ev):
        if not self.grabbed and self.submenu is None:
            self.hide_menu()
        return False

    def on_grab_broken(self, w, ev):
        self.grabbed = False
        return False

    # -------------------------------------------------------------- launching
    def activate(self, cb):
        self.hide_menu()
        GLib.idle_add(lambda: cb() and False)

    def launch(self, info):
        self.hide_menu()
        launch_app(info)
        self.mfu.record(info.get_id())

    # --------------------------------------------------------------- submenus
    def hover_open(self, widget, opener):
        self.cancel_hover()
        if self.submenu is not None and getattr(self, "submenu_owner", None) is widget:
            return False

        def fire():
            self.hover_source = 0
            opener(widget)
            return False
        self.hover_source = GLib.timeout_add(400, fire)
        return False

    def cancel_hover(self):
        if self.hover_source:
            GLib.source_remove(self.hover_source)
            self.hover_source = 0

    def close_submenu(self):
        if self.submenu is not None:
            m = self.submenu
            self.submenu = None
            m.popdown()

    def popup(self, menu, widget, below=False):
        self.close_submenu()
        css_class(menu, "xp-startmenu-popup")
        menu.show_all()
        self.ungrab()
        self.submenu = menu
        self.submenu_owner = widget
        menu.connect("deactivate", self.on_submenu_closed)
        menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_EAST, Gdk.Gravity.SOUTH_WEST, None)

    def on_submenu_closed(self, menu):
        if self.submenu is menu:
            self.submenu = None
        if self.get_visible():
            self.grab_tries = 0
            GLib.timeout_add(20, self.try_grab)

    def menu_item(self, label, pixbuf=None, icon=None, cb=None, submenu=None):
        mi = Gtk.MenuItem()
        box = Gtk.Box(spacing=6)
        img = Gtk.Image.new_from_pixbuf(pixbuf) if pixbuf else image(icon, 16)
        img.set_size_request(16, 16)
        box.pack_start(img, False, False, 0)
        lbl = Gtk.Label(label=label, xalign=0)
        if len(label) > 48:
            lbl.set_text(label[:46] + "\u2026")
        box.pack_start(lbl, True, True, 0)
        mi.add(box)
        if submenu is not None:
            mi.set_submenu(submenu)
        elif cb is not None:
            mi.connect("activate", lambda *_: cb())
        return mi

    def build_programs(self):
        root = apps.tree(apps.all_entries())
        # XP keeps a "Startup" folder in All Programs.
        startup = apps.autostart_entries()

        def build(node, top=False):
            menu = Gtk.Menu()
            css_class(menu, "xp-startmenu-popup")
            folders = dict(node["folders"])
            if top:
                folders.setdefault("Startup", {"folders": {}, "items": []})
            for fname in sorted(folders, key=str.lower):
                sub = folders[fname]
                if top and fname == "Startup":
                    sm = Gtk.Menu()
                    css_class(sm, "xp-startmenu-popup")
                    for info in startup:
                        sm.append(self.menu_item(info.get_display_name(),
                                                 pixbuf=gicon_pixbuf(info.get_icon(), 16),
                                                 cb=lambda i=info: self.launch(i)))
                    if not startup:
                        e = Gtk.MenuItem(label="(Empty)")
                        e.set_sensitive(False)
                        sm.append(e)
                else:
                    sm = build(sub)
                menu.append(self.menu_item(fname, icon="whistler-programs-folder", submenu=sm))
            for e in sorted(node["items"], key=lambda e: e.name.lower()):
                menu.append(self.menu_item(e.name, pixbuf=gicon_pixbuf(e.gicon, 16),
                                           cb=lambda i=e.info: self.launch(i)))
            return menu
        return build(root, top=True)

    def show_programs(self, widget):
        if self.programs_menu is None:
            self.programs_menu = self.build_programs()
        self.popup(self.programs_menu, widget)
        return False

    def show_recent(self, widget):
        menu = Gtk.Menu()
        items = apps.recent_documents()
        for it in items:
            gicon = it.get_gicon()
            menu.append(self.menu_item(it.get_display_name(), pixbuf=gicon_pixbuf(gicon, 16),
                                       cb=lambda u=it.get_uri(): self.activate(lambda: open_uri(u))))
        if not items:
            e = Gtk.MenuItem(label="(Empty)")
            e.set_sensitive(False)
            menu.append(e)
        self.popup(menu, widget)
        return False

    def show_connect(self, widget):
        menu = Gtk.Menu()
        menu.append(self.menu_item("Network Connections", icon="network-wired",
                                   cb=lambda: self.activate(lambda: spawn(["nm-connection-editor"]))))
        menu.append(self.menu_item("My Network Places", icon="network-workgroup",
                                   cb=lambda: self.activate(lambda: open_uri("network:///"))))
        self.popup(menu, widget)
        return False


class StartMenuApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.whistler.StartMenu",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        load_css("startmenu.css")
        self.window = StartMenu(self)
        for name, cb in (("toggle", lambda *_: self.window.toggle()),
                         ("show", lambda *_: self.window.show_menu()),
                         ("hide", lambda *_: self.window.hide_menu()),
                         ("reload", lambda *_: self.window.build())):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", cb)
            self.add_action(action)
        self.hold()

    def do_activate(self):
        pass

    def do_command_line(self, cmdline):
        args = cmdline.get_arguments()[1:]
        if "--show" in args:
            self.window.show_menu()
        elif "--hide" in args:
            self.window.hide_menu()
        elif "--toggle" in args:
            self.window.toggle()
        elif "--reload" in args:
            self.window.build()
        elif "--quit" in args:
            self.quit()
        return 0


def main():
    app = StartMenuApp()
    return app.run(sys.argv)
