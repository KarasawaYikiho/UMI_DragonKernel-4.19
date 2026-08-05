#!/usr/bin/env bash
set -euo pipefail

if (( $# != 1 )); then
  echo "usage: $0 <destination-root>" >&2
  exit 2
fi

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
IFS=$'\t' read -r name url ref commit < <(
  python3 -c 'import json,sys; value=json.load(open(sys.argv[1]))["toolchain"]; print(value["name"], value["url"], value["ref"], value["commit"], sep="\t")' "$baseline"
)
toolchain="$1/$name"

git clone --depth=1 --single-branch --branch "$ref" "$url" "$toolchain"
test "$(git -C "$toolchain" rev-parse HEAD)" = "$commit"
printf 'TOOLCHAIN_DIR=%s\n' "$toolchain"
