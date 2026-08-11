#!/system/bin/sh
for pid in $(pidof dragon-dac 2>/dev/null); do
  kill -TERM "$pid" 2>/dev/null || true
done
# Phase 1 owns no kernel resources. Future versions must restore before exit.
