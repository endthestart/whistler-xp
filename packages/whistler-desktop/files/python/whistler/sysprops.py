"""System Properties (and the "About Whistler" box)."""
import os
import platform
import socket
import subprocess
import sys

from gi.repository import GdkPixbuf, GLib, Gtk

from .common import css_class, display_name, image, load_css, spawn

LOGO = "/usr/share/whistler/logos/wordmark.png"


def os_release():
    info = {}
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if "=" in line:
                    k, v = line.rstrip("\n").split("=", 1)
                    info[k] = v.strip('"')
    except OSError:
        pass
    return info


def cpu_model():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "Unknown processor"


def cpu_count():
    return os.cpu_count() or 1


def ram():
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    kb = int(line.split()[1])
                    return kb * 1024
    except OSError:
        pass
    return 0


def human(n):
    if n >= 1024 ** 3:
        return "%.2f GB" % (n / 1024 ** 3)
    return "%d MB" % (n / 1024 ** 2)


def logo_widget(width=300):
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file(LOGO)
        scale = width / pb.get_width()
        pb = pb.scale_simple(width, int(pb.get_height() * scale), GdkPixbuf.InterpType.BILINEAR)
        img = Gtk.Image.new_from_pixbuf(pb)
    except GLib.Error:
        img = image("whistler-logo", 96)
    # the wordmark is white-on-transparent: give it the dark XP banner
    box = Gtk.EventBox()
    box.add(img)
    box.override_background_color(Gtk.StateFlags.NORMAL, _rgba("#00309C"))
    return box


def _rgba(hexcolor):
    from gi.repository import Gdk
    c = Gdk.RGBA()
    c.parse(hexcolor)
    return c


