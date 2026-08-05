#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
compat_patch="$root/patches/sukisu/v4.1.3-kernel-4.19.patch"
susfs_patch="$root/patches/sukisu/v4.1.3-susfs-v1.5.5.patch"
kernel_patch="$root/patches/susfs/kernel-4.19.patch"

json_value() {
  python3 -c 'import json,sys; value=json.load(open(sys.argv[1])); [value := value[key] for key in sys.argv[2:]]; print(value)' "$baseline" "$@"
}

expected_commit=$(json_value upstreams sukisu_ultra commit)
expected_compat_hash=$(json_value upstreams sukisu_ultra compat_patch_sha256)
expected_susfs_hash=$(json_value upstreams sukisu_ultra susfs_patch_sha256)
expected_kernel_hash=$(json_value upstreams susfs_4_19 kernel_patch_sha256)
actual_commit=$(git -C "$root/drivers/sukisu" rev-parse HEAD 2>/dev/null || true)
actual_compat_hash=$(sha256sum "$compat_patch" | cut -d' ' -f1)
actual_susfs_hash=$(sha256sum "$susfs_patch" | cut -d' ' -f1)
actual_kernel_hash=$(sha256sum "$kernel_patch" | cut -d' ' -f1)

[[ "$actual_commit" == "$expected_commit" ]]
[[ "$actual_compat_hash" == "$expected_compat_hash" ]]
[[ "$actual_susfs_hash" == "$expected_susfs_hash" ]]
[[ "$actual_kernel_hash" == "$expected_kernel_hash" ]]
git -C "$root" diff --quiet -- arch fs include kernel
git -C "$root/drivers/sukisu" diff --quiet
git -C "$root" apply --check --exclude=arch/arm64/configs/vendor/dragonkernel-kernelsu.config "$kernel_patch"
git -C "$root/drivers/sukisu" apply --check "$compat_patch"
git -C "$root" apply --exclude=arch/arm64/configs/vendor/dragonkernel-kernelsu.config "$kernel_patch"
git -C "$root/drivers/sukisu" apply "$compat_patch"
git -C "$root/drivers/sukisu" apply --check "$susfs_patch"
git -C "$root/drivers/sukisu" apply "$susfs_patch"

echo "SukiSU + KPM + SUSFS patches applied"
