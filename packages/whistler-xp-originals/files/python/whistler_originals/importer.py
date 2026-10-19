"""Import artwork, fonts and sounds from the user's own Windows XP media.

Sources: an XP installation CD/ISO (I386 folder with compressed *.??_ files)
or an installed Windows XP folder (C:\\WINDOWS from a disk or backup).
Nothing is downloaded; everything comes from the media the user points at.
Output goes to /var/lib/whistler/originals (see whistler-assets).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

from . import theme
from .pe import PE

ROOT = os.environ.get("WHISTLER_ORIGINALS_ROOT", "/var/lib/whistler/originals")

# ----------------------------------------------------------------- catalogue
# (installed long name, CD short compressed name)
MSSTYLES = [("Luna.msstyles", "LUNA.MS_")]
BLISS = [("Bliss.bmp", None), ("bliss.jpg", "BLISS.JP_")]
SOUNDS = {
    "system-bootup": ("Windows XP Startup.wav", "XPSTARTU.WA_"),
    "desktop-login": ("Windows XP Logon Sound.wav", "XPLOGON.WA_"),
    "desktop-logout": ("Windows XP Logoff Sound.wav", "XPLOGOFF.WA_"),
    "system-shutdown": ("Windows XP Shutdown.wav", "XPSHUTDN.WA_"),
    "dialog-information": ("Windows XP Ding.wav", "XPDING.WA_"),
    "dialog-warning": ("Windows XP Exclamation.wav", "XPEXCL.WA_"),
    "dialog-error": ("Windows XP Error.wav", "XPERROR.WA_"),
    "dialog-question": ("Windows XP Balloon.wav", "XPBALLN.WA_"),
    "bell": ("Windows XP Default.wav", "XPDEF.WA_"),
    "message-new-instant": ("Windows XP Notify.wav", "XPNOTIFY.WA_"),
    "device-added": ("Windows XP Hardware Insertion.wav", "XPHDINST.WA_"),
    "device-removed": ("Windows XP Hardware Removal.wav", "XPHDREM.WA_"),
    "trash-empty": ("Windows XP Recycle.wav", "XPRECYCL.WA_"),
    "battery-low": ("Windows XP Battery Low.wav", "XPBATLOW.WA_"),
}
FONTS = ["tahoma", "tahomabd", "trebuc", "trebucbd", "trebucit", "trebucbi", "framd", "framdit", "lucon",
         "verdana", "verdanab", "verdanai", "verdanaz", "arial", "arialbd", "ariali", "arialbi", "ariblk",
         "times", "timesbd", "timesi", "timesbi", "cour", "courbd", "couri", "courbi", "comic", "comicbd",
         "georgia", "georgiab", "georgiai", "georgiaz", "impact", "webdings", "wingding", "symbol",
         "micross", "pala", "palab", "palai", "palabi", "sylfaen", "l_10646", "estre", "mvboli"]
USER_PICTURES = ["airplane", "astro", "ball", "beach", "butterfl", "car", "cat", "chess", "dirtbike", "dog",
                 "drip", "duck", "fish", "frog", "guitar", "horses", "kick", "liftoff", "palmtree", "pnkflowr",
                 "redflowr", "skater", "snwflake", "soccer"]
BMP_WALLPAPERS = ["zapotec", "santafe", "rvrsumid", "rhody", "prairie", "gonefish", "feather", "coffeebn",
                  "bubbles", "blulac16", "grnstone", "soapbubl"]
PE_FILES = {"shell32": ("shell32.dll", "SHELL32.DL_"), "explorer": ("explorer.exe", "EXPLORER.EX_"),
            "mydocs": ("mydocs.dll", "MYDOCS.DL_"), "logonui": ("logonui.exe", "LOGONUI.EX_"),
            "user32": ("user32.dll", "USER32.DL_"), "msgina": ("msgina.dll", "MSGINA.DL_")}

# freedesktop icon name -> (file key, icon group id)
ICONS = {
    "places": {
        "folder": ("shell32", 4), "folder-open": ("shell32", 5), "user-home": ("mydocs", 100),
        "folder-documents": ("mydocs", 100), "folder-pictures": ("shell32", 236), "folder-music": ("shell32", 237),
        "folder-videos": ("shell32", 238), "folder-download": ("shell32", 146),
        "folder-publicshare": ("shell32", 267), "folder-remote": ("shell32", 172), "folder-templates": ("shell32", 37),
        "user-desktop": ("shell32", 35), "network-workgroup": ("shell32", 18), "network-server": ("shell32", 15),
        "user-trash": ("shell32", 32), "user-trash-full": ("shell32", 33), "inode-directory": ("shell32", 4),
    },
    "devices": {
        "computer": ("shell32", 16), "drive-harddisk": ("shell32", 8), "drive-harddisk-system": ("shell32", 8),
        "drive-optical": ("shell32", 12), "drive-removable-media": ("shell32", 300),
        "drive-removable-media-usb": ("shell32", 300), "media-floppy": ("shell32", 7),
        "media-optical": ("shell32", 302), "printer": ("shell32", 17), "input-mouse": ("shell32", 229),
        "camera-photo": ("shell32", 248), "phone": ("shell32", 310), "audio-speakers": ("shell32", 277),
    },
    "apps": {
        "preferences-system": ("explorer", 103), "system-search": ("shell32", 23), "system-run": ("shell32", 25),
        "help-browser": ("shell32", 24), "system-users": ("shell32", 269),
        "preferences-desktop-theme": ("shell32", 270), "preferences-desktop-display": ("shell32", 250),
        "preferences-desktop-wallpaper": ("shell32", 250), "preferences-system-time": ("shell32", 276),
        "preferences-desktop-accessibility": ("shell32", 268), "system-software-install": ("shell32", 271),
        "multimedia-volume-control": ("shell32", 277), "preferences-desktop-default-applications": ("explorer", 107),
        "internet-web-browser": ("explorer", 253), "mail-client": ("explorer", 254),
        "utilities-system-monitor": ("shell32", 275), "system-file-manager": ("shell32", 46),
        "whistler-help": ("shell32", 24),
    },
    "mimetypes": {
        "text-x-generic": ("shell32", 152), "application-x-executable": ("shell32", 3),
        "application-x-ms-dos-executable": ("shell32", 3), "application-x-msi": ("shell32", 154),
        "audio-x-generic": ("shell32", 225), "video-x-generic": ("shell32", 224),
        "application-octet-stream": ("shell32", 1), "unknown": ("shell32", 1),
    },
    "actions": {
        "edit-delete": ("shell32", 240), "edit-find": ("shell32", 23), "go-home": ("shell32", 259),
        "folder-new": ("shell32", 258), "system-log-out": ("shell32", 45), "system-shutdown": ("shell32", 28),
        "process-stop": ("shell32", 200), "document-print": ("shell32", 17), "document-open-recent": ("shell32", 21),
    },
    "status": {
        "dialog-information": ("explorer", 109), "dialog-warning": ("explorer", 110),
        "dialog-error": ("explorer", 111), "dialog-question": ("shell32", 263),
    },
}
SIZES = (16, 22, 24, 32, 48)
CURSORS = {  # user32.dll cursor group -> Xcursor name (+ aliases created below)
    100: "default", 101: "text", 102: "wait", 103: "crosshair", 105: "nwse-resize", 106: "nesw-resize",
    107: "ew-resize", 108: "ns-resize", 109: "move", 110: "not-allowed", 111: "progress", 112: "help",
    113: "pencil", 114: "pointer",
}
CURSOR_ALIASES = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "left-arrow", "context-menu", "copy", "alias", "dnd-none"],
    "text": ["xterm", "ibeam", "vertical-text"], "wait": ["watch"],
    "progress": ["left_ptr_watch", "half-busy", "08e8e1c95fe2fc01f976f1e063a24ccd",
                 "3ecb610c1bf2410f44200f48c40d3599"],
    "crosshair": ["cross", "tcross", "cell", "plus"], "pencil": ["draft"], "pointer": ["hand1", "hand2", "hand", "pointing_hand",
                                                                  "9d800788f1b08800ae810202380a0822",
                                                                  "e29285e634086352946a0e7090d73106", "grab",
                                                                  "openhand", "grabbing", "closedhand"],
    "move": ["fleur", "all-scroll", "size_all", "dnd-move"],
    "ew-resize": ["sb_h_double_arrow", "h_double_arrow", "size_hor", "e-resize", "w-resize", "left_side",
                  "right_side", "col-resize", "028006030e0e7ebffc7f7070c0600140", "14fef782d02440884392942c11205230"],
    "ns-resize": ["sb_v_double_arrow", "v_double_arrow", "size_ver", "n-resize", "s-resize", "top_side",
                  "bottom_side", "row-resize", "00008160000006810000408080010102", "2870a09082c103050810ffdffffe0204"],
    "nwse-resize": ["nw-resize", "se-resize", "top_left_corner", "bottom_right_corner", "size_fdiag",
                    "fd_double_arrow", "c7088f0f3e6c8088236ef8e1e3e70000"],
    "nesw-resize": ["ne-resize", "sw-resize", "top_right_corner", "bottom_left_corner", "size_bdiag",
                    "bd_double_arrow", "fcf1c3c7cd4491d801f1e1c78f100000"],
    "not-allowed": ["no-drop", "forbidden", "crossed_circle", "circle", "03b6e0fcb3499374a867c041f52298f0"],
    "help": ["question_arrow", "whats_this", "left_ptr_help", "dnd-ask", "5c6cd98b3f3ebcb1f9c7f1c204630408",
             "d9ce0ab605698f320427677b8f8af0bd"],
}


class ImportError_(Exception):
    pass


# ------------------------------------------------------------------- sources
class Source:
    """Find files on an XP CD/ISO or in an installed Windows folder."""

    def __init__(self, path, work):
        self.path = os.path.abspath(path)
        self.work = work
        self.iso_members = None
        self.index = {}
        if os.path.isfile(self.path):
            if not self.path.lower().endswith((".iso", ".img")):
                raise ImportError_("%s is not an ISO image or a folder" % path)
            out = subprocess.run(["7z", "l", "-slt", "-ba", self.path], capture_output=True, text=True)
            if out.returncode != 0:
                raise ImportError_("cannot read %s: %s" % (path, out.stderr.strip()[:200]))
            self.iso_members = [l[7:].strip() for l in out.stdout.splitlines() if l.startswith("Path = ")]
            for m in self.iso_members:
                self.index.setdefault(os.path.basename(m).lower(), m)
        elif os.path.isdir(self.path):
            for d, _dirs, files in os.walk(self.path):
                for f in files:
                    self.index.setdefault(f.lower(), os.path.join(d, f))
        else:
            raise ImportError_("%s does not exist" % path)
        if not any(k in self.index for k in ("luna.ms_", "luna.msstyles", "shell32.dl_", "shell32.dll")):
            raise ImportError_("%s does not look like Windows XP media (no Luna visual style or shell32 found)" % path)

    def _materialize(self, key):
        loc = self.index[key]
        if self.iso_members is None:
            return loc
        dest = os.path.join(self.work, "iso")
        os.makedirs(dest, exist_ok=True)
        subprocess.run(["7z", "x", "-y", "-o" + dest, self.path, loc], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False)
        p = os.path.join(dest, loc)
        return p if os.path.exists(p) else None

    def _expand(self, packed):
        """Decompress a CD file such as LUNA.MS_ (a one-file cabinet)."""
        dest = tempfile.mkdtemp(prefix="cab-", dir=self.work)
        if shutil.which("7z"):
            subprocess.run(["7z", "x", "-y", "-o" + dest, packed], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        if not os.listdir(dest) and shutil.which("bsdtar"):
            subprocess.run(["bsdtar", "-xf", packed, "-C", dest], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        files = [os.path.join(dest, f) for f in os.listdir(dest)]
        if not files:
            # not a cabinet after all: maybe stored uncompressed
            return packed
        return files[0]

    def get(self, *candidates):
        """Return a local path for the first candidate found (long or CD name)."""
        for c in candidates:
            if not c:
                continue
            key = c.lower()
            if key in self.index:
                p = self._materialize(key)
                if p:
                    return self._expand(p) if key.endswith("_") else p
        return None

    def names(self, pattern):
        rx = re.compile(pattern, re.I)
        return sorted(k for k in self.index if rx.search(k))


# ---------------------------------------------------------------- converters
def save_wav(src, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(src, dest)


def square(img, size):
    img = img.convert("RGBA")
    if img.width != img.height:
        side = max(img.size)
        c = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        c.alpha_composite(img, ((side - img.width) // 2, (side - img.height) // 2))
        img = c
    if img.width == size:
        return img
    return img.resize((size, size), Image.LANCZOS)


def write_icon(root, context, name, sizes):
    """sizes: {px: image}; renders every theme size from the closest source."""
    for s in SIZES:
        src = sizes.get(s)
        if src is None:
            bigger = [k for k in sizes if k >= s]
            src = sizes[min(bigger)] if bigger else sizes[max(sizes)]
        out = os.path.join(root, "%d" % s, context, name + ".png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        square(src, s).save(out)


def icon_theme_index(root):
    dirs = ["%d/%s" % (s, c) for s in SIZES for c in ICONS]
    ctx = {"places": "Places", "devices": "Devices", "apps": "Applications", "mimetypes": "MimeTypes",
           "actions": "Actions", "status": "Status"}
    with open(os.path.join(root, "index.theme"), "w") as f:
        f.write("[Icon Theme]\nName=Whistler XP originals\nComment=Icons imported from the user's Windows XP media\n")
        f.write("Hidden=true\nDirectories=%s\n" % ",".join(dirs))
        for d in dirs:
            s, c = d.split("/")
            f.write("\n[%s]\nSize=%s\nContext=%s\nType=Fixed\n" % (d, s, ctx[c]))


def make_cursors(user32, root, work, log):
    pe = PE(user32)
    groups = set(pe.names("RT_GROUP_CURSOR"))
    frames = os.path.join(work, "cursors")
    os.makedirs(frames, exist_ok=True)
    cdir = os.path.join(root, "cursors")
    os.makedirs(cdir, exist_ok=True)
    made = 0
    for gid, name in CURSORS.items():
        if gid not in groups:
            continue
        cur = pe.cursor(gid)
        if not cur:
            continue
        img, (hx, hy) = cur
        lines = []
        for size in (32, 48):
            scale = size / img.width
            big = img.resize((size, size), Image.NEAREST)
            # XP showed a soft pointer shadow
            shadow = Image.new("RGBA", big.size, (0, 0, 0, 0))
            alpha = big.split()[3].point(lambda a: int(a * 0.35))
            shadow.paste((0, 0, 0, 255), (0, 0), alpha)
            canvas = Image.new("RGBA", big.size, (0, 0, 0, 0))
            from PIL import ImageFilter
            if name in ("text", "crosshair"):
                # these invert the screen on Windows: give the black shape a white halo instead
                halo = big.split()[3].filter(ImageFilter.MaxFilter(3))
                white = Image.new("RGBA", big.size, (255, 255, 255, 0))
                white.putalpha(halo)
                canvas.alpha_composite(white)
            else:
                canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(1.2 * scale)),
                                       (int(2 * scale), int(2 * scale)))
            canvas.alpha_composite(big)
            fn = "%s-%d.png" % (name, size)
            canvas.save(os.path.join(frames, fn))
            lines.append("%d %d %d %s" % (size, int(hx * scale), int(hy * scale), fn))
        cfg = os.path.join(frames, name + ".cfg")
        with open(cfg, "w") as f:
            f.write("\n".join(lines) + "\n")
        r = subprocess.run(["xcursorgen", cfg, os.path.join(cdir, name)], cwd=frames,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            made += 1
            for alias in CURSOR_ALIASES.get(name, []):
                p = os.path.join(cdir, alias)
                if not os.path.lexists(p):
                    os.symlink(name, p)
    log("cursors: %d" % made)


def import_all(source_path, root=ROOT, log=print, progress=lambda pct, msg: None):
    work = tempfile.mkdtemp(prefix="whistler-import-")
    staging = root + ".new"
    shutil.rmtree(staging, ignore_errors=True)
    assets = os.path.join(staging, "assets")
    icons = os.path.join(staging, "icons")
    os.makedirs(assets)
    try:
        progress(2, "Reading the Windows XP files...")
        src = Source(source_path, work)
        counts = {}

        progress(10, "Converting the visual style...")
        ms = src.get(*[n for pair in MSSTYLES for n in pair])
        if ms:
            counts["theme images"] = theme.convert(ms, assets, log=log)
            os.makedirs(os.path.join(staging, "wine", "luna"), exist_ok=True)
            shutil.copyfile(ms, os.path.join(staging, "wine", "luna", "luna.msstyles"))

        progress(35, "Copying the desktop background...")
        b = src.get(*[n for pair in BLISS for n in pair])
        if b:
            os.makedirs(os.path.join(assets, "wallpaper"), exist_ok=True)
            Image.open(b).convert("RGB").save(os.path.join(assets, "wallpaper", "default.jpg"), quality=95)
            counts["wallpaper"] = 1
        walls = os.path.join(staging, "wallpapers")
        n = 0
        for key in src.names(r"\.jp_$|\.jpg$") + ["%s.bm_" % w for w in BMP_WALLPAPERS] + \
                ["%s.bmp" % w for w in BMP_WALLPAPERS]:
            if key.startswith(("xptht", "wpa")) or key not in src.index:
                continue
            p = src.get(key)
            try:
                im = Image.open(p).convert("RGB")
            except (OSError, TypeError):
                continue
            if im.width < 200:
                continue
            os.makedirs(walls, exist_ok=True)
            im.save(os.path.join(walls, os.path.splitext(os.path.basename(p))[0].lower() + ".jpg"), quality=95)
            n += 1
        counts["wallpapers"] = n

        progress(45, "Copying sounds...")
        n = 0
        for fd, (long_name, cd_name) in SOUNDS.items():
            p = src.get(long_name, cd_name)
            if p:
                save_wav(p, os.path.join(assets, "sounds", fd + ".wav"))
                n += 1
        counts["sounds"] = n

        progress(55, "Installing fonts...")
        n = 0
        for f in FONTS:
            p = src.get(f + ".ttf", f.upper() + ".TT_")
            if p:
                os.makedirs(os.path.join(assets, "fonts"), exist_ok=True)
                shutil.copyfile(p, os.path.join(assets, "fonts", f + ".ttf"))
                n += 1
        counts["fonts"] = n

        progress(65, "Extracting icons...")
        pes = {}
        for key, names in PE_FILES.items():
            p = src.get(*names)
            if p:
                try:
                    pes[key] = PE(p)
                except Exception as e:  # noqa: BLE001
                    log("cannot read %s: %s" % (names[0], e))
        n = 0
        for context, table in ICONS.items():
            for fd, (key, gid) in table.items():
                pe = pes.get(key)
                if pe is None:
                    continue
                sizes = pe.icon(gid)
                if sizes:
                    write_icon(icons, context, fd, sizes)
                    n += 1
        # start button flag, log off / turn off buttons, all programs arrow, welcome screen
        ex = pes.get("explorer")
        if ex:
            flag = ex.bitmap(143)
            if flag:
                write_icon(icons, "apps", "whistler-start-logo", {flag.width: flag})
                n += 1
            lb = ex.bitmap(7010)
            gina = pes.get("msgina")
            strip = gina.bitmap(20150) if gina else None
            big = {}
            if strip is not None and strip.height >= 320:
                fh = strip.height // 10
                big = {"turnoff": strip.crop((0, 0, strip.width, fh)),
                       "standby": strip.crop((0, 3 * fh, strip.width, 4 * fh)),
                       "restart": strip.crop((0, 6 * fh, strip.width, 7 * fh))}
                write_icon(icons, "apps", "whistler-standby", {32: big["standby"]})
                write_icon(icons, "apps", "whistler-restart", {32: big["restart"]})
                n += 2
            if lb and lb.width >= 72:
                write_icon(icons, "apps", "whistler-logoff", {24: lb.crop((24, 0, 48, 24))})
                sizes = {24: lb.crop((48, 0, 72, 24))}
                if "turnoff" in big:
                    sizes[32] = big["turnoff"]
                write_icon(icons, "apps", "whistler-turnoff", sizes)
                n += 2
            if gina:
                flag = gina.bitmap(20141)
                bg = gina.bitmap(20140)
                if flag is not None:
                    write_icon(icons, "apps", "whistler-dialog-logo", {40: flag})
                if bg is not None:
                    os.makedirs(os.path.join(assets, "dialogs"), exist_ok=True)
                    bg.save(os.path.join(assets, "dialogs", "turnoff-background.png"))
                    os.makedirs(os.path.join(assets, "css"), exist_ok=True)
                    with open(os.path.join(assets, "css", "dialogs.css"), "w") as f:
                        f.write("""/* Generated from the user's own Windows XP files. */
