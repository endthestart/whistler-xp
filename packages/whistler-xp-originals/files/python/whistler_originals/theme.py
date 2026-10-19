"""Convert the user's Windows XP visual style (luna.msstyles) into Whistler's
asset layout (same file names as /usr/share/whistler/assets/lookalike)."""
import os
import re

from PIL import Image

from .pe import PE, key_out

VARIANTS = {"blue": "NORMALBLUE", "olive": "NORMALHOMESTEAD", "silver": "NORMALMETALLIC"}


def _resname(path):
    """'Blue\\button.bmp' -> 'BLUE_BUTTON_BMP' (how packthem names bitmaps)."""
    return re.sub(r"[\\/.]", "_", path.strip()).upper()


class Style:
    def __init__(self, path, variant="blue"):
        self.pe = PE(path)
        ini = self.pe.text("TEXTFILE", VARIANTS[variant] + "_INI")
        if not ini:
            raise ValueError("no %s colour scheme in %s" % (variant, path))
        self.sections = {}
        cur = None
        for line in ini.replace("\r", "").split("\n"):
            line = line.split(";", 1)[0].strip()
            if not line:
                continue
            m = re.match(r"\[(.+)\]$", line)
            if m:
                cur = self.sections.setdefault(m.group(1).lower(), {})
                continue
            if "=" in line and cur is not None:
                k, v = line.split("=", 1)
                cur[k.strip().lower()] = v.strip()

    def sec(self, name):
        return self.sections.get(name.lower(), {})

    def margins(self, name):
        v = self.sec(name).get("sizingmargins", "0,0,0,0")
        nums = [int(x) for x in re.findall(r"-?\d+", v)][:4]
        return tuple(nums + [0] * (4 - len(nums)))

    def font(self, name):
        return self.sec(name).get("font")

    def color(self, name, key="textcolor"):
        v = self.sec(name).get(key)
        if not v:
            return None
        r, g, b = (int(x) for x in re.findall(r"\d+", v)[:3])
        return "#%02X%02X%02X" % (r, g, b)

    def bitmap(self, resname, transparent=None):
        img = self.pe.bitmap(resname)
        if img is None:
            return None
        if transparent is not None:
            img = key_out(img, transparent)
        elif img.getextrema()[3][0] == 255:
            img = key_out(img)          # opaque bitmap: magenta is the conventional key
        return img

    def frames(self, name, resname=None, count=None):
        s = self.sec(name)
        f = s.get("imagefile") or s.get("imagefile1")
        if resname is None:
            if not f:
                return []
            resname = _resname(f)
        tc = s.get("transparentcolor")
        key = tuple(int(x) for x in re.findall(r"\d+", tc)[:3]) if tc else None
        img = self.bitmap(resname, key)
        if img is None:
            return []
        n = count or int(re.findall(r"\d+", s.get("imagecount", "1"))[0])
        horizontal = s.get("imagelayout", "vertical").lower().startswith("h")
        out = []
        for i in range(n):
            if horizontal:
                w = img.width // n
                out.append(img.crop((i * w, 0, (i + 1) * w, img.height)))
            else:
                h = img.height // n
                out.append(img.crop((0, i * h, img.width, (i + 1) * h)))
        return out


