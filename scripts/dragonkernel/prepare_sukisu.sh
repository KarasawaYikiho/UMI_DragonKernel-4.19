#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
patch="$root/patches/sukisu/v4.1.3-kernel-4.19.patch"

json_value() {
  python3 -c 'import json,sys; value=json.load(open(sys.argv[1])); [value := value[key] for key in sys.argv[2:]]; print(value)' "$baseline" "$@"
}

expected_commit=$(json_value upstreams sukisu_ultra commit)
expected_hash=$(json_value upstreams sukisu_ultra compat_patch_sha256)
actual_commit=$(git -C "$root/drivers/sukisu" rev-parse HEAD 2>/dev/null || true)
actual_hash=$(sha256sum "$patch" | cut -d' ' -f1)

[[ "$actual_commit" == "$expected_commit" ]]
[[ "$actual_hash" == "$expected_hash" ]]
git -C "$root/drivers/sukisu" diff --quiet
git -C "$root/drivers/sukisu" apply --check "$patch"
git -C "$root/drivers/sukisu" apply "$patch"

echo "SukiSU 4.19 compatibility patch applied"
