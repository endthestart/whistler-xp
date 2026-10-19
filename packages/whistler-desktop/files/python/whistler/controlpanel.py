"""Control Panel with XP's category view and classic view."""
import os
import shutil
import sys

from gi.repository import Gdk, Gio, GLib, Gtk, Pango

from .common import TaskPane, css_class, image, load_css, open_uri, spawn

# (id, title, icon, description, tasks[(label, cmd)], applets[ids])
CATEGORIES = [
    ("appearance", "Appearance and Themes", "preferences-desktop-theme",
     "Change the appearance of desktop items, apply a theme or screen saver, or customize the Start menu or taskbar.",
     [("Change the computer's theme", "xfce4-appearance-settings"),
      ("Use the original Windows XP artwork and sounds", "whistler-xp-originals"),
      ("Change the desktop background", "xfdesktop-settings"),
      ("Choose a screen saver", "xfce4-screensaver-preferences"),
      ("Change the screen resolution", "xfce4-display-settings")],
     ["display", "taskbar", "folders", "fonts", "windows", "xporiginals"]),
    ("network", "Network and Internet Connections", "network-workgroup",
     "Connect to the Internet, create a home or small office network, configure network settings.",
     [("Set up or change your Internet connection", "nm-connection-editor"),
      ("Change Firefox settings", "firefox about:preferences")],
     ["netconn", "internet"]),
    ("programs", "Add or Remove Programs", "system-software-install",
     "Install or remove programs and Windows programs.", None, None),
    ("sound", "Sounds, Speech, and Audio Devices", "multimedia-volume-control",
     "Change the sound scheme, or configure the settings for your speakers and recording devices.",
     [("Adjust the system volume", "whistler-volume"),
      ("Change advanced sound settings", "pavucontrol"),
      ("Change the sound scheme", "xfce4-appearance-settings")],
     ["sounds"]),
    ("performance", "Performance and Maintenance", "utilities-system-monitor",
     "Schedule maintenance checks, increase space on your hard disk, or configure energy-saving settings.",
     [("See basic information about your computer", "whistler-sysprops"),
      ("Rearrange items on your hard disk", "gparted"),
      ("Free up space on your hard disk", "xfce4-terminal --hold -x sh -c 'echo Cleaning package cache...; pkexec paccache -rk1'"),
      ("Back up your data", "thunar")],
     ["system", "power", "taskmgr", "session", "disks"]),
    ("hardware", "Printers and Other Hardware", "printer",
     "Change settings for printers, keyboard, mouse, and other hardware.",
     [("View installed printers or fax printers", "system-config-printer"),
      ("Add a printer", "system-config-printer")],
     ["printers", "mouse", "keyboard", "removable", "bluetooth"]),
    ("users", "User Accounts", "system-users",
     "Change user account settings and passwords for people who share this computer.", None, None),
    ("datetime", "Date, Time, Language, and Regional Options", "preferences-system-time",
     "Change the date, time, and time zone for your computer, the language, and how numbers and dates are shown.",
     [("Change the date and time", "whistler-control datetime"),
      ("Change the format of numbers, dates, and times", "whistler-control regional")],
     ["datetimeapplet"]),
    ("access", "Accessibility Options", "preferences-desktop-accessibility",
     "Adjust your computer settings for vision, hearing, and mobility.",
     [("Adjust the contrast for text and colors on your screen", "xfce4-appearance-settings")],
     ["accessibility"]),
    ("wine", "Windows Programs (Wine)", "whistler-winecenter",
     "Install, run and configure Windows programs and their compatibility settings.", None, None),
]

