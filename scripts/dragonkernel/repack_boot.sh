#!/usr/bin/env bash
set -euo pipefail

if (( $# != 3 )); then
  echo "usage: $0 <template-boot.img> <Image> <output-boot.img>" >&2
  exit 2
fi

root=$(git rev-parse --show-toplevel)
baseline=$root/Documentation/dragonkernel/baseline.json
expected_sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["magiskboot"]["binary_sha256"])' "$baseline")
expected_avb_commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["avbtool"]["commit"])' "$baseline")
magiskboot=${MAGISKBOOT:-"$HOME/toolchains/magisk-v30.7/magiskboot"}
avbtool=${AVBTOOL:-"$HOME/toolchains/avb-android-15/avbtool.py"}
template=$(realpath "$1")
kernel=$(realpath "$2")
output=$(realpath --canonicalize-missing "$3")

test "$template" != "$output"
test -s "$template"
test -s "$kernel"
echo "$expected_sha  $magiskboot" | sha256sum --check --status
test "$(git -C "$(dirname "$avbtool")" rev-parse HEAD)" = "$expected_avb_commit"
mkdir -p "$(dirname "$output")"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"
"$magiskboot" unpack -h "$template" >/dev/null 2>&1
test -s kernel
install -m 0644 "$kernel" kernel
"$magiskboot" repack "$template" "$work/repacked.img" >/dev/null 2>&1
test -s "$work/repacked.img"
test "$(stat -c %s "$work/repacked.img")" -le "$(stat -c %s "$template")"
python3 "$root/scripts/dragonkernel/refresh_avb_footer.py" "$avbtool" "$template" "$work/repacked.img"

mkdir "$work/verify"
cd "$work/verify"
"$magiskboot" unpack "$work/repacked.img" >/dev/null 2>&1
cmp -s kernel "$kernel"
install -m 0644 "$work/repacked.img" "$output"
