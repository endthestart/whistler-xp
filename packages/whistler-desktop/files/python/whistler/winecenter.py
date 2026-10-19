"""Wine Center: install, run and manage Windows programs with Wine."""
import configparser
import glob
import os
import re
import shlex
import shutil
import subprocess
import sys

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango

from .common import (DATA_HOME, TaskPane, WizardHeader, css_class, gicon_pixbuf, icon_pixbuf, image,
                     load_css, open_uri, run_async, spawn, xp_message)

PREFIX_ROOT = os.path.join(GLib.get_user_data_dir(), "wineprefixes")
WINE_APPS = os.path.join(GLib.get_user_data_dir(), "applications", "wine")

WINDOWS_VERSIONS = [("Windows 10", "win10"), ("Windows 11", "win11"), ("Windows 7", "win7"),
                    ("Windows XP", "winxp64"), ("Windows 8.1", "win81"), ("Windows Vista", "vista")]

# Curated winetricks verbs: (verb, title, description, default-on in wizard)
COMPONENTS = [
    ("vcrun2022", "Visual C++ 2015-2022 runtime", "Needed by most modern programs and games.", False),
    ("vcrun2010", "Visual C++ 2010 runtime", "Needed by many programs from around 2010.", False),
    ("vcrun2008", "Visual C++ 2008 runtime", "Needed by older programs.", False),
    ("vcrun6", "Visual C++ 6 runtime", "Needed by very old programs.", False),
    ("dotnet48", ".NET Framework 4.8", "For programs written in .NET. Large download; installs slowly.", False),
    ("dotnet35", ".NET Framework 3.5", "For older .NET programs.", False),
    ("d3dx9", "DirectX 9 extra libraries", "Helper libraries used by many older games.", False),
    ("d3dcompiler_47", "Direct3D shader compiler", "Used by some games and browsers.", False),
    ("xact", "DirectX audio (XACT)", "Sound for some older games.", False),
    ("dxvk", "DXVK (fast Direct3D 9/10/11)", "Runs Direct3D through Vulkan for better game performance.", False),
    ("vkd3d", "VKD3D-Proton (Direct3D 12)", "Direct3D 12 through Vulkan.", False),
    ("corefonts", "Microsoft core fonts", "Arial, Times New Roman, Verdana and friends.", False),
    ("vb6run", "Visual Basic 6 runtime", "For classic Visual Basic programs.", False),
    ("mfc42", "MFC 4.2 libraries", "For old Microsoft Foundation Class programs.", False),
    ("gdiplus", "GDI+ graphics library", "Fixes drawing problems in some programs.", False),
    ("quartz", "DirectShow (quartz)", "Video playback in some older programs.", False),
]