.xp-off-dialog {
  background-image: url("/usr/share/whistler/assets/current/dialogs/turnoff-background.png");
  background-size: 100% 100%;
  border: none;
}
.xp-off-top, .xp-off-middle, .xp-off-bottom {
  background-image: none;
  background-color: transparent;
  border: none;
}
.xp-off-title {
  font-family: "Franklin Gothic Medium", "Trebuchet MS", sans-serif;
}
""")
        if ms:
            st = theme.Style(ms)
            arrow = st.bitmap("BLUE_STARTPANELMOREPROGARROW_BMP")
            if arrow:
                write_icon(icons, "apps", "whistler-allprograms-arrow", {24: square(arrow, 24)})
                n += 1
        lu = pes.get("logonui")
        if lu:
            gdir = os.path.join(assets, "greeter")
            os.makedirs(gdir, exist_ok=True)
            for rid, name in ((123, "logo"), (100, "glow"), (125, "line-top"), (126, "line-bottom"),
                              (124, "divider"), (112, "tile-selected"), (113, "frame"), (119, "frame-selected"),
                              (103, "go"), (104, "go-hot"), (105, "help"), (106, "help-hot"), (107, "turnoff"),
                              (121, "turnoff-hot"), (114, "default-picture")):
                im = lu.bitmap(rid)
                if im:
                    if name == "logo":
                        # 24-bit bitmap drawn on a solid background: make that transparent
                        im = im.convert("RGBA")
                        bg = im.getpixel((0, 0))[:3]
                        px = im.load()
                        for y in range(im.height):
                            for x in range(im.width):
                                r, g, b, a = px[x, y]
                                d = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
                                if d < 24:
                                    px[x, y] = (r, g, b, 0)
                                elif d < 60:
                                    px[x, y] = (r, g, b, int(255 * (d - 24) / 36))
                    im.save(os.path.join(gdir, name + ".png"))
            for rid, fd in ((103, "whistler-go"), (105, "whistler-help-tile")):
                im = lu.bitmap(rid)
                if im:
                    write_icon(icons, "apps", fd, {im.width: im})
            counts["welcome screen images"] = len(os.listdir(gdir))
            A = "/usr/share/whistler/assets/current/greeter"
            os.makedirs(os.path.join(assets, "css"), exist_ok=True)
            with open(os.path.join(assets, "css", "greeter.css"), "w") as f:
                f.write("""/* Generated from the user's own Windows XP files. */
