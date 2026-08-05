#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
baseline=$root/Documentation/dragonkernel/baseline.json
version=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["magiskboot"]["version"])' "$baseline")
url=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["magiskboot"]["url"])' "$baseline")
apk_sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["magiskboot"]["apk_sha256"])' "$baseline")
binary_sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["magiskboot"]["binary_sha256"])' "$baseline")
destination=${MAGISKBOOT_DIR:-"$HOME/toolchains/magisk-$version"}
apk=$destination/Magisk-$version.apk
binary=$destination/magiskboot

mkdir -p "$destination"
if ! echo "$apk_sha  $apk" | sha256sum --check --status 2>/dev/null; then
  curl --fail --location --silent --show-error "$url" --output "$apk"
fi
echo "$apk_sha  $apk" | sha256sum --check --status

temporary=$(mktemp "$destination/.magiskboot.XXXXXX")
trap 'rm -f "$temporary"' EXIT
unzip -p "$apk" lib/x86_64/libmagiskboot.so > "$temporary"
echo "$binary_sha  $temporary" | sha256sum --check --status
install -m 0755 "$temporary" "$binary"
printf '%s\n' "$binary"
