"""My Computer: drives and folders in the XP Explorer layout."""
import glob
import os
import sys

from gi.repository import Gdk, Gio, GLib, Gtk, Pango

from .common import (TaskPane, css_class, display_name, icon_pixbuf, image, load_css, open_uri,
                     spawn, user_dir)


def human(n):
    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return ("%.0f %s" if unit in ("bytes", "KB") else "%.1f %s") % (n, unit)
        n /= 1024.0


def space(path):
    try:
        st = os.statvfs(path)
    except OSError:
        return None
    return st.f_bavail * st.f_frsize, st.f_blocks * st.f_frsize


def wine_prefixes():
    """[(label, drive_c path)] for the default prefix and Wine Center environments."""
    out = []
    home = os.path.expanduser("~")
    if os.path.isdir(os.path.join(home, ".wine", "drive_c")):
        out.append(("Windows Drive (C:)", os.path.join(home, ".wine", "drive_c")))
    for d in sorted(glob.glob(os.path.join(GLib.get_user_data_dir(), "wineprefixes", "*", "drive_c"))):
        name = os.path.basename(os.path.dirname(d))
        out.append(("%s (C:)" % name, d))
    return out


class Tile(Gtk.EventBox):
    def __init__(self, icon, title, lines, activate, gicon=None):
        super().__init__()
        self.activate_cb = activate
        box = Gtk.Box(spacing=8)
        box.set_size_request(236, 52)
        css_class(box, "xp-tile")
        if gicon is not None:
            img = Gtk.Image.new_from_gicon(gicon, Gtk.IconSize.DIALOG)
            img.set_pixel_size(48)
        else:
            img = image(icon, 48)
        box.pack_start(img, False, False, 0)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        col.set_valign(Gtk.Align.CENTER)
        t = Gtk.Label(label=title, xalign=0)
        t.set_ellipsize(Pango.EllipsizeMode.END)
        t.set_max_width_chars(28)
        col.pack_start(t, False, False, 0)
        for line in lines:
            l = Gtk.Label(label=line, xalign=0)
            l.get_style_context().add_class("dim-label")
            l.set_ellipsize(Pango.EllipsizeMode.END)
            l.set_max_width_chars(30)
            col.pack_start(l, False, False, 0)
        box.pack_start(col, True, True, 0)
        self.add(box)
        self.connect("button-press-event", self.on_press)

    def on_press(self, w, ev):
        if ev.type == Gdk.EventType._2BUTTON_PRESS and ev.button == 1:
            self.activate_cb()
            return True
        return False


