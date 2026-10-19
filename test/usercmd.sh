#!/usr/bin/env bash
# Run a command inside the VM's desktop session as the live user.
cd "$(dirname "$0")/.."
cmd="$*"
exec test/ssh.sh "sudo -u ${VMUSER:-user} env DISPLAY=:0 XAUTHORITY=/home/${VMUSER:-user}/.Xauthority DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/${VMUID:-1000}/bus XDG_RUNTIME_DIR=/run/user/${VMUID:-1000} XDG_CONFIG_DIRS=/etc/xdg/whistler:/etc/xdg XDG_DATA_DIRS=/usr/share/whistler/xdg-data:/usr/local/share:/usr/share GTK_OVERLAY_SCROLLING=0 XDG_CURRENT_DESKTOP=XFCE XDG_MENU_PREFIX=xfce- XDG_SESSION_DESKTOP=whistler DESKTOP_SESSION=whistler bash -lc $(printf %q "$cmd")"
