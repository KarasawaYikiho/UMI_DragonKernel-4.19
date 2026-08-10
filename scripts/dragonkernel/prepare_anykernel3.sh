#!/usr/bin/env bash
set -euo pipefail

if (( $# != 1 )); then
  echo "usage: $0 <tool-root>" >&2
  exit 2
fi

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
readarray -t lock < <(python3 -c '
import json, sys
value = json.load(open(sys.argv[1]))["boot_tools"]["anykernel3"]
print(value["url"])
print(value["commit"])
' "$baseline")
url=${lock[0]}
commit=${lock[1]}
destination=$(realpath --canonicalize-missing "$1")/anykernel3-$commit

if [[ ! -d "$destination/.git" ]]; then
  test ! -e "$destination"
  git init -q "$destination"
  git -C "$destination" remote add origin "$url"
  git -C "$destination" fetch -q --depth=1 origin "$commit"
  git -C "$destination" checkout -q --detach FETCH_HEAD
fi

test "$(git -C "$destination" rev-parse HEAD)" = "$commit"
git -C "$destination" diff --quiet
git -C "$destination" diff --cached --quiet
test -z "$(git -C "$destination" ls-files --others --exclude-standard)"
test -s "$destination/LICENSE"
test -s "$destination/tools/ak3-core.sh"
test -s "$destination/META-INF/com/google/android/update-binary"
printf 'ANYKERNEL3_DIR=%s\n' "$destination"
