#!/usr/bin/env bash
# Build Whistler XP on any x86_64 Docker host.
#   ./build.sh [all|packages [pkg...]|iso|clean] [--fast] [--debug]
# The finished ISO is copied to ./out/ (older ISOs there are removed).
#
# On macOS an isolated Colima profile "winxp" is used, kept entirely under
# $WHISTLER_HOME (default: the directory containing this script) so its disk
# image lives next to the sources; the global Docker context is left alone.
set -euo pipefail
cd "$(dirname "$0")"

STAGE=all
ARGS=()
for a in "$@"; do
    case "$a" in
        --fast) export WHISTLER_FAST=1 ;;
        --debug) export WHISTLER_DEBUG=1 ;;
        all|packages|iso|clean) STAGE=$a ;;
        *) ARGS+=("$a") ;;
    esac
done

if [ "$(uname -s)" = Darwin ]; then
    export COLIMA_HOME="${WHISTLER_HOME:-$PWD}/colima"
    mkdir -p "$COLIMA_HOME"   # colima falls back to ~/.colima if this does not exist
    export DOCKER_HOST="unix://$COLIMA_HOME/winxp/docker.sock"
    if ! colima status winxp >/dev/null 2>&1; then
        [ "$(uname -m)" = x86_64 ] || echo "warning: building x86_64 on $(uname -m) runs under emulation (slow)" >&2
        colima start winxp --cpu "${WHISTLER_CPUS:-2}" --memory "${WHISTLER_MEM:-8}" --disk "${WHISTLER_DISK:-30}" --vm-type vz
        docker context use default >/dev/null 2>&1 || true
    fi
fi

if [ "${WHISTLER_DEBUG:-0}" = 1 ]; then
    key=test/ssh/id_ed25519
    [ -f "$key" ] || { mkdir -p test/ssh; ssh-keygen -q -t ed25519 -N '' -f "$key"; }
    export SSH_PUBKEY="$(cat "$key.pub")"
fi

docker volume create whistler-work >/dev/null
docker volume create whistler-pkgcache >/dev/null

if [ "$STAGE" = clean ]; then
    docker run --rm -v whistler-work:/work -v whistler-pkgcache:/var/cache/pacman/pkg busybox \
        sh -c 'rm -rf /work/archiso-tmp /work/pkgbuild /work/out; find /var/cache/pacman/pkg -name "whistler-*" -delete'
    docker image prune -f >/dev/null
    docker builder prune -af >/dev/null
    exit 0
fi

docker build -q --platform linux/amd64 -t whistler-builder docker/ >/dev/null

docker run --rm --privileged --platform linux/amd64 \
    -v "$PWD":/src:ro -v whistler-work:/work -v whistler-pkgcache:/var/cache/pacman/pkg \
    -e WHISTLER_FAST -e WHISTLER_DEBUG -e SSH_PUBKEY \
    whistler-builder bash /src/scripts/container-build.sh "$STAGE" ${ARGS[@]+"${ARGS[@]}"}

if [ "$STAGE" != packages ]; then
    mkdir -p out
    rm -f out/*.iso
    docker run --rm --platform linux/amd64 -v whistler-work:/work -v "$PWD/out":/out whistler-builder \
        sh -c 'mv /work/out/*.iso /out/ && rm -rf /work/out /work/archiso-tmp'
    ls -lh out/*.iso
fi
