#!/system/bin/sh
set -eu

moddir=${0%/*}
install_root=/data/adb/dragon-dac
daemon="$moddir/bin/dragon-dac"
state="$install_root/state.json"
config="$install_root/config/dac.conf"
crash_marker="$install_root/crash-loop"
runtime_root=/dev/dragon-dac
heartbeat="$runtime_root/heartbeat"
umask 077
mkdir -p "$install_root"
chmod 0700 "$install_root"

[ "$(getprop ro.bootmode 2>/dev/null || true)" = "recovery" ] && exit 0
until [ "$(getprop sys.boot_completed 2>/dev/null || true)" = "1" ]; do
  sleep 5
done

for pid in $(pidof dragon-dac 2>/dev/null || true); do
  [ "$(readlink "/proc/$pid/exe" 2>/dev/null || true)" = "$daemon" ] && exit 0
done

boot_id=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo unknown)
if [ "$(cat "$crash_marker" 2>/dev/null || true)" = "$boot_id" ]; then
  exit 0
fi
rm -f "$crash_marker"
mkdir -p "$runtime_root"
chmod 0700 "$runtime_root"

failures=0
while [ "$failures" -lt 3 ]; do
  rm -f "$heartbeat"
  read -r uptime _ </proc/uptime
  started=${uptime%%.*}
  "$daemon" daemon --config "$config" --state "$state" \
    --heartbeat "$heartbeat" >/dev/null 2>&1 &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    sleep 30
    kill -0 "$pid" 2>/dev/null || break
    read -r uptime _ </proc/uptime
    now=${uptime%%.*}
    seen=$(cat "$heartbeat" 2>/dev/null || echo 0)
    case "$seen" in *[!0-9]*|'') seen=0 ;; esac
    if [ "$seen" -eq 0 ] || [ $((now - seen)) -gt 90 ]; then
      kill -TERM "$pid" 2>/dev/null || true
      sleep 5
      kill -KILL "$pid" 2>/dev/null || true
      break
    fi
  done
  if wait "$pid"; then
    exit 0
  fi
  read -r uptime _ </proc/uptime
  stopped=${uptime%%.*}
  if [ $((stopped - started)) -ge 300 ]; then
    failures=1
  else
    failures=$((failures + 1))
  fi
  [ "$failures" -lt 3 ] && sleep 30
done

marker_tmp="$crash_marker.$$"
printf '%s\n' "$boot_id" >"$marker_tmp"
chmod 0600 "$marker_tmp"
mv -f "$marker_tmp" "$crash_marker"
