#!/usr/bin/env python3
"""Compose the Whistler icon SVG sources (icons/src) from the drawing code here.

usage: compose.py [SRC_DIR] [NAME_REGEX]

Every icon is drawn once on a 48x48 grid and written as <name>.svg plus
pixel-snapped variants <name>.16/.22/.24/.32.svg that gen/build_icons.py picks
for those sizes. Without NAME_REGEX all existing sources are replaced, so edit
the drawing code rather than the generated SVGs. Only the standard library is
needed.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Ctx  # noqa: E402
from registry import ICONS  # noqa: E402
import icons_places  # noqa: E402,F401
import icons_devices  # noqa: E402,F401
import icons_apps  # noqa: E402,F401
import icons_mime  # noqa: E402,F401
import icons_actions  # noqa: E402,F401
import icons_status  # noqa: E402,F401

VARIANTS = (16, 22, 24, 32)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "src")
    rx = re.compile(sys.argv[2]) if len(sys.argv) > 2 else None
    if rx is None and os.path.isdir(out):
        for ctx in os.listdir(out):
            cdir = os.path.join(out, ctx)
            if os.path.isdir(cdir):
                for fn in os.listdir(cdir):
                    if fn.endswith(".svg"):
                        os.remove(os.path.join(cdir, fn))
    n = 0
    for (ctx, name), fn in sorted(ICONS.items()):
        if rx and not rx.search("%s/%s" % (ctx, name)):
            continue
        dd = os.path.join(out, ctx)
        os.makedirs(dd, exist_ok=True)
        for v in (48,) + VARIANTS:
            c = Ctx(v)
            fn(c)
            fn_out = name + ".svg" if v == 48 else "%s.%d.svg" % (name, v)
            with open(os.path.join(dd, fn_out), "w") as fh:
                fh.write(c.svg())
        n += 1
    print("wrote %d icons" % n)


if __name__ == "__main__":
    main()
