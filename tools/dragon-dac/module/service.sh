#!/system/bin/sh
moddir=${0%/*}
install_root=/data/adb/dragon-dac
mkdir -p "$install_root"

until [ "$(getprop sys.boot_completed)" = 1 ]; do
  sleep 5
done

"$moddir/bin/dragon-dac" daemon \
  --config "$install_root/config/dac.conf" \
  --state "$install_root/state.json" \
  >/dev/null 2>&1 &
