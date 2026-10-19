#!/usr/bin/env python3
"""Build the Whistler icon theme from its SVG sources.

usage:
  build_icons.py SRC_DIR OUT_DIR
      Render SRC_DIR/<context>/<name>.svg into OUT_DIR/Whistler/ (fixed-size
      PNGs, scalable SVGs, alias symlinks, index.theme).

  build_icons.py [SRC_DIR] --preview OUT.png [--only REGEX] [--sizes 48,32,16] [--zoom N]
      Render a labelled contact sheet of every icon on white and on XP blue.

Size-specific sources: next to <name>.svg there may be <name>.<N>.svg (for
example folder.16.svg, folder.24.svg). For a target size the exact variant is
used when present, otherwise the nearest larger variant below 48, otherwise the
main drawing.

Aliases come from SRC_DIR/../aliases.txt (override with --aliases), one per
line: "context/alias-name target-name" (or "context/alias target-context/target").
Every icon and alias also gets a "<name>-symbolic" link in the fixed-size
directories. These are deliberately PNG-only: GTK recolours any file named
*-symbolic.svg to a single foreground colour, which would flatten the full-colour
artwork, while *-symbolic.png is drawn as is.

Only cairosvg, Pillow and the standard library are used.
"""
import argparse
import os
import re
import shutil
import sys

import cairosvg

THEME = "Whistler"
SIZES = (16, 22, 24, 32, 48)
CONTEXTS = {
    "actions": "Actions",
    "apps": "Applications",
    "devices": "Devices",
    "mimetypes": "MimeTypes",
    "places": "Places",
    "status": "Status",
}
INHERITS = "whistler-xp-originals,AdwaitaLegacy,Adwaita,hicolor"
VARIANT_RE = re.compile(r"^(?P<name>.+)\.(?P<size>\d+)\.svg$")
XP_BLUE = (0x24, 0x5E, 0xDC)


# ---------------------------------------------------------------- sources

def scan_sources(src):
    """Return {(context, name): {"main": path, "variants": {size: path}}}."""
    icons = {}
    for ctx in sorted(os.listdir(src)):
        cdir = os.path.join(src, ctx)
        if not os.path.isdir(cdir):
            continue
        if ctx not in CONTEXTS:
            sys.exit("unknown icon context directory: %s" % cdir)
        for fn in sorted(os.listdir(cdir)):
            if not fn.endswith(".svg"):
                continue
            path = os.path.join(cdir, fn)
            m = VARIANT_RE.match(fn)
            if m:
                entry = icons.setdefault((ctx, m.group("name")), {"main": None, "variants": {}})
                entry["variants"][int(m.group("size"))] = path
            else:
                entry = icons.setdefault((ctx, fn[:-4]), {"main": None, "variants": {}})
                entry["main"] = path
    for (ctx, name), entry in icons.items():
        if entry["main"] is None:
            sys.exit("size variants without a main drawing: %s/%s.svg" % (ctx, name))
    return icons


def pick_source(entry, size):
    """The SVG to render at a given pixel size."""
    variants = entry["variants"]
    if size in variants:
        return variants[size]
    larger = sorted(s for s in variants if size < s < 48)
    if larger:
        return variants[larger[0]]
    return entry["main"]


def render(svg_path, size):
    return cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)


def parse_aliases(path, icons):
    """Return [(context, alias, target_context, target_name)]."""
    if not path or not os.path.exists(path):
        return []
    by_name = {}
    for ctx, name in icons:
        by_name.setdefault(name, []).append(ctx)
    out, seen = [], set()
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2 or "/" not in parts[0]:
                sys.exit("%s:%d: expected 'context/alias target'" % (path, lineno))
            actx, alias = parts[0].split("/", 1)
            if actx not in CONTEXTS:
                sys.exit("%s:%d: unknown context %r" % (path, lineno, actx))
            target = parts[1]
            if "/" in target:
                tctx, tname = target.split("/", 1)
                if (tctx, tname) not in icons:
                    sys.exit("%s:%d: no icon %s" % (path, lineno, target))
            else:
                ctxs = by_name.get(target)
                if not ctxs:
                    sys.exit("%s:%d: no icon named %r" % (path, lineno, target))
                tctx, tname = (actx if actx in ctxs else ctxs[0]), target
            if (actx, alias) in icons:
                sys.exit("%s:%d: alias %s/%s shadows a real icon" % (path, lineno, actx, alias))
            if (actx, alias) in seen:
                sys.exit("%s:%d: duplicate alias %s/%s" % (path, lineno, actx, alias))
            seen.add((actx, alias))
            out.append((actx, alias, tctx, tname))
    return out


# ------------------------------------------------------------------ build

def link(target_ctx, target_file, link_ctx, link_path):
    rel = target_file if target_ctx == link_ctx else os.path.join("..", target_ctx, target_file)
    if os.path.lexists(link_path):
        os.remove(link_path)
    os.symlink(rel, link_path)


