#!/usr/bin/env bash
# Runs inside the whistler-builder container (x86_64 Arch).
#   container-build.sh packages [name...]   build AUR + local packages into /work/repo
#   container-build.sh iso                  build the live ISO from /work/repo
#   container-build.sh all
# Env: WHISTLER_FAST=1 (quicker, larger squashfs), WHISTLER_DEBUG=1 (sshd + SSH_PUBKEY)
set -euo pipefail

SRC=/src
WORK=/work
REPO=$WORK/repo
BUILD=$WORK/pkgbuild
AUR_PACKAGES=()
LOCAL_PACKAGES=(whistler-artwork whistler-desktop whistler-xp-originals)
BUILDNUM=${BUILDNUM:-$(date +%y%m%d%H%M)}

log() { printf '\033[1;34m==> %s\033[0m\n' "$*"; }

setup_repo() {
    mkdir -p "$REPO" "$BUILD"
    chown -R builder:builder "$BUILD"
    if [ ! -f "$REPO/whistler.db.tar.zst" ]; then
        # an empty repository database
        bsdtar --zstd -cf "$REPO/whistler.db.tar.zst" -T /dev/null
        ln -sf whistler.db.tar.zst "$REPO/whistler.db"
    fi
    if ! grep -q '^\[whistler\]' /etc/pacman.conf; then
        # local repo first so our builds win
        awk -v repo="$REPO" 'done == 0 && /^\[(cachyos|core)\]/ {
                print "[whistler]\nSigLevel = Optional TrustAll\nServer = file://" repo "\n"; done = 1 }
            { print }' /etc/pacman.conf > /etc/pacman.conf.new && mv /etc/pacman.conf.new /etc/pacman.conf
    fi
    pacman -Sy --noconfirm >/dev/null
}

add_to_repo() {
    local f
    for f in "$@"; do
        cp "$f" "$REPO/"
        repo-add -q -R "$REPO/whistler.db.tar.zst" "$REPO/$(basename "$f")"
    done
    pacman -Sy --noconfirm >/dev/null
}

build_aur() {
    local name=$1 dir="$BUILD/aur-$1"
    if ls "$REPO/$name"-*.pkg.tar.zst >/dev/null 2>&1; then
        log "AUR $name already built"
        return
    fi
    log "Building AUR package $name"
    rm -rf "$dir"
    sudo -u builder git clone -q "https://aur.archlinux.org/$name.git" "$dir"
    (cd "$dir" && sudo -u builder makepkg -s --noconfirm --needed -f)
    add_to_repo "$dir"/*.pkg.tar.zst
}

build_local() {
    local name=$1 dir="$BUILD/$1"
    log "Building $name (build $BUILDNUM)"
    rm -rf "$dir"
    cp -r "$SRC/packages/$name" "$dir"
    sed -i "s/^pkgrel=.*/pkgrel=$BUILDNUM/" "$dir/PKGBUILD"
    chown -R builder:builder "$dir"
    # install build-time needs only; runtime deps may be other local packages
    local mk
    mk=$(cd "$dir" && set +u && startdir=$PWD && source ./PKGBUILD && echo "${makedepends[@]}")
    [ -z "$mk" ] || pacman -S --noconfirm --needed --asdeps $mk >/dev/null
    (cd "$dir" && sudo -u builder makepkg -d --noconfirm -f)
    rm -f "$REPO/$name"-[0-9]*.pkg.tar.zst
    add_to_repo "$dir"/"$name"-[0-9]*.pkg.tar.zst
    rm -f /var/cache/pacman/pkg/"$name"-[0-9]*
}

stage_packages() {
    setup_repo
    local names=("$@")
    if [ ${#names[@]} -eq 0 ]; then
        for a in ${AUR_PACKAGES[@]+"${AUR_PACKAGES[@]}"}; do build_aur "$a"; done
        names=("${LOCAL_PACKAGES[@]}")
    fi
    for n in "${names[@]}"; do
        if [ -d "$SRC/packages/$n" ]; then build_local "$n"; else build_aur "$n"; fi
    done
}

stage_iso() {
    setup_repo
    local profile="$WORK/profile"
    log "Preparing archiso profile"
    rm -rf "$profile"
    cp -a "$SRC/profile" "$profile"
    sed -i "s#@REPO@#$REPO#" "$profile/pacman.conf"
    if [ "${WHISTLER_FAST:-0}" = 1 ]; then
        sed -i "s/'-Xcompression-level' '[0-9]*'/'-Xcompression-level' '3'/" "$profile/profiledef.sh"
    fi
    if [ "${WHISTLER_DEBUG:-0}" = 1 ]; then
        log "Debug build: enabling sshd"
        echo openssh >> "$profile/packages.x86_64"
        ln -sf /usr/lib/systemd/system/sshd.service \
            "$profile/airootfs/etc/systemd/system/multi-user.target.wants/sshd.service"
        install -d -m700 "$profile/airootfs/root/.ssh"
        printf '%s\n' "${SSH_PUBKEY:-}" > "$profile/airootfs/root/.ssh/authorized_keys"
        install -d "$profile/airootfs/etc/ssh/sshd_config.d"
        printf 'PermitRootLogin prohibit-password\n' > "$profile/airootfs/etc/ssh/sshd_config.d/10-debug.conf"
    fi
    # Ship our packages on the medium as an offline repository, so optional
    # add-ons (whistler-xp-originals) can be installed later without network.
    install -d "$profile/airootfs/opt/whistler/repo"
    cp "$REPO"/*.pkg.tar.zst "$profile/airootfs/opt/whistler/repo/"
    repo-add -q "$profile/airootfs/opt/whistler/repo/whistler.db.tar.zst" "$profile"/airootfs/opt/whistler/repo/*.pkg.tar.zst
    # Boot menu splash comes from the artwork package.
    local art
    art=$(ls "$REPO"/whistler-artwork-[0-9]*.pkg.tar.zst | head -1)
    bsdtar -xOf "$art" usr/share/whistler/logos/syslinux-splash.png > "$profile/syslinux/splash.png"
    rm -f /var/cache/pacman/pkg/whistler-*
    rm -rf "$WORK/archiso-tmp"
    mkdir -p "$WORK/out"
    log "Running mkarchiso"
    mkarchiso -v -r -w "$WORK/archiso-tmp" -o "$WORK/out" "$profile"
    ls -lh "$WORK/out"
}

case "${1:-all}" in
    packages) shift; stage_packages "$@" ;;
    iso) stage_iso ;;
    all) stage_packages; stage_iso ;;
    *) echo "unknown stage $1" >&2; exit 2 ;;
esac