class MyComputer(Gtk.Window):
    def __init__(self):
        super().__init__(title="My Computer")
        self.set_icon_name("computer")
        self.set_default_size(820, 560)
        self.connect("destroy", Gtk.main_quit)
        self.monitor = Gio.VolumeMonitor.get()
        for sig in ("mount-added", "mount-removed", "volume-added", "volume-removed", "drive-changed"):
            self.monitor.connect(sig, lambda *_: GLib.idle_add(self.refresh))

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(outer)
        outer.pack_start(self.build_menubar(), False, False, 0)
        outer.pack_start(self.build_toolbar(), False, False, 0)

        paned = Gtk.Box()
        outer.pack_start(paned, True, True, 0)
        pane = TaskPane()
        pane.add_group("System Tasks", [
            ("dialog-information", "View system information", lambda: spawn(["whistler-sysprops"])),
            ("system-software-install", "Add or remove programs", lambda: spawn(["whistler-addremove"])),
            ("preferences-system", "Change a setting", lambda: spawn(["whistler-control"])),
        ], special=True)
        pane.add_group("Other Places", [
            ("network-workgroup", "My Network Places", lambda: open_uri("network:///")),
            ("folder-documents", "My Documents",
             lambda: open_uri(user_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS, "~"))),
            ("folder-publicshare", "Shared Documents",
             lambda: open_uri(user_dir(GLib.UserDirectory.DIRECTORY_PUBLIC_SHARE, "~/Public"))),
            ("preferences-system", "Control Panel", lambda: spawn(["whistler-control"])),
        ])
        pane.add_group("Details", [(None, "<b>My Computer</b>\nSystem Folder", None)])
        paned.pack_start(pane, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        css_class(scroller, "xp-content")
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.content.set_border_width(10)
        scroller.add(self.content)
        paned.pack_start(scroller, True, True, 0)

        self.status = Gtk.Label(xalign=0)
        sb = Gtk.Box()
        css_class(sb, "xp-statusbar")
        sb.pack_start(self.status, True, True, 0)
        outer.pack_start(sb, False, False, 0)

        self.refresh()
        self.show_all()

    def build_menubar(self):
        mb = Gtk.MenuBar()

        def menu(title, items):
            top = Gtk.MenuItem.new_with_mnemonic(title)
            m = Gtk.Menu()
            for label, cb in items:
                if label is None:
                    m.append(Gtk.SeparatorMenuItem())
                    continue
                mi = Gtk.MenuItem.new_with_mnemonic(label)
                mi.connect("activate", lambda *_a, f=cb: f())
                m.append(mi)
            top.set_submenu(m)
            mb.append(top)
        menu("_File", [("_Close", self.destroy)])
        menu("_Edit", [("Select _All", lambda: None)])
        menu("_View", [("_Refresh", self.refresh)])
        menu("F_avorites", [("My _Documents", lambda: open_uri(user_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS, "~")))])
        menu("_Tools", [("_Folder Options...", lambda: spawn(["thunar-settings"]))])
        menu("_Help", [("_About Whistler XP", lambda: spawn(["whistler-sysprops", "--about"]))])
        return mb

    def build_toolbar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tb = Gtk.Box(spacing=2)
        css_class(tb, "xp-toolbar")
        for icon, label, cb, sensitive in (("go-previous", "Back", None, False),
                                           ("go-next", None, None, False),
                                           ("go-up", None, None, False),
                                           ("system-search", "Search", lambda: spawn(["catfish"]), True),
                                           ("folder", "Folders", lambda: spawn(["thunar", "/"]), True)):
            b = Gtk.Button()
            b.set_relief(Gtk.ReliefStyle.NONE)
            bb = Gtk.Box(spacing=4)
            bb.pack_start(image(icon, 24), False, False, 0)
            if label:
                bb.pack_start(Gtk.Label(label=label), False, False, 0)
            b.add(bb)
            b.set_sensitive(sensitive)
            if cb:
                b.connect("clicked", lambda *_a, f=cb: f())
            tb.pack_start(b, False, False, 0)
        box.pack_start(tb, False, False, 0)
        ab = Gtk.Box(spacing=4)
        css_class(ab, "xp-addressbar")
        ab.pack_start(Gtk.Label(label="Address"), False, False, 4)
        entry = Gtk.Entry()
        entry.set_text("My Computer")
        entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "computer")
        entry.connect("activate", lambda e: open_uri(e.get_text()) if e.get_text() != "My Computer" else None)
        ab.pack_start(entry, True, True, 0)
        go = Gtk.Button()
        gb = Gtk.Box(spacing=3)
        gb.pack_start(image("whistler-go", 16), False, False, 0)
        gb.pack_start(Gtk.Label(label="Go"), False, False, 0)
        go.add(gb)
        go.set_relief(Gtk.ReliefStyle.NONE)
        go.connect("clicked", lambda *_: entry.activate())
        ab.pack_start(go, False, False, 0)
        box.pack_start(ab, False, False, 0)
        return box

    def section(self, title, tiles):
        if not tiles:
            return
        lbl = Gtk.Label(label=title, xalign=0)
        css_class(lbl, "xp-section-title")
        self.content.pack_start(lbl, False, False, 0)
        rule = Gtk.Box()
        css_class(rule, "xp-section-rule")
        self.content.pack_start(rule, False, False, 0)
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        flow.set_max_children_per_line(4)
        flow.set_min_children_per_line(1)
        flow.set_homogeneous(True)
        flow.set_column_spacing(8)
        flow.set_row_spacing(4)
        for t in tiles:
            flow.add(t)
        flow.connect("child-activated", lambda fb, child: child.get_child().activate_cb())
        self.content.pack_start(flow, False, False, 0)

    def refresh(self):
        for c in self.content.get_children():
            c.destroy()
        n = 0
        docs = user_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS, "~")
        public = user_dir(GLib.UserDirectory.DIRECTORY_PUBLIC_SHARE, "~/Public")
        files = [Tile("folder-publicshare", "Shared Documents", ["File Folder"], lambda: open_uri(public)),
                 Tile("folder-documents", "%s's Documents" % display_name(), ["File Folder"],
                      lambda: open_uri(docs))]
        self.section("Files Stored on This Computer", files)

        disks = []
        sp = space("/")
        lines = ["Local Disk"]
        if sp:
            lines.append("%s free of %s" % (human(sp[0]), human(sp[1])))
        disks.append(Tile("drive-harddisk-system", "Local Disk (/)", lines, lambda: open_uri("/")))
        removable, network = [], []
        seen = set()
        for mount in self.monitor.get_mounts():
            root = mount.get_root()
            path = root.get_path()
            if path in seen or (path and path == "/"):
                continue
            seen.add(path)
            name = mount.get_name()
            drive = mount.get_drive()
            info = []
            if path:
                s = space(path)
                if s:
                    info.append("%s free of %s" % (human(s[0]), human(s[1])))
            uri = root.get_uri()
            tile = Tile(None, name, info or [""], lambda u=uri: open_uri(u), gicon=mount.get_icon())
            if path is None:
                network.append(tile)
            elif drive is not None and (drive.is_removable() or drive.is_media_removable()):
                removable.append(tile)
            else:
                disks.append(tile)
        for vol in self.monitor.get_volumes():
            if vol.get_mount() is not None:
                continue
            drive = vol.get_drive()
            tile = Tile(None, vol.get_name(), ["Not mounted - double-click to open"],
                        lambda v=vol: self.mount_and_open(v), gicon=vol.get_icon())
            if drive is not None and (drive.is_removable() or drive.is_media_removable()):
                removable.append(tile)
            else:
                disks.append(tile)
        for drive in self.monitor.get_connected_drives():
            if drive.has_media() or not drive.is_media_removable():
                continue
            removable.append(Tile(None, drive.get_name(), ["No disc"], lambda: None, gicon=drive.get_icon()))
        self.section("Hard Disk Drives", disks)

        wine = []
        for label, path in wine_prefixes():
            s = space(path)
            wine.append(Tile("drive-harddisk", label,
                             ["Windows programs", "%s free" % human(s[0]) if s else ""],
                             lambda p=path: open_uri(p)))
        if not wine:
            wine.append(Tile("drive-harddisk", "Windows Drive (C:)", ["Not set up yet - double-click"],
                             lambda: spawn(["whistler-winecenter", "--open-drive"])))
        self.section("Windows Programs", wine)
        self.section("Devices with Removable Storage", removable)
        self.section("Network Drives", network)
        n = len(files) + len(disks) + len(wine) + len(removable) + len(network)
        self.status.set_text("%d objects" % n)
        self.content.show_all()
        return False

    def mount_and_open(self, vol):
        op = Gtk.MountOperation.new(self)

        def done(v, res):
            try:
                v.mount_finish(res)
            except GLib.Error as e:
                dlg = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                                        buttons=Gtk.ButtonsType.OK, text="Cannot open %s" % v.get_name())
                dlg.format_secondary_text(e.message)
                dlg.run()
                dlg.destroy()
                return
            m = v.get_mount()
            if m:
                open_uri(m.get_root().get_uri())
        vol.mount(Gio.MountMountFlags.NONE, op, None, done)


def main():
    load_css("whistler.css")
    MyComputer()
    Gtk.main()
    return 0
