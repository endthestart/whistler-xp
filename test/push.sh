#!/usr/bin/env bash
# Hot-sync whistler-desktop files into the running test VM (debug ISO).
cd "$(dirname "$0")/.."
F=packages/whistler-desktop/files
SSH="ssh -q -i test/ssh/id_ed25519 -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@127.0.0.1"
COPYFILE_DISABLE=1 tar --no-xattrs --no-mac-metadata -C "$F" -cf - python/whistler share/css bin help | $SSH '
set -e; d=$(mktemp -d); tar -C "$d" -xf -
rm -rf "$d"/python/whistler/__pycache__
cp -r "$d"/python/whistler/. /usr/lib/whistler/whistler/
cp -r "$d"/share/css/. /usr/share/whistler/css/
mkdir -p /usr/share/whistler/help; cp -r "$d"/help/. /usr/share/whistler/help/
for f in "$d"/bin/*; do case "$f" in */xfce4-session-logout) install -m755 "$f" /usr/local/bin/ ;; *) install -m755 "$f" /usr/bin/ ;; esac; done
rm -rf "$d"; echo pushed'
COPYFILE_DISABLE=1 tar --no-xattrs --no-mac-metadata -C packages/whistler-xp-originals/files/python -cf - whistler_originals \
  | $SSH '[ -d /usr/lib/whistler/whistler_originals ] || exit 0; d=$(mktemp -d); tar -C "$d" -xf -; rm -rf "$d"/whistler_originals/__pycache__; cp -r "$d"/whistler_originals/. /usr/lib/whistler/whistler_originals/; rm -rf "$d"; echo originals pushed'
if [ -n "${1:-}" ]; then
    COPYFILE_DISABLE=1 tar --no-xattrs --no-mac-metadata -C packages/whistler-artwork -cf - theme | $SSH 'd=$(mktemp -d); tar -C "$d" -xf -; cp "$d"/theme/whistler-panel.css /usr/share/themes/Whistler/gtk-3.20/; rm -rf "$d"; echo theme pushed'
fi
