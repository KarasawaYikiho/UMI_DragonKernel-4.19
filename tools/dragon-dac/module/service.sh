#!/system/bin/sh
set -eu

moddir=${0%/*}
install_root=/data/adb/dragon-dac
mkdir -p "$install_root"
chmod 0700 "$install_root"

"$moddir/bin/dragon-dac" daemon \
  --config "$install_root/config/dac.conf" \
  --state "$install_root/state.json" \
  >/dev/null 2>&1 &
