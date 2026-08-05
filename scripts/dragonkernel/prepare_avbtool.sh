#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
baseline=$root/Documentation/dragonkernel/baseline.json
url=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["avbtool"]["url"])' "$baseline")
ref=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["avbtool"]["ref"])' "$baseline")
commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["boot_tools"]["avbtool"]["commit"])' "$baseline")
destination=${AVBTOOL_DIR:-"$HOME/toolchains/avb-android-15"}

if [[ ! -d "$destination/.git" ]]; then
  git clone --depth=1 --branch "$ref" "$url" "$destination"
fi
test "$(git -C "$destination" rev-parse HEAD)" = "$commit"
test -s "$destination/avbtool.py"
printf '%s\n' "$destination/avbtool.py"
