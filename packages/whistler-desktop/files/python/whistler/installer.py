"""Whistler XP Setup: XP-style text-mode disk selection, then the graphical Setup."""
import json
import os
import random
import re
import shlex
import socket
import subprocess
import sys
import tempfile
import time

from gi.repository import Gdk, GLib, Gtk, Pango

from .common import WizardHeader, css_class, image, load_css

USERPICS = "/usr/share/whistler/assets/current/userpics"
LAYOUTS = [("United States", "us"), ("United Kingdom", "gb"), ("German", "de"), ("French", "fr"),
           ("Spanish", "es"), ("Italian", "it"), ("Portuguese (Brazil)", "br"), ("Portuguese", "pt"),
           ("Russian", "ru"), ("Polish", "pl"), ("Dutch", "nl"), ("Swedish", "se"), ("Norwegian", "no"),
           ("Danish", "dk"), ("Finnish", "fi"), ("Swiss", "ch"), ("Canadian French", "ca"),
           ("Japanese", "jp"), ("Korean", "kr"), ("Turkish", "tr"), ("Czech", "cz"), ("Hungarian", "hu")]
STEPS = ["Collecting information", "Preparing installation", "Installing Whistler XP",
         "Finalizing installation"]
BILLBOARDS = [
    ("Familiar on the outside",
     "Whistler XP looks and works like the desktop you know. The Start menu, taskbar, My Computer and "
     "Control Panel are all right where you expect them."),
    ("Your Windows programs",
     "Run many programs made for Windows with Wine Center. Double-click a setup file to install it, and "
     "find it later in All Programs."),
    ("Fast, safe and up to date",
     "Underneath, Whistler XP is CachyOS: a fast, modern, secure Linux that updates with a single command."),
    ("Thousands of free programs",
     "Add or Remove Programs can install free software from the CachyOS and Arch Linux catalogs: office suites, "
     "photo editors, games and more."),
    ("Make it yours",
     "Change your picture, your desktop background and your theme from Control Panel. "
     "Every account has its own settings."),
]
CSS = b"""
.ts-screen { background-color: #0000A8; }
.ts-screen label { color: #AAAAAA; font-family: "Terminus", "DejaVu Sans Mono", monospace; font-size: 15pt; }
.ts-title label { color: #FFFFFF; }
.ts-bright { color: #FFFFFF; }
.ts-status { background-color: #AAAAAA; }
.ts-status label { color: #000000; }
.ts-selected { background-color: #AAAAAA; }
.ts-selected label { color: #0000A8; }
.ts-box { border: 2px solid #AAAAAA; padding: 6px 12px; }
.ts-progress trough { background-color: #0000A8; border: 1px solid #AAAAAA; min-height: 18px; border-radius: 0; }
.ts-progress progress { background-color: #FFFF55; background-image: none; border-radius: 0; min-height: 18px; }
.gs-root { background-color: #5A7EDC; }
.gs-top { background-color: #00309C; min-height: 70px; }
.gs-bottom { background-color: #00309C; min-height: 6px; }
.gs-side { background-image: linear-gradient(to right, #0B3AA8, #3B66D1); padding: 30px 20px; min-width: 220px; }
.gs-side label { color: #FFFFFF; font-family: Tahoma, sans-serif; font-size: 10pt; }
.gs-step-current { font-weight: bold; }
.gs-step-done { color: #B8C9F2; }
.gs-billboard-title { color: #FFFFFF; font-family: "Trebuchet MS", Tahoma, sans-serif; font-size: 22pt; font-weight: bold; }
.gs-billboard-text { color: #FFFFFF; font-family: Tahoma, sans-serif; font-size: 12pt; }
.gs-status { color: #FFFFFF; font-family: Tahoma, sans-serif; }
.gs-progress trough { background-color: #FFFFFF; border: 1px solid #00309C; min-height: 14px; border-radius: 2px; }
.gs-progress progress { background-image: repeating-linear-gradient(to right, #2FB52F 0px, #2FB52F 8px, transparent 8px, transparent 10px); background-color: transparent; border-radius: 0; min-height: 12px; }
.gs-dialog { background-color: #ECE9D8; border: 1px solid #0831D9; }
.gs-dialog-title { background-image: linear-gradient(to bottom, #0A5EEC, #0446D8 50%, #0447D8); padding: 4px 8px; }
.gs-dialog-title label { color: #FFFFFF; font-family: "Trebuchet MS", Tahoma, sans-serif; font-weight: bold; font-size: 10pt; }
"""


