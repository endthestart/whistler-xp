"""Volume Control in the style of XP's sndvol32 (PulseAudio/PipeWire via pactl)."""
import json
import re
import subprocess
import sys

from gi.repository import Gdk, GLib, Gtk

from .common import css_class, image, load_css, spawn


def pactl(*args, as_json=False):
    argv = ["pactl"] + (["-f", "json"] if as_json else []) + list(args)
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return [] if as_json else ""
    if as_json:
        try:
            return json.loads(out or "[]")
        except ValueError:
            return []
    return out


def percent(entry):
    vols = entry.get("volume", {})
    vals = [int(re.sub(r"[^\d]", "", v.get("value_percent", "0")) or 0) for v in vols.values()]
    return max(vals) if vals else 0


class Channel(Gtk.Box):
    """One vertical fader column: title, balance, slider, mute checkbox."""

    def __init__(self, title, value, muted, on_volume, on_mute, icon=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        css_class(self, "xp-volume-channel")
        self.set_border_width(8)
        self.updating = False
        if icon:
            self.pack_start(image(icon, 32), False, False, 0)
        t = Gtk.Label(label=title)
        t.set_line_wrap(True)
        t.set_max_width_chars(12)
        t.set_justify(Gtk.Justification.CENTER)
        css_class(t, "bold")
        self.pack_start(t, False, False, 0)
        self.pack_start(Gtk.Label(label="Volume:"), False, False, 4)
        adj = Gtk.Adjustment(value=value, lower=0, upper=100, step_increment=2, page_increment=10)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL, adjustment=adj)
        self.scale.set_inverted(True)
        self.scale.set_draw_value(False)
        self.scale.set_size_request(-1, 150)
        for mark in range(0, 101, 10):
            self.scale.add_mark(mark, Gtk.PositionType.RIGHT, None)
        self.scale.connect("value-changed", lambda s: None if self.updating else on_volume(int(s.get_value())))
        self.pack_start(self.scale, True, True, 0)
        self.mute = Gtk.CheckButton(label="Mute")
        self.mute.set_active(muted)
        self.mute.connect("toggled", lambda b: None if self.updating else on_mute(b.get_active()))
        self.pack_start(self.mute, False, False, 0)

    def set(self, value, muted):
        self.updating = True
        if abs(self.scale.get_value() - value) > 1:
            self.scale.set_value(value)
        self.mute.set_active(muted)
        self.updating = False


class VolumeControl(Gtk.Window):
    def __init__(self):
        super().__init__(title="Volume Control")
        self.set_icon_name("multimedia-volume-control")
        self.set_resizable(False)
        self.connect("destroy", Gtk.main_quit)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(outer)
        mb = Gtk.MenuBar()
        opts = Gtk.MenuItem.new_with_mnemonic("_Options")
        om = Gtk.Menu()
        adv = Gtk.MenuItem.new_with_mnemonic("_Advanced Controls...")
        adv.connect("activate", lambda *_: spawn(["pavucontrol"]))
        om.append(adv)
        om.append(Gtk.SeparatorMenuItem())
        ex = Gtk.MenuItem.new_with_mnemonic("E_xit")
        ex.connect("activate", lambda *_: self.destroy())
        om.append(ex)
        opts.set_submenu(om)
        mb.append(opts)
        helpm = Gtk.MenuItem.new_with_mnemonic("_Help")
        mb.append(helpm)
        outer.pack_start(mb, False, False, 0)
        self.row = Gtk.Box(spacing=0)
        self.row.set_border_width(6)
        outer.pack_start(self.row, True, True, 0)
        self.status = Gtk.Label(xalign=0)
        sb = Gtk.Box()
        css_class(sb, "xp-statusbar")
        sb.pack_start(self.status, True, True, 0)
        outer.pack_start(sb, False, False, 0)
        self.channels = {}
        self.rebuild()
        self.show_all()
        GLib.timeout_add(1500, self.poll)

    def rebuild(self):
        for c in self.row.get_children():
            c.destroy()
        self.channels = {}
        sinks = pactl("list", "sinks", as_json=True)
        default = pactl("get-default-sink").strip()
        sink = next((s for s in sinks if s.get("name") == default), sinks[0] if sinks else None)
        if sink is None:
            self.row.pack_start(Gtk.Label(label="No sound devices were found."), True, True, 20)
            self.status.set_text("No audio device")
            self.row.show_all()
            return
        name = sink["name"]
        ch = Channel("Volume Control", percent(sink), sink.get("mute", False),
                     lambda v: pactl("set-sink-volume", name, "%d%%" % v),
                     lambda m: pactl("set-sink-mute", name, "1" if m else "0"),
                     icon="audio-speakers")
        self.channels[("sink", name)] = ch
        self.row.pack_start(ch, False, False, 0)
        for inp in pactl("list", "sink-inputs", as_json=True):
            idx = str(inp.get("index"))
            props = inp.get("properties", {})
            title = props.get("application.name") or props.get("media.name") or "Program"
            self.row.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
            c = Channel(title, percent(inp), inp.get("mute", False),
                        lambda v, i=idx: pactl("set-sink-input-volume", i, "%d%%" % v),
                        lambda m, i=idx: pactl("set-sink-input-mute", i, "1" if m else "0"),
                        icon=props.get("application.icon_name") or "applications-multimedia")
            self.channels[("input", idx)] = c
            self.row.pack_start(c, False, False, 0)
        sources = pactl("list", "sources", as_json=True)
        dsrc = pactl("get-default-source").strip()
        src = next((s for s in sources if s.get("name") == dsrc and ".monitor" not in dsrc), None)
        if src is not None:
            sname = src["name"]
            self.row.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
            c = Channel("Microphone", percent(src), src.get("mute", False),
                        lambda v: pactl("set-source-volume", sname, "%d%%" % v),
                        lambda m: pactl("set-source-mute", sname, "1" if m else "0"),
                        icon="audio-input-microphone")
            self.channels[("source", sname)] = c
            self.row.pack_start(c, False, False, 0)
        self.status.set_text(sink.get("description", name))
        self.row.show_all()

    def poll(self):
        sinks = {s["name"]: s for s in pactl("list", "sinks", as_json=True)}
        inputs = {str(i["index"]): i for i in pactl("list", "sink-inputs", as_json=True)}
        want = {("input", k) for k in inputs}
        have = {k for k in self.channels if k[0] == "input"}
        if want != have:
            self.rebuild()
            self.resize(1, 1)
            return True
        for (kind, key), ch in self.channels.items():
            if kind == "sink" and key in sinks:
                ch.set(percent(sinks[key]), sinks[key].get("mute", False))
            elif kind == "input" and key in inputs:
                ch.set(percent(inputs[key]), inputs[key].get("mute", False))
        return True


def main():
    load_css("whistler.css")
    VolumeControl()
    Gtk.main()
    return 0
