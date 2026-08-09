#!/usr/bin/env bash
set -euo pipefail

variant=${1:-}
device=${2:-}
case "$variant" in
  original|kernelsu|sukisu) ;;
  *) echo "usage: $0 {original|kernelsu|sukisu} {umi|cmi|cas|thyme|apollo}" >&2; exit 2 ;;
esac
case "$device" in
  umi|cmi|cas|thyme|apollo) ;;
  *) echo "usage: $0 {original|kernelsu|sukisu} {umi|cmi|cas|thyme|apollo}" >&2; exit 2 ;;
esac

root=$(git rev-parse --show-toplevel)
baseline="$root/Documentation/dragonkernel/baseline.json"
json_value() {
  python3 -c 'import json,sys; value=json.load(open(sys.argv[1])); [value := value[key] for key in sys.argv[2:]]; print(value)' "$baseline" "$@"
}

toolchain_name=$(json_value toolchain name)
toolchain_commit=$(json_value toolchain commit)
toolchain_dir=${TOOLCHAIN_DIR:-"$HOME/toolchains/$toolchain_name"}
out=${OUT_ROOT:-"$HOME/out/dragonkernel"}/$variant/$device
jobs=${JOBS:-$(nproc)}

actual_toolchain_commit=$(git -C "$toolchain_dir" rev-parse HEAD 2>/dev/null || true)
if [[ "$actual_toolchain_commit" != "$toolchain_commit" ]]; then
  echo "toolchain mismatch: expected $toolchain_commit, got ${actual_toolchain_commit:-missing}" >&2
  exit 1
fi

config_targets=(
  vendor/kona-perf_defconfig
  vendor/debugfs.config
  vendor/xiaomi/sm8250-common.config
  "vendor/xiaomi/$device.config"
)
local_suffix=o
if [[ "$variant" == kernelsu ]]; then
  expected_kernelsu_commit=$(json_value upstreams kernelsu_non_gki commit)
  actual_kernelsu_commit=$(git -C "$root/drivers/kernelsu" rev-parse HEAD 2>/dev/null || true)
  if [[ "$actual_kernelsu_commit" != "$expected_kernelsu_commit" ]]; then
    echo "KernelSU mismatch: expected $expected_kernelsu_commit, got ${actual_kernelsu_commit:-missing}" >&2
    exit 1
  fi
  config_targets+=(vendor/dragonkernel-kernelsu.config)
  local_suffix=ksu
elif [[ "$variant" == sukisu ]]; then
  expected_sukisu_commit=$(json_value upstreams sukisu_ultra commit)
  actual_sukisu_commit=$(git -C "$root/drivers/sukisu" rev-parse HEAD 2>/dev/null || true)
  if [[ "$actual_sukisu_commit" != "$expected_sukisu_commit" ]]; then
    echo "SukiSU mismatch: expected $expected_sukisu_commit, got ${actual_sukisu_commit:-missing}" >&2
    exit 1
  fi
  config_targets+=(vendor/dragonkernel-sukisu.config)
  local_suffix=suki
fi

mkdir -p "$out"
exec > >(tee "$out/build.log") 2>&1
export PATH="$toolchain_dir/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export ARCH=arm64
export SUBARCH=arm64
export KBUILD_BUILD_USER=Karasawa
export KBUILD_BUILD_HOST=DragonKernel-WSL
export KBUILD_BUILD_TIMESTAMP
KBUILD_BUILD_TIMESTAMP=$(git -C "$root" show -s --format=%cD HEAD)

make_args=(-C "$root" O="$out" ARCH=arm64 LLVM=1 LLVM_IAS=1
  LOCALVERSION="-DK-$local_suffix-$device")

if [[ "${USE_CCACHE:-0}" == 1 ]]; then
  command -v ccache >/dev/null
  export CCACHE_BASEDIR="$root"
  export CCACHE_COMPILERCHECK=content
  export CCACHE_DIR=${CCACHE_DIR:-"$HOME/.cache/ccache"}
  ccache --max-size "${CCACHE_MAXSIZE:-1G}" >/dev/null
  make_args+=("CC=ccache clang" "HOSTCC=ccache clang")
fi

echo "variant=$variant"
echo "device=$device"
echo "kernel_commit=$(git -C "$root" rev-parse HEAD)"
echo "toolchain_commit=$toolchain_commit"
clang --version | head -2

make "${make_args[@]}" "${config_targets[@]}" olddefconfig
make -j"$jobs" "${make_args[@]}" Image dtbs modules

image="$out/arch/arm64/boot/Image"
kernel_release="$out/include/config/kernel.release"
test -s "$image"
test -s "$kernel_release"
mapfile -d '' dtbs < <(find "$out/arch/arm64/boot/dts" -type f -name '*.dtb' -print0 | sort -z)
mapfile -d '' dtbos < <(find "$out/arch/arm64/boot/dts" -type f -name '*.dtbo' -print0 | sort -z)
mapfile -d '' modules < <(find "$out" -type f -name '*.ko' -print0 | sort -z)
((${#dtbs[@]} > 0))
((${#dtbos[@]} > 0))
((${#modules[@]} > 0))
grep -qx 'CONFIG_UCLAMP_TASK=y' "$out/.config"
grep -qx 'CONFIG_UCLAMP_TASK_GROUP=y' "$out/.config"

if [[ "$variant" == kernelsu ]]; then
  grep -qx 'CONFIG_DRAGONKERNEL_KERNELSU=y' "$out/.config"
  grep -qx 'CONFIG_KSU=y' "$out/.config"
  grep -qx 'CONFIG_KPROBES=y' "$out/.config"
  grep -qx 'CONFIG_KSU_SUSFS=y' "$out/.config"
  grep -qx '# CONFIG_KSU_SUSFS_HAS_MAGIC_MOUNT is not set' "$out/.config"
  grep -qx 'CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS=y' "$out/.config"
  grep -qx '# CONFIG_KSU_SUSFS_ENABLE_LOG is not set' "$out/.config"
  grep -q ' ksu_kernelsu_init$' "$out/System.map"
  grep -q ' susfs_init$' "$out/System.map"
elif [[ "$variant" == sukisu ]]; then
  grep -qx 'CONFIG_DRAGONKERNEL_SUKISU=y' "$out/.config"
  grep -qx 'CONFIG_KSU=y' "$out/.config"
  grep -qx 'CONFIG_KPM=y' "$out/.config"
  grep -qx 'CONFIG_KALLSYMS_ALL=y' "$out/.config"
  grep -qx 'CONFIG_KSU_SUSFS=y' "$out/.config"
  grep -qx 'CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS=y' "$out/.config"
  grep -qx '# CONFIG_KSU_SUSFS_ENABLE_LOG is not set' "$out/.config"
  grep -q ' kernelsu_init$' "$out/System.map"
  grep -q ' susfs_init$' "$out/System.map"
  grep -q ' ksu_susfs_handle_command$' "$out/System.map"
else
  grep -qx 'CONFIG_DRAGONKERNEL_ROOT_NONE=y' "$out/.config"
  ! grep -Eq '^CONFIG_(KSU|KPM|KSU_SUSFS)=y$' "$out/.config"
fi

sha256sum "$out/.config" "$kernel_release" "$image" "${dtbs[@]}" "${dtbos[@]}" "${modules[@]}" > "$out/SHA256SUMS"
echo "built Image, ${#dtbs[@]} DTBs, ${#dtbos[@]} DTBOs and ${#modules[@]} modules"
