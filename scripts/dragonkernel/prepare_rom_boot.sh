#!/usr/bin/env bash
set -euo pipefail

if (( $# != 2 )); then
  echo "usage: $0 <rom-package-or-boot.img> {umi|cmi|cas|thyme|apollo}" >&2
  exit 2
fi

case "$2" in
  umi|cmi|cas|thyme|apollo) ;;
  *) echo "unsupported device" >&2; exit 2 ;;
esac

root=$(git rev-parse --show-toplevel)
input=$(realpath "$1")
private_root=${DRAGONKERNEL_PRIVATE_ROOT:-"$root/.dragonkernel-private"}
destination="$private_root/rom/$2"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
boot="$work/boot.img"

extract_zip() {
  local entry
  entry=$(unzip -Z1 "$input" | awk -F/ '
    tolower($NF) == "boot.img" { count++; selected=$0 }
    END { if (count == 1) print selected; else exit 1 }
  ') || true
  if [[ -n "$entry" ]]; then
    unzip -p "$input" "$entry" > "$boot"
    return
  fi

  local payload_dumper=${PAYLOAD_DUMPER:-"$HOME/toolchains/payload-dumper-v0.1.6/payload-dumper"}
  test -x "$payload_dumper"
  mkdir "$work/payload"
  "$payload_dumper" extract "$input" -p boot -o "$work/payload" >/dev/null 2>&1
  install -m 0600 "$work/payload/boot.img" "$boot"
}

extract_tar() {
  local entry
  entry=$(tar -tf "$input" | awk -F/ '
    tolower($NF) == "boot.img" { count++; selected=$0 }
    END { if (count == 1) print selected; else exit 1 }
  ')
  tar -xOf "$input" "$entry" > "$boot"
}

magic=$(od -An -N8 -tx1 "$input" | tr -d ' \n')
case "$magic" in
  414e44524f494421*) install -m 0600 "$input" "$boot" ;;
  504b0304*|504b0506*|504b0708*) extract_zip ;;
  *)
    if tar -tf "$input" >/dev/null 2>&1; then
      extract_tar
    else
      echo "ROM package does not contain a directly extractable boot image" >&2
      exit 1
    fi
    ;;
esac

test "$(od -An -N8 -tx1 "$boot" | tr -d ' \n')" = 414e44524f494421
mkdir -p "$destination"
install -m 0600 "$boot" "$destination/boot.img"
echo "ROM boot template prepared for local compatibility validation."
