"""The XP "Run" dialog."""
import os
import re
import shlex
import shutil
import sys

from gi.repository import Gdk, GLib, Gtk

from .common import DATA_HOME, css_class, image, load_css, open_uri, spawn, xp_message

HISTORY = os.path.join(DATA_HOME, "run-history")

# Windows command names mapped to their Whistler equivalents.
ALIASES = {
    "cmd": "whistler-cmd", "command": "whistler-cmd",
    "notepad": "mousepad", "calc": "galculator", "mspaint": "mtpaint", "pbrush": "mtpaint",
    "write": "abiword", "wordpad": "abiword", "explorer": "thunar", "iexplore": "firefox",
    "wmplayer": "parole", "charmap": "gucharmap", "taskmgr": "xfce4-taskmanager",
    "control": "whistler-control", "regedit": "wine regedit", "winecfg": "winecfg",
    "winver": "whistler-sysprops --about", "msinfo32": "whistler-sysprops", "dxdiag": "whistler-sysprops",
    "msconfig": "xfce4-session-settings", "sndvol32": "whistler-volume", "sndvol": "whistler-volume",
    "shutdown": "whistler-shutdown", "logoff": "whistler-logoff", "winmine": "whistler-minesweeper",
    "sol": "sol --variation klondike", "freecell": "sol --variation freecell",
    "spider": "sol --variation spider", "appwiz.cpl": "whistler-addremove",
    "desk.cpl": "xfce4-appearance-settings", "ncpa.cpl": "nm-connection-editor",
    "sysdm.cpl": "whistler-sysprops", "mmsys.cpl": "whistler-volume", "main.cpl": "xfce4-mouse-settings",
    "nusrmgr.cpl": "whistler-useraccounts", "timedate.cpl": "whistler-control datetime",
    "intl.cpl": "whistler-control regional", "access.cpl": "xfce4-accessibility-settings",
    "printers": "system-config-printer", "diskmgmt.msc": "gnome-disks", "devmgmt.msc": "whistler-sysprops --hardware",
    "services.msc": "xfce4-session-settings", "magnify": "xfce4-accessibility-settings",
}

WINDOWS_EXT = (".exe", ".msi", ".bat", ".com", ".lnk")


def load_history():
    try:
        with open(HISTORY) as f:
            return [l.rstrip("\n") for l in f if l.strip()]
    except OSError:
        return []


def save_history(entry, hist):
    hist = [entry] + [h for h in hist if h != entry]
    os.makedirs(DATA_HOME, exist_ok=True)
    with open(HISTORY, "w") as f:
        f.write("\n".join(hist[:26]) + "\n")


def execute(text):
    """Try to run `text` the way Windows' Run box would. Returns True on success."""
    text = text.strip()
    if not text:
        return False
    if re.match(r"^[a-z][a-z0-9+.-]*://", text, re.I) or text.lower().startswith("www."):
        return open_uri(text if "://" in text else "http://" + text)
    expanded = os.path.expandvars(os.path.expanduser(text))
    if re.match(r"^[A-Za-z]:\\", text):
        return spawn(["wine", "start", text])
    if os.path.exists(expanded):
        if expanded.lower().endswith(WINDOWS_EXT):
            return spawn(["whistler-winecenter", "--run", expanded])
        if os.path.isdir(expanded) or not os.access(expanded, os.X_OK):
            return open_uri(expanded)
        return spawn([expanded])
    try:
        argv = shlex.split(text)
    except ValueError:
        argv = text.split()
    if not argv:
        return False
    if len(argv) == 1 and argv[0] != text and os.path.exists(os.path.expanduser(argv[0])):
        return execute(argv[0])
    head = argv[0].lower()
    if head in ALIASES:
        return spawn(shlex.split(ALIASES[head]) + argv[1:])
    if head.endswith(".exe") and head[:-4] in ALIASES:
        return spawn(shlex.split(ALIASES[head[:-4]]) + argv[1:])
    if shutil.which(argv[0]):
        return spawn(["sh", "-c", text])
    if head.endswith(".exe"):
        return spawn(["wine"] + argv)
    return False