def wine_version():
    try:
        return subprocess.run(["wine", "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "wine (unknown version)"


class Env:
    def __init__(self, name, path, default=False):
        self.name = name
        self.path = path
        self.default = default

    @property
    def drive_c(self):
        return os.path.join(self.path, "drive_c")

    @property
    def label(self):
        return "Shared environment (C:)" if self.default else "%s (C:)" % self.name

    def ready(self):
        return os.path.isfile(os.path.join(self.path, "system.reg"))

    def environ(self):
        return {"WINEPREFIX": self.path, "WINEDEBUG": "-all"}

    def windows_version(self):
        try:
            with open(os.path.join(self.path, "system.reg"), encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            return "Not set up yet"
        m = re.search(r'\[Software\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\][^\[]*?"ProductName"="([^"]*)"',
                      text)
        return m.group(1) if m else "Unknown"

    def __eq__(self, other):
        return isinstance(other, Env) and os.path.realpath(self.path) == os.path.realpath(other.path)


def environments():
    envs = [Env("Default", os.path.expanduser("~/.wine"), default=True)]
    for p in sorted(glob.glob(os.path.join(PREFIX_ROOT, "*"))):
        if os.path.isdir(p):
            envs.append(Env(os.path.basename(p), p))
    return envs


def env_for_file(path):
    real = os.path.realpath(path)
    for e in environments():
        if real.startswith(os.path.realpath(e.drive_c) + os.sep):
            return e
    return environments()[0]


class Program:
    def __init__(self, desktop_file, info):
        self.file = desktop_file
        self.info = info
        self.name = info.get_display_name() or info.get_name()
        self.gicon = info.get_icon()
        cmd = info.get_commandline() or ""
        m = re.search(r'WINEPREFIX="([^"]+)"', cmd) or re.search(r"WINEPREFIX=(\S+)", cmd)
        self.prefix = m.group(1) if m else os.path.expanduser("~/.wine")


def programs(env=None):
    out = []
    for f in glob.glob(os.path.join(WINE_APPS, "**", "*.desktop"), recursive=True):
        if os.sep + "Programs" + os.sep not in f:
            continue
        try:
            info = Gio.DesktopAppInfo.new_from_filename(f)
        except TypeError:
            info = None
        if info is None:
            continue
        p = Program(f, info)
        low = p.name.lower()
        if any(w in low for w in ("uninstall", "readme", "read me", "help", "website", "license", "manual")):
            continue
        if env is None or os.path.realpath(p.prefix) == os.path.realpath(env.path):
            out.append(p)
    out.sort(key=lambda p: p.name.lower())
    return out


def trust_desktop_shortcuts():
    """Mark .desktop shortcuts Wine put on the desktop as trusted for xfdesktop."""
    subprocess.run(["whistler-wine-trust"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def launch_argv(path):
    low = path.lower()
    if low.endswith(".msi"):
        return ["wine", "msiexec", "/i", path]
    if low.endswith((".bat", ".cmd")):
        return ["wine", "cmd", "/c", path]
    if low.endswith(".lnk"):
        return ["wine", "start", "/unix", path]
    return ["wine", path]


def run_windows_program(path, env=None):
    """Start a Windows program detached; trust any shortcuts it creates when it exits."""
    env = env or env_for_file(path)
    argv = launch_argv(path)
    full = dict(os.environ)
    full.update(env.environ())
    cmd = " ".join(shlex.quote(a) for a in argv) + "; wineserver -w; whistler-wine-menus --prefix " + \
        shlex.quote(env.path)
    subprocess.Popen(["sh", "-c", cmd], env=full, cwd=os.path.dirname(os.path.abspath(path)) or None,
                     start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------------------
class ProgressWindow(Gtk.Window):
    """XP-style 'please wait' window with a pulsing bar and a details log."""

    def __init__(self, parent, title, text):
        super().__init__(title=title)
        if parent:
            self.set_transient_for(parent)
            self.set_modal(True)
        self.set_icon_name("whistler-winecenter")
        self.set_default_size(420, -1)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_deletable(False)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(14)
        self.add(box)
        row = Gtk.Box(spacing=12)
        row.pack_start(image("whistler-winecenter", 32), False, False, 0)
        self.label = Gtk.Label(label=text, xalign=0)
        self.label.set_line_wrap(True)
        self.label.set_max_width_chars(48)
        row.pack_start(self.label, True, True, 0)
        box.pack_start(row, False, False, 0)
        self.bar = Gtk.ProgressBar()
        box.pack_start(self.bar, False, False, 0)
        self.log = LogView()
        exp = Gtk.Expander(label="Details")
        exp.add(self.log)
        box.pack_start(exp, True, True, 0)
        self.pulse_id = GLib.timeout_add(120, lambda: self.bar.pulse() or True)
        self.connect("destroy", lambda *_: GLib.source_remove(self.pulse_id))
        self.show_all()

    def set_text(self, text):
        self.label.set_text(text)


LOG_FILE = os.path.join(GLib.get_user_cache_dir(), "whistler", "winecenter.log")


class LogView(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        self.set_size_request(-1, 140)
        self.view = Gtk.TextView()
        self.view.set_editable(False)
        self.view.set_monospace(True)
        self.add(self.view)

    def append(self, text):
        try:
            with open(LOG_FILE, "a") as f:
                f.write(text)
        except OSError:
            pass
        buf = self.view.get_buffer()
        buf.insert(buf.get_end_iter(), text)
        self.view.scroll_to_iter(buf.get_end_iter(), 0, False, 0, 0)


def run_steps(steps, log, on_done):
    """steps: list of (description, argv, env, label_cb). Runs sequentially."""
    steps = list(steps)

    def next_step(code=0, out=""):
        if out:
            log.append(out if out.endswith("\n") else out + "\n")
        if not steps:
            on_done(code)
            return
        desc, argv, env, before = steps.pop(0)
        if before:
            before(desc)
        log.append("$ %s\n" % " ".join(argv))
        try:
            run_async(argv, lambda c, o: next_step(c, o), env=env)
        except GLib.Error as e:
            log.append("failed: %s\n" % e.message)
            next_step(1)
    next_step()


def ensure_env(parent, env, on_ready, winver=None):
    """Create the prefix if needed (showing progress), then call on_ready()."""
    if env.ready() and not winver:
        on_ready()
        return
    win = ProgressWindow(parent, "Wine Center",
                         "Preparing the Windows environment \"%s\". This happens once and can take a few minutes..."
                         % env.name)
    argv = ["whistler-wine-init", "--prefix", env.path]
    if winver:
        argv += ["--winver", winver]

    def done(code):
        win.destroy()
        on_ready()
    run_steps([("init", argv, env.environ(), None)], win.log, done)


# ---------------------------------------------------------------------------
class InstallWizard(Gtk.Window):
    """Add Windows Program Wizard."""

    def __init__(self, center, setup_file=None):
        super().__init__(title="Add Windows Program Wizard")
        self.center = center
        if center:
            self.set_transient_for(center)
        self.set_icon_name("whistler-winecenter")
        self.set_default_size(560, 400)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.page = 0
        self.setup_file = setup_file
        self.before = set()
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.root)
        self.content = Gtk.Box()
        self.root.pack_start(self.content, True, True, 0)
        buttons = Gtk.Box(spacing=6)
        css_class(buttons, "xp-wizard-buttons")
        self.back_btn = Gtk.Button(label="< Back")
        self.next_btn = Gtk.Button(label="Next >")
        self.cancel_btn = Gtk.Button(label="Cancel")
        for b in (self.back_btn, self.next_btn, self.cancel_btn):
            b.set_size_request(75, 23)
        buttons.pack_end(self.cancel_btn, False, False, 0)
        buttons.pack_end(self.next_btn, False, False, 6)
        buttons.pack_end(self.back_btn, False, False, 0)
        self.root.pack_start(buttons, False, False, 0)
        self.back_btn.connect("clicked", lambda *_: self.go(self.page - 1))
        self.next_btn.connect("clicked", lambda *_: self.on_next())
        self.cancel_btn.connect("clicked", lambda *_: self.destroy())

        # wizard state (pages rebuild their widgets from these)
        self.setup_path = setup_file or ""
        self.use_new_env = False
        self.env_path = environments()[0].path
        self.new_env_name = ""
        self.winver = WINDOWS_VERSIONS[0][1]
        self.verbs = {verb for verb, _t, _d, on in COMPONENTS if on}
        self.go(0)
        self.show_all()

    # pages -------------------------------------------------------------
    def go(self, page):
        self.page = page
        for c in self.content.get_children():
            self.content.remove(c)
        getattr(self, "page_%d" % page)()
        self.content.show_all()
        self.update_buttons()

    def welcome_layout(self, title, text):
        side = Gtk.Box()
        css_class(side, "xp-wizard-sidebar")
        side.set_size_request(164, -1)
        side_img = image("whistler-winecenter", 96)
        side_img.set_valign(Gtk.Align.START)
        side_img.set_margin_top(20)
        side.pack_start(side_img, True, True, 0)
        self.content.pack_start(side, False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        css_class(body, "xp-wizard-white")
        t = Gtk.Label(label=title, xalign=0)
        t.set_line_wrap(True)
        css_class(t, "xp-wizard-welcome-title")
        body.pack_start(t, False, False, 0)
        l = Gtk.Label(label=text, xalign=0)
        l.set_line_wrap(True)
        l.set_max_width_chars(52)
        body.pack_start(l, False, False, 0)
        self.content.pack_start(body, True, True, 0)
        return body

    def interior_layout(self, title, subtitle):
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        col.pack_start(WizardHeader(title, subtitle, "whistler-winecenter"), False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        css_class(body, "xp-wizard-body")
        col.pack_start(body, True, True, 0)
        self.content.pack_start(col, True, True, 0)
        return body

    def page_0(self):
        self.welcome_layout("Welcome to the Add Windows Program Wizard",
                            "This wizard helps you install a program made for Microsoft Windows.\n\n"
                            "You will need the program's setup file - usually called setup.exe, "
                            "install.exe, or a file ending in .msi.\n\n"
                            "To continue, click Next.")

    def page_1(self):
        body = self.interior_layout("Setup File", "Which program do you want to install?")
        body.pack_start(Gtk.Label(label="Type the location of the setup program, or click Browse:", xalign=0),
                        False, False, 0)
        row = Gtk.Box(spacing=6)
        self.file_entry = Gtk.Entry()
        self.file_entry.set_text(self.setup_path)
        self.file_entry.connect("changed", self.on_file_changed)
        row.pack_start(self.file_entry, True, True, 0)
        br = Gtk.Button(label="Browse...")
        br.connect("clicked", self.browse)
        row.pack_start(br, False, False, 0)
        body.pack_start(row, False, False, 0)
        hint = Gtk.Label(label="Tip: CD-ROM setup programs are usually in the top folder of the disc. "
                               "Downloaded installers are in My Documents\\Downloads.", xalign=0)
        hint.set_line_wrap(True)
        hint.set_max_width_chars(60)
        body.pack_start(hint, False, False, 8)

    def page_2(self):
        body = self.interior_layout("Windows Environment",
                                    "Choose where the program will be installed.")
        shared = Gtk.RadioButton.new_with_label(None, "Install into the shared Windows environment (recommended)")
        new = Gtk.RadioButton.new_with_label_from_widget(shared, "Install into a new, separate environment:")
        (new if self.use_new_env else shared).set_active(True)
        body.pack_start(shared, False, False, 0)
        combo = Gtk.ComboBoxText()
        for e in environments():
            combo.append(e.path, e.label)
        combo.set_active_id(self.env_path)
        if combo.get_active() < 0:
            combo.set_active(0)
        row = Gtk.Box(spacing=6)
        row.set_margin_start(24)
        row.pack_start(combo, True, True, 0)
        body.pack_start(row, False, False, 0)
        body.pack_start(new, False, False, 0)
        grid = Gtk.Grid(column_spacing=8, row_spacing=6)
        grid.set_margin_start(24)
        grid.attach(Gtk.Label(label="Name:", xalign=0), 0, 0, 1, 1)
        if not self.new_env_name and self.setup_file_name():
            self.new_env_name = self.suggest_name()
        name = Gtk.Entry()
        name.set_text(self.new_env_name)
        grid.attach(name, 1, 0, 1, 1)
        grid.attach(Gtk.Label(label="Pretend to be:", xalign=0), 0, 1, 1, 1)
        ver = Gtk.ComboBoxText()
        for label, code in WINDOWS_VERSIONS:
            ver.append(code, label)
        ver.set_active_id(self.winver)
        grid.attach(ver, 1, 1, 1, 1)
        body.pack_start(grid, False, False, 0)
        note = Gtk.Label(label="A separate environment keeps this program's settings and add-ons away from "
                               "your other Windows programs. Use one for games or programs that need special "
                               "components.", xalign=0)
        note.set_line_wrap(True)
        note.set_max_width_chars(60)
        body.pack_start(note, False, False, 6)

        def sync(*_):
            self.use_new_env = new.get_active()
            self.env_path = combo.get_active_id() or self.env_path
            self.new_env_name = name.get_text().strip()
            self.winver = ver.get_active_id() or self.winver
            self.update_buttons()
        for w, sig in ((new, "toggled"), (combo, "changed"), (name, "changed"), (ver, "changed")):
            w.connect(sig, sync)

    def page_3(self):
        body = self.interior_layout("Additional Components",
                                    "Some programs need extra Microsoft components. Select any your program needs.")
        sc = Gtk.ScrolledWindow()
        sc.set_size_request(-1, 210)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for verb, title, desc, _on in COMPONENTS:
            cb = Gtk.CheckButton(label=title)
            cb.set_tooltip_text(desc + " (winetricks: %s)" % verb)
            cb.set_active(verb in self.verbs)
            cb.connect("toggled", lambda b, v=verb: (self.verbs.add(v) if b.get_active() else self.verbs.discard(v)))
            box.pack_start(cb, False, False, 0)
        sc.add(box)
        body.pack_start(sc, True, True, 0)
        body.pack_start(Gtk.Label(label="Not sure? Leave these unchecked - you can add components later.",
                                  xalign=0), False, False, 0)

    def page_4(self):
        body = self.interior_layout("Installing", "Please wait while the program is installed.")
        self.status = Gtk.Label(label="Preparing...", xalign=0)
        self.status.set_line_wrap(True)
        body.pack_start(self.status, False, False, 0)
        self.bar = Gtk.ProgressBar()
        body.pack_start(self.bar, False, False, 0)
        self.log = LogView()
        exp = Gtk.Expander(label="Details")
        exp.add(self.log)
        body.pack_start(exp, True, True, 0)
        self.pulse = GLib.timeout_add(120, lambda: self.bar.pulse() or True)
        GLib.idle_add(self.start_install)

    def page_5(self):
        new = [p for p in programs(self.env) if p.file not in self.before]
        if self.result == 0 or new:
            text = "The setup program has finished.\n\n"
            if new:
                text += "These programs are now in your Start menu under All Programs:\n\n" + \
                        "\n".join("    • " + p.name for p in new[:10])
            else:
                text += "If the program added a shortcut, you will find it in the Start menu under All Programs, " \
                        "or in Wine Center."
        else:
            text = "The setup program did not finish successfully (code %d).\n\n" \
                   "Try installing again in a new separate environment, or add components such as " \
                   "the Visual C++ runtime or .NET Framework." % self.result
        self.welcome_layout("Completing the Add Windows Program Wizard", text + "\n\nTo close this wizard, click Finish.")

    # navigation --------------------------------------------------------
    def update_buttons(self):
        self.back_btn.set_sensitive(self.page in (1, 2, 3))
        self.next_btn.set_label("Finish" if self.page == 5 else ("Install" if self.page == 3 else "Next >"))
        ok = True
        if self.page == 1:
            f = self.setup_file_name()
            ok = bool(f) and os.path.isfile(f)
        elif self.page == 2:
            ok = not self.use_new_env or bool(re.match(r"^[\w .-]+$", self.new_env_name))
        elif self.page == 4:
            ok = False
        self.next_btn.set_sensitive(ok)
        self.cancel_btn.set_sensitive(self.page != 4)

    def on_next(self):
        if self.page == 5:
            self.destroy()
            if self.center:
                self.center.refresh()
            return
        self.go(self.page + 1)

    def on_file_changed(self, entry):
        self.setup_path = entry.get_text()
        self.update_buttons()

    def setup_file_name(self):
        return os.path.expanduser(self.setup_path.strip())

    def suggest_name(self):
        base = os.path.splitext(os.path.basename(self.setup_file_name()))[0]
        base = re.sub(r"(?i)[-_ ]*(setup|install(er)?|x64|x86|win(32|64)?)[-_ ]*", " ", base)
        base = re.sub(r"[^\w .-]", "", base).strip() or "Program"
        return base[:32]

    def browse(self, *_):
        dlg = Gtk.FileChooserDialog(title="Browse", transient_for=self, action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.ACCEPT)
        f = Gtk.FileFilter()
        f.set_name("Setup programs (*.exe, *.msi)")
        for pat in ("*.exe", "*.EXE", "*.msi", "*.MSI", "*.bat"):
            f.add_pattern(pat)
        dlg.add_filter(f)
        a = Gtk.FileFilter()
        a.set_name("All files")
        a.add_pattern("*")
        dlg.add_filter(a)
        dl = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        if dl and os.path.isdir(dl):
            dlg.set_current_folder(dl)
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            self.file_entry.set_text(dlg.get_filename())
        dlg.destroy()

    # installation -------------------------------------------------------
    def start_install(self):
        if self.use_new_env:
            name = self.new_env_name
            self.env = Env(name, os.path.join(PREFIX_ROOT, name))
            winver = self.winver
        else:
            self.env = next((e for e in environments() if e.path == self.env_path), environments()[0])
            winver = None
        self.before = {p.file for p in programs(self.env)}
        env = self.env.environ()
        setup = self.setup_file_name()
        steps = []

        def say(text):
            self.status.set_text(text)
        if not self.env.ready() or winver:
            init = ["whistler-wine-init", "--prefix", self.env.path]
            if winver:
                init += ["--winver", winver]
            steps.append(("Preparing the Windows environment \"%s\"... (this can take a few minutes)"
                          % self.env.name, init, env, say))
        verbs = [v for v, _t, _d, _o in COMPONENTS if v in self.verbs]
        if verbs:
            steps.append(("Installing components: %s..." % ", ".join(verbs),
                          ["winetricks", "-q", "--unattended"] + verbs, env, say))
        steps.append(("Running %s. Follow the instructions in the setup program's window."
                      % os.path.basename(setup), launch_argv(setup), env, say))
        steps.append(("Finishing...", ["wineserver", "-w"], env, say))
        steps.append(("Adding the program to the Start menu...",
                      ["whistler-wine-menus", "--prefix", self.env.path], env, say))

        def done(code):
            GLib.source_remove(self.pulse)
            self.result = code
            trust_desktop_shortcuts()
            self.go(5)
        run_steps(steps, self.log, done)
        return False


# ---------------------------------------------------------------------------
class ComponentsDialog(Gtk.Dialog):
    def __init__(self, parent, env):
        super().__init__(title="Install Components - %s" % env.label, transient_for=parent, modal=True)
        self.env = env
        self.set_default_size(460, 460)
        self.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Install", Gtk.ResponseType.OK)
        area = self.get_content_area()
        area.pack_start(WizardHeader("Windows Components",
                                     "Select components to add to this Windows environment.",
                                     "system-software-install"), False, False, 0)
        sc = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_border_width(10)
        self.checks = []
        for verb, title, desc, _on in COMPONENTS:
            cb = Gtk.CheckButton()
            lb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            t = Gtk.Label(label=title, xalign=0)
            css_class(t, "bold")
            d = Gtk.Label(label=desc, xalign=0)
            d.get_style_context().add_class("dim-label")
            lb.pack_start(t, False, False, 0)
            lb.pack_start(d, False, False, 0)
            cb.add(lb)
            cb.verb = verb
            self.checks.append(cb)
            box.pack_start(cb, False, False, 0)
        sc.add(box)
        area.pack_start(sc, True, True, 0)
        more = Gtk.Button(label="More components (winetricks)...")
        more.set_halign(Gtk.Align.START)
        more.set_margin_start(10)
        more.connect("clicked", lambda *_: spawn_env(["winetricks", "--gui"], env))
        area.pack_start(more, False, False, 6)
        self.show_all()


def spawn_env(argv, env, cwd=None):
    full = dict(os.environ)
    full.update(env.environ())
    try:
        subprocess.Popen(argv, env=full, cwd=cwd, start_new_session=True, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


class EnvPropertiesDialog(Gtk.Dialog):
    def __init__(self, parent, env):
        super().__init__(title="%s Properties" % env.label, transient_for=parent, modal=True)
        self.env = env
        self.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)
        nb = Gtk.Notebook()
        nb.set_border_width(8)
        self.get_content_area().pack_start(nb, True, True, 0)

        g = Gtk.Grid(column_spacing=10, row_spacing=10)
        g.set_border_width(14)
        g.attach(image("drive-harddisk", 32), 0, 0, 1, 1)
        g.attach(Gtk.Label(label=env.label, xalign=0), 1, 0, 1, 1)
        g.attach(Gtk.Label(label="Location:", xalign=0), 0, 1, 1, 1)
        loc = Gtk.Label(label=env.path, xalign=0, selectable=True)
        g.attach(loc, 1, 1, 1, 1)
        g.attach(Gtk.Label(label="Pretend to be:", xalign=0), 0, 2, 1, 1)
        self.ver = Gtk.ComboBoxText()
        self.ver.append("", "(unchanged: %s)" % env.windows_version())
        for label, code in WINDOWS_VERSIONS:
            self.ver.append(code, label)
        self.ver.set_active(0)
        g.attach(self.ver, 1, 2, 1, 1)
        g.attach(Gtk.Label(label="Wine:", xalign=0), 0, 3, 1, 1)
        g.attach(Gtk.Label(label=wine_version(), xalign=0), 1, 3, 1, 1)
        nb.append_page(g, Gtk.Label(label="General"))

        d = Gtk.Grid(column_spacing=10, row_spacing=10)
        d.set_border_width(14)
        self.vdesk = Gtk.CheckButton(label="Run programs inside a virtual desktop window")
        d.attach(self.vdesk, 0, 0, 2, 1)
        d.attach(Gtk.Label(label="Desktop size:", xalign=0), 0, 1, 1, 1)
        self.vsize = Gtk.ComboBoxText.new_with_entry()
        for s in ("800x600", "1024x768", "1280x720", "1280x1024", "1920x1080"):
            self.vsize.append_text(s)
        self.vsize.get_child().set_text("1024x768")
        d.attach(self.vsize, 1, 1, 1, 1)
        d.attach(Gtk.Label(label="Screen resolution (DPI):", xalign=0), 0, 2, 1, 1)
        self.dpi = Gtk.SpinButton.new_with_range(72, 288, 1)
        self.dpi.set_value(96)
        d.attach(self.dpi, 1, 2, 1, 1)
        nb.append_page(d, Gtk.Label(label="Display"))

        a = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        a.set_border_width(14)
        for label, argv in (("Wine Configuration (winecfg)...", ["winecfg"]),
                            ("Registry Editor...", ["wine", "regedit"]),
                            ("Windows Task Manager...", ["wine", "taskmgr"]),
                            ("Command Prompt (cmd.exe)...", ["wineconsole", "cmd"]),
                            ("Control Panel...", ["wine", "control"])):
            b = Gtk.Button(label=label)
            b.set_halign(Gtk.Align.START)
            b.connect("clicked", lambda _w, x=argv: spawn_env(x, env))
            a.pack_start(b, False, False, 0)
        nb.append_page(a, Gtk.Label(label="Advanced"))
        self.show_all()

    def apply(self):
        env = self.env.environ()
        cmds = []
        code = self.ver.get_active_id()
        if code:
            cmds.append(["winecfg", "-v", code])
        if self.vdesk.get_active():
            cmds.append(["wine", "reg", "add", r"HKCU\Software\Wine\Explorer", "/v", "Desktop", "/d", "Default", "/f"])
            cmds.append(["wine", "reg", "add", r"HKCU\Software\Wine\Explorer\Desktops", "/v", "Default", "/d",
                         self.vsize.get_child().get_text(), "/f"])
        else:
            cmds.append(["wine", "reg", "delete", r"HKCU\Software\Wine\Explorer", "/v", "Desktop", "/f"])
        cmds.append(["wine", "reg", "add", r"HKCU\Control Panel\Desktop", "/v", "LogPixels", "/t", "REG_DWORD",
                     "/d", str(int(self.dpi.get_value())), "/f"])
        script = "; ".join(" ".join(shlex.quote(x) for x in c) for c in cmds)
        full = dict(os.environ)
        full.update(env)
        subprocess.Popen(["sh", "-c", script], env=full, start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------------------
class WineCenter(Gtk.Window):
    def __init__(self):
        super().__init__(title="Wine Center")
        self.set_icon_name("whistler-winecenter")
        self.set_default_size(880, 580)
        self.connect("destroy", Gtk.main_quit)
        self.envs = environments()
        self.env = self.envs[0]

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(outer)
        outer.pack_start(self.build_menubar(), False, False, 0)

        bar = Gtk.Box(spacing=6)
        css_class(bar, "xp-addressbar")
        bar.pack_start(Gtk.Label(label="Environment"), False, False, 4)
        self.env_combo = Gtk.ComboBoxText()
        self.env_combo.connect("changed", self.on_env_changed)
        bar.pack_start(self.env_combo, False, False, 0)
        outer.pack_start(bar, False, False, 0)

        body = Gtk.Box()
        outer.pack_start(body, True, True, 0)
        self.pane_holder = Gtk.Box()
        body.pack_start(self.pane_holder, False, False, 0)

        sc = Gtk.ScrolledWindow()
        css_class(sc, "xp-content")
        self.main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.main.set_border_width(14)
        sc.add(self.main)
        body.pack_start(sc, True, True, 0)

        sb = Gtk.Box()
        css_class(sb, "xp-statusbar")
        self.status = Gtk.Label(xalign=0)
        sb.pack_start(self.status, True, True, 0)
        outer.pack_start(sb, False, False, 0)

        self.fill_envs()
        self.show_all()
        watch = Gio.File.new_for_path(WINE_APPS)
        try:
            os.makedirs(WINE_APPS, exist_ok=True)
            self.monitor = watch.monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
            self.monitor.connect("changed", lambda *_: GLib.timeout_add(800, self.refresh_once))
        except GLib.Error:
            pass

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
        menu("_File", [("_Install a Windows Program...", self.install), ("_Run a Windows Program...", self.run_dialog),
                       (None, None), ("_Close", self.destroy)])
        menu("_Environment", [("_New Environment...", self.new_env), ("_Properties...", self.properties),
                              ("Install _Components...", self.components), (None, None),
                              ("Open Drive _C:", self.open_drive), ("_Restart Windows", self.restart),
                              ("_Stop All Windows Programs", self.kill), (None, None),
                              ("_Delete Environment...", self.delete_env)])
        menu("_Help", [("_About Wine Center", self.about)])
        return mb

    def fill_envs(self, select=None):
        self.envs = environments()
        self.env_combo.remove_all()
        for e in self.envs:
            self.env_combo.append(e.path, e.label)
        target = select or self.env
        idx = next((i for i, e in enumerate(self.envs) if e == target), 0)
        self.env_combo.set_active(idx)

    def on_env_changed(self, combo):
        path = combo.get_active_id()
        if path is None:
            return
        self.env = next((e for e in self.envs if e.path == path), self.envs[0])
        self.refresh()

    def build_pane(self):
        for c in self.pane_holder.get_children():
            c.destroy()
        pane = TaskPane(width=220)
        pane.add_group("Program Tasks", [
            ("system-software-install", "Install a Windows program", self.install),
            ("application-x-executable", "Run a Windows program", self.run_dialog),
            ("drive-harddisk", "Open Windows drive C:", self.open_drive),
            ("edit-delete", "Uninstall a program", lambda: self.wine(["wine", "uninstaller"])),
        ], special=True, icon="whistler-winecenter")
        pane.add_group("Environment Tasks", [
            ("list-add", "Create a new environment", self.new_env),
            ("preferences-system", "Change environment settings", self.properties),
            ("package-x-generic", "Add Microsoft components", self.components),
            ("view-refresh", "Restart Windows", self.restart),
            ("process-stop", "Stop all Windows programs", self.kill),
        ])
        pane.add_group("Other Places", [
            ("computer", "My Computer", lambda: spawn(["whistler-mycomputer"])),
            ("preferences-system", "Control Panel", lambda: spawn(["whistler-control"])),
            ("help-browser", "Help with Windows programs", lambda: spawn(["whistler-help", "wine"])),
        ])
        pane.add_group("Details", [(None, "<b>%s</b>\n%s\n%s" % (
            GLib.markup_escape_text(self.env.label),
            GLib.markup_escape_text(self.env.windows_version()),
            GLib.markup_escape_text(wine_version())), None)])
        self.pane_holder.pack_start(pane, True, True, 0)
        self.pane_holder.show_all()

    def refresh_once(self):
        self.refresh()
        return False

    def refresh(self):
        self.build_pane()
        for c in self.main.get_children():
            c.destroy()
        progs = programs(self.env)
        t = Gtk.Label(label="Windows Programs", xalign=0)
        css_class(t, "xp-section-title")
        self.main.pack_start(t, False, False, 0)
        rule = Gtk.Box()
        css_class(rule, "xp-section-rule")
        self.main.pack_start(rule, False, False, 0)
        if not progs:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            box.set_margin_top(30)
            box.pack_start(image("whistler-winecenter", 96), False, False, 0)
            msg = Gtk.Label()
            msg.set_markup("<b>No Windows programs are installed here yet.</b>\n\n"
                           "Click <b>Install a Windows program</b> to run a setup program, or simply\n"
                           "double-click any .exe or .msi file in Windows Explorer.")
            msg.set_justify(Gtk.Justification.CENTER)
            box.pack_start(msg, False, False, 0)
            b = Gtk.Button(label="Install a Windows program...")
            b.set_halign(Gtk.Align.CENTER)
            b.connect("clicked", lambda *_: self.install())
            box.pack_start(b, False, False, 0)
            self.main.pack_start(box, False, False, 0)
        else:
            flow = Gtk.FlowBox()
            flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
            flow.set_max_children_per_line(12)
            flow.set_row_spacing(10)
            flow.set_column_spacing(6)
            for p in progs:
                cell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                cell.set_size_request(96, 84)
                cell.pack_start(Gtk.Image.new_from_pixbuf(gicon_pixbuf(p.gicon, 48)), False, False, 0)
                l = Gtk.Label(label=p.name)
                l.set_line_wrap(True)
                l.set_justify(Gtk.Justification.CENTER)
                l.set_max_width_chars(14)
                l.set_lines(2)
                l.set_ellipsize(Pango.EllipsizeMode.END)
                cell.pack_start(l, False, False, 0)
                ev = Gtk.EventBox()
                ev.add(cell)
                ev.program = p
                ev.connect("button-press-event", self.on_program_click)
                flow.add(ev)
            flow.connect("child-activated", lambda fb, ch: self.launch(ch.get_child().program))
            self.main.pack_start(flow, False, False, 0)
        self.main.show_all()
        self.status.set_text("%d program(s)    %s    %s" % (len(progs), self.env.path, wine_version()))

    def on_program_click(self, w, ev):
        if ev.type == Gdk.EventType._2BUTTON_PRESS and ev.button == 1:
            self.launch(w.program)
            return True
        if ev.button == 3:
            m = Gtk.Menu()
            for label, cb in (("_Open", lambda: self.launch(w.program)),
                              ("Open File _Location", lambda: self.open_location(w.program)),
                              ("Send to _Desktop (create shortcut)", lambda: self.to_desktop(w.program)),
                              ("_Remove from Start menu", lambda: self.remove_entry(w.program))):
                mi = Gtk.MenuItem.new_with_mnemonic(label)
                mi.connect("activate", lambda *_a, f=cb: f())
                m.append(mi)
            m.show_all()
            m.popup_at_pointer(ev)
            return True
        return False

    # actions -----------------------------------------------------------
    def launch(self, prog):
        prog.info.launch([], None)

    def open_location(self, prog):
        path = None
        cmd = prog.info.get_commandline() or ""
        m = re.search(r'Path=(.*)', open(prog.file, encoding="utf-8", errors="replace").read())
        if m:
            path = m.group(1).strip()
        open_uri(path if path and os.path.isdir(path) else self.env.drive_c)

    def to_desktop(self, prog):
        desk = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP) or os.path.expanduser("~/Desktop")
        dest = os.path.join(desk, os.path.basename(prog.file))
        shutil.copy(prog.file, dest)
        os.chmod(dest, 0o755)
        trust_desktop_shortcuts()

    def remove_entry(self, prog):
        try:
            os.unlink(prog.file)
        except OSError:
            pass
        self.refresh()

    def wine(self, argv):
        ensure_env(self, self.env, lambda: spawn_env(argv, self.env))

    def install(self, setup_file=None):
        InstallWizard(self, setup_file)

    def run_dialog(self):
        dlg = Gtk.FileChooserDialog(title="Run a Windows Program", transient_for=self,
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Run", Gtk.ResponseType.ACCEPT)
        f = Gtk.FileFilter()
        f.set_name("Windows programs")
        for pat in ("*.exe", "*.EXE", "*.msi", "*.MSI", "*.bat", "*.lnk"):
            f.add_pattern(pat)
        dlg.add_filter(f)
        if os.path.isdir(self.env.drive_c):
            dlg.set_current_folder(self.env.drive_c)
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            path = dlg.get_filename()
            ensure_env(self, self.env, lambda: run_windows_program(path, self.env))
        dlg.destroy()

    def open_drive(self):
        ensure_env(self, self.env, lambda: open_uri(self.env.drive_c))

    def restart(self):
        spawn_env(["wineboot", "-r"], self.env)

    def kill(self):
        spawn_env(["wineserver", "-k"], self.env)

    def properties(self):
        def show():
            d = EnvPropertiesDialog(self, self.env)
            if d.run() == Gtk.ResponseType.OK:
                d.apply()
            d.destroy()
            GLib.timeout_add(1500, self.refresh_once)
        ensure_env(self, self.env, show)

    def components(self):
        def show():
            d = ComponentsDialog(self, self.env)
            r = d.run()
            verbs = [c.verb for c in d.checks if c.get_active()]
            d.destroy()
            if r != Gtk.ResponseType.OK or not verbs:
                return
            win = ProgressWindow(self, "Installing Components",
                                 "Installing %s. Some components show their own setup windows; "
                                 "downloads may take a while." % ", ".join(verbs))
            run_steps([("", ["winetricks", "-q", "--unattended"] + verbs, self.env.environ(), None)],
                      win.log, lambda code: (win.destroy(), code and xp_message(
                          self, "Some components could not be installed.",
                          "Open Details in the progress window next time to see why.",
                          kind=Gtk.MessageType.WARNING)))
        ensure_env(self, self.env, show)

    def new_env(self):
        dlg = Gtk.Dialog(title="New Windows Environment", transient_for=self, modal=True)
        dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Create", Gtk.ResponseType.OK)
        g = Gtk.Grid(column_spacing=8, row_spacing=8)
        g.set_border_width(14)
        g.attach(Gtk.Label(label="Name:", xalign=0), 0, 0, 1, 1)
        name = Gtk.Entry()
        name.set_activates_default(True)
        g.attach(name, 1, 0, 1, 1)
        g.attach(Gtk.Label(label="Pretend to be:", xalign=0), 0, 1, 1, 1)
        ver = Gtk.ComboBoxText()
        for label, code in WINDOWS_VERSIONS:
            ver.append(code, label)
        ver.set_active(0)
        g.attach(ver, 1, 1, 1, 1)
        dlg.get_content_area().pack_start(g, True, True, 0)
        dlg.set_default_response(Gtk.ResponseType.OK)
        dlg.show_all()
        r = dlg.run()
        n, code = name.get_text().strip(), ver.get_active_id()
        dlg.destroy()
        if r != Gtk.ResponseType.OK or not n:
            return
        if not re.match(r"^[\w .-]+$", n):
            xp_message(self, "Environment names can only contain letters, numbers, spaces, dots and dashes.",
                       kind=Gtk.MessageType.ERROR)
            return
        env = Env(n, os.path.join(PREFIX_ROOT, n))
        os.makedirs(PREFIX_ROOT, exist_ok=True)
        ensure_env(self, env, lambda: self.fill_envs(select=env), winver=code)

    def delete_env(self):
        if self.env.default:
            xp_message(self, "The shared environment cannot be deleted.",
                       "You can delete separate environments you created.", kind=Gtk.MessageType.INFO)
            return
        r = xp_message(self, "Are you sure you want to delete \"%s\"?" % self.env.name,
                       "All Windows programs and files inside it will be permanently deleted.",
                       kind=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.YES_NO, title="Confirm Delete")
        if r != Gtk.ResponseType.YES:
            return
        subprocess.run(["wineserver", "-k"], env=dict(os.environ, **self.env.environ()),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for p in programs(self.env):
            try:
                os.unlink(p.file)
            except OSError:
                pass
        shutil.rmtree(self.env.path, ignore_errors=True)
        self.env = environments()[0]
        self.fill_envs()

    def about(self):
        dlg = Gtk.AboutDialog(transient_for=self, modal=True)
        dlg.set_program_name("Wine Center")
        dlg.set_logo_icon_name("whistler-winecenter")
        dlg.set_comments("Install, run and manage Windows programs on Whistler XP.\n" + wine_version())
        dlg.set_license_type(Gtk.License.GPL_3_0)
        dlg.run()
        dlg.destroy()


def main():
    load_css("whistler.css")
    args = sys.argv[1:]
    if args and args[0] == "--run" and len(args) > 1:
        path = os.path.abspath(args[1])
        env = env_for_file(path)
        if env.ready():
            run_windows_program(path, env)
            return 0
        Gtk.init(None)
        ensure_env(None, env, lambda: (run_windows_program(path, env), Gtk.main_quit()))
        Gtk.main()
        return 0
    if args and args[0] == "--open-drive":
        env = environments()[0]
        if env.ready():
            open_uri(env.drive_c)
            return 0
        ensure_env(None, env, lambda: (open_uri(env.drive_c), Gtk.main_quit()))
        Gtk.main()
        return 0
    if args and args[0] == "--install":
        w = InstallWizard(None, args[1] if len(args) > 1 else None)
        w.connect("destroy", Gtk.main_quit)
        Gtk.main()
        return 0
    center = WineCenter()
    if args and os.path.isfile(args[0]):
        f = os.path.abspath(args[0])
        if re.search(r"(?i)(setup|install).*\.(exe|msi)$", os.path.basename(f)) or f.lower().endswith(".msi"):
            center.install(f)
        else:
            run_windows_program(f)
    Gtk.main()
    return 0
