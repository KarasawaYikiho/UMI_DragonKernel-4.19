#!/system/bin/sh
set -eu

ui_print "- Dragon Adaptive Controller"
arch=${ARCH:-$(getprop ro.product.cpu.abi)}
case "$arch" in arm64|arm64-v8a) ;; *) abort "arm64 device required" ;; esac
sdk=${API:-$(getprop ro.build.version.sdk)}
[ "${sdk:-0}" -ge 35 ] || abort "Android 15 or newer required"

install_root=/data/adb/dragon-dac
mkdir -p "$install_root/config"
if [ ! -f "$install_root/config/dac.conf" ]; then
  cp "$MODPATH/config/dac.conf" "$install_root/config/dac.conf"
fi
chmod 0700 "$MODPATH/bin/dragon-dac"
chmod 0600 "$install_root/config/dac.conf"
ui_print "- Installed disabled and dry-run by default"
