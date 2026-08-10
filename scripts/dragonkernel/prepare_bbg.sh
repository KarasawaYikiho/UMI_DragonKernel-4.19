#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
patch="$root/patches/bbg/a54e0dc6-hardening.patch"
python_bin=${PYTHON:-python3}

json_value() {
  "$python_bin" -c 'import json,sys; value=json.load(open(sys.argv[1])); [value := value[key] for key in sys.argv[2:]]; print(value)' "$baseline" "$@"
}

expected_commit=$(json_value upstreams baseband_guard commit)
expected_hash=$(json_value upstreams baseband_guard hardening_patch_sha256)
actual_commit=$(git -C "$root/drivers/baseband-guard" rev-parse HEAD 2>/dev/null || true)
actual_hash=$(sha256sum "$patch" | cut -d' ' -f1)

[[ "$actual_commit" == "$expected_commit" ]]
[[ "$actual_hash" == "$expected_hash" ]]
git -C "$root/drivers/baseband-guard" diff --quiet
git -C "$root/drivers/baseband-guard" apply --check "$patch"
git -C "$root/drivers/baseband-guard" apply "$patch"

echo "Pinned Baseband Guard hardening patch applied"
