#!/usr/bin/env bash
# Capture the VM screen: test/shot.sh name  -> test/shots/name.png  (needs vncdotool)
cd "$(dirname "$0")/.."
"${VNCDO:-vncdo}" -s 127.0.0.1::5901 capture "test/shots/${1:-shot}.png" && echo "test/shots/${1:-shot}.png"