def nine(img, margins, size):
    """Scale `img` to `size` keeping the margin regions (l, r, t, b) intact."""
    l, r, t, b = (max(0, m) for m in margins)
    W, H = img.size
    w, h = size

    def fit(a, c, limit):
        if a + c <= limit:
            return a, c
        k = limit / float(a + c)
        a2 = int(a * k)
        return a2, max(0, limit - a2 - 1) if c else 0
    l, r = fit(l, r, W)
    l, r = fit(l, r, w)
    t, b = fit(t, b, H)
    t, b = fit(t, b, h)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    xs = [(0, l, 0, l), (l, W - r, l, w - r), (W - r, W, w - r, w)]
    ys = [(0, t, 0, t), (t, H - b, t, h - b), (H - b, H, h - b, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            if sx1 <= sx0 or sy1 <= sy0 or dx1 <= dx0 or dy1 <= dy0:
                continue
            part = img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.BILINEAR)
            out.paste(part, (dx0, dy0))
    return out


def center(img, size):
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(img.convert("RGBA"), ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    return out


def compose(bg, glyph):
    out = bg.convert("RGBA").copy()
    if glyph is not None:
        out.alpha_composite(glyph.convert("RGBA"), ((out.width - glyph.width) // 2, (out.height - glyph.height) // 2))
    return out


def _save(img, root, *parts):
    path = os.path.join(root, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


def _font_css(spec, fallback_px=None):
    """'Franklin Gothic Medium, 14, italic' -> CSS declarations."""
    if not spec:
        return ""
    parts = [p.strip() for p in spec.split(",")]
    css = ["font-family: \"%s\";" % parts[0]]
    if len(parts) > 1 and parts[1].isdigit():
        css.append("font-size: %spt;" % parts[1])
    rest = " ".join(parts[2:]).lower()
    if "italic" in rest:
        css.append("font-style: italic;")
    if "bold" in rest:
        css.append("font-weight: bold;")
    return " ".join(css)


def convert(msstyles, out, variant="blue", log=print):
    st = Style(msstyles, variant)
    gtk = os.path.join(out, "gtk")
    pnl = os.path.join(out, "panel")
    wm = os.path.join(out, "xfwm4")
    A = "/usr/share/whistler/assets/current"
    n = 0

    # --- check boxes and radio buttons -----------------------------------
    cb = st.frames("Button.CheckBox")
    sfx = ["", "-hover", "-active", "-insensitive"]
    if len(cb) >= 12:
        for ki, kind in enumerate(("unchecked", "checked", "mixed")):
            for si, s in enumerate(sfx):
                c = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                c.alpha_composite(cb[ki * 4 + si], (1, 1))
                _save(c, gtk, "checkbox-%s%s.png" % (kind, s))
                n += 1
    big = st.frames("Button.CheckBox", "BLUE_CHECKBOX25_BMP" if variant == "blue" else None, 12)
    if len(big) >= 12:
        for name, idx in (("checkbox-selectionmode", 0), ("checkbox-hover-selectionmode", 1),
                          ("checkbox-active-selectionmode", 2), ("checkbox-checked-selectionmode", 4),
                          ("checkbox-checked-hover-selectionmode", 5), ("checkbox-checked-active-selectionmode", 6)):
            _save(center(big[idx], (41, 41)), gtk, name + ".png")
            n += 1
    rb = st.frames("Button.RadioButton")
    if len(rb) >= 8:
        for kind, base in (("unchecked", 0), ("checked", 4), ("mixed", 0)):
            for si, s in enumerate(sfx):
                c = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                c.alpha_composite(rb[base + si], (1, 1))
                _save(c, gtk, "radio-%s%s.png" % (kind, s))
                n += 1

    # --- push buttons and progress bar (used by css overrides) -------------
    btn = st.frames("Button.PushButton")
    for i, name in enumerate(("normal", "hover", "pressed", "disabled", "default")):
        if i < len(btn):
            _save(btn[i], gtk, "xp-button-%s.png" % name)
            n += 1
    chunk = st.frames("Progress.Chunk")
    track = st.frames("Progress.Bar")
    if chunk:
        _save(chunk[0], gtk, "xp-progress-chunk.png")
    if track:
        _save(track[0], gtk, "xp-progress-track.png")

    # --- scroll bars ----------------------------------------------------------
    arrows = st.frames("ScrollBar.ArrowBtn")
    glyph_img = st.bitmap("BLUE_SCROLLARROWGLYPHS_BMP") if variant == "blue" else None
    glyphs = []
    if glyph_img is not None:
        gh = glyph_img.height // 16
        glyphs = [glyph_img.crop((0, i * gh, glyph_img.width, (i + 1) * gh)) for i in range(16)]
    if len(arrows) >= 16:
        for di, base in enumerate(("top-stepper", "bottom-stepper", "left-stepper", "right-stepper")):
            for si, s in enumerate(("", "-hover", "-active")):
                idx = di * 4 + si
                img = compose(arrows[idx], glyphs[idx] if len(glyphs) > idx else None)
                _save(center(img, (17, 17)), gtk, base + s + ".png")
                n += 1
    for orient, part, grip, canvas, gcanvas, bgbox in (
            ("vert", "Scrollbar.ThumbBtnVert", "Scrollbar.GripperVert", (17, 22), (9, 10), (4, 5, 11, 17)),
            ("horz", "Scrollbar.ThumbBtnHorz", "Scrollbar.GripperHorz", (22, 17), (10, 9), (5, 4, 17, 11))):
        th = st.frames(part)
        gr = st.frames(grip)
        for si, s in enumerate(("", "-hover", "-active")):
            if si < len(th):
                img = nine(th[si], st.margins(part), (canvas[0] - (2 if orient == "vert" else 0),
                                                      canvas[1] - (2 if orient == "horz" else 0)))
                _save(center(img, canvas), gtk, "scrollbar-slider-%s%s.png" % (orient, s))
                bw, bh = (7, 12) if orient == "vert" else (12, 7)
                mid = th[si].crop((th[si].width // 2 - 1, th[si].height // 2 - 1,
                                   th[si].width // 2 + 1, th[si].height // 2 + 1)).resize((bw, bh))
                _save(mid, gtk, "slider-bg-%s%s.png" % (orient, s))
                n += 2
            if si < len(gr):
                _save(center(gr[si], gcanvas), gtk, "handle-%s%s.png" % (orient, s))
                n += 1
    sv = st.frames("Scrollbar.LowerTrackVert")
    if sv:
        f = sv[0]
        _save(f.crop((0, f.height // 2, f.width, f.height // 2 + 1)), gtk, "trough-scrollbar-vert.png")
    sh = st.frames("Scrollbar.LowerTrackHorz")
    if sh:
        f = sh[0]
        _save(f.crop((f.width // 2, 0, f.width // 2 + 1, f.height)), gtk, "trough-scrollbar-horz.png")

    # --- trackbars ------------------------------------------------------------
    order = {"": 0, "-hover": 1, "-active": 2, "-insensitive": 4}
    for part, name, size in (("TrackBar.ThumbBottom", "slider-horz-scale-has-marks-below", (11, 21)),
                             ("TrackBar.ThumbTop", "slider-horz-scale-has-marks-above", (11, 21)),
                             ("TrackBar.Thumb", "slider-horz", (11, 22)),
                             ("TrackBar.ThumbRight", "slider-vert-scale-has-marks-below", (21, 11)),
                             ("TrackBar.ThumbLeft", "slider-vert-scale-has-marks-above", (21, 11)),
                             ("TrackBar.ThumbVert", "slider-vert", (22, 11))):
        fr = st.frames(part)
        for s, idx in order.items():
            if idx < len(fr):
                _save(center(fr[idx], size), gtk, "%s%s.png" % (name, s))
                n += 1
    tr = st.frames("TrackBar.Track")
    if tr:
        _save(tr[0].crop((0, 0, 5, 4)), gtk, "trough-horz.png")
        _save(tr[0].crop((0, 0, 4, 5)), gtk, "trough-vert.png")

    # --- title bar and window frame -------------------------------------------
    cap = st.frames("Window.Caption")
    btn_bg = st.frames("Window.MaxButton")
    close_bg = st.frames("Window.CloseButton")
    glyph_res = {"close": "BLUE_CLOSEGLYPH_BMP", "minimize": "BLUE_MINIMIZEGLYPH_BMP",
                 "maximize": "BLUE_MAXIMIZEGLYPH_BMP", "restore": "BLUE_RESTOREGLYPH_BMP"}
    glyph_frames = {}
    for kind, res in glyph_res.items():
        img = st.bitmap(res) if variant == "blue" else None
        if img is not None:
            h = img.height // 8
            glyph_frames[kind] = [img.crop((0, i * h, img.width, (i + 1) * h)) for i in range(8)]

    def button(kind, idx):
        bgs = close_bg if kind == "close" else btn_bg
        if len(bgs) <= idx:
            return None
        g = glyph_frames.get(kind)
        return compose(bgs[idx], g[idx] if g and len(g) > idx else None)

    for kind in ("close", "minimize", "maximize", "restore"):
        for name, idx in (("normal", 0), ("hover", 1), ("active", 2), ("backdrop", 4), ("backdrop-hover", 5)):
            img = button(kind, idx)
            if img is not None:
                _save(img.resize((21, 21)), gtk, "%s-%s.png" % (kind, name))
                n += 1
    xf = {"close": "close", "hide": "minimize", "maximize": "maximize", "maximize-toggled": "restore"}
    for fname, kind in xf.items():
        for st_name, idx in (("active", 0), ("inactive", 4), ("prelight", 1), ("pressed", 2)):
            img = button(kind, idx)
            if img is not None:
                _save(img, wm, "%s-%s.png" % (fname, st_name))
                n += 1
    if len(cap) >= 2:
        W, H = cap[0].size
        corner = 8
        for (state, fr), focus in zip((("active", cap[0]), ("inactive", cap[1])), ("focused", "unfocused")):
            _save(fr.crop((0, 0, corner, H)), wm, "top-left-%s.png" % state)
            _save(fr.crop((W - corner, 0, W, H)), wm, "top-right-%s.png" % state)
            mid = fr.crop((W // 2 - 1, 0, W // 2 + 1, H))
            for i in range(1, 6):
                _save(mid, wm, "title-%d-%s.png" % (i, state))
            _save(fr.crop((W // 2, 0, W // 2 + 1, H)), gtk, "titlebar-%s-middle.png" % focus)
            n += 8
    for part, name in (("Window.FrameLeft", "left"), ("Window.FrameRight", "right")):
        fr = st.frames(part)
        for state, idx in (("active", 0), ("inactive", 1)):
            if idx < len(fr):
                f = fr[idx]
                _save(f.crop((0, f.height // 2 - 4, f.width, f.height // 2 + 4)), wm, "%s-%s.png" % (name, state))
                n += 1
    fb = st.frames("Window.FrameBottom")
    side_w = st.frames("Window.FrameLeft")[0].width if st.frames("Window.FrameLeft") else 4
    for state, idx in (("active", 0), ("inactive", 1)):
        if idx < len(fb):
            f = fb[idx]
            _save(f.crop((f.width // 2 - 4, 0, f.width // 2 + 4, f.height)), wm, "bottom-%s.png" % state)
            _save(f.crop((0, 0, side_w, f.height)), wm, "bottom-left-%s.png" % state)
            _save(f.crop((f.width - side_w, 0, f.width, f.height)), wm, "bottom-right-%s.png" % state)
            n += 3
    with open(os.path.join(wm, "themerc"), "w") as f:
        f.write("""# Whistler window frame from the user's own XP visual style
active_text_color=#FFFFFF
active_text_shadow_color=#0A1864
title_shadow_active=true
inactive_text_color=#D8E4F8
title_shadow_inactive=false
full_width_title=true
title_vertical_offset_active=1
title_vertical_offset_inactive=1
title_horizontal_offset=3
button_offset=5
button_spacing=2
show_app_icon=true
maximized_offset=4
""")

    # --- taskbar, start button, tray, start menu --------------------------------
    tb = st.frames("TaskBar.BackgroundBottom")
    if tb:
        _save(nine(tb[0], st.margins("TaskBar.BackgroundBottom"), (tb[0].width, 30)).crop((0, 0, 20, 30)),
              pnl, "taskbar.png")
        n += 1
    tray = st.frames("TrayNotifyHoriz::TrayNotify.Background")
    if tray:
        t = nine(tray[0], st.margins("TrayNotifyHoriz::TrayNotify.Background"), (tray[0].width, 30))
        _save(t.crop((t.width - 30, 0, t.width - 10, 30)), pnl, "tray.png")
        alpha = t.split()[3]
        x0 = next((x for x in range(t.width) if alpha.crop((x, 0, x + 1, 30)).getextrema()[1] > 0), 0)
        _save(t.crop((x0, 0, x0 + 10, 30)), pnl, "tray-edge.png")
        n += 2
    sb = st.frames("Start::Button")
    for i, name in enumerate(("normal", "hover", "pressed")):
        if i < len(sb):
            _save(nine(sb[i], st.margins("Start::Button"), (sb[i].width, 30)), pnl, "start-%s.png" % name)
            n += 1
    task = st.frames("TaskBand::Toolbar.Button")
    for i, name in ((0, "normal"), (1, "hover"), (4, "active"), (5, "active-hover")):
        if i < len(task):
            _save(nine(task[i], st.margins("TaskBand::Toolbar.Button"), (160, 25)), pnl, "xp-task-%s.png" % name)
            n += 1
    for part, name, size in (("StartPanel.UserPane", "xp-startmenu-top.png", (380, None)),
                             ("StartPanel.Logoff", "xp-startmenu-bottom.png", (380, None)),
                             ("StartPanel.ProgList", "xp-startmenu-left.png", (190, 1000)),
                             ("StartPanel.PlacesList", "xp-startmenu-right.png", (190, 1000)),
                             ("StartPanel.ProgListSeparator", "xp-startmenu-sep-left.png", (None, None)),
                             ("StartPanel.PlacesListSeparator", "xp-startmenu-sep-right.png", (None, None)),
                             ("StartPanel.MorePrograms", "xp-startmenu-allprograms.png", (None, None)),
                             ("StartPanel.UserPicture", "xp-startmenu-userpic.png", (None, None))):
        fr = st.frames(part)
        if fr:
            img = fr[0]
            w = size[0] or img.width
            h = size[1] or img.height
            _save(nine(img, st.margins(part), (w, h)), pnl, name)
            n += 1

    # --- stylesheets that switch widgets to the imported bitmaps ---------------
    css_dir = os.path.join(out, "css")
    os.makedirs(css_dir, exist_ok=True)
    start_font = _font_css(st.font("Start::Button")) or "font-style: italic;"
    shadow = st.color("Start::Button", "textshadowcolor") or "#454C10"
    bm = st.margins("Button.PushButton")
    with open(os.path.join(css_dir, "gtk-overrides.css"), "w") as f:
        f.write("""/* Generated from the user's own Windows XP visual style. */
#xp-start-button,
.xfce4-panel.panel #xp-start-button {
  min-width: 99px;
  padding: 0 24px 0 10px;
}
#xp-start-label {
  %(font)s
  text-shadow: 2px 2px 0 %(shadow)s;
}
.xfce4-panel.panel .tasklist button,
.xfce4-panel.panel .tasklist button.flat {
  border-image: none;
  border-width: 0;
  border-radius: 0;
  padding: 0 6px;
  background-image: url("%(A)s/panel/xp-task-normal.png");
  background-size: 100%% 100%%;
  background-repeat: no-repeat;
}
.xfce4-panel.panel .tasklist button:hover {
  border-image: none;
  background-image: url("%(A)s/panel/xp-task-hover.png");
}
.xfce4-panel.panel .tasklist button:active,
.xfce4-panel.panel .tasklist button:checked {
  border-image: none;
  background-image: url("%(A)s/panel/xp-task-active.png");
}
.xfce4-panel.panel .tasklist button:active:hover,
.xfce4-panel.panel .tasklist button:checked:hover {
  border-image: none;
  background-image: url("%(A)s/panel/xp-task-active-hover.png");
}
button.text-button:not(.flat):not(.titlebutton),
button.text-button.default:not(.flat) {
  border-style: solid;
  border-width: 3px;
  border-radius: 0;
  border-image: url("%(A)s/gtk/xp-button-normal.png") %(bt)d %(br)d %(bb)d %(bl)d / 3px stretch;
  background-image: none;
  background-color: transparent;
  box-shadow: none;
}
button.text-button:not(.flat):not(.titlebutton):hover {
  border-image: url("%(A)s/gtk/xp-button-hover.png") %(bt)d %(br)d %(bb)d %(bl)d / 3px stretch;
  background-image: none;
  box-shadow: none;
}
button.text-button:not(.flat):not(.titlebutton):active,
button.text-button:not(.flat):not(.titlebutton):checked {
  border-image: url("%(A)s/gtk/xp-button-pressed.png") %(bt)d %(br)d %(bb)d %(bl)d / 3px stretch;
  background-image: none;
  box-shadow: none;
}
button.text-button:not(.flat):not(.titlebutton):disabled {
  border-image: url("%(A)s/gtk/xp-button-disabled.png") %(bt)d %(br)d %(bb)d %(bl)d / 3px stretch;
  background-image: none;
}
button.text-button.default:not(.flat):not(:hover):not(:active) {
  border-image: url("%(A)s/gtk/xp-button-default.png") %(bt)d %(br)d %(bb)d %(bl)d / 3px stretch;
}
progressbar progress {
  background-color: transparent;
  background-image: url("%(A)s/gtk/xp-progress-chunk.png");
  background-repeat: repeat-x;
  background-size: auto 100%%;
  border: none;
  border-radius: 0;
}
""" % {"font": start_font, "shadow": shadow, "A": A, "bl": bm[0], "br": bm[1], "bt": bm[2], "bb": bm[3]})
    user_font = _font_css(st.font("StartPanel.UserPane"))
    user_shadow = st.color("StartPanel.UserPane", "textshadowcolor") or "#09428B"
    places_color = st.color("StartPanel.PlacesList") or "#0A246A"
    prog_color = st.color("StartPanel.ProgList") or "#373738"
    with open(os.path.join(css_dir, "startmenu.css"), "w") as f:
        f.write("""/* Generated from the user's own Windows XP visual style. */
#sm-header {
  background-color: transparent;
  background-image: url("%(A)s/panel/xp-startmenu-top.png");
  background-size: 100%% 100%%;
}
#sm-username {
  %(user_font)s
  text-shadow: 2px 2px 0 %(user_shadow)s;
}
#sm-orange-line {
  min-height: 0;
  background-image: none;
}
#sm-left {
  background-color: #FFFFFF;
  background-image: url("%(A)s/panel/xp-startmenu-left.png");
  background-size: 100%% auto;
  background-repeat: no-repeat;
  background-position: top center;
}
#sm-right {
  background-color: #D3E5FA;
  background-image: url("%(A)s/panel/xp-startmenu-right.png");
  background-size: 100%% auto;
  background-repeat: no-repeat;
  background-position: top center;
  border-left: none;
}
.sm-right-item label { color: %(places)s; }
#sm-left .sm-item label { color: %(prog)s; }
.sm-sep-left {
  background-image: url("%(A)s/panel/xp-startmenu-sep-left.png");
  background-size: 100%% 100%%;
  min-height: 2px;
}
.sm-sep-right {
  background-image: url("%(A)s/panel/xp-startmenu-sep-right.png");
  background-size: 100%% 100%%;
  min-height: 2px;
}
#sm-footer {
  background-color: transparent;
  background-image: url("%(A)s/panel/xp-startmenu-bottom.png");
  background-size: 100%% 100%%;
}
""" % {"A": A, "user_font": user_font, "user_shadow": user_shadow, "places": places_color, "prog": prog_color})
    log("theme: %d images from %s" % (n, os.path.basename(msstyles)))
    return n