def disks():
    """[(path, size_bytes, model, removable, is_boot_medium)]"""
    try:
        out = subprocess.run(["lsblk", "-J", "-b", "-d", "-o", "NAME,SIZE,MODEL,TYPE,RM,TRAN,RO"],
                             capture_output=True, text=True).stdout
        data = json.loads(out)["blockdevices"]
    except (OSError, ValueError, KeyError):
        return []
    boot = ""
    try:
        src = subprocess.run(["findmnt", "-no", "SOURCE", "/run/archiso/bootmnt"], capture_output=True,
                             text=True).stdout.strip()
        boot = re.sub(r"p?\d+$", "", src) if src else ""
    except OSError:
        pass
    res = []
    for d in data:
        if d.get("type") != "disk" or d.get("ro") in (True, "1"):
            continue
        if d["name"].startswith(("loop", "sr", "zram", "ram")):
            continue
        path = "/dev/" + d["name"]
        res.append((path, int(d.get("size") or 0), (d.get("model") or "Disk").strip(),
                    d.get("rm") in (True, "1"), path == boot))
    return res


def mb(n):
    return n // (1024 * 1024)


class TextScreen(Gtk.Box):
    """A blue text-mode setup screen with a title and grey status line."""

    def __init__(self, status):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        css_class(self, "ts-screen")
        title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        css_class(title, "ts-title")
        title.set_margin_start(16)
        title.set_margin_top(8)
        title.pack_start(Gtk.Label(label="Whistler XP Setup", xalign=0), False, False, 0)
        title.pack_start(Gtk.Label(label="═" * 19, xalign=0), False, False, 0)
        self.pack_start(title, False, False, 0)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.body.set_margin_start(40)
        self.body.set_margin_end(40)
        self.body.set_margin_top(20)
        self.pack_start(self.body, True, True, 0)
        bar = Gtk.Box()
        css_class(bar, "ts-status")
        self.status = Gtk.Label(label=status, xalign=0)
        self.status.set_margin_start(16)
        bar.pack_start(self.status, True, True, 0)
        self.pack_end(bar, False, False, 0)

    def line(self, text="", bright=False, indent=0):
        l = Gtk.Label(label=text, xalign=0)
        l.set_line_wrap(True)
        l.set_margin_start(indent)
        if bright:
            css_class(l, "ts-bright")
        self.body.pack_start(l, False, False, 0)
        return l


