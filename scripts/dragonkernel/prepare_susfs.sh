#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
kernel_patch="$root/patches/susfs/kernel-4.19.patch"
kernelsu_patch="$root/patches/susfs/kernelsu-v0.9.5.patch"

json_value() {
  python3 -c 'import json,sys; value=json.load(open(sys.argv[1])); [value := value[key] for key in sys.argv[2:]]; print(value)' "$baseline" "$@"
}

expected_kernelsu=$(json_value upstreams kernelsu_non_gki commit)
actual_kernelsu=$(git -C "$root/drivers/kernelsu" rev-parse HEAD 2>/dev/null || true)
if [[ "$actual_kernelsu" != "$expected_kernelsu" ]]; then
  echo "KernelSU mismatch: expected $expected_kernelsu, got ${actual_kernelsu:-missing}" >&2
  exit 1
fi

expected_kernel_hash=$(json_value upstreams susfs_4_19 kernel_patch_sha256)
expected_kernelsu_hash=$(json_value upstreams susfs_4_19 kernelsu_patch_sha256)
actual_kernel_hash=$(sha256sum "$kernel_patch" | cut -d' ' -f1)
actual_kernelsu_hash=$(sha256sum "$kernelsu_patch" | cut -d' ' -f1)
[[ "$actual_kernel_hash" == "$expected_kernel_hash" ]]
[[ "$actual_kernelsu_hash" == "$expected_kernelsu_hash" ]]

git -C "$root" diff --quiet -- arch fs include kernel
git -C "$root/drivers/kernelsu" diff --quiet
git -C "$root" apply --check --exclude=arch/arm64/configs/vendor/dragonkernel-kernelsu.config "$kernel_patch"
git -C "$root/drivers/kernelsu" apply --check "$kernelsu_patch"
git -C "$root" apply --exclude=arch/arm64/configs/vendor/dragonkernel-kernelsu.config "$kernel_patch"
git -C "$root/drivers/kernelsu" apply "$kernelsu_patch"

echo "SUSFS 4.19 patches applied"
