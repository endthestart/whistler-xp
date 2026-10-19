"""Application catalogue: groups desktop entries into an XP-style program tree."""
import json
import os
import time

from gi.repository import Gio, GLib

from .common import DATA_HOME

MFU_FILE = os.path.join(DATA_HOME, "mfu.json")

# Seed for "frequently used programs" on a fresh profile (XP shows six).
DEFAULT_MFU = [
    "whistler-winecenter.desktop",
    "org.xfce.mousepad.desktop",
    "whistler-cmd.desktop",
    "mtpaint.desktop",
    "galculator.desktop",
    "org.xfce.Parole.desktop",
]

PINNED = [
    ("firefox.desktop", "Internet", "Mozilla Firefox"),
    ("whistler-winecenter.desktop", "Windows Programs", "Wine Center"),
]

CATEGORY_FOLDERS = [
    (("Game",), "Games"),
    (("Accessibility",), "Accessories/Accessibility"),
    (("Wine",), "Wine"),
    (("Settings", "DesktopSettings", "HardwareSettings", "PackageManager"), None),
    (("System", "Monitor", "FileTools", "Filesystem"), "Accessories/System Tools"),
    (("Development", "IDE"), "Programming"),
    (("Office", "WordProcessor", "Spreadsheet"), "Office"),
    (("Graphics",), "Graphics"),
    (("AudioVideo", "Audio", "Video", "Player"), "Accessories/Entertainment"),
    (("Network", "WebBrowser", "Email", "Chat"), "Internet"),
    (("Utility", "TextEditor", "Calculator", "Archiving", "Core"), "Accessories"),
]


def _wine_folder(filename):
    marker = "/applications/wine/Programs/"
    if filename and marker in filename:
        rel = filename.split(marker, 1)[1]
        parts = rel.split("/")[:-1]
        return "/".join(parts)
    return None


def folder_for(info):
    """Return the folder path ("" is top level) or None to hide the entry."""
    custom = info.get_string("X-Whistler-Folder")
    if custom is not None:
        return None if custom == "-" else custom
    wf = _wine_folder(info.get_filename())
    if wf is not None:
        return wf
    cats = [c for c in (info.get_categories() or "").split(";") if c]
    for keys, folder in CATEGORY_FOLDERS:
        if any(k in cats for k in keys):
            return folder
    return "Accessories"


class Entry:
    __slots__ = ("info", "id", "name", "gicon", "folder", "comment")

    def __init__(self, info, folder):
        self.info = info
        self.id = info.get_id()
        self.name = info.get_display_name() or info.get_name()
        self.gicon = info.get_icon()
        self.comment = info.get_description() or ""
        self.folder = folder


def all_entries():
    entries = []
    for info in Gio.AppInfo.get_all():
        if not isinstance(info, Gio.DesktopAppInfo) or not info.should_show():
            continue
        folder = folder_for(info)
        if folder is None:
            continue
        entries.append(Entry(info, folder))
    return entries


def tree(entries):
    """Nested dict {"folders": {name: subtree}, "items": [Entry]}."""
    root = {"folders": {}, "items": []}
    for e in entries:
        node = root
        if e.folder:
            for part in e.folder.split("/"):
                node = node["folders"].setdefault(part, {"folders": {}, "items": []})
        node["items"].append(e)
    return root


def lookup(app_id):
    try:
        info = Gio.DesktopAppInfo.new(app_id)
    except TypeError:
        info = None
    return info


class MFU:
    def __init__(self):
        self.data = {}
        try:
            with open(MFU_FILE) as f:
                self.data = json.load(f)
        except (OSError, ValueError):
            now = time.time()
            self.data = {a: {"count": len(DEFAULT_MFU) - i, "last": now}
                         for i, a in enumerate(DEFAULT_MFU)}

    def record(self, app_id):
        d = self.data.setdefault(app_id, {"count": 0, "last": 0})
        d["count"] += 1
        d["last"] = time.time()
        os.makedirs(DATA_HOME, exist_ok=True)
        tmp = MFU_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.data, f)
        os.replace(tmp, MFU_FILE)

    def top(self, n, exclude=()):
        ranked = sorted(self.data.items(),
                        key=lambda kv: (kv[1]["count"], kv[1]["last"]), reverse=True)
        out = []
        for app_id, _ in ranked:
            if app_id in exclude:
                continue
            info = lookup(app_id)
            if info is None or not info.should_show():
                continue
            out.append(info)
            if len(out) >= n:
                break
        return out


def recent_documents(limit=15):
    from gi.repository import Gtk
    items = Gtk.RecentManager.get_default().get_items()
    items = [i for i in items if i.exists() and i.is_local()]
    items.sort(key=lambda i: i.get_modified(), reverse=True)
    return items[:limit]


def autostart_entries():
    d = os.path.join(GLib.get_user_config_dir(), "autostart")
    out = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".desktop"):
                try:
                    info = Gio.DesktopAppInfo.new_from_filename(os.path.join(d, f))
                except TypeError:
                    info = None
                if info and not info.get_is_hidden() and not info.get_nodisplay():
                    out.append(info)
    return out
