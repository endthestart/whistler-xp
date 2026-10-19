#!/usr/bin/env bash
# Boot a Whistler ISO in QEMU. Display on VNC 127.0.0.1:5901, SSH on 127.0.0.1:2222.
#   test/run-vm.sh [--bios] [--disk-only] [--res WxH] [iso]
set -euo pipefail
cd "$(dirname "$0")/.."
FIRMWARE=uefi
BOOT=cdrom
RES=1024x768
ISO=""
while [ $# -gt 0 ]; do
    case "$1" in
        --bios) FIRMWARE=bios ;;
        --disk-only) BOOT=disk ;;
        --res) RES=$2; shift ;;
        *) ISO=$1 ;;
    esac
    shift
done
ISO=${ISO:-$(ls -t out/*.iso 2>/dev/null | head -1)}
DISK=test/disk.qcow2
[ -f "$DISK" ] || qemu-img create -q -f qcow2 "$DISK" 30G
SHARE=$(dirname "$(dirname "$(command -v qemu-system-x86_64)")")/share/qemu
CPUS=${VM_CPUS:-2}
MEM=${VM_MEM:-4096}
if [ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = x86_64 ] && [ "$(sysctl -n kern.hv_support 2>/dev/null)" = 1 ]; then
    ACCEL=(-accel hvf -cpu host)
elif [ -w /dev/kvm ]; then
    ACCEL=(-accel kvm -cpu host)
else
    ACCEL=(-accel tcg,thread=multi,tb-size=1024 -cpu max)
fi
args=(-machine q35 "${ACCEL[@]}" -smp "$CPUS" -m "$MEM"
      -device virtio-vga,xres=${RES%x*},yres=${RES#*x} -display none -vnc 127.0.0.1:1
      -device qemu-xhci -device usb-tablet -device usb-kbd
      -netdev user,id=n0,hostfwd=tcp:127.0.0.1:2222-:22 -device virtio-net-pci,netdev=n0
      -audiodev none,id=snd0 -device intel-hda -device hda-duplex,audiodev=snd0
      -drive file="$DISK",if=virtio,cache=unsafe
      -serial file:test/serial.log -monitor unix:test/monitor.sock,server,nowait
      -qmp unix:test/qmp.sock,server,nowait -name whistler)
if [ "$FIRMWARE" = uefi ]; then
    [ -f test/efivars.fd ] || cp "$SHARE/edk2-i386-vars.fd" test/efivars.fd
    args+=(-drive if=pflash,format=raw,readonly=on,file="$SHARE/edk2-x86_64-code.fd"
           -drive if=pflash,format=raw,file=test/efivars.fd)
fi
if [ "$BOOT" = cdrom ]; then
    args+=(-drive file="$ISO",media=cdrom,if=none,id=cd0,readonly=on
           -device ide-cd,drive=cd0,bootindex=0)
fi
echo "Booting ${ISO:-disk} ($FIRMWARE, ${ACCEL[*]}, $CPUS vCPU, $MEM MiB). VNC 127.0.0.1:5901, ssh -p 2222 root@127.0.0.1"
exec qemu-system-x86_64 "${args[@]}"
