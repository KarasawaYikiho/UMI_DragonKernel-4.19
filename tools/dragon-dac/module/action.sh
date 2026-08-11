#!/system/bin/sh
moddir=${0%/*}
"$moddir/bin/dragon-dac" status --state /data/adb/dragon-dac/state.json
