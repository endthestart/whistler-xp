"""Shared helpers for the Whistler desktop applications."""
import os
import shlex
import subprocess

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk  # noqa: E402

SHARE = os.environ.get("WHISTLER_SHARE", "/usr/share/whistler")
DATA_HOME = os.path.join(GLib.get_user_data_dir(), "whistler")
CONFIG_HOME = os.path.join(GLib.get_user_config_dir(), "whistler")

_css_loaded = set()


ASSETS = "/usr/share/whistler/assets/current"


def load_css(name_or_path):
    """Load a stylesheet from SHARE (or an absolute path) once per process,
    plus its override from the swappable asset tree (imported XP originals)."""
    path = name_or_path if os.path.isabs(name_or_path) else os.path.join(SHARE, "css", name_or_path)
    extra = None if os.path.isabs(name_or_path) else os.path.join(ASSETS, "css", name_or_path)
    for prio, p in ((1, path), (2, extra)):
        if not p or p in _css_loaded or not os.path.exists(p):
            continue
        provider = Gtk.CssProvider()
        try:
            provider.load_from_path(p)
        except GLib.Error:
            continue
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + prio)
        _css_loaded.add(p)


def css_class(widget, *classes):
    ctx = widget.get_style_context()
    for c in classes:
        ctx.add_class(c)
    return widget


def icon_pixbuf(name, size):
    """Look up an icon (theme name or file path) as a pixbuf of `size` px."""
    theme = Gtk.IconTheme.get_default()
    try:
        if name and os.path.isabs(name) and os.path.exists(name):
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(name, size, size, True)
        for n in (name, "application-x-executable", "image-missing"):
            if n and theme.has_icon(n):
                return theme.load_icon(n, size, Gtk.IconLookupFlags.FORCE_SIZE)
    except GLib.Error:
        pass
    return None


def image(name, size):
    pb = icon_pixbuf(name, size)
    img = Gtk.Image.new_from_pixbuf(pb) if pb else Gtk.Image()
    img.set_size_request(size, size)
    return img


def gicon_pixbuf(gicon, size):
    if gicon is None:
        return icon_pixbuf("application-x-executable", size)
    theme = Gtk.IconTheme.get_default()
    try:
        info = theme.lookup_by_gicon(gicon, size, Gtk.IconLookupFlags.FORCE_SIZE)
        if info:
            return info.load_icon()
    except GLib.Error:
        pass
    return icon_pixbuf("application-x-executable", size)


