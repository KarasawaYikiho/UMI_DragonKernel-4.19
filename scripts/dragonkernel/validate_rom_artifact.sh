#!/usr/bin/env bash
set -euo pipefail

if (( $# != 3 )); then
  echo "usage: $0 {umi|cmi|cas|thyme|apollo} <artifact-dir> <output-boot.img>" >&2
  exit 2
fi

case "$1" in
  umi|cmi|cas|thyme|apollo) ;;
  *) echo "unsupported device" >&2; exit 2 ;;
esac

root=$(git rev-parse --show-toplevel)
artifact=$(realpath "$2")
output=$(realpath --canonicalize-missing "$3")
private_root=${DRAGONKERNEL_PRIVATE_ROOT:-"$root/.dragonkernel-private"}
template="$private_root/rom/$1/boot.img"
image="$artifact/arch/arm64/boot/Image"
config="$artifact/.config"

test -s "$template"
test -s "$image"
test -s "$config"
case "$1" in
  umi) symbol=CONFIG_MACH_XIAOMI_UMI ;;
  cmi) symbol=CONFIG_MACH_XIAOMI_CMI ;;
  cas) symbol=CONFIG_MACH_XIAOMI_CAS ;;
  thyme) symbol=CONFIG_MACH_XIAOMI_THYME ;;
  apollo) symbol=CONFIG_MACH_XIAOMI_APOLLO ;;
esac
grep -qx "$symbol=y" "$config"
test "$(od -An -j56 -N4 -tx1 "$image" | tr -d ' \n')" = 41524d64

"$root/scripts/dragonkernel/repack_boot.sh" "$template" "$image" "$output"
echo "ROM-matched boot image passed structural compatibility validation."
