#!/usr/bin/env bash
# Linux Node LTS; cache lives on the Linux filesystem for WSL performance.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION=v22.23.4
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/accessledger"
mkdir -p "$CACHE" "$ROOT/.tools/node"
if [ ! -x "$CACHE/node-$VERSION-linux-x64/bin/node" ]; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL "https://nodejs.org/dist/$VERSION/node-$VERSION-linux-x64.tar.xz" -o "$tmp/node-$VERSION-linux-x64.tar.xz"
  curl -fsSL "https://nodejs.org/dist/$VERSION/SHASUMS256.txt" -o "$tmp/SHASUMS256.txt"
  (cd "$tmp" && rg " node-$VERSION-linux-x64.tar.xz$" SHASUMS256.txt | sha256sum -c -)
  tar -xJf "$tmp/node-$VERSION-linux-x64.tar.xz" -C "$CACHE"
fi
ln -sfn "$CACHE/node-$VERSION-linux-x64" "$ROOT/.tools/node/current"
"$ROOT/.tools/node/current/bin/node" --version