APPLETS = {
    "display": ("Display", "preferences-desktop-display", "xfce4-display-settings"),
    "taskbar": ("Taskbar and Start Menu", "preferences-desktop", "xfce4-panel --preferences"),
    "folders": ("Folder Options", "folder", "thunar-settings"),
    "fonts": ("Fonts", "preferences-desktop-font", "xfce4-appearance-settings"),
    "windows": ("Window Behavior", "preferences-system-windows", "xfwm4-tweaks-settings"),
    "netconn": ("Network Connections", "network-wired", "nm-connection-editor"),
    "internet": ("Internet Options", "firefox", "firefox about:preferences"),
    "sounds": ("Sounds and Audio Devices", "multimedia-volume-control", "whistler-volume"),
    "system": ("System", "computer", "whistler-sysprops"),
    "power": ("Power Options", "xfce4-power-manager-settings", "xfce4-power-manager-settings"),
    "taskmgr": ("Task Manager", "utilities-system-monitor", "xfce4-taskmanager"),
    "session": ("Startup Programs", "xfce4-session", "xfce4-session-settings"),
    "disks": ("Disk Management", "drive-harddisk", "gparted"),
    "printers": ("Printers and Faxes", "printer", "system-config-printer"),
    "mouse": ("Mouse", "input-mouse", "xfce4-mouse-settings"),
    "keyboard": ("Keyboard", "input-keyboard", "xfce4-keyboard-settings"),
    "removable": ("Removable Drives and Media", "drive-removable-media", "thunar-volman-settings"),
    "bluetooth": ("Bluetooth Devices", "bluetooth", "blueman-manager"),
    "users": ("User Accounts", "system-users", "whistler-useraccounts"),
    "programs": ("Add or Remove Programs", "system-software-install", "whistler-addremove"),
    "datetimeapplet": ("Date and Time", "preferences-system-time", "whistler-control datetime"),
    "regional": ("Regional and Language Options", "preferences-desktop-locale", "whistler-control regional"),
    "accessibility": ("Accessibility Options", "preferences-desktop-accessibility", "xfce4-accessibility-settings"),
    "wine": ("Wine Center", "whistler-winecenter", "whistler-winecenter"),
    "winecfg": ("Wine Configuration", "wine-winecfg", "winecfg"),
    "defaults": ("Default Programs", "preferences-desktop-default-applications", "xfce4-mime-settings"),
    "shortcuts": ("Keyboard Shortcuts", "preferences-desktop-keyboard-shortcuts", "xfce4-keyboard-settings"),
    "notifications": ("Notifications", "preferences-desktop-notification", "xfce4-notifyd-config"),
    "screensaver": ("Screen Saver", "preferences-desktop-screensaver", "xfce4-screensaver-preferences"),
    "appearance": ("Appearance", "preferences-desktop-theme", "xfce4-appearance-settings"),
    "background": ("Desktop Background", "preferences-desktop-wallpaper", "xfdesktop-settings"),
    "xporiginals": ("Windows XP Originals", "system-software-install", "whistler-xp-originals"),
}


def available(cmd):
    return shutil.which(cmd.split()[0]) is not None