class SystemProperties(Gtk.Window):
    def __init__(self, page=0):
        super().__init__(title="System Properties")
        self.set_icon_name("computer")
        self.set_resizable(False)
        self.connect("destroy", Gtk.main_quit)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_border_width(8)
        self.add(outer)
        nb = Gtk.Notebook()
        outer.pack_start(nb, True, True, 0)
        nb.append_page(self.general(), Gtk.Label(label="General"))
        nb.append_page(self.computer_name(), Gtk.Label(label="Computer Name"))
        nb.append_page(self.hardware(), Gtk.Label(label="Hardware"))
        nb.append_page(self.advanced(), Gtk.Label(label="Advanced"))
        btns = Gtk.Box(spacing=6)
        for label, cb in (("OK", self.destroy), ("Cancel", self.destroy)):
            b = Gtk.Button(label=label)
            b.set_size_request(75, 23)
            b.connect("clicked", lambda *_a, f=cb: f())
            btns.pack_end(b, False, False, 0)
        outer.pack_start(btns, False, False, 0)
        self.show_all()
        nb.set_current_page(page)

    def general(self):
        rel = os_release()
        box = Gtk.Box(spacing=16)
        box.set_border_width(14)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left.pack_start(logo_widget(220), False, False, 0)
        box.pack_start(left, False, False, 0)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        def line(text, indent=True, bold=False):
            l = Gtk.Label(label=text, xalign=0)
            if indent:
                l.set_margin_start(16)
            if bold:
                css_class(l, "bold")
            right.pack_start(l, False, False, 0)
        line("System:", indent=False)
        line(rel.get("PRETTY_NAME", "Whistler XP"))
        line("Version %s" % rel.get("VERSION_ID", "1.0"))
        line("Linux %s" % platform.release())
        right.pack_start(Gtk.Label(label=""), False, False, 4)
        line("Registered to:", indent=False)
        line(display_name())
        line(socket.gethostname())
        right.pack_start(Gtk.Label(label=""), False, False, 4)
        line("Computer:", indent=False)
        line(cpu_model())
        line("%d processor(s)" % cpu_count())
        line("%s of RAM" % human(ram()))
        box.pack_start(right, True, True, 0)
        return box

    def computer_name(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(14)
        top = Gtk.Box(spacing=12)
        top.pack_start(image("computer", 32), False, False, 0)
        msg = Gtk.Label(label="Whistler uses the following information to identify your computer on the network.",
                        xalign=0)
        msg.set_line_wrap(True)
        top.pack_start(msg, True, True, 0)
        box.pack_start(top, False, False, 0)
        g = Gtk.Grid(column_spacing=12, row_spacing=8)
        g.attach(Gtk.Label(label="Full computer name:", xalign=0), 0, 0, 1, 1)
        g.attach(Gtk.Label(label=socket.getfqdn(), xalign=0), 1, 0, 1, 1)
        g.attach(Gtk.Label(label="Workgroup:", xalign=0), 0, 1, 1, 1)
        g.attach(Gtk.Label(label="WORKGROUP", xalign=0), 1, 1, 1, 1)
        box.pack_start(g, False, False, 0)
        row = Gtk.Box(spacing=8)
        row.pack_start(Gtk.Label(label="To rename this computer, click Change.", xalign=0), True, True, 0)
        ch = Gtk.Button(label="Change...")
        ch.connect("clicked", self.rename)
        row.pack_end(ch, False, False, 0)
        box.pack_end(row, False, False, 0)
        return box

    def rename(self, *_):
        d = Gtk.Dialog(title="Computer Name Changes", transient_for=self, modal=True)
        d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)
        box = d.get_content_area()
        box.set_border_width(12)
        box.pack_start(Gtk.Label(label="Computer name:", xalign=0), False, False, 0)
        e = Gtk.Entry()
        e.set_text(socket.gethostname())
        box.pack_start(e, False, False, 4)
        d.show_all()
        if d.run() == Gtk.ResponseType.OK:
            name = e.get_text().strip()
            if name and all(c.isalnum() or c == "-" for c in name):
                spawn(["pkexec", "hostnamectl", "set-hostname", name])
        d.destroy()

    def hardware(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(10)
        h = Gtk.Label(label="Device Manager", xalign=0)
        css_class(h, "bold")
        box.pack_start(h, False, False, 0)
        store = Gtk.TreeStore(str, str)
        groups = {}
        try:
            out = subprocess.run(["lspci", "-mm"], capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.TimeoutExpired):
            out = ""
        for line in out.splitlines():
            parts = [p.strip('"') for p in line.split('" "')]
            if len(parts) < 4:
                continue
            cls, vendor, dev = parts[0].split('"')[-1], parts[1], parts[2]
            icon = "computer"
            if "VGA" in cls or "Display" in cls:
                icon = "video-display"
            elif "Audio" in cls:
                icon = "audio-card"
            elif "Network" in cls or "Ethernet" in cls:
                icon = "network-wired"
            elif "USB" in cls:
                icon = "drive-removable-media"
            elif "SATA" in cls or "storage" in cls.lower() or "IDE" in cls:
                icon = "drive-harddisk"
            if cls not in groups:
                groups[cls] = store.append(None, [icon, cls])
            store.append(groups[cls], [icon, "%s %s" % (vendor, dev)])
        view = Gtk.TreeView(model=store)
        view.set_headers_visible(False)
        col = Gtk.TreeViewColumn()
        ri = Gtk.CellRendererPixbuf()
        rt = Gtk.CellRendererText()
        col.pack_start(ri, False)
        col.pack_start(rt, True)
        col.add_attribute(ri, "icon-name", 0)
        col.add_attribute(rt, "text", 1)
        view.append_column(col)
        sc = Gtk.ScrolledWindow()
        sc.set_size_request(380, 230)
        sc.add(view)
        box.pack_start(sc, True, True, 0)
        return box

    def advanced(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(14)
        frame = Gtk.Frame(label="Performance")
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        inner.set_border_width(10)
        inner.pack_start(Gtk.Label(label="Visual effects (window compositing, menu shadows):", xalign=0),
                         False, False, 0)
        best_look = Gtk.RadioButton.new_with_label(None, "Adjust for best appearance")
        best_perf = Gtk.RadioButton.new_with_label_from_widget(best_look, "Adjust for best performance")
        try:
            v = subprocess.run(["xfconf-query", "-c", "xfwm4", "-p", "/general/use_compositing"],
                               capture_output=True, text=True).stdout.strip()
        except OSError:
            v = "true"
        (best_look if v != "false" else best_perf).set_active(True)
        best_look.connect("toggled", lambda b: spawn(["xfconf-query", "-c", "xfwm4", "-p",
                                                       "/general/use_compositing", "-s",
                                                       "true" if b.get_active() else "false"]))
        inner.pack_start(best_look, False, False, 0)
        inner.pack_start(best_perf, False, False, 0)
        frame.add(inner)
        box.pack_start(frame, False, False, 0)
        frame2 = Gtk.Frame(label="Startup")
        inner2 = Gtk.Box(spacing=6)
        inner2.set_border_width(10)
        inner2.pack_start(Gtk.Label(label="Programs that start when you log on:", xalign=0), True, True, 0)
        b = Gtk.Button(label="Settings...")
        b.connect("clicked", lambda *_: spawn(["xfce4-session-settings"]))
        inner2.pack_end(b, False, False, 0)
        frame2.add(inner2)
        box.pack_start(frame2, False, False, 0)
        return box


class About(Gtk.Window):
    def __init__(self):
        super().__init__(title="About Whistler XP")
        self.set_icon_name("whistler-logo")
        self.set_resizable(False)
        self.connect("destroy", Gtk.main_quit)
        rel = os_release()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(box)
        box.pack_start(logo_widget(420), False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        body.set_border_width(16)
        for text in ("%s" % rel.get("PRETTY_NAME", "Whistler XP"),
                     "Version %s (Linux %s)" % (rel.get("VERSION_ID", "1.0"), platform.release()),
                     "Built on CachyOS and Arch Linux. Copyright © The Whistler Project.",
                     "",
                     "This product is licensed to:",
                     "    " + display_name(),
                     "",
                     "Physical memory available to Whistler: %s" % human(ram())):
            body.pack_start(Gtk.Label(label=text, xalign=0), False, False, 0)
        ok = Gtk.Button(label="OK")
        ok.set_size_request(75, 23)
        ok.set_halign(Gtk.Align.END)
        ok.connect("clicked", lambda *_: self.destroy())
        body.pack_start(ok, False, False, 8)
        box.pack_start(body, True, True, 0)
        self.show_all()


def main():
    load_css("whistler.css")
    if "--about" in sys.argv:
        About()
    else:
        SystemProperties(2 if "--hardware" in sys.argv else 0)
    Gtk.main()
    return 0
