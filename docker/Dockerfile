# Build environment for Whistler XP (CachyOS, x86_64).
FROM cachyos/cachyos:latest

# pacman's syscall sandbox does not work under qemu-user emulation (arm64 hosts).
RUN grep -q '^DisableSandbox' /etc/pacman.conf || sed -i '/^\[options\]/a DisableSandbox' /etc/pacman.conf \
 && pacman -Syu --noconfirm --needed \
      archiso base-devel git python python-yaml python-pillow python-numpy python-cairo \
      python-cairosvg python-gobject gtk3 librsvg imagemagick xorg-xcursorgen gettext \
      xfce4-panel cabextract fontconfig ttf-dejavu ttf-liberation ttf-fira-sans noto-fonts \
      noto-fonts-emoji gdk-pixbuf2 rsync \
 && useradd -m builder \
 && echo 'builder ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/builder \
 && sed -i 's/^#MAKEFLAGS=.*/MAKEFLAGS="-j$(nproc)"/; s/^\(OPTIONS=(.*[( ]\)debug/\1!debug/' /etc/makepkg.conf \
 && pacman -Scc --noconfirm

WORKDIR /src