class RunDialog(Gtk.Window):
    def __init__(self):
        super().__init__(title="Run")
        self.set_resizable(False)
        self.set_icon_name("system-run")
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_keep_above(True)
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self.on_key)
        css_class(self, "xp-run-dialog")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(11)
        self.add(box)

        top = Gtk.Box(spacing=12)
        top.pack_start(image("system-run", 32), False, False, 0)
        msg = Gtk.Label(label="Type the name of a program, folder, document, or Internet "
                              "resource, and Whistler will open it for you.", xalign=0)
        msg.set_line_wrap(True)
        msg.set_max_width_chars(46)
        top.pack_start(msg, True, True, 0)
        box.pack_start(top, False, False, 0)

        row = Gtk.Box(spacing=8)
        lbl = Gtk.Label.new_with_mnemonic("_Open:")
        row.pack_start(lbl, False, False, 0)
        self.hist = load_history()
        self.combo = Gtk.ComboBoxText.new_with_entry()
        for h in self.hist:
            self.combo.append_text(h)
        entry = self.combo.get_child()
        if self.hist:
            entry.set_text(self.hist[0])
            entry.select_region(0, -1)
        entry.set_activates_default(True)
        entry.set_width_chars(36)
        lbl.set_mnemonic_widget(entry)
        row.pack_start(self.combo, True, True, 0)
        box.pack_start(row, False, False, 0)

        buttons = Gtk.Box(spacing=6)
        buttons.set_halign(Gtk.Align.END)
        ok = Gtk.Button(label="OK")
        ok.set_can_default(True)
        ok.connect("clicked", self.on_ok)
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda *_: self.destroy())
        browse = Gtk.Button.new_with_mnemonic("_Browse...")
        browse.connect("clicked", self.on_browse)
        for b in (ok, cancel, browse):
            b.set_size_request(75, 23)
            buttons.pack_start(b, False, False, 0)
        box.pack_start(buttons, False, False, 0)
        self.ok = ok

        self.connect("realize", lambda w: w.get_window().set_functions(
            Gdk.WMFunction.MOVE | Gdk.WMFunction.CLOSE))
        self.show_all()
        ok.grab_default()
        entry.grab_focus()
        self.place()

    def place(self):
        display = Gdk.Display.get_default()
        mon = display.get_primary_monitor() or display.get_monitor(0)
        work = mon.get_workarea()
        w, h = self.get_size()
        self.move(work.x + 6, work.y + work.height - h - 40)

    def on_key(self, w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    def on_ok(self, *_):
        text = self.combo.get_child().get_text().strip()
        if not text:
            return
        if execute(text):
            save_history(text, self.hist)
            self.destroy()
        else:
            xp_message(self, "Whistler cannot find '%s'. Make sure you typed the name correctly, "
                             "and then try again. To search for a file, click the Start button, "
                             "and then click Search." % text, kind=Gtk.MessageType.ERROR, title=text)

    def on_browse(self, *_):
        dlg = Gtk.FileChooserDialog(title="Browse", transient_for=self, action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.ACCEPT)
        f = Gtk.FileFilter()
        f.set_name("Programs")
        for pat in ("*.exe", "*.msi", "*.bat", "*.sh", "*.desktop", "*.AppImage"):
            f.add_pattern(pat)
        dlg.add_filter(f)
        a = Gtk.FileFilter()
        a.set_name("All Files")
        a.add_pattern("*")
        dlg.add_filter(a)
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            path = dlg.get_filename()
            self.combo.get_child().set_text(shlex.quote(path) if " " in path else path)
        dlg.destroy()


def main():
    load_css("whistler.css")
    RunDialog()
    Gtk.main()
    return 0
