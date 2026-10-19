"""Import Windows XP Files wizard (runs as the user; the work happens in a
root backend started with pkexec)."""
import glob
import os
import subprocess
import sys

import whistler  # noqa: F401  (sets GI versions)
from gi.repository import GLib, Gtk

from whistler.common import WizardHeader, css_class, image, load_css, spawn, xp_message

BACKEND = "/usr/lib/whistler/whistler-import-xp-backend"
ROOT = "/var/lib/whistler/originals"
SOUND = "/usr/share/whistler/assets/current/sounds/system-bootup.wav"


def find_cd():
    for base in ("/run/media", "/media", "/mnt"):
        for d in glob.glob(os.path.join(base, "*", "*")) + glob.glob(os.path.join(base, "*")):
            if os.path.isdir(os.path.join(d, "I386")) or os.path.isdir(os.path.join(d, "i386")):
                return d
    return None


def imported():
    return os.path.isdir(os.path.join(ROOT, "assets"))


def reload_desktop():
    """Make the running session pick up new theme files."""
    cmds = [
        "xfconf-query -c xsettings -p /Net/ThemeName -s Default && sleep 1 && "
        "xfconf-query -c xsettings -p /Net/ThemeName -s Whistler",
        "xfconf-query -c xsettings -p /Net/IconThemeName -s hicolor && sleep 1 && "
        "xfconf-query -c xsettings -p /Net/IconThemeName -s Whistler",
        "xfwm4 --replace >/dev/null 2>&1 &",
        "xfce4-panel -r",
        "xfdesktop --reload",
        "whistler-startmenu --quit; sleep 1; whistler-startmenu --daemon >/dev/null 2>&1 &",
    ]
    for c in cmds:
        subprocess.Popen(["sh", "-c", c], start_new_session=True, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)


