"""Add or Remove Programs: pacman packages and Windows (Wine) programs."""
import glob
import os
import re
import subprocess
import threading

from gi.repository import Gio, GLib, Gtk, Pango

from .common import css_class, gicon_pixbuf, icon_pixbuf, image, load_css, run_async, spawn, xp_message

BASE_PACKAGES = {"whistler-desktop", "whistler-artwork", "xfce4-panel", "xfwm4", "xfdesktop", "thunar",
                 "xfce4-session", "xfce4-settings", "lightdm", "python", "gtk3", "wine", "linux", "systemd",
                 "glibc", "pacman", "networkmanager", "xfce4-notifyd", "xfce4-power-manager", "exo", "garcon",
                 "xfce4-terminal", "thunar-volman", "network-manager-applet", "lightdm-gtk-greeter",
                 "xdg-utils", "xfce4-pulseaudio-plugin"}


def human(n):
    if n >= 1024 ** 3:
        return "%.2fGB" % (n / 1024 ** 3)
    if n >= 1024 ** 2:
        return "%.2fMB" % (n / 1024 ** 2)
    return "%.0fKB" % (n / 1024)


def parse_size(text):
    m = re.match(r"([\d.,]+)\s*(\w+)", text.strip())
    if not m:
        return 0
    v = float(m.group(1).replace(",", "."))
    mult = {"B": 1, "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3}.get(m.group(2), 1)
    return int(v * mult)


def installed_linux_programs():
    """[(name, gicon, package, size)] for menu applications, grouped by package."""
    apps = {}
    for info in Gio.AppInfo.get_all():
        if not isinstance(info, Gio.DesktopAppInfo) or not info.should_show():
            continue
        fn = info.get_filename()
        if fn and fn.startswith("/usr/share/whistler/xdg-data/applications/"):
            fn = "/usr/share/applications/" + os.path.basename(fn)
        if not fn or not fn.startswith("/usr/share/applications/") or not os.path.exists(fn):
            continue
        cats = (info.get_categories() or "").split(";")
        if "Settings" in cats or "DesktopSettings" in cats or os.path.basename(fn).startswith("whistler-"):
            continue
        apps[fn] = info
    if not apps:
        return []
    files = sorted(apps)
    owners = {}
    out = subprocess.run(["pacman", "-Qo"] + files, capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.match(r"(.+) is owned by (\S+) ", line)
        if m and m.group(2) not in BASE_PACKAGES:
            owners[m.group(1)] = m.group(2)
    pkgs = sorted(set(owners.values()))
    sizes = {}
    if pkgs:
        info = subprocess.run(["pacman", "-Qi"] + pkgs, capture_output=True, text=True).stdout
        cur = None
        for line in info.splitlines():
            if line.startswith("Name"):
                cur = line.split(":", 1)[1].strip()
            elif line.startswith("Installed Size") and cur:
                sizes[cur] = parse_size(line.split(":", 1)[1])
    seen = set()
    result = []
    for fn in files:
        pkg = owners.get(fn)
        if not pkg or pkg in seen:
            continue
        seen.add(pkg)
        info = apps[fn]
        result.append((info.get_display_name(), info.get_icon(), pkg, sizes.get(pkg, 0)))
    return result


def wine_programs():
    """[(name, prefix, guid)] from `wine uninstaller --list` for every prefix."""
    prefixes = [os.path.expanduser("~/.wine")] + glob.glob(os.path.join(GLib.get_user_data_dir(),
                                                                        "wineprefixes", "*"))
    out = []
    for p in prefixes:
        if not os.path.isfile(os.path.join(p, "system.reg")):
            continue
        try:
            r = subprocess.run(["wine", "uninstaller", "--list"], capture_output=True, text=True, timeout=60,
                               env=dict(os.environ, WINEPREFIX=p, WINEDEBUG="-all"))
        except (OSError, subprocess.TimeoutExpired):
            continue
        for line in r.stdout.splitlines():
            if "|||" in line:
                guid, name = line.split("|||", 1)
                if "Wine Mono" in name or "Wine Gecko" in name:
                    continue
                out.append((name.strip(), p, guid.strip()))
    return out


class Row(Gtk.ListBoxRow):
    def __init__(self, name, pixbuf, size_text, kind, data, app):
        super().__init__()
        self.kind, self.data, self.app, self.name = kind, data, app, name
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_border_width(4)
        top = Gtk.Box(spacing=8)
        top.pack_start(Gtk.Image.new_from_pixbuf(pixbuf) if pixbuf else image("application-x-executable", 32),
                       False, False, 0)
        lbl = Gtk.Label(label=name, xalign=0)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        css_class(lbl, "bold")
        top.pack_start(lbl, True, True, 0)
        if size_text:
            top.pack_end(Gtk.Label(label="Size  " + size_text), False, False, 0)
        box.pack_start(top, False, False, 0)
        self.detail = Gtk.Box(spacing=8)
        self.detail.set_margin_start(40)
        self.detail.pack_start(Gtk.Label(label="To remove this program from your computer, click Remove.",
                                         xalign=0), True, True, 0)
        rm = Gtk.Button(label="Change/Remove" if kind == "wine" else "Remove")
        rm.connect("clicked", lambda *_: app.remove(self))
        self.detail.pack_end(rm, False, False, 0)
        self.detail.set_no_show_all(True)
        box.pack_start(self.detail, False, False, 4)
        self.add(box)


class AddRemove(Gtk.Window):
    def __init__(self):
        super().__init__(title="Add or Remove Programs")
        self.set_icon_name("system-software-install")
        self.set_default_size(780, 560)
        self.connect("destroy", Gtk.main_quit)
        outer = Gtk.Box()
        self.add(outer)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        css_class(side, "xp-taskpane")
        side.set_size_request(118, -1)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for icon, label, cb in (("system-software-install", "Change or\nRemove\nPrograms", self.show_installed),
                                ("list-add", "Add New\nPrograms", self.show_add),
                                ("whistler-winecenter", "Add/Remove\nWindows\nComponents",
                                 lambda: spawn(["whistler-winecenter"])),
                                ("preferences-desktop-default-applications", "Set Program\nAccess and\nDefaults",
                                 lambda: spawn(["xfce4-mime-settings"]))):
            b = Gtk.Button()
            b.set_relief(Gtk.ReliefStyle.NONE)
            css_class(b, "xp-tasklink")
            bb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            bb.pack_start(image(icon, 32), False, False, 0)
            l = Gtk.Label(label=label)
            l.set_justify(Gtk.Justification.CENTER)
            bb.pack_start(l, False, False, 0)
            b.add(bb)
            b.set_margin_top(8)
            b.connect("clicked", lambda *_a, f=cb: f())
            side.pack_start(b, False, False, 0)
        outer.pack_start(side, False, False, 0)
        outer.pack_start(self.content, True, True, 0)
        self.show_all()
        self.show_installed()

    def clear(self):
        for c in self.content.get_children():
            c.destroy()

    def show_installed(self):
        self.clear()
        head = Gtk.Box(spacing=8)
        head.set_border_width(8)
        head.pack_start(Gtk.Label(label="Currently installed programs:", xalign=0), True, True, 0)
        self.content.pack_start(head, False, False, 0)
        sc = Gtk.ScrolledWindow()
        self.list = Gtk.ListBox()
        self.list.connect("row-selected", self.on_selected)
        sc.add(self.list)
        self.content.pack_start(sc, True, True, 0)
        self.spinner_row = Gtk.Label(label="Please wait while the list is being populated...")
        self.list.add(self.spinner_row)
        self.content.show_all()
        threading.Thread(target=self.load, daemon=True).start()

    def load(self):
        linux = installed_linux_programs()
        wine = wine_programs()
        GLib.idle_add(self.populate, linux, wine)

    def populate(self, linux, wine):
        for c in self.list.get_children():
            c.destroy()
        rows = []
        for name, prefix, guid in wine:
            rows.append(Row(name + "  (Windows)", icon_pixbuf("whistler-winecenter", 32), "", "wine",
                            (prefix, guid), self))
        for name, gicon, pkg, size in linux:
            rows.append(Row(name, gicon_pixbuf(gicon, 32), human(size) if size else "", "pkg", pkg, self))
        for r in sorted(rows, key=lambda r: r.name.lower()):
            self.list.add(r)
        self.list.show_all()
        return False

    def on_selected(self, lb, row):
        for r in lb.get_children():
            if isinstance(r, Row):
                if r is row:
                    r.detail.set_no_show_all(False)
                    r.detail.show_all()
                else:
                    r.detail.hide()

    def remove(self, row):
        if row.kind == "wine":
            prefix, guid = row.data
            subprocess.Popen(["wine", "uninstaller", "--remove", guid],
                             env=dict(os.environ, WINEPREFIX=prefix, WINEDEBUG="-all"),
                             start_new_session=True)
            GLib.timeout_add(4000, lambda: self.show_installed() and False)
            return
        pkg = row.data
        if pkg in BASE_PACKAGES:
            xp_message(self, "%s is part of Whistler XP and cannot be removed." % row.name,
                       kind=Gtk.MessageType.INFO)
            return
        r = xp_message(self, "Are you sure you want to remove %s from your computer?" % row.name,
                       "Package: %s" % pkg, kind=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.YES_NO)
        if r != Gtk.ResponseType.YES:
            return
        self.run_pacman(["pacman", "-Rns", "--noconfirm", pkg], "Removing %s..." % row.name, self.show_installed)

    def run_pacman(self, argv, title, after):
        dlg = Gtk.Dialog(title=title, transient_for=self, modal=True)
        dlg.set_default_size(460, 300)
        box = dlg.get_content_area()
        box.set_border_width(10)
        lbl = Gtk.Label(label=title, xalign=0)
        box.pack_start(lbl, False, False, 4)
        bar = Gtk.ProgressBar()
        box.pack_start(bar, False, False, 4)
        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_monospace(True)
        sc = Gtk.ScrolledWindow()
        sc.add(tv)
        box.pack_start(sc, True, True, 0)
        close = dlg.add_button("Close", Gtk.ResponseType.CLOSE)
        close.set_sensitive(False)
        dlg.show_all()
        pulse = GLib.timeout_add(120, lambda: bar.pulse() or True)

        def done(code, out):
            GLib.source_remove(pulse)
            bar.set_fraction(1.0)
            tv.get_buffer().set_text(out)
            lbl.set_text("Done." if code == 0 else "The operation did not complete (code %d)." % code)
            close.set_sensitive(True)
        run_async(["pkexec"] + argv, done)
        dlg.run()
        dlg.destroy()
        after()

    # ----------------------------------------------------------- add new
    def show_add(self):
        self.clear()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(10)
        self.content.pack_start(box, True, True, 0)
        win = Gtk.Box(spacing=10)
        win.pack_start(image("whistler-winecenter", 48), False, False, 0)
        wl = Gtk.Label(label="Add a program made for Windows from a CD-ROM or a downloaded setup file", xalign=0)
        wl.set_line_wrap(True)
        win.pack_start(wl, True, True, 0)
        wb = Gtk.Button(label="CD or File...")
        wb.connect("clicked", lambda *_: spawn(["whistler-winecenter", "--install"]))
        win.pack_end(wb, False, False, 0)
        box.pack_start(win, False, False, 6)
        box.pack_start(Gtk.Separator(), False, False, 4)
        top = Gtk.Box(spacing=10)
        top.pack_start(image("system-software-install", 48), False, False, 0)
        top.pack_start(Gtk.Label(label="Add programs from the CachyOS and Arch Linux software catalogs", xalign=0), True, True, 0)
        box.pack_start(top, False, False, 0)
        row = Gtk.Box(spacing=6)
        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Type a program name, e.g. vlc, gimp, libreoffice")
        self.search.connect("activate", lambda *_: self.do_search())
        row.pack_start(self.search, True, True, 0)
        go = Gtk.Button(label="Search")
        go.connect("clicked", lambda *_: self.do_search())
        row.pack_start(go, False, False, 0)
        box.pack_start(row, False, False, 0)
        sc = Gtk.ScrolledWindow()
        self.results = Gtk.ListBox()
        sc.add(self.results)
        box.pack_start(sc, True, True, 0)
        self.content.show_all()

    def do_search(self):
        term = self.search.get_text().strip()
        if not term:
            return
        for c in self.results.get_children():
            c.destroy()
        self.results.add(Gtk.Label(label="Searching..."))
        self.results.show_all()

        def worker():
            if not glob.glob("/var/lib/pacman/sync/*.db"):
                subprocess.run(["pkexec", "pacman", "-Sy"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            out = subprocess.run(["pacman", "-Ss", term], capture_output=True, text=True).stdout
            items = []
            lines = out.splitlines()
            for i in range(0, len(lines) - 1, 2):
                m = re.match(r"(\S+)/(\S+) (\S+)(.*)", lines[i])
                if m:
                    items.append((m.group(2), m.group(3), lines[i + 1].strip(), "[installed" in m.group(4)))
            GLib.idle_add(self.show_results, items[:200])
        threading.Thread(target=worker, daemon=True).start()

    def show_results(self, items):
        for c in self.results.get_children():
            c.destroy()
        if not items:
            self.results.add(Gtk.Label(label="No programs found."))
        for name, ver, desc, installed in items:
            row = Gtk.Box(spacing=8)
            row.set_border_width(4)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            t = Gtk.Label(label="%s %s" % (name, ver), xalign=0)
            css_class(t, "bold")
            d = Gtk.Label(label=desc, xalign=0)
            d.set_ellipsize(Pango.EllipsizeMode.END)
            col.pack_start(t, False, False, 0)
            col.pack_start(d, False, False, 0)
            row.pack_start(col, True, True, 0)
            b = Gtk.Button(label="Installed" if installed else "Add")
            b.set_sensitive(not installed)
            b.connect("clicked", lambda _w, n=name: self.run_pacman(
                ["pacman", "-S", "--noconfirm", "--needed", n], "Installing %s..." % n, lambda: None))
            row.pack_end(b, False, False, 0)
            self.results.add(row)
        self.results.show_all()
        return False


def main():
    load_css("whistler.css")
    AddRemove()
    Gtk.main()
    return 0