class ControlPanel(Gtk.Window):
    def __init__(self, start=None):
        super().__init__(title="Control Panel")
        self.set_icon_name("preferences-system")
        self.set_default_size(860, 580)
        self.connect("destroy", Gtk.main_quit)
        self.classic = False
        self.history = []

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(outer)
        tb = Gtk.Box(spacing=2)
        css_class(tb, "xp-toolbar")
        self.back = Gtk.Button()
        self.back.set_relief(Gtk.ReliefStyle.NONE)
        bb = Gtk.Box(spacing=4)
        bb.pack_start(image("go-previous", 24), False, False, 0)
        bb.pack_start(Gtk.Label(label="Back"), False, False, 0)
        self.back.add(bb)
        self.back.connect("clicked", lambda *_: self.go_back())
        tb.pack_start(self.back, False, False, 0)
        search = Gtk.Button()
        search.set_relief(Gtk.ReliefStyle.NONE)
        sb = Gtk.Box(spacing=4)
        sb.pack_start(image("system-search", 24), False, False, 0)
        sb.pack_start(Gtk.Label(label="Search"), False, False, 0)
        search.add(sb)
        search.connect("clicked", lambda *_: spawn(["catfish"]))
        tb.pack_start(search, False, False, 0)
        outer.pack_start(tb, False, False, 0)

        self.body = Gtk.Box()
        outer.pack_start(self.body, True, True, 0)
        self.show_all()
        if start in dict((c[0], c) for c in CATEGORIES):
            self.show_category(start)
        else:
            self.show_home()

    # ------------------------------------------------------------- pages
    def clear(self):
        for c in self.body.get_children():
            c.destroy()

    def pane(self, extra=None):
        pane = TaskPane()
        pane.add_group("Control Panel", [
            ("view-list-symbolic" if not self.classic else "view-grid-symbolic",
             "Switch to Category View" if self.classic else "Switch to Classic View", self.toggle_view)],
            special=True, icon="preferences-system")
        if extra:
            pane.add_group(*extra)
            return pane
        pane.add_group("See Also", [
            ("software-update-available", "Software Update", self.software_update),
            ("help-browser", "Help and Support", lambda: spawn(["whistler-help"])),
        ])
        return pane

    def content_scroller(self):
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        css_class(sc, "xp-content")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(18)
        sc.add(box)
        return sc, box

    def show_home(self):
        self.clear()
        self.back.set_sensitive(bool(self.history))
        self.set_title("Control Panel")
        self.body.pack_start(self.pane(), False, False, 0)
        sc, box = self.content_scroller()
        if self.classic:
            self.fill_classic(box)
        else:
            h = Gtk.Label(label="Pick a category", xalign=0)
            css_class(h, "xp-heading")
            box.pack_start(h, False, False, 4)
            grid = Gtk.Grid(column_spacing=24, row_spacing=10)
            for i, (cid, title, icon, desc, tasks, applets) in enumerate(CATEGORIES):
                btn = Gtk.Button()
                btn.set_relief(Gtk.ReliefStyle.NONE)
                css_class(btn, "xp-category-link")
                b = Gtk.Box(spacing=10)
                b.pack_start(image(icon, 48), False, False, 0)
                lbl = Gtk.Label(label=title, xalign=0)
                lbl.set_line_wrap(True)
                lbl.set_max_width_chars(26)
                b.pack_start(lbl, True, True, 0)
                btn.add(b)
                btn.set_tooltip_text(desc)
                btn.set_size_request(270, 56)
                btn.connect("clicked", lambda _w, c=cid: self.open_category(c))
                grid.attach(btn, i % 2, i // 2, 1, 1)
            box.pack_start(grid, False, False, 0)
        self.body.pack_start(sc, True, True, 0)
        self.body.show_all()

    def fill_classic(self, box):
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        flow.set_max_children_per_line(10)
        flow.set_column_spacing(4)
        flow.set_row_spacing(8)
        items = {}
        for key, (name, icon, cmd) in APPLETS.items():
            if available(cmd):
                items[name] = (icon, cmd)
        for info in Gio.AppInfo.get_all():
            if not isinstance(info, Gio.DesktopAppInfo):
                continue
            cats = info.get_categories() or ""
            if "Settings" not in cats.split(";") or info.get_nodisplay():
                continue
            name = info.get_display_name()
            if name in items or name.startswith("Whistler"):
                continue
            items[name] = (info, None)
        for name in sorted(items, key=str.lower):
            icon, cmd = items[name]
            cell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            cell.set_size_request(86, 76)
            if isinstance(icon, Gio.DesktopAppInfo):
                img = Gtk.Image.new_from_gicon(icon.get_icon(), Gtk.IconSize.DND) if icon.get_icon() else image("preferences-system", 32)
                img.set_pixel_size(32)
                act = (lambda i=icon: i.launch([], None))
            else:
                img = image(icon, 32)
                act = (lambda c=cmd: spawn(c))
            cell.pack_start(img, False, False, 0)
            l = Gtk.Label(label=name)
            l.set_line_wrap(True)
            l.set_justify(Gtk.Justification.CENTER)
            l.set_max_width_chars(12)
            cell.pack_start(l, False, False, 0)
            ev = Gtk.EventBox()
            ev.add(cell)
            ev.activate_cb = act
            ev.connect("button-press-event", lambda w, e: (w.activate_cb() or True)
                       if e.type == Gdk.EventType._2BUTTON_PRESS else False)
            flow.add(ev)
        flow.connect("child-activated", lambda fb, ch: ch.get_child().activate_cb())
        box.pack_start(flow, True, True, 0)

    def open_category(self, cid):
        cat = dict((c[0], c) for c in CATEGORIES)[cid]
        if cat[4] is None:
            spawn({"programs": "whistler-addremove", "users": "whistler-useraccounts",
                   "wine": "whistler-winecenter"}[cid])
            return
        self.history.append("home")
        self.show_category(cid)

    def show_category(self, cid):
        cid, title, icon, desc, tasks, applets = dict((c[0], c) for c in CATEGORIES)[cid]
        self.clear()
        self.back.set_sensitive(True)
        self.set_title(title)
        others = [(c[2], c[1], (lambda x=c[0]: self.open_category(x))) for c in CATEGORIES if c[0] != cid][:4]
        self.body.pack_start(self.pane(("See Also", others)), False, False, 0)
        sc, box = self.content_scroller()
        head = Gtk.Box(spacing=12)
        head.pack_start(image(icon, 48), False, False, 0)
        h = Gtk.Label(label=title, xalign=0)
        css_class(h, "xp-heading")
        head.pack_start(h, False, False, 0)
        box.pack_start(head, False, False, 0)
        lbl = Gtk.Label(label="Pick a task...", xalign=0)
        css_class(lbl, "xp-section-title")
        box.pack_start(lbl, False, False, 0)
        for label, cmd in tasks:
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            css_class(btn, "xp-category-link")
            b = Gtk.Box(spacing=8)
            b.pack_start(image("whistler-allprograms-arrow", 16), False, False, 0)
            b.pack_start(Gtk.Label(label=label, xalign=0), False, False, 0)
            btn.add(b)
            btn.set_halign(Gtk.Align.START)
            btn.connect("clicked", lambda _w, c=cmd: self.run(c))
            box.pack_start(btn, False, False, 0)
        lbl = Gtk.Label(label="or pick a Control Panel icon", xalign=0)
        css_class(lbl, "xp-section-title")
        box.pack_start(lbl, False, False, 8)
        grid = Gtk.Grid(column_spacing=24, row_spacing=6)
        n = 0
        for a in applets:
            name, aicon, cmd = APPLETS[a]
            if not available(cmd):
                continue
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            css_class(btn, "xp-category-link")
            b = Gtk.Box(spacing=8)
            b.pack_start(image(aicon, 32), False, False, 0)
            b.pack_start(Gtk.Label(label=name, xalign=0), False, False, 0)
            btn.add(b)
            btn.set_size_request(260, -1)
            btn.connect("clicked", lambda _w, c=cmd: self.run(c))
            grid.attach(btn, n % 2, n // 2, 1, 1)
            n += 1
        box.pack_start(grid, False, False, 0)
        self.body.pack_start(sc, True, True, 0)
        self.body.show_all()

    def run(self, cmd):
        if cmd.startswith("whistler-control "):
            sub = cmd.split()[1]
            if sub == "datetime":
                DateTimeDialog(self)
            elif sub == "regional":
                RegionalDialog(self)
            return
        spawn(cmd)

    def go_back(self):
        if self.history:
            self.history.pop()
        self.show_home()

    def toggle_view(self):
        self.classic = not self.classic
        self.history = []
        self.show_home()

    def software_update(self):
        spawn(["xfce4-terminal", "--title=Software Update", "--hold", "-x", "sh", "-c",
               "echo 'Checking for updates...'; pkexec pacman -Syu"])


class DateTimeDialog(Gtk.Dialog):
    """Date and Time Properties: time zone and Internet time (timedatectl)."""

    def __init__(self, parent):
        super().__init__(title="Date and Time Properties", transient_for=parent, modal=True)
        self.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)
        nb = Gtk.Notebook()
        nb.set_border_width(8)
        self.get_content_area().pack_start(nb, True, True, 0)

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(12)
        now = GLib.DateTime.new_now_local()
        cal = Gtk.Calendar()
        page.pack_start(cal, False, False, 0)
        page.pack_start(Gtk.Label(label="Current time: " + now.format("%-I:%M:%S %p"), xalign=0), False, False, 0)
        nb.append_page(page, Gtk.Label(label="Date & Time"))

        tz = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tz.set_border_width(12)
        self.zone = Gtk.ComboBoxText.new_with_entry()
        zones = []
        try:
            out = os.popen("timedatectl list-timezones").read().split()
            zones = out
        except OSError:
            pass
        current = os.path.realpath("/etc/localtime").split("zoneinfo/")[-1]
        for i, z in enumerate(zones):
            self.zone.append_text(z)
            if z == current:
                self.zone.set_active(i)
        tz.pack_start(Gtk.Label(label="Time zone:", xalign=0), False, False, 0)
        tz.pack_start(self.zone, False, False, 0)
        nb.append_page(tz, Gtk.Label(label="Time Zone"))

        net = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        net.set_border_width(12)
        self.ntp = Gtk.CheckButton(label="Automatically synchronize with an Internet time server")
        self.ntp.set_active("NTP=yes" in os.popen("timedatectl show -p NTP").read())
        net.pack_start(self.ntp, False, False, 0)
        nb.append_page(net, Gtk.Label(label="Internet Time"))
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            z = self.zone.get_active_text()
            cmds = []
            if z and z != current:
                cmds.append("timedatectl set-timezone %s" % z)
            cmds.append("timedatectl set-ntp %s" % ("true" if self.ntp.get_active() else "false"))
            spawn(["pkexec", "sh", "-c", " && ".join(cmds)])
        self.destroy()


class RegionalDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Regional and Language Options", transient_for=parent, modal=True)
        self.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(14)
        self.get_content_area().pack_start(box, True, True, 0)
        box.pack_start(Gtk.Label(label="Standards and formats (language used for menus and dates):", xalign=0),
                       False, False, 0)
        self.combo = Gtk.ComboBoxText()
        cur = os.environ.get("LANG", "en_US.UTF-8")
        locales = []
        try:
            with open("/usr/share/i18n/SUPPORTED") as f:
                locales = [l.split()[0] for l in f if "UTF-8" in l]
        except OSError:
            locales = [cur]
        for i, l in enumerate(locales):
            self.combo.append_text(l)
            if l == cur:
                self.combo.set_active(i)
        box.pack_start(self.combo, False, False, 0)
        kb = Gtk.Button(label="Keyboard layouts...")
        kb.connect("clicked", lambda *_: spawn(["xfce4-keyboard-settings"]))
        kb.set_halign(Gtk.Align.START)
        box.pack_start(kb, False, False, 0)
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            l = self.combo.get_active_text()
            if l and l != cur:
                spawn(["pkexec", "sh", "-c",
                       "sed -i 's/^#\\?%s/%s/' /etc/locale.gen && locale-gen && localectl set-locale LANG=%s"
                       % (l.replace(".", "\\."), l, l)])
        self.destroy()


def main():
    load_css("whistler.css")
    start = sys.argv[1] if len(sys.argv) > 1 else None
    if start == "datetime":
        DateTimeDialog(None)
        return 0
    if start == "regional":
        RegionalDialog(None)
        return 0
    ControlPanel(start)
    Gtk.main()
    return 0