class Wizard(Gtk.Window):
    def __init__(self, source=None):
        super().__init__(title="Import Windows XP Files Wizard")
        self.set_icon_name("system-software-install")
        self.set_default_size(560, 400)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)
        self.source = source or find_cd() or ""
        self.kind = "iso" if self.source.lower().endswith(".iso") else "folder"
        self.page = 0
        self.result = None
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)
        self.content = Gtk.Box()
        root.pack_start(self.content, True, True, 0)
        btns = Gtk.Box(spacing=6)
        css_class(btns, "xp-wizard-buttons")
        self.back = Gtk.Button(label="< Back")
        self.next = Gtk.Button(label="Next >")
        self.cancel = Gtk.Button(label="Cancel")
        for b in (self.back, self.next, self.cancel):
            b.set_size_request(75, 23)
        btns.pack_end(self.cancel, False, False, 0)
        btns.pack_end(self.next, False, False, 6)
        btns.pack_end(self.back, False, False, 0)
        root.pack_start(btns, False, False, 0)
        self.back.connect("clicked", lambda *_: self.go(self.page - 1))
        self.next.connect("clicked", lambda *_: self.on_next())
        self.cancel.connect("clicked", lambda *_: self.destroy())
        self.go(0)
        self.show_all()

    def clear(self):
        for c in self.content.get_children():
            c.destroy()

    def side_layout(self, title, text):
        side = Gtk.Box()
        css_class(side, "xp-wizard-sidebar")
        side.set_size_request(164, -1)
        img = image("system-software-install", 96)
        img.set_valign(Gtk.Align.START)
        img.set_margin_top(20)
        side.pack_start(img, True, True, 0)
        self.content.pack_start(side, False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        css_class(body, "xp-wizard-white")
        t = Gtk.Label(label=title, xalign=0)
        t.set_line_wrap(True)
        css_class(t, "xp-wizard-welcome-title")
        body.pack_start(t, False, False, 0)
        lab = Gtk.Label(label=text, xalign=0)
        lab.set_line_wrap(True)
        lab.set_max_width_chars(52)
        body.pack_start(lab, False, False, 0)
        self.content.pack_start(body, True, True, 0)
        return body

    def interior(self, title, subtitle):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        col.pack_start(WizardHeader(title, subtitle, "system-software-install"), False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        css_class(body, "xp-wizard-body")
        col.pack_start(body, True, True, 0)
        self.content.pack_start(col, True, True, 0)
        return body

    def go(self, page):
        self.page = page
        self.clear()
        getattr(self, "page_%d" % page)()
        self.content.show_all()
        self.update()

    def update(self):
        self.back.set_sensitive(self.page == 1)
        self.next.set_label({1: "Import", 3: "Finish"}.get(self.page, "Next >"))
        ok = True
        if self.page == 1:
            ok = bool(self.source) and os.path.exists(self.source)
        if self.page == 2:
            ok = False
        self.next.set_sensitive(ok)
        self.cancel.set_sensitive(self.page != 2)

    def page_0(self):
        body = self.side_layout(
            "Welcome to the Import Windows XP Files Wizard",
            "Whistler XP comes with its own lookalike artwork. If you have a Windows XP CD, ISO image "
            "or an old Windows XP folder, this wizard can copy the original visual style, wallpapers, "
            "icons, pointers, fonts and sounds from it - including the famous startup sound.\n\n"
            "Nothing is downloaded: only the media you choose is used. Please use media you are "
            "licensed to use.\n\nTo continue, click Next.")
        if imported():
            box = Gtk.Box(spacing=8)
            box.pack_start(Gtk.Label(label="Original Windows XP files are already imported.", xalign=0),
                           True, True, 0)
            rm = Gtk.Button(label="Remove them")
            rm.connect("clicked", lambda *_: self.remove())
            box.pack_end(rm, False, False, 0)
            body.pack_end(box, False, False, 0)

    def page_1(self):
        body = self.interior("Windows XP Files", "Where are your Windows XP files?")
        iso = Gtk.RadioButton.new_with_label(None, "A Windows XP CD or ISO image file (.iso)")
        folder = Gtk.RadioButton.new_with_label_from_widget(
            iso, "A folder: a mounted CD, an I386 folder, or a Windows folder from an old disk")
        (iso if self.kind == "iso" else folder).set_active(True)
        body.pack_start(iso, False, False, 0)
        body.pack_start(folder, False, False, 0)
        row = Gtk.Box(spacing=6)
        entry = Gtk.Entry()
        entry.set_text(self.source)
        row.pack_start(entry, True, True, 0)
        br = Gtk.Button(label="Browse...")
        row.pack_start(br, False, False, 0)
        body.pack_start(row, False, False, 6)
        hint = Gtk.Label(label="Tip: insert your Windows XP CD and Whistler finds it automatically.", xalign=0)
        hint.set_line_wrap(True)
        body.pack_start(hint, False, False, 0)

        def changed(*_):
            self.source = entry.get_text().strip()
            self.kind = "iso" if iso.get_active() else "folder"
            self.update()

        def browse(*_):
            action = Gtk.FileChooserAction.OPEN if iso.get_active() else Gtk.FileChooserAction.SELECT_FOLDER
            dlg = Gtk.FileChooserDialog(title="Browse", transient_for=self, action=action)
            dlg.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.ACCEPT)
            if iso.get_active():
                f = Gtk.FileFilter()
                f.set_name("CD images (*.iso)")
                f.add_pattern("*.iso")
                f.add_pattern("*.ISO")
                dlg.add_filter(f)
            if dlg.run() == Gtk.ResponseType.ACCEPT:
                entry.set_text(dlg.get_filename())
            dlg.destroy()
        entry.connect("changed", changed)
        iso.connect("toggled", changed)
        br.connect("clicked", browse)

    def page_2(self):
        body = self.interior("Importing", "Please wait while Whistler copies the Windows XP files.")
        self.status = Gtk.Label(label="Starting...", xalign=0)
        body.pack_start(self.status, False, False, 0)
        self.bar = Gtk.ProgressBar()
        body.pack_start(self.bar, False, False, 0)
        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_monospace(True)
        sc = Gtk.ScrolledWindow()
        sc.set_size_request(-1, 150)
        sc.add(tv)
        exp = Gtk.Expander(label="Details")
        exp.add(sc)
        body.pack_start(exp, True, True, 0)
        self.log = tv.get_buffer()
        self.counts = {}
        self.error = None
        GLib.idle_add(self.start)

    def page_3(self):
        if self.result == 0:
            lines = "\n".join("    • %s: %s" % (k.capitalize(), v) for k, v in self.counts.items())
            text = ("The original Windows XP files were imported:\n\n%s\n\nThe new look is applied now. "
                    "Some programs show it after you log off and on again.\n\nTo close this wizard, "
                    "click Finish." % lines)
            reload_desktop()
            if os.path.exists(SOUND):
                GLib.timeout_add(2500, lambda: spawn(["paplay", SOUND]) and False)
        else:
            text = "The files could not be imported.\n\n%s" % (self.error or "Unknown problem.")
        self.side_layout("Completing the Import Windows XP Files Wizard", text)

    def on_next(self):
        if self.page == 3:
            self.destroy()
            return
        self.go(self.page + 1)

    def start(self):
        try:
            self.proc = subprocess.Popen(["pkexec", BACKEND, self.source], stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, bufsize=1)
        except OSError as e:
            self.error = str(e)
            self.result = 1
            self.go(3)
            return False
        GLib.io_add_watch(self.proc.stdout, GLib.PRIORITY_DEFAULT, GLib.IO_IN | GLib.IO_HUP, self.on_output)
        return False

    def on_output(self, src, cond):
        line = src.readline()
        if not line:
            self.result = self.proc.wait()
            if self.result == 126 or self.result == 127:
                self.error = self.error or "Permission was not granted."
            self.go(3)
            return False
        line = line.rstrip("\n")
        self.log.insert(self.log.get_end_iter(), line + "\n")
        if line.startswith("PROGRESS "):
            _, pct, msg = line.split(" ", 2)
            self.bar.set_fraction(int(pct) / 100)
            self.status.set_text(msg)
        elif line.startswith("COUNT "):
            k, v = line[6:].split("=", 1)
            self.counts[k] = v
        elif line.startswith("ERROR "):
            self.error = line[6:]
        return True

    def remove(self):
        r = xp_message(self, "Remove the imported Windows XP files?",
                       "Whistler XP goes back to its own lookalike artwork and sounds.",
                       kind=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.YES_NO)
        if r != Gtk.ResponseType.YES:
            return
        subprocess.run(["pkexec", BACKEND, "--remove"])
        reload_desktop()
        self.go(0)


def main():
    load_css("whistler.css")
    Wizard(sys.argv[1] if len(sys.argv) > 1 else None)
    Gtk.main()
    return 0
