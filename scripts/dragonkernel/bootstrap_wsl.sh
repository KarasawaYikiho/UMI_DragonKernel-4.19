#!/usr/bin/env bash
set -euo pipefail

if ! grep -qi microsoft /proc/sys/kernel/osrelease; then
  echo "This script must run inside WSL 2." >&2
  exit 1
fi

if (( EUID == 0 )); then
  SUDO=()
else
  SUDO=(sudo)
fi

"${SUDO[@]}" apt-get update
"${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y \
  bc bison build-essential ccache cpio curl device-tree-compiler flex git kmod \
  libelf-dev libncurses-dev libssl-dev lld llvm lz4 lzop pahole python3 rsync \
  unzip xz-utils zip zstd

mkdir -p "$HOME/src" "$HOME/toolchains" "$HOME/.cache/dragonkernel"

git config --global user.name "Karasawa"
git config --global user.email "2339725024@qq.com"

echo "DragonKernel WSL dependencies are ready."