def write_index(root, dirs):
    lines = [
        "[Icon Theme]",
        "Name=%s" % THEME,
        "Comment=Original XP-era icons for Whistler XP",
        "Inherits=%s" % INHERITS,
        "Example=folder",
        "Directories=%s" % ",".join(d for d, _s, _c in dirs),
        "",
    ]
    for d, size, ctx in dirs:
        lines.append("[%s]" % d)
        lines.append("Context=%s" % CONTEXTS[ctx])
        if size == "scalable":
            lines += ["Size=48", "MinSize=8", "MaxSize=512", "Type=Scalable"]
        else:
            lines += ["Size=%d" % size, "Type=Fixed"]
        lines.append("")
    with open(os.path.join(root, "index.theme"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def build(src, out, aliases_path):
    icons = scan_sources(src)
    aliases = parse_aliases(aliases_path, icons)
    root = os.path.join(out, THEME)
    if os.path.exists(root):
        shutil.rmtree(root)
    used = sorted({ctx for ctx, _ in icons} | {a[0] for a in aliases})
    dirs = [("%d/%s" % (s, c), s, c) for s in SIZES for c in used]
    dirs += [("scalable/%s" % c, "scalable", c) for c in used]
    for d, _s, _c in dirs:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    for (ctx, name), entry in sorted(icons.items()):
        for size in SIZES:
            png = render(pick_source(entry, size), size)
            with open(os.path.join(root, str(size), ctx, name + ".png"), "wb") as fh:
                fh.write(png)
        shutil.copyfile(entry["main"], os.path.join(root, "scalable", ctx, name + ".svg"))

    names = {}  # (ctx, name) -> (target ctx, target name)
    for key in icons:
        names[key] = key
    for actx, alias, tctx, tname in aliases:
        names[(actx, alias)] = (tctx, tname)
        for size in SIZES:
            link(tctx, tname + ".png", actx, os.path.join(root, str(size), actx, alias + ".png"))
        link(tctx, tname + ".svg", actx, os.path.join(root, "scalable", actx, alias + ".svg"))

    nsym = 0
    for (ctx, name), (tctx, tname) in sorted(names.items()):
        if name.endswith("-symbolic") or (ctx, name + "-symbolic") in names:
            continue
        for size in SIZES:
            link(tctx, tname + ".png", ctx, os.path.join(root, str(size), ctx, name + "-symbolic.png"))
        nsym += 1

    write_index(root, dirs)
    print("%s: %d icons, %d aliases, %d symbolic links, sizes %s + scalable"
          % (root, len(icons), len(aliases), nsym, ",".join(map(str, SIZES))))


# ---------------------------------------------------------------- preview

def load_font(size):
    from PIL import ImageFont
    for name in ("DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def preview(src, out_png, only=None, sizes=(48, 32, 16), zoom=1, columns=None):
    import io

    from PIL import Image, ImageDraw

    icons = scan_sources(src)
    keys = sorted(icons, key=lambda k: (k[0], k[1]))
    if only:
        rx = re.compile(only)
        keys = [k for k in keys if rx.search("%s/%s" % k)]
    if not keys:
        sys.exit("no icons match")
    pad = 6
    strip_h = max(sizes) + 2 * pad
    cell_w = max(sum(sizes) + pad * (len(sizes) + 1), 132)
    label_h = 14
    cell_h = label_h + 2 * strip_h + 4
    if columns is None:
        columns = max(1, min(len(keys), 1600 // cell_w))
    font = load_font(11)
    hfont = load_font(14)

    rows = []  # list of ("header", ctx) or ("icons", [keys])
    for ctx in sorted({k[0] for k in keys}):
        rows.append(("header", ctx))
        group = [k for k in keys if k[0] == ctx]
        for i in range(0, len(group), columns):
            rows.append(("icons", group[i:i + columns]))
    header_h = 24
    W = columns * cell_w
    H = sum(header_h if kind == "header" else cell_h for kind, _ in rows)
    sheet = Image.new("RGB", (W, H), (236, 233, 216))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for kind, payload in rows:
        if kind == "header":
            draw.rectangle([0, y, W, y + header_h - 1], fill=(49, 106, 197))
            draw.text((8, y + 4), CONTEXTS[payload], fill="white", font=hfont)
            y += header_h
            continue
        for col, key in enumerate(payload):
            x0 = col * cell_w
            entry = icons[key]
            draw.text((x0 + 4, y + 1), key[1][:22], fill=(0, 0, 0), font=font)
            for row, bg in enumerate(((255, 255, 255), XP_BLUE)):
                sy = y + label_h + row * strip_h
                draw.rectangle([x0 + 2, sy, x0 + cell_w - 3, sy + strip_h - 1], fill=bg)
                x = x0 + pad
                for s in sizes:
                    png = render(pick_source(entry, s), s)
                    im = Image.open(io.BytesIO(png)).convert("RGBA")
                    sheet.paste(im, (x, sy + strip_h - pad - s), im)
                    x += s + pad
        y += cell_h
    if zoom > 1:
        sheet = sheet.resize((W * zoom, H * zoom), Image.NEAREST)
    sheet.save(out_png)
    print("%s: %d icons" % (out_png, len(keys)))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_src = os.path.join(here, "..", "icons", "src")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?", default=default_src, help="icon source directory (icons/src)")
    ap.add_argument("out", nargs="?", help="output directory; the theme goes to OUT/Whistler")
    ap.add_argument("--aliases", help="alias list (default: SRC/../aliases.txt)")
    ap.add_argument("--preview", metavar="OUT.png", help="render a contact sheet instead of building")
    ap.add_argument("--only", metavar="REGEX", help="preview only icons whose context/name matches")
    ap.add_argument("--sizes", default="48,32,16", help="preview sizes (default 48,32,16)")
    ap.add_argument("--zoom", type=int, default=1, help="nearest-neighbour zoom for the preview")
    ap.add_argument("--columns", type=int, help="preview columns")
    a = ap.parse_args()
    src = os.path.abspath(a.src)
    if a.preview:
        sizes = tuple(int(s) for s in a.sizes.split(","))
        preview(src, a.preview, a.only, sizes, a.zoom, a.columns)
        return
    if not a.out:
        ap.error("OUT_DIR is required unless --preview is given")
    aliases = a.aliases or os.path.join(src, "..", "aliases.txt")
    build(src, os.path.abspath(a.out), aliases)


if __name__ == "__main__":
    main()
