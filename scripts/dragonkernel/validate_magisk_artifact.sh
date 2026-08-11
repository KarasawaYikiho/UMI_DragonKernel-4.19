#!/usr/bin/env bash
set -euo pipefail

magisk_cpio_is_patched() {
  local status
  if "$1" cpio "$2" test >/dev/null 2>&1; then
    status=0
  else
    status=$?
  fi
  [[ "$status" -eq 1 ]]
}

if [[ "${1:-}" == --self-test ]]; then
  fake=$(mktemp)
  trap 'rm -f "$fake"' EXIT
  printf '%s\n' '#!/usr/bin/env bash' 'exit "${MAGISKBOOT_TEST_STATUS:?}"' > "$fake"
  chmod +x "$fake"
  for status in 0 1 2 3; do
    if MAGISKBOOT_TEST_STATUS=$status magisk_cpio_is_patched "$fake" "$fake"; then
      test "$status" -eq 1
    else
      test "$status" -ne 1
    fi
  done
  echo "Magisk ramdisk status contract OK."
  exit 0
fi

if (( $# != 3 )); then
  echo "usage: $0 {umi|cmi|cas|thyme|apollo} <original-artifact-dir> <output-boot.img>" >&2
  exit 2
fi

case "$1" in
  umi|cmi|cas|thyme|apollo) ;;
  *) echo "unsupported device" >&2; exit 2 ;;
esac

root=$(git rev-parse --show-toplevel)
baseline=$root/Documentation/dragonkernel/baseline.json
artifact=$(realpath "$2")
output=$(realpath --canonicalize-missing "$3")
private_root=${DRAGONKERNEL_PRIVATE_ROOT:-"$root/.dragonkernel-private"}
template="$private_root/magisk/$1/boot.img"
image="$artifact/arch/arm64/boot/Image"
config="$artifact/.config"
magisk_version=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["magiskboot"]["version"])' "$baseline")
expected_sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["magiskboot"]["binary_sha256"])' "$baseline")
magiskboot=${MAGISKBOOT:-"$HOME/toolchains/magisk-$magisk_version/magiskboot"}

test -s "$template"
test -s "$image"
test -s "$config"
echo "$expected_sha  $magiskboot" | sha256sum --check --status
case "$1" in
  umi) symbol=CONFIG_MACH_XIAOMI_UMI ;;
  cmi) symbol=CONFIG_MACH_XIAOMI_CMI ;;
  cas) symbol=CONFIG_MACH_XIAOMI_CAS ;;
  thyme) symbol=CONFIG_MACH_XIAOMI_THYME ;;
  apollo) symbol=CONFIG_MACH_XIAOMI_APOLLO ;;
esac
grep -qx "$symbol=y" "$config"
grep -qx 'CONFIG_DRAGONKERNEL_ROOT_NONE=y' "$config"
grep -qx 'CONFIG_BBG=y' "$config"
! grep -Eq '^CONFIG_(KSU|KPM|KSU_SUSFS)=y$' "$config"
test "$(od -An -j56 -N4 -tx1 "$image" | tr -d ' \n')" = 41524d64

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
extract_ramdisk() {
  local source=$1 destination=$2 candidate
  mkdir "$destination"
  (
    cd "$destination"
    "$magiskboot" unpack "$source" >/dev/null 2>&1
  )
  for candidate in \
    "$destination/ramdisk.cpio" \
    "$destination/vendor_ramdisk/init_boot.cpio" \
    "$destination/vendor_ramdisk/ramdisk.cpio"; do
    if [[ -s "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return
    fi
  done
  return 1
}

template_ramdisk=$(extract_ramdisk "$template" "$work/template")
magisk_cpio_is_patched "$magiskboot" "$template_ramdisk"
if ! "$root/scripts/dragonkernel/repack_boot.sh" "$template" "$image" "$output" >/dev/null 2>&1; then
  echo "Magisk-preserving boot repack failed." >&2
  exit 1
fi
output_ramdisk=$(extract_ramdisk "$output" "$work/output")
magisk_cpio_is_patched "$magiskboot" "$output_ramdisk"
cmp -s "$template_ramdisk" "$output_ramdisk"
echo "Magisk-preserving ROM boot image passed structural validation."
