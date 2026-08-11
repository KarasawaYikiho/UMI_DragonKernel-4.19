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

expected_bbg_commit=$(json_value upstreams baseband_guard commit)
actual_bbg_commit=$(git -C "$root/drivers/baseband-guard" rev-parse HEAD 2>/dev/null || true)
if [[ "$actual_bbg_commit" != "$expected_bbg_commit" ]]; then
  echo "Baseband Guard mismatch: expected $expected_bbg_commit, got ${actual_bbg_commit:-missing}" >&2
  exit 1
fi
if ! git -C "$root/drivers/baseband-guard" apply --reverse --check \
  "$root/patches/bbg/a54e0dc6-hardening.patch"; then
  echo "Baseband Guard hardening patch is not applied" >&2
  exit 1
fi
bbg_header="$root/drivers/baseband-guard/baseband_guard.h"
bbg_boot_block=$(sed -n '/^#ifndef CONFIG_BBG_BLOCK_BOOT$/,/^#endif$/p' "$bbg_header")
for partition in dtbo vbmeta vbmeta_system vbmeta_vendor; do
  [[ $(grep -Fc "\"$partition\"" "$bbg_header") -eq 1 ]]
  grep -Fq "\"$partition\"" <<<"$bbg_boot_block"
done

mkdir -p "$out"
exec > >(tee "$out/build.log") 2>&1
export PATH="$toolchain_dir/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export ARCH=arm64
export SUBARCH=arm64
export KBUILD_BUILD_USER=Karasawa
export KBUILD_BUILD_HOST=DragonKernel-WSL
export KBUILD_BUILD_TIMESTAMP
KBUILD_BUILD_TIMESTAMP=$(git -C "$root" show -s --format=%cD HEAD)
export SOURCE_DATE_EPOCH
SOURCE_DATE_EPOCH=$(git -C "$root" show -s --format=%ct HEAD)

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
for option in \
  CONFIG_SCHED_WALT=y \
  CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y \
  CONFIG_UCLAMP_TASK=y \
  CONFIG_UCLAMP_TASK_GROUP=y \
  CONFIG_PSI=y \
  CONFIG_ZRAM=y \
  CONFIG_IOSCHED_BFQ=y \
  CONFIG_BFQ_GROUP_IOSCHED=y \
  CONFIG_F2FS_FS=y \
  CONFIG_BLK_WBT=y \
  CONFIG_BLK_WBT_SQ=y \
  CONFIG_THERMAL=y \
  CONFIG_CPU_THERMAL=y \
  CONFIG_THERMAL_TSENS=y \
  CONFIG_QTI_BCL_PMIC5=y \
  CONFIG_QTI_BCL_SOC_DRIVER=y \
  CONFIG_QTI_THERMAL_LIMITS_DCVS=y \
  CONFIG_BBG=y \
  CONFIG_BBG_BLOCK_BOOT=y \
  '# CONFIG_BBG_BLOCK_RECOVERY is not set'; do
  grep -qx "$option" "$out/.config"
done
grep -q '^CONFIG_LSM=.*baseband_guard' "$out/.config"
grep -q ' bbg_init$' "$out/System.map"

case "$device" in
  umi|thyme)
    device_options=(CONFIG_LN8282=y CONFIG_BQ2597X_CHARGE_PUMP=y
      CONFIG_BQ_PUMP_WIRELESS_CHARGE=y)
    ;;
  cmi)
    device_options=(CONFIG_LN8282=y CONFIG_FUEL_GAUGE_BQ27Z561=y
      CONFIG_BQ2597X_CHARGE_PUMP=y CONFIG_BQ_PUMP_WIRELESS_CHARGE=y)
    ;;
  cas)
    device_options=(CONFIG_QPNP_SMB5_CAS=y CONFIG_SMB1398_CHARGER_CAS=y
      CONFIG_FUEL_GAUGE_BQ28Z610=y CONFIG_CHARGER_BQ25790=y)
    ;;
  apollo)
    device_options=(CONFIG_BQ2597X_CHARGE_PUMP=y)
    ;;
esac
for option in "${device_options[@]}"; do
  grep -qx "$option" "$out/.config"
done

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
