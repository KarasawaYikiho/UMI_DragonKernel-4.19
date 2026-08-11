#!/system/bin/sh
for pid in $(pidof dragon-dac 2>/dev/null); do
  kill -TERM "$pid" 2>/dev/null || true
done
# The daemon detaches only its own cgroup BPF programs before exit.
