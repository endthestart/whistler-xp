"""User Accounts, in the style of the XP control panel applet (AccountsService backend)."""
import os
import pty
import pwd
import re
import shutil
import subprocess
import sys
import time

from gi.repository import GdkPixbuf, Gio, GLib, Gtk

from .common import TaskPane, css_class, image, load_css, spawn, xp_message

USERPICS = "/usr/share/whistler/assets/current/userpics"
BUS = "org.freedesktop.Accounts"


def accounts_proxy(path="/org/freedesktop/Accounts", iface="org.freedesktop.Accounts"):
    return Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
                                          BUS, path, iface, None)


class Account:
    def __init__(self, path):
        self.path = path
        self.proxy = accounts_proxy(path, "org.freedesktop.Accounts.User")

    def prop(self, name, default=None):
        v = self.proxy.get_cached_property(name)
        return v.unpack() if v is not None else default

    @property
    def name(self):
        return self.prop("UserName", "")

    @property
    def real_name(self):
        return self.prop("RealName") or self.name

    @property
    def admin(self):
        return self.prop("AccountType", 0) == 1

    @property
    def icon(self):
        f = self.prop("IconFile", "")
        if f and os.path.isfile(f):
            return f
        home = self.prop("HomeDirectory", "")
        face = os.path.join(home, ".face") if home else ""
        return face if face and os.access(face, os.R_OK) else None

    @property
    def has_password(self):
        return self.prop("PasswordMode", 0) == 0 and not self.prop("Locked", False)

    def call(self, method, sig, *args):
        self.proxy.call_sync(method, GLib.Variant(sig, args) if sig else None,
                             Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, 120000, None)


def all_accounts():
    out = []
    try:
        mgr = accounts_proxy()
    except GLib.Error:
        return out
    for p in pwd.getpwall():
        if p.pw_uid < 1000 or p.pw_uid >= 60000 or p.pw_shell.endswith(("nologin", "false")):
            continue
        try:
            path = mgr.call_sync("FindUserByName", GLib.Variant("(s)", (p.pw_name,)),
                                 Gio.DBusCallFlags.NONE, 5000, None).unpack()[0]
            out.append(Account(path))
        except GLib.Error:
            continue
    return out


def crypt_password(pw):
    r = subprocess.run(["openssl", "passwd", "-6", "-stdin"], input=pw, capture_output=True, text=True)
    return r.stdout.strip()


