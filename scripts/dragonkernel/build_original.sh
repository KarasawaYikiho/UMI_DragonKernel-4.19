#!/usr/bin/env bash
set -euo pipefail

device=${1:-}
case "$device" in
  umi|cmi|cas|thyme|apollo) ;;
  *) echo "usage: $0 {umi|cmi|cas|thyme|apollo}" >&2; exit 2 ;;
esac

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
toolchain_name=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["toolchain"]["name"])' "$baseline")
toolchain_commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["toolchain"]["commit"])' "$baseline")
toolchain_dir=${TOOLCHAIN_DIR:-"$HOME/toolchains/$toolchain_name"}
out=${OUT_ROOT:-"$HOME/out/dragonkernel"}/original/$device
jobs=${JOBS:-$(nproc)}

actual_toolchain_commit=$(git -C "$toolchain_dir" rev-parse HEAD 2>/dev/null || true)
if [[ "$actual_toolchain_commit" != "$toolchain_commit" ]]; then
  echo "toolchain mismatch: expected $toolchain_commit, got ${actual_toolchain_commit:-missing}" >&2
  exit 1
fi

mkdir -p "$out"
export PATH="$toolchain_dir/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export ARCH=arm64
export SUBARCH=arm64
export KBUILD_BUILD_USER=Karasawa
export KBUILD_BUILD_HOST=DragonKernel-WSL
export KBUILD_BUILD_TIMESTAMP
KBUILD_BUILD_TIMESTAMP=$(git -C "$root" show -s --format=%cD HEAD)

make_args=(-C "$root" O="$out" ARCH=arm64 LLVM=1 LLVM_IAS=1
  LOCALVERSION="-DK-o-$device")

{
  echo "device=$device"
  echo "kernel_commit=$(git -C "$root" rev-parse HEAD)"
  echo "toolchain_commit=$toolchain_commit"
  clang --version | head -2

  make "${make_args[@]}" \
    vendor/kona-perf_defconfig \
    vendor/debugfs.config \
    vendor/xiaomi/sm8250-common.config \
    "vendor/xiaomi/$device.config" \
    olddefconfig
  make -j"$jobs" "${make_args[@]}" Image dtbs modules

  image="$out/arch/arm64/boot/Image"
  test -s "$image"
  mapfile -d '' dtbs < <(find "$out/arch/arm64/boot/dts" -type f -name '*.dtb' -print0)
  ((${#dtbs[@]} > 0))
  sha256sum "$out/.config" "$image" "${dtbs[@]}" > "$out/SHA256SUMS"
  echo "built Image and ${#dtbs[@]} DTBs"
} 2>&1 | tee "$out/build.log"
