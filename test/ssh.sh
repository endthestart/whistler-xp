#!/usr/bin/env bash
# Run a command in the test VM as root (debug ISOs only).
cd "$(dirname "$0")/.."
exec ssh -q -i test/ssh/id_ed25519 -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=5 root@127.0.0.1 "$@"