def spawn(cmd):
    """Run a command (string or argv list) detached from us."""
    argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    try:
        subprocess.Popen(argv, start_new_session=True, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


def open_uri(target):
    """Open a path or URI with the user's default handler."""
    if target.startswith("~"):
        target = os.path.expanduser(target)
    if "://" not in target and not target.startswith("/"):
        target = os.path.abspath(target)
    return spawn(["exo-open", target]) or spawn(["xdg-open", target])


def launch_app(app_id_or_info):
    info = app_id_or_info
    if isinstance(info, str):
        info = Gio.DesktopAppInfo.new(info)
    if info is None:
        return False
    try:
        ctx = Gdk.Display.get_default().get_app_launch_context()
        return info.launch([], ctx)
    except GLib.Error:
        return False


def user_dir(kind, fallback):
    d = GLib.get_user_special_dir(kind)
    return d or os.path.expanduser(fallback)


def display_name():
    import pwd
    pw = pwd.getpwuid(os.getuid())
    full = pw.pw_gecos.split(",")[0].strip()
    return full or pw.pw_name


def user_picture():
    for p in (os.path.expanduser("~/.face"),
              "/var/lib/AccountsService/icons/" + os.environ.get("USER", ""),
              os.path.join(ASSETS, "userpics", "duck.png")):
        if os.path.isfile(p):
            return p
    return None


def notify(title, body, icon="dialog-information", timeout=8000):
    spawn(["notify-send", "-i", icon, "-t", str(timeout), title, body])


def screen_size():
    display = Gdk.Display.get_default()
    mon = display.get_primary_monitor() or display.get_monitor(0)
    return mon.get_geometry(), mon.get_workarea()


class TaskPane(Gtk.ScrolledWindow):
    """The blue XP Explorer task pane with collapsible groups of links."""

    def __init__(self, width=210):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_size_request(width, -1)
        css_class(self, "xp-taskpane")
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        css_class(self.box, "xp-taskpane-box")
        self.add(self.box)

    def add_group(self, title, links, special=False, icon=None):
        """links: list of (icon, label, callback); a None callback makes plain text."""
        group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        css_class(group, "xp-taskgroup")
        if special:
            css_class(group, "special")
        header = Gtk.Button()
        header.set_relief(Gtk.ReliefStyle.NONE)
        css_class(header, "xp-taskgroup-header")
        hb = Gtk.Box(spacing=6)
        if icon:
            hb.pack_start(image(icon, 24), False, False, 0)
        lbl = Gtk.Label(label=title, xalign=0)
        css_class(lbl, "xp-taskgroup-title")
        hb.pack_start(lbl, True, True, 0)
        chevron = Gtk.Label(label="˄")
        css_class(chevron, "xp-chevron")
        hb.pack_end(chevron, False, False, 0)
        header.add(hb)
        group.pack_start(header, False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        css_class(body, "xp-taskgroup-body")
        for icon_name, text, cb in links:
            if cb is None:
                lab = Gtk.Label(label=text, xalign=0)
                lab.set_line_wrap(True)
                lab.set_use_markup(True)
                css_class(lab, "xp-taskgroup-text")
                body.pack_start(lab, False, False, 0)
                continue
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            css_class(btn, "xp-tasklink")
            b = Gtk.Box(spacing=6)
            if icon_name:
                b.pack_start(image(icon_name, 16), False, False, 0)
            t = Gtk.Label(label=text, xalign=0)
            t.set_line_wrap(True)
            b.pack_start(t, True, True, 0)
            btn.add(b)
            btn.connect("clicked", lambda _w, f=cb: f())
            body.pack_start(btn, False, False, 0)
        revealer = Gtk.Revealer()
        revealer.set_reveal_child(True)
        revealer.add(body)
        group.pack_start(revealer, False, False, 0)

        def toggle(_b):
            shown = not revealer.get_reveal_child()
            revealer.set_reveal_child(shown)
            chevron.set_text("˄" if shown else "˅")
        header.connect("clicked", toggle)
        self.box.pack_start(group, False, False, 0)
        return group


class WizardHeader(Gtk.Box):
    """White wizard banner: bold title, indented subtitle, icon on the right."""

    def __init__(self, title, subtitle, icon=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        css_class(self, "xp-wizard-header")
        row = Gtk.Box(spacing=8)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.title = Gtk.Label(label=title, xalign=0)
        css_class(self.title, "xp-wizard-title")
        self.subtitle = Gtk.Label(label=subtitle, xalign=0)
        self.subtitle.set_line_wrap(True)
        self.subtitle.set_max_width_chars(64)
        css_class(self.subtitle, "xp-wizard-subtitle")
        texts.pack_start(self.title, False, False, 0)
        texts.pack_start(self.subtitle, False, False, 0)
        row.pack_start(texts, True, True, 0)
        self.icon = image(icon, 48) if icon else Gtk.Image()
        row.pack_end(self.icon, False, False, 0)
        self.pack_start(row, True, True, 0)
        sep = Gtk.Separator()
        self.pack_end(sep, False, False, 0)

    def set(self, title, subtitle, icon=None):
        self.title.set_text(title)
        self.subtitle.set_text(subtitle)
        if icon:
            pb = icon_pixbuf(icon, 48)
            if pb:
                self.icon.set_from_pixbuf(pb)


def xp_message(parent, text, secondary=None, kind=Gtk.MessageType.INFO,
               buttons=Gtk.ButtonsType.OK, title=None):
    dlg = Gtk.MessageDialog(transient_for=parent, modal=True, message_type=kind,
                            buttons=buttons, text=text)
    if secondary:
        dlg.format_secondary_text(secondary)
    if title:
        dlg.set_title(title)
    r = dlg.run()
    dlg.destroy()
    return r


def run_async(argv, on_done=None, env=None, cwd=None):
    """Run argv in the background; call on_done(returncode, output) on the main loop."""
    launcher = Gio.SubprocessLauncher.new(
        Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE)
    for k, v in (env or {}).items():
        launcher.setenv(k, v, True)
    if cwd:
        launcher.set_cwd(cwd)
    proc = launcher.spawnv([str(a) for a in argv])

    def done(p, res):
        out = ""
        try:
            _ok, out, _err = p.communicate_utf8_finish(res)
        except GLib.Error as e:
            out = str(e)
        if on_done:
            code = p.get_exit_status() if p.get_if_exited() else 1
            on_done(code, out or "")
    proc.communicate_utf8_async(None, None, done)
    return proc