class Setup(Gtk.Window):
    def __init__(self):
        super().__init__(title="Whistler XP Setup")
        self.set_icon_name("whistler-setup")
        self.fullscreen()
        self.connect("key-press-event", self.on_key)
        self.connect("delete-event", lambda *_: True)
        self.stack = Gtk.Stack()
        self.add(self.stack)
        self.disk_list = disks()
        self.disk_index = next((i for i, d in enumerate(self.disk_list) if not d[4]), 0)
        self.screen = None
        self.info = {}
        self.show_all()
        self.text_welcome()

    # ------------------------------------------------------ text mode
    def set_screen(self, name, widget):
        old = self.stack.get_child_by_name(name)
        if old:
            old.destroy()
        self.stack.add_named(widget, name)
        widget.show_all()
        self.stack.set_visible_child(widget)
        self.screen = name

    def text_welcome(self):
        s = TextScreen("  ENTER=Continue   F3=Quit")
        s.line("Welcome to Setup.", bright=True)
        s.line()
        s.line("This portion of the Setup program prepares Whistler XP to run on your computer.")
        s.line()
        s.line("•  To set up Whistler XP now, press ENTER.", indent=24)
        s.line()
        s.line("•  To quit Setup without installing Whistler XP, press F3.", indent=24)
        self.set_screen("welcome", s)

    def text_license(self):
        s = TextScreen("  F8=I agree   ESC=I do not agree   F3=Quit")
        s.line("Whistler XP Licensing Agreement", bright=True)
        s.line()
        s.line("Whistler XP is free software. It is made of thousands of programs from CachyOS, Arch Linux, "
               "the Xfce desktop, Wine and other projects, each under its own free software license "
               "(mostly the GNU General Public License).")
        s.line()
        s.line("You may use, copy, study, change and share this software. It comes with ABSOLUTELY NO "
               "WARRANTY, to the extent permitted by law.")
        s.line()
        s.line("Whistler XP is not affiliated with or endorsed by Microsoft. Windows programs run through "
               "Wine, an independent compatibility layer.")
        s.line()
        s.line("To agree, press F8.", bright=True)
        self.set_screen("license", s)

    def text_disks(self):
        s = TextScreen("  ENTER=Install   F3=Quit")
        s.line("The following list shows the disks on this computer.")
        s.line()
        s.line("Use the UP and DOWN ARROW keys to select an item in the list.")
        s.line()
        s.line("•  To set up Whistler XP on the selected disk, press ENTER.", indent=24)
        s.line()
        s.line("•  To quit Setup without installing Whistler XP, press F3.", indent=24)
        s.line()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        css_class(box, "ts-box")
        if not self.disk_list:
            box.pack_start(Gtk.Label(label="Setup did not find any hard disks on this computer.", xalign=0),
                           False, False, 0)
        for i, (path, size, model, rm, boot) in enumerate(self.disk_list):
            text = "%8d MB Disk %d at %s  [%s]%s%s" % (mb(size), i, path, model, "  (removable)" if rm else "",
                                                       "  (Setup medium)" if boot else "")
            row = Gtk.Box()
            l = Gtk.Label(label=text, xalign=0)
            row.pack_start(l, True, True, 0)
            if i == self.disk_index:
                css_class(row, "ts-selected")
            box.pack_start(row, False, False, 0)
        s.body.pack_start(box, False, False, 0)
        self.set_screen("disks", s)

    def text_confirm(self):
        path, size, model, rm, boot = self.disk_list[self.disk_index]
        s = TextScreen("  C=Continue   ESC=Cancel")
        s.line("You chose to set up Whistler XP on:", bright=True)
        s.line()
        s.line("%d MB Disk %d at %s [%s]" % (mb(size), self.disk_index, path, model), indent=24)
        s.line()
        s.line("WARNING: Setup will delete EVERYTHING on this disk, including all partitions, programs "
               "and files. This cannot be undone.", bright=True)
        s.line()
        s.line("•  To continue and erase this disk, press C.", indent=24)
        s.line()
        s.line("•  To choose a different disk, press ESC.", indent=24)
        self.set_screen("confirm", s)

    def on_key(self, w, ev):
        k = ev.keyval
        if self.screen == "welcome":
            if k in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
                self.text_license()
            elif k == Gdk.KEY_F3:
                self.quit_setup()
        elif self.screen == "license":
            if k == Gdk.KEY_F8:
                self.text_disks()
            elif k in (Gdk.KEY_Escape, Gdk.KEY_F3):
                self.quit_setup()
        elif self.screen == "disks":
            if k == Gdk.KEY_Up and self.disk_index > 0:
                self.disk_index -= 1
                self.text_disks()
            elif k == Gdk.KEY_Down and self.disk_index < len(self.disk_list) - 1:
                self.disk_index += 1
                self.text_disks()
            elif k in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and self.disk_list:
                if self.disk_list[self.disk_index][4]:
                    return True
                if self.disk_list[self.disk_index][1] < 12 * 1024 ** 3:
                    return True
                self.text_confirm()
            elif k == Gdk.KEY_F3:
                self.quit_setup()
        elif self.screen == "confirm":
            if k in (Gdk.KEY_c, Gdk.KEY_C):
                self.info["disk"] = self.disk_list[self.disk_index][0]
                self.gui_setup()
            elif k == Gdk.KEY_Escape:
                self.text_disks()
        else:
            return False
        return True

    def quit_setup(self):
        self.destroy()
        Gtk.main_quit()

    # -------------------------------------------------------- GUI mode
    def gui_setup(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        css_class(root, "gs-root")
        top = Gtk.Box()
        css_class(top, "gs-top")
        logo = Gtk.Image.new_from_file("/usr/share/whistler/logos/wordmark-small.png")
        logo.set_margin_start(24)
        top.pack_start(logo, False, False, 0)
        root.pack_start(top, False, False, 0)
        mid = Gtk.Box()
        root.pack_start(mid, True, True, 0)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        css_class(side, "gs-side")
        self.step_labels = []
        for s in STEPS:
            l = Gtk.Label(label="○  " + s, xalign=0)
            self.step_labels.append(l)
            side.pack_start(l, False, False, 0)
        self.eta = Gtk.Label(label="", xalign=0)
        self.eta.set_line_wrap(True)
        self.eta.set_max_width_chars(24)
        side.pack_start(self.eta, False, False, 30)
        mid.pack_start(side, False, False, 0)
        self.overlay = Gtk.Overlay()
        mid.pack_start(self.overlay, True, True, 0)
        bb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        bb.set_margin_start(60)
        bb.set_margin_end(80)
        bb.set_valign(Gtk.Align.CENTER)
        self.bb_title = Gtk.Label(xalign=0)
        css_class(self.bb_title, "gs-billboard-title")
        self.bb_text = Gtk.Label(xalign=0)
        self.bb_text.set_line_wrap(True)
        self.bb_text.set_max_width_chars(50)
        css_class(self.bb_text, "gs-billboard-text")
        bb.pack_start(self.bb_title, False, False, 0)
        bb.pack_start(self.bb_text, False, False, 0)
        self.overlay.add(bb)
        self.billboard_box = bb
        self.billboard = 0
        self.next_billboard()
        GLib.timeout_add_seconds(25, self.next_billboard)

        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        bottom.set_margin_start(240)
        bottom.set_margin_bottom(20)
        bottom.set_margin_end(300)
        self.status = Gtk.Label(label="", xalign=0)
        css_class(self.status, "gs-status")
        self.bar = Gtk.ProgressBar()
        css_class(self.bar, "gs-progress")
        bottom.pack_start(self.status, False, False, 0)
        bottom.pack_start(self.bar, False, False, 0)
        root.pack_start(bottom, False, False, 0)
        strip = Gtk.Box()
        css_class(strip, "gs-bottom")
        root.pack_start(strip, False, False, 0)
        self.set_screen("gui", root)
        self.set_step(0)
        self.eta.set_text("Setup will complete in approximately:\n15 minutes")
        self.dialog_personalize()

    def next_billboard(self):
        t, x = BILLBOARDS[self.billboard % len(BILLBOARDS)]
        self.bb_title.set_text(t)
        self.bb_text.set_text(x)
        self.billboard += 1
        return True

    def set_step(self, i):
        for n, l in enumerate(self.step_labels):
            ctx = l.get_style_context()
            for c in ("gs-step-current", "gs-step-done"):
                ctx.remove_class(c)
            mark = "●" if n == i else ("✓" if n < i else "○")
            l.set_text("%s  %s" % (mark, STEPS[n]))
            if n == i:
                ctx.add_class("gs-step-current")
            elif n < i:
                ctx.add_class("gs-step-done")

    def dialog(self, title, header, subtitle, icon):
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        css_class(frame, "gs-dialog")
        frame.set_halign(Gtk.Align.CENTER)
        frame.set_valign(Gtk.Align.CENTER)
        frame.set_size_request(520, 380)
        tb = Gtk.Box()
        css_class(tb, "gs-dialog-title")
        tb.pack_start(Gtk.Label(label="Whistler XP Setup", xalign=0), True, True, 0)
        frame.pack_start(tb, False, False, 0)
        frame.pack_start(WizardHeader(header, subtitle, icon), False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        css_class(body, "xp-wizard-body")
        frame.pack_start(body, True, True, 0)
        btns = Gtk.Box(spacing=6)
        css_class(btns, "xp-wizard-buttons")
        frame.pack_end(btns, False, False, 0)
        for c in self.overlay.get_children()[1:]:
            c.destroy()
        self.overlay.add_overlay(frame)
        self.billboard_box.hide()
        return frame, body, btns

    def nav(self, btns, back, nxt, next_label="Next >"):
        b = Gtk.Button(label="< Back")
        b.set_size_request(75, 23)
        b.set_sensitive(back is not None)
        if back:
            b.connect("clicked", lambda *_: back())
        n = Gtk.Button(label=next_label)
        n.set_size_request(75, 23)
        n.connect("clicked", lambda *_: nxt())
        btns.pack_end(n, False, False, 0)
        btns.pack_end(b, False, False, 0)
        return n

    def dialog_personalize(self):
        frame, body, btns = self.dialog("Setup", "Personalize Your Software",
                                        "Setup uses the information you provide about yourself to personalize "
                                        "Whistler XP.", "system-users")
        body.pack_start(Gtk.Label(label="Type your full name.", xalign=0), False, False, 0)
        g = Gtk.Grid(column_spacing=10, row_spacing=8)
        g.attach(Gtk.Label(label="Name:", xalign=0), 0, 0, 1, 1)
        name = Gtk.Entry()
        name.set_text(self.info.get("fullname", ""))
        name.set_hexpand(True)
        g.attach(name, 1, 0, 1, 1)
        body.pack_start(g, False, False, 0)
        err = Gtk.Label(xalign=0)
        body.pack_start(err, False, False, 0)

        def nxt():
            n = name.get_text().strip()
            if not n:
                err.set_text("Please type your name.")
                return
            self.info["fullname"] = n
            self.dialog_computer()
        self.nav(btns, None, nxt)
        frame.show_all()
        name.grab_focus()

    def dialog_computer(self):
        frame, body, btns = self.dialog("Setup", "Computer Name and Password",
                                        "Choose a name for this computer and a password for your account.",
                                        "computer")
        login = re.sub(r"[^a-z0-9_-]", "", self.info["fullname"].lower().split()[0]) or "user"
        if login[0].isdigit():
            login = "u" + login
        g = Gtk.Grid(column_spacing=10, row_spacing=8)
        hn = Gtk.Entry()
        hn.set_text(self.info.get("hostname", (login + "-pc")[:15]))
        lg = Gtk.Entry()
        lg.set_text(self.info.get("login", login))
        pw1 = Gtk.Entry()
        pw1.set_visibility(False)
        pw2 = Gtk.Entry()
        pw2.set_visibility(False)
        pw1.set_text(self.info.get("password", ""))
        pw2.set_text(self.info.get("password", ""))
        rows = [("Computer name:", hn), ("User name (for logging on):", lg), ("Password:", pw1),
                ("Confirm password:", pw2)]
        for i, (t, w) in enumerate(rows):
            g.attach(Gtk.Label(label=t, xalign=0), 0, i, 1, 1)
            w.set_hexpand(True)
            g.attach(w, 1, i, 1, 1)
        body.pack_start(g, False, False, 0)
        auto = Gtk.CheckButton(label="Log on automatically (no Welcome screen)")
        auto.set_active(self.info.get("autologin", False))
        body.pack_start(auto, False, False, 0)
        hint = Gtk.Label(label="If you leave the password blank, anyone can use this account.", xalign=0)
        hint.set_line_wrap(True)
        body.pack_start(hint, False, False, 0)
        err = Gtk.Label(xalign=0)
        body.pack_start(err, False, False, 0)

        def nxt():
            h = hn.get_text().strip()
            l = lg.get_text().strip()
            if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}$", h):
                err.set_text("The computer name may only contain letters, numbers and dashes.")
                return
            if not re.match(r"^[a-z_][a-z0-9_-]{0,30}$", l) or l in ("root", "bin", "daemon", "user"):
                err.set_text("The user name must start with a lowercase letter and use only a-z, 0-9, - and _.")
                return
            if pw1.get_text() != pw2.get_text():
                err.set_text("The passwords do not match.")
                return
            self.info.update(hostname=h, login=l, password=pw1.get_text(),
                             autologin=auto.get_active() or not pw1.get_text())
            self.dialog_regional()
        self.nav(btns, self.dialog_personalize, nxt)
        frame.show_all()

    def dialog_regional(self):
        frame, body, btns = self.dialog("Setup", "Regional and Time Settings",
                                        "Set your keyboard layout and time zone.", "preferences-system-time")
        g = Gtk.Grid(column_spacing=10, row_spacing=10)
        kb = Gtk.ComboBoxText()
        for label, code in LAYOUTS:
            kb.append(code, label)
        kb.set_active_id(self.info.get("xkb", "us"))
        tz = Gtk.ComboBoxText()
        try:
            zones = subprocess.run(["timedatectl", "list-timezones"], capture_output=True,
                                   text=True).stdout.split()
        except OSError:
            zones = ["UTC"]
        cur = self.info.get("timezone") or os.path.realpath("/etc/localtime").split("zoneinfo/")[-1]
        for z in zones:
            tz.append(z, z.replace("_", " "))
        tz.set_active_id(cur if cur in zones else "UTC")
        g.attach(Gtk.Label(label="Keyboard layout:", xalign=0), 0, 0, 1, 1)
        g.attach(kb, 1, 0, 1, 1)
        g.attach(Gtk.Label(label="Time zone:", xalign=0), 0, 1, 1, 1)
        g.attach(tz, 1, 1, 1, 1)
        body.pack_start(g, False, False, 0)

        def nxt():
            self.info.update(xkb=kb.get_active_id() or "us", timezone=tz.get_active_id() or "UTC")
            self.dialog_ready()
        self.nav(btns, self.dialog_computer, nxt)
        frame.show_all()

    def dialog_ready(self):
        frame, body, btns = self.dialog("Setup", "Ready to Install",
                                        "Setup has collected the information it needs.", "whistler-setup")
        for t in ("Disk:  %s (will be erased)" % self.info["disk"],
                  "Name:  %s" % self.info["fullname"],
                  "User name:  %s" % self.info["login"],
                  "Computer name:  %s" % self.info["hostname"],
                  "Keyboard:  %s     Time zone:  %s" % (self.info["xkb"], self.info["timezone"])):
            body.pack_start(Gtk.Label(label=t, xalign=0), False, False, 0)
        body.pack_start(Gtk.Label(label="To start installing, click Install.", xalign=0), False, False, 10)
        self.nav(btns, self.dialog_regional, self.start_install, next_label="Install")
        frame.show_all()

    # --------------------------------------------------------- install
    def start_install(self):
        for c in self.overlay.get_children()[1:]:
            c.destroy()
        self.billboard_box.show_all()
        self.overlay.queue_draw()
        self.set_step(1)
        self.started = time.monotonic()
        pics = sorted(f for f in os.listdir(USERPICS) if f.endswith(".png")) if os.path.isdir(USERPICS) else []
        conf = {
            "DISK": self.info["disk"], "FULLNAME": self.info["fullname"], "LOGIN": self.info["login"],
            "PASSWORD": self.info["password"], "HOSTNAME": self.info["hostname"],
            "TIMEZONE": self.info["timezone"], "XKB_LAYOUT": self.info["xkb"],
            "AUTOLOGIN": "yes" if self.info["autologin"] else "no",
            "USERPIC": os.path.join(USERPICS, random.choice(pics)) if pics else "",
        }
        fd, path = tempfile.mkstemp(prefix="whistler-setup-", suffix=".conf")
        with os.fdopen(fd, "w") as f:
            for k, v in conf.items():
                f.write("%s=%s\n" % (k, shlex.quote(v)))
        argv = ["pkexec", "/usr/bin/whistler-install-backend", path]
        if os.geteuid() == 0:
            argv = argv[1:]
        self.proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                     bufsize=1)
        GLib.io_add_watch(self.proc.stdout, GLib.PRIORITY_DEFAULT, GLib.IO_IN | GLib.IO_HUP, self.on_output)
        self.status.set_text("Preparing installation...")
        self.error = None

    def on_output(self, src, cond):
        line = src.readline()
        if not line:
            self.proc.wait()
            self.finished(self.proc.returncode)
            return False
        line = line.strip()
        if line.startswith("PROGRESS "):
            parts = line.split(" ", 2)
            pct = int(parts[1])
            msg = parts[2] if len(parts) > 2 else ""
            self.bar.set_fraction(pct / 100)
            self.status.set_text(msg)
            self.set_step(1 if pct < 8 else (2 if pct < 79 else 3))
            elapsed = time.monotonic() - self.started
            if pct > 3:
                remaining = elapsed * (100 - pct) / pct
                mins = max(1, int(remaining / 60 + 0.5))
                self.eta.set_text("Setup will complete in approximately:\n%d minute%s" % (mins, "s" * (mins != 1)))
        elif line.startswith("ERROR "):
            self.error = line[6:]
        return True

    def finished(self, code):
        if code == 0:
            self.set_step(4)
            self.eta.set_text("")
            frame, body, btns = self.dialog("Setup", "Completing Whistler XP Setup",
                                            "Whistler XP has been installed on your computer.", "whistler-setup")
            body.pack_start(Gtk.Label(label="Remove the CD or USB stick, then click Restart Now to start "
                                            "Whistler XP from the hard disk.", xalign=0, wrap=True),
                            False, False, 0)
            self.countdown = 30
            cd = Gtk.Label(label="", xalign=0)
            body.pack_start(cd, False, False, 10)
            r = Gtk.Button(label="Restart Now")
            r.connect("clicked", lambda *_: subprocess.Popen(["systemctl", "reboot"]))
            btns.pack_end(r, False, False, 0)
            later = Gtk.Button(label="Close")
            later.connect("clicked", lambda *_: self.quit_setup())
            btns.pack_end(later, False, False, 0)
            frame.show_all()

            def tick():
                self.countdown -= 1
                cd.set_text("Your computer will restart in %d seconds." % self.countdown)
                if self.countdown <= 0:
                    subprocess.Popen(["systemctl", "reboot"])
                    return False
                return True
            GLib.timeout_add_seconds(1, tick)
        else:
            frame, body, btns = self.dialog("Setup", "Setup Failed",
                                            "Whistler XP could not be installed.", "dialog-error")
            body.pack_start(Gtk.Label(label=self.error or "Setup stopped unexpectedly (code %d)." % code,
                                      xalign=0, wrap=True), False, False, 0)
            body.pack_start(Gtk.Label(label="Details are in /var/log/whistler-install.log.", xalign=0),
                            False, False, 0)
            c = Gtk.Button(label="Close")
            c.connect("clicked", lambda *_: self.quit_setup())
            btns.pack_end(c, False, False, 0)
            frame.show_all()


def main():
    load_css("whistler.css")
    prov = Gtk.CssProvider()
    prov.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
    if not os.path.isdir("/run/archiso/airootfs"):
        Gtk.init(None)
        dlg = Gtk.MessageDialog(message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                text="Whistler XP is already installed.")
        dlg.format_secondary_text("Setup only runs from the Whistler XP CD or USB stick.")
        dlg.run()
        return 0
    Setup()
    Gtk.main()
    return 0
