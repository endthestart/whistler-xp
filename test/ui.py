#!/usr/bin/env python3
"""Drive the test VM's desktop over VNC + SSH.

usage: ui.py COMMAND [args...]   (commands can be chained with '--')
  shot NAME                 save test/shots/NAME.png
  click X Y | dclick X Y | rclick X Y | move X Y
  key KEY                   e.g. alt-f4, ctrl-a, enter, super_l
  type TEXT
  wait SECONDS
  win TITLE                 print geometry "x y w h" of the first window matching TITLE
  clickwin TITLE DX DY      click relative to a window's client origin (negative = from right/bottom)
  run CMD                   run a shell command in the user's session (background)
  sh CMD                    run a shell command in the user's session and print output
"""
import os
import re
import shlex
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VNC = "127.0.0.1::5901"
VNCDO = os.environ.get("VNCDO", "vncdo")   # pip install vncdotool


def vnc(*args):
    subprocess.run([VNCDO, "-s", VNC] + [str(a) for a in args], check=True)


def user_sh(cmd, capture=True):
    r = subprocess.run([os.path.join(ROOT, "test", "usercmd.sh"), cmd], capture_output=capture, text=True)
    return r.stdout if capture else ""


def win(title):
    out = user_sh("xwininfo -root -tree")
    for line in out.splitlines():
        if '"' in line and title.lower() in line.split('"')[1].lower():
            m = re.search(r"(\d+)x(\d+)\+-?\d+\+-?\d+\s+\+(-?\d+)\+(-?\d+)", line)
            if m:
                w, h, x, y = map(int, m.groups())
                if w > 50 and h > 30:
                    return x, y, w, h
    return None


def main(argv):
    cmds = []
    cur = []
    for a in argv:
        if a == "--":
            cmds.append(cur)
            cur = []
        else:
            cur.append(a)
    if cur:
        cmds.append(cur)
    for c in cmds:
        op, args = c[0], c[1:]
        if op == "shot":
            path = os.path.join(ROOT, "test", "shots", args[0] + ".png")
            vnc("capture", path)
            print(path)
        elif op in ("click", "dclick", "rclick", "move"):
            x, y = args[0], args[1]
            if op == "move":
                vnc("move", x, y)
            elif op == "click":
                vnc("move", x, y, "click", 1)
            elif op == "rclick":
                vnc("move", x, y, "click", 3)
            else:
                vnc("move", x, y, "click", 1, "click", 1)
        elif op == "key":
            vnc("key", args[0])
        elif op == "type":
            vnc("type", " ".join(args))
        elif op == "wait":
            time.sleep(float(args[0]))
        elif op == "win":
            print(win(" ".join(args)))
        elif op == "clickwin":
            g = win(args[0])
            if g is None:
                print("window not found: %s" % args[0], file=sys.stderr)
                sys.exit(1)
            x, y, w, h = g
            dx, dy = int(args[1]), int(args[2])
            px = x + (dx if dx >= 0 else w + dx)
            py = y + (dy if dy >= 0 else h + dy)
            vnc("move", px, py, "click", 1)
        elif op == "run":
            user_sh("(nohup %s >/tmp/ui-run-$(id -u).log 2>&1 &)" % " ".join(args), capture=False)
        elif op == "sh":
            print(user_sh(" ".join(args)), end="")
        else:
            print("unknown command %s" % op, file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