def change_own_password(old, new):
    """Drive passwd(1) through a pty; returns (ok, message)."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp("passwd", ["passwd"])
    out = b""
    deadline = time.time() + 30
    sent = set()
    while time.time() < deadline:
        try:
            chunk = os.read(fd, 1024)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
        text = out.decode(errors="replace").lower()
        if "current" in text and "current" not in sent:
            os.write(fd, (old + "\n").encode())
            sent.add("current")
        elif "retype" in text and "retype" not in sent:
            os.write(fd, (new + "\n").encode())
            sent.add("retype")
        elif "new password" in text and "new" not in sent:
            os.write(fd, (new + "\n").encode())
            sent.add("new")
    _, status = os.waitpid(pid, 0)
    msg = out.decode(errors="replace").strip().splitlines()
    return os.WEXITSTATUS(status) == 0, (msg[-1] if msg else "")


def pic_pixbuf(path, size):
    try:
        return GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, False)
    except (GLib.Error, TypeError):
        return None


class UserAccounts(Gtk.Window):
    def __init__(self):
        super().__init__(title="User Accounts")
        self.set_icon_name("system-users")
        self.set_default_size(760, 520)
        self.connect("destroy", Gtk.main_quit)
        self.me = pwd.getpwuid(os.getuid()).pw_name
        self.body = Gtk.Box()
        self.add(self.body)
        self.show_home()
        self.show_all()

    def page(self, pane_groups):
        for c in self.body.get_children():
            c.destroy()
        pane = TaskPane()
        for g in pane_groups:
            pane.add_group(*g)
        self.body.pack_start(pane, False, False, 0)
        sc = Gtk.ScrolledWindow()
        css_class(sc, "xp-content")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(20)
        sc.add(box)
        self.body.pack_start(sc, True, True, 0)
        return box

    def heading(self, box, text):
        h = Gtk.Label(label=text, xalign=0)
        h.set_line_wrap(True)
        css_class(h, "xp-heading")
        box.pack_start(h, False, False, 4)

    def link(self, box, text, cb):
        b = Gtk.Button()
        b.set_relief(Gtk.ReliefStyle.NONE)
        css_class(b, "xp-category-link")
        bb = Gtk.Box(spacing=8)
        bb.pack_start(image("whistler-allprograms-arrow", 16), False, False, 0)
        bb.pack_start(Gtk.Label(label=text, xalign=0), False, False, 0)
        b.add(bb)
        b.set_halign(Gtk.Align.START)
        b.connect("clicked", lambda *_: cb())
        box.pack_start(b, False, False, 0)

    def tile(self, acct, cb):
        b = Gtk.Button()
        b.set_relief(Gtk.ReliefStyle.NONE)
        css_class(b, "xp-category-link")
        row = Gtk.Box(spacing=10)
        pb = pic_pixbuf(acct.icon, 48) if acct.icon else None
        row.pack_start(Gtk.Image.new_from_pixbuf(pb) if pb else image("avatar-default", 48), False, False, 0)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        n = Gtk.Label(label=acct.real_name, xalign=0)
        css_class(n, "bold")
        col.pack_start(n, False, False, 0)
        col.pack_start(Gtk.Label(label="Computer administrator" if acct.admin else "Limited account", xalign=0),
                       False, False, 0)
        if acct.has_password:
            col.pack_start(Gtk.Label(label="Password protected", xalign=0), False, False, 0)
        row.pack_start(col, False, False, 0)
        b.add(row)
        b.set_size_request(250, -1)
        b.connect("clicked", lambda *_: cb(acct))
        return b

    # ----------------------------------------------------------- pages
    def show_home(self):
        box = self.page([("Learn About", [("help-browser", "User accounts", lambda: spawn(["whistler-help", "users"])),
                                          ("help-browser", "User account types", lambda: spawn(["whistler-help", "users"]))])])
        self.heading(box, "Pick a task...")
        self.link(box, "Change an account", lambda: None)
        self.link(box, "Create a new account", self.create_account)
        lbl = Gtk.Label(label="or pick an account to change", xalign=0)
        css_class(lbl, "xp-section-title")
        box.pack_start(lbl, False, False, 10)
        grid = Gtk.FlowBox()
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.set_max_children_per_line(2)
        for a in all_accounts():
            grid.add(self.tile(a, self.show_account))
        box.pack_start(grid, False, False, 0)
        self.body.show_all()

    def show_account(self, acct):
        mine = acct.name == self.me
        box = self.page([("Related Tasks", [("go-home", "Back to User Accounts home", self.show_home)])])
        who = "your" if mine else "%s's" % acct.real_name
        self.heading(box, "What do you want to change about %s account?" % who)
        row = Gtk.Box(spacing=16)
        tasks = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.link(tasks, "Change %s name" % ("my" if mine else "the"), lambda: self.change_name(acct))
        self.link(tasks, ("Change %s password" if acct.has_password else "Create %s password")
                  % ("my" if mine else "the"), lambda: self.change_password(acct))
        self.link(tasks, "Change %s picture" % ("my" if mine else "the"), lambda: self.change_picture(acct))
        self.link(tasks, "Change %s account type" % ("my" if mine else "the"), lambda: self.change_type(acct))
        if not mine:
            self.link(tasks, "Delete the account", lambda: self.delete(acct))
        row.pack_start(tasks, True, True, 0)
        row.pack_start(self.tile(acct, lambda a: None), False, False, 0)
        box.pack_start(row, False, False, 0)
        self.body.show_all()

    def change_name(self, acct):
        d = Gtk.Dialog(title="Change name", transient_for=self, modal=True)
        d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Change Name", Gtk.ResponseType.OK)
        box = d.get_content_area()
        box.set_border_width(14)
        box.pack_start(Gtk.Label(label="Type a new name for %s:" % acct.real_name, xalign=0), False, False, 0)
        e = Gtk.Entry()
        e.set_text(acct.real_name)
        e.set_activates_default(True)
        d.set_default_response(Gtk.ResponseType.OK)
        box.pack_start(e, False, False, 6)
        box.pack_start(Gtk.Label(label="This name will appear on the Welcome screen and on the Start menu.",
                                 xalign=0), False, False, 0)
        d.show_all()
        if d.run() == Gtk.ResponseType.OK and e.get_text().strip():
            try:
                acct.call("SetRealName", "(s)", e.get_text().strip())
                spawn(["whistler-startmenu", "--quit"])
            except GLib.Error as err:
                xp_message(self, "The name could not be changed.", err.message, kind=Gtk.MessageType.ERROR)
        d.destroy()
        self.show_account(Account(acct.path))

    def change_password(self, acct):
        mine = acct.name == self.me
        d = Gtk.Dialog(title="Password", transient_for=self, modal=True)
        d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)
        g = Gtk.Grid(column_spacing=10, row_spacing=8)
        g.set_border_width(14)
        entries = []
        labels = (["Type your current password:"] if mine and acct.has_password else []) + \
                 ["Type a new password:", "Type the new password again to confirm:"]
        for i, l in enumerate(labels):
            g.attach(Gtk.Label(label=l, xalign=0), 0, i, 1, 1)
            e = Gtk.Entry()
            e.set_visibility(False)
            g.attach(e, 1, i, 1, 1)
            entries.append(e)
        d.get_content_area().pack_start(g, True, True, 0)
        d.show_all()
        while d.run() == Gtk.ResponseType.OK:
            vals = [e.get_text() for e in entries]
            new, again = vals[-2], vals[-1]
            if new != again:
                xp_message(d, "The passwords you typed do not match.", kind=Gtk.MessageType.ERROR)
                continue
            if mine:
                ok, msg = change_own_password(vals[0] if len(vals) == 3 else "", new)
                if not ok:
                    xp_message(d, "Your password was not changed.", msg, kind=Gtk.MessageType.ERROR)
                    continue
            else:
                try:
                    acct.call("SetPassword", "(ss)", crypt_password(new), "")
                except GLib.Error as err:
                    xp_message(d, "The password could not be set.", err.message, kind=Gtk.MessageType.ERROR)
                    continue
            break
        d.destroy()

    def change_picture(self, acct):
        box = self.page([("Related Tasks", [("go-previous", "Back", lambda: self.show_account(acct))])])
        self.heading(box, "Pick a new picture for %s account" % ("your" if acct.name == self.me else "the"))
        box.pack_start(Gtk.Label(label="The picture you choose will appear on the Welcome screen.", xalign=0),
                       False, False, 0)
        flow = Gtk.FlowBox()
        flow.set_max_children_per_line(8)
        flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        pics = sorted(os.path.join(USERPICS, f) for f in os.listdir(USERPICS) if f.endswith(".png")) \
            if os.path.isdir(USERPICS) else []
        for p in pics:
            img = Gtk.Image.new_from_pixbuf(pic_pixbuf(p, 48))
            img.path = p
            flow.add(img)
        box.pack_start(flow, False, False, 0)
        row = Gtk.Box(spacing=8)
        browse = Gtk.Button(label="Browse for more pictures...")
        row.pack_start(browse, False, False, 0)
        ok = Gtk.Button(label="Change Picture")
        row.pack_end(ok, False, False, 0)
        box.pack_start(row, False, False, 10)

        def apply(path):
            try:
                if acct.name == self.me:
                    shutil.copy(path, os.path.expanduser("~/.face"))
                acct.call("SetIconFile", "(s)", path)
            except (GLib.Error, OSError) as err:
                xp_message(self, "The picture could not be changed.", str(err), kind=Gtk.MessageType.ERROR)
            spawn(["whistler-startmenu", "--quit"])
            self.show_account(Account(acct.path))

        def on_ok(*_):
            sel = flow.get_selected_children()
            if sel:
                apply(sel[0].get_child().path)

        def on_browse(*_):
            dlg = Gtk.FileChooserDialog(title="Open", transient_for=self, action=Gtk.FileChooserAction.OPEN)
            dlg.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.ACCEPT)
            f = Gtk.FileFilter()
            f.set_name("Pictures")
            f.add_pixbuf_formats()
            dlg.add_filter(f)
            if dlg.run() == Gtk.ResponseType.ACCEPT:
                src = dlg.get_filename()
                pb = pic_pixbuf(src, 96)
                if pb:
                    dest = os.path.join(GLib.get_user_cache_dir(), "whistler-face.png")
                    pb.savev(dest, "png", [], [])
                    apply(dest)
            dlg.destroy()
        ok.connect("clicked", on_ok)
        flow.connect("child-activated", lambda *_: on_ok())
        browse.connect("clicked", on_browse)
        self.body.show_all()

    def change_type(self, acct):
        d = Gtk.Dialog(title="Account type", transient_for=self, modal=True)
        d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Change Account Type", Gtk.ResponseType.OK)
        box = d.get_content_area()
        box.set_border_width(14)
        admin = Gtk.RadioButton.new_with_label(None, "Computer administrator")
        limited = Gtk.RadioButton.new_with_label_from_widget(admin, "Limited")
        (admin if acct.admin else limited).set_active(True)
        box.pack_start(admin, False, False, 0)
        box.pack_start(Gtk.Label(label="    Can install programs, change system settings and manage accounts.",
                                 xalign=0), False, False, 0)
        box.pack_start(limited, False, False, 6)
        box.pack_start(Gtk.Label(label="    Can use programs and change their own settings.", xalign=0),
                       False, False, 0)
        d.show_all()
        if d.run() == Gtk.ResponseType.OK:
            try:
                acct.call("SetAccountType", "(i)", 1 if admin.get_active() else 0)
            except GLib.Error as err:
                xp_message(self, "The account type could not be changed.", err.message, kind=Gtk.MessageType.ERROR)
        d.destroy()
        self.show_account(Account(acct.path))

    def delete(self, acct):
        r = xp_message(self, "Do you want to delete %s's account?" % acct.real_name,
                       "Their files and settings will be deleted too.", kind=Gtk.MessageType.WARNING,
                       buttons=Gtk.ButtonsType.YES_NO)
        if r == Gtk.ResponseType.YES:
            try:
                accounts_proxy().call_sync("DeleteUser", GLib.Variant("(xb)", (acct.prop("Uid", 0), True)),
                                           Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, 120000, None)
            except GLib.Error as err:
                xp_message(self, "The account could not be deleted.", err.message, kind=Gtk.MessageType.ERROR)
        self.show_home()

    def create_account(self):
        d = Gtk.Dialog(title="Create a new account", transient_for=self, modal=True)
        d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Create Account", Gtk.ResponseType.OK)
        g = Gtk.Grid(column_spacing=10, row_spacing=8)
        g.set_border_width(14)
        g.attach(Gtk.Label(label="Name for the new account:", xalign=0), 0, 0, 1, 1)
        name = Gtk.Entry()
        g.attach(name, 1, 0, 1, 1)
        admin = Gtk.RadioButton.new_with_label(None, "Computer administrator")
        limited = Gtk.RadioButton.new_with_label_from_widget(admin, "Limited")
        g.attach(admin, 0, 1, 2, 1)
        g.attach(limited, 0, 2, 2, 1)
        g.attach(Gtk.Label(label="Password (optional):", xalign=0), 0, 3, 1, 1)
        pw = Gtk.Entry()
        pw.set_visibility(False)
        g.attach(pw, 1, 3, 1, 1)
        d.get_content_area().pack_start(g, True, True, 0)
        d.show_all()
        if d.run() == Gtk.ResponseType.OK and name.get_text().strip():
            full = name.get_text().strip()
            login = re.sub(r"[^a-z0-9_-]", "", full.lower().replace(" ", ""))[:31] or "user"
            if login[0].isdigit():
                login = "u" + login
            try:
                path = accounts_proxy().call_sync(
                    "CreateUser", GLib.Variant("(ssi)", (login, full, 1 if admin.get_active() else 0)),
                    Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, 120000, None).unpack()[0]
                acct = Account(path)
                if pw.get_text():
                    acct.call("SetPassword", "(ss)", crypt_password(pw.get_text()), "")
                else:
                    acct.call("SetPasswordMode", "(i)", 2)
                pics = sorted(f for f in os.listdir(USERPICS) if f.endswith(".png"))
                if pics:
                    acct.call("SetIconFile", "(s)", os.path.join(USERPICS, pics[hash(login) % len(pics)]))
            except GLib.Error as err:
                xp_message(self, "The account could not be created.", err.message, kind=Gtk.MessageType.ERROR)
        d.destroy()
        self.show_home()


def main():
    load_css("whistler.css")
    UserAccounts()
    Gtk.main()
    return 0