.xp-user-box.hover, .xp-user-box.selected {
  background-image: url("%(A)s/tile-selected.png");
  background-size: 100%% 100%%;
  border-radius: 0;
}
.xp-user-picture {
  background-color: transparent;
  background-image: url("%(A)s/frame.png");
  background-size: 100%% 100%%;
  border: none;
  border-radius: 0;
  padding: 5px;
}
.xp-user-box.hover .xp-user-picture, .xp-user-box.selected .xp-user-picture {
  background-image: url("%(A)s/frame-selected.png");
}
""" % {"A": A})
        counts["icons"] = n
        if n:
            icon_theme_index(icons)

        progress(80, "Converting mouse pointers...")
        u32 = src.get(*PE_FILES["user32"])
        if u32 and shutil.which("xcursorgen"):
            try:
                make_cursors(u32, icons, work, log)
            except Exception as e:  # noqa: BLE001
                log("pointers skipped: %s" % e)

        progress(88, "Copying account pictures...")
        n = 0
        for pic in USER_PICTURES:
            p = src.get(pic + ".bmp", pic.upper() + ".BM_")
            if p:
                os.makedirs(os.path.join(assets, "userpics"), exist_ok=True)
                try:
                    Image.open(p).convert("RGB").save(os.path.join(assets, "userpics", "xp-%s.png" % pic))
                    n += 1
                except OSError:
                    pass
        counts["account pictures"] = n

        if not counts.get("theme images") and not counts.get("sounds") and not counts.get("icons"):
            raise ImportError_("no usable Windows XP files were found in %s" % source_path)

        progress(94, "Saving...")
        old = root + ".old"
        shutil.rmtree(old, ignore_errors=True)
        if os.path.exists(root):
            os.rename(root, old)
        os.makedirs(os.path.dirname(root), exist_ok=True)
        os.rename(staging, root)
        shutil.rmtree(old, ignore_errors=True)
        return counts
    finally:
        shutil.rmtree(work, ignore_errors=True)
        shutil.rmtree(staging, ignore_errors=True)


def apply_system():
    """Point the system at the imported files (run as root)."""
    subprocess.run(["whistler-assets", "refresh"], check=False)
    icons = os.path.join(ROOT, "icons")
    if os.path.isdir(icons):
        subprocess.run(["gtk-update-icon-cache", "-q", "-f", "-t", icons], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def remove_all():
    shutil.rmtree(ROOT, ignore_errors=True)
    subprocess.run(["whistler-assets", "refresh"], check=False)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: whistler-import-xp-backend XP_ISO | --remove\n"
              "  XP_ISO: a Windows XP CD image (.iso), a mounted CD or an installed Windows folder")
        return 2
    if os.geteuid() != 0:
        print("ERROR must run as root", flush=True)
        return 1
    if argv[0] == "--remove":
        remove_all()
        print("DONE removed", flush=True)
        return 0

    def progress(pct, msg):
        print("PROGRESS %d %s" % (pct, msg), flush=True)

    def log(msg):
        print("LOG %s" % msg, flush=True)
    try:
        counts = import_all(argv[0], log=log, progress=progress)
    except ImportError_ as e:
        print("ERROR %s" % e, flush=True)
        return 1
    except Exception as e:  # noqa: BLE001
        print("ERROR unexpected problem: %s" % e, flush=True)
        return 1
    progress(97, "Applying...")
    apply_system()
    for k, v in counts.items():
        print("COUNT %s=%s" % (k, v), flush=True)
    print("DONE ok", flush=True)
    return 0
