#!/usr/bin/env python3
"""Capture read-only DragonKernel runtime evidence through adb."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROBES = (
    ("identity", "uname -a; cat /proc/version; cat /proc/cmdline; getprop ro.product.device; getprop ro.build.version.sdk"),
    ("cgroup_layout", "cat /proc/cgroups; cat /proc/self/cgroup; mount | grep -E 'cgroup|cpuset' || true"),
    ("task_groups", "for d in /dev/cpuset /dev/stune /sys/fs/cgroup; do [ -d \"$d\" ] && find \"$d\" -maxdepth 3 -type f 2>/dev/null | sort; done"),
    ("task_profile_owners", "for f in /system/etc/task_profiles.json /vendor/etc/task_profiles.json /product/etc/task_profiles.json; do [ -r \"$f\" ] && printf '%s=readable\\n' \"$f\"; done; for p in $(pidof system_server surfaceflinger com.android.systemui 2>/dev/null); do printf '[pid=%s]\\n' \"$p\"; cat \"/proc/$p/comm\" \"/proc/$p/cgroup\" 2>/dev/null; done"),
    ("uclamp_schedtune", "for f in /proc/sys/kernel/sched_* /dev/stune/*/schedtune.* /sys/fs/cgroup/*/cpu.uclamp.*; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done"),
    ("cpu_topology", "for f in /sys/devices/system/cpu/cpu[0-9]*/topology/* /sys/devices/system/cpu/cpu[0-9]*/cpu_capacity; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done"),
    ("cpufreq", "for f in /sys/devices/system/cpu/cpufreq/policy*/*; do case \"$f\" in */affected_cpus|*/related_cpus|*/scaling_available_frequencies|*/scaling_available_governors|*/scaling_cur_freq|*/scaling_governor|*/stats/time_in_state|*/schedutil/*) [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\";; esac; done"),
    ("cpu_idle", "for f in /sys/devices/system/cpu/cpu[0-9]*/cpuidle/state*/name /sys/devices/system/cpu/cpu[0-9]*/cpuidle/state*/usage /sys/devices/system/cpu/cpu[0-9]*/cpuidle/state*/time; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done"),
    ("core_ctl_boost", "for f in /sys/devices/system/cpu/cpu*/core_ctl/* /sys/devices/system/cpu/cpu_boost/*; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done"),
    ("kgsl", "for f in /sys/class/kgsl/kgsl-3d0/devfreq/* /sys/class/kgsl/kgsl-3d0/gpu_busy_percentage /sys/class/kgsl/kgsl-3d0/min_pwrlevel /sys/class/kgsl/kgsl-3d0/max_pwrlevel; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done"),
    ("devfreq", "for d in /sys/class/devfreq/*; do [ -d \"$d\" ] || continue; printf '[%s]\\n' \"$d\"; for f in name governor available_governors available_frequencies cur_freq min_freq max_freq trans_stat; do [ -r \"$d/$f\" ] && printf '%s=' \"$f\" && cat \"$d/$f\"; done; done"),
    ("thermal", "for d in /sys/class/thermal/thermal_zone* /sys/class/thermal/cooling_device*; do [ -d \"$d\" ] || continue; printf '[%s]\\n' \"$d\"; for f in type temp policy mode cur_state max_state trip_point_*_temp trip_point_*_type trip_point_*_hyst; do [ -r \"$d/$f\" ] && printf '%s=' \"$f\" && cat \"$d/$f\"; done; done"),
    ("battery", "for d in /sys/class/power_supply/*; do [ -d \"$d\" ] || continue; printf '[%s]\\n' \"$d\"; for f in capacity voltage_now current_now temp charge_full charge_full_design charge_counter cycle_count health status charge_type constant_charge_current_max constant_charge_voltage_max; do [ -r \"$d/$f\" ] && printf '%s=' \"$f\" && cat \"$d/$f\"; done; done"),
    ("battery_learning", "for f in /sys/bus/i2c/devices/*/{fcc,fcc_soh,soh,Qmax,rm}; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done"),
    ("memory", "cat /proc/meminfo; cat /proc/vmstat; cat /proc/swaps; for f in /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io /sys/block/zram0/mm_stat /sys/block/zram0/comp_algorithm /sys/block/zram0/disksize; do [ -r \"$f\" ] && printf '[%s]\\n' \"$f\" && cat \"$f\"; done"),
    ("freezer", "for f in /sys/fs/cgroup/cgroup.controllers /sys/fs/cgroup/cgroup.events /sys/fs/cgroup/cgroup.freeze /dev/freezer/freezer.state; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done; grep -i freezer /proc/cgroups || true"),
    ("framework_freezer", "settings get global cached_apps_freezer 2>/dev/null || true; device_config get activity_manager_native_boot use_freezer 2>/dev/null || true; dumpsys activity settings 2>/dev/null | grep -iE 'freez|compact' || true"),
    ("lmkd", "getprop | grep -iE '(^|\\[)(ro\\.)?(lmk|lmkd|low_ram)' || true; dumpsys activity settings 2>/dev/null | grep -iE 'lmk|low.?memory|cached.*limit' || true"),
    ("storage", "mount | grep -E 'f2fs| /data '; for d in /sys/block/*/queue; do [ -d \"$d\" ] || continue; for f in scheduler wbt_lat_usec; do [ -r \"$d/$f\" ] && printf '%s=' \"$d/$f\" && cat \"$d/$f\"; done; done; for f in /sys/bus/platform/drivers/ufshcd/*/{rpm_lvl,spm_lvl,auto_hibern8,rpm_target_link_state,spm_target_link_state}; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done"),
    ("interrupts", "cat /proc/interrupts; for f in /proc/irq/*/smp_affinity_list /proc/irq/*/effective_affinity_list; do [ -r \"$f\" ] && printf '%s=' \"$f\" && cat \"$f\"; done"),
    ("wakeup_sources", "cat /sys/kernel/debug/wakeup_sources 2>/dev/null || { for d in /sys/class/wakeup/*; do [ -d \"$d\" ] || continue; for f in name active_count event_count total_time_ms prevent_suspend_time_ms; do [ -r \"$d/$f\" ] && printf '%s=' \"$d/$f\" && cat \"$d/$f\"; done; done; }"),
    ("joyose_package", "cmd package path com.xiaomi.joyose 2>/dev/null || true; dumpsys package com.xiaomi.joyose 2>/dev/null || true"),
    ("joyose_runtime", "for p in $(pidof com.xiaomi.joyose 2>/dev/null); do printf '[pid=%s]\\n' \"$p\"; cat \"/proc/$p/cgroup\" \"/proc/$p/status\" 2>/dev/null; done; getprop | grep -iE 'joyose|perf|sched|thermal' || true"),
    ("android_process_state", "dumpsys activity activities 2>/dev/null | grep -E 'mResumedActivity|topResumedActivity|mFocusedApp' || true; dumpsys window windows 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' || true"),
    ("surfaceflinger", "dumpsys SurfaceFlinger --timestats -dump 2>/dev/null || dumpsys SurfaceFlinger 2>/dev/null | grep -iE 'refresh|vsync|frame.?timeline' || true"),
    ("android_power", "service list 2>/dev/null | grep -iE 'power|thermal|performance' || true; dumpsys android.hardware.power.IPower/default 2>/dev/null || true; dumpsys power 2>/dev/null || true; dumpsys thermalservice 2>/dev/null || true"),
    ("dac_runtime", "for f in /data/adb/dragon-dac/state.json /dev/dragon-dac/heartbeat /data/adb/dragon-dac/crash-loop; do [ -r \"$f\" ] && printf '[%s]\\n' \"$f\" && cat \"$f\"; done"),
    ("bbg_runtime", "cat /sys/kernel/security/lsm 2>/dev/null || true; zcat /proc/config.gz 2>/dev/null | grep -E '^CONFIG_(BBG|LSM)=' || true"),
)

FORBIDDEN = (" setprop ", " chmod ", " chown ", " rm ", " mv ", " stop ", " start ", " tee ")


def self_test() -> None:
    keys = [key for key, _ in PROBES]
    assert len(keys) == len(set(keys))
    assert {
        "identity",
        "task_profile_owners",
        "joyose_package",
        "joyose_runtime",
        "android_process_state",
        "surfaceflinger",
        "thermal",
        "battery_learning",
        "freezer",
        "framework_freezer",
        "lmkd",
        "dac_runtime",
        "bbg_runtime",
    } <= set(keys)
    for _, command in PROBES:
        padded = f" {command} "
        assert not any(token in padded for token in FORBIDDEN), command
    assert adb_command(None, "id", False) == ["adb", "exec-out", "sh", "-c", "id"]
    assert adb_command("serial", "id", True) == ["adb", "-s", "serial", "exec-out", "su", "-c", "id"]


def adb_command(serial: str | None, command: str, use_su: bool) -> list[str]:
    result = ["adb"]
    if serial:
        result += ["-s", serial]
    shell = ["su", "-c"] if use_su else ["sh", "-c"]
    return result + ["exec-out", *shell, command]


def capture(serial: str | None, timeout: int, use_su: bool) -> dict[str, object]:
    results: dict[str, object] = {}
    for key, command in PROBES:
        try:
            process = subprocess.run(
                adb_command(serial, command, use_su),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=timeout,
                check=False,
            )
            results[key] = {
                "ok": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": process.stdout.rstrip(),
                "stderr": process.stderr.rstrip(),
            }
        except (OSError, subprocess.TimeoutExpired) as error:
            results[key] = {"ok": False, "error": str(error), "stdout": "", "stderr": ""}
    return {
        "schema": 1,
        "read_only": True,
        "su_requested": use_su,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "probes": results,
    }


def markdown_summary(data: dict[str, object]) -> str:
    probes = data["probes"]
    assert isinstance(probes, dict)
    lines = ["# DragonKernel runtime capture", "", "Read-only capture. Values remain local.", "", "| Probe | Result | Bytes |", "|---|---:|---:|"]
    for key, value in probes.items():
        assert isinstance(value, dict)
        output = str(value.get("stdout", ""))
        lines.append(f"| `{key}` | {'ok' if value.get('ok') else 'unavailable'} | {len(output.encode())} |")
    lines += ["", "Unavailable probes are capabilities to resolve, not automatic failures.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--su", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    out_dir = args.out_dir or Path(".dragonkernel-private/runtime") / datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=False)
    data = capture(args.serial, args.timeout, args.su)
    (out_dir / "runtime.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "runtime.md").write_text(markdown_summary(data), encoding="utf-8")
    print(out_dir)


if __name__ == "__main__":
    main()
