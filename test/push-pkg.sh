#!/usr/bin/env bash
# Install freshly built whistler packages from the build host's repository into the test VM.
#   test/push-pkg.sh [pkgname...]
cd "$(dirname "$0")/.."
for n in "${@:-whistler-artwork whistler-desktop}"; do
  for name in $n; do
    echo "installing $name"
    remote/mp "docker run --rm -v whistler-work:/work whistler-builder sh -c 'cat \$(ls /work/repo/$name-[0-9]*.pkg.tar.zst | tail -1)'" \
      | test/ssh.sh "cat > /tmp/$name.pkg.tar.zst && pacman -U --noconfirm --overwrite '*' /tmp/$name.pkg.tar.zst >/dev/null && echo ok"
  done
done
