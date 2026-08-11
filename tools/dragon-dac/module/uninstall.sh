#!/system/bin/sh
moddir=${0%/*}
for pid in $(pidof dragon-dac 2>/dev/null); do
  [ "$(readlink "/proc/$pid/exe" 2>/dev/null)" = "$moddir/bin/dragon-dac" ] || continue
  kill -TERM "$pid" 2>/dev/null || true
done
# The daemon detaches only its own cgroup BPF programs before exit.
