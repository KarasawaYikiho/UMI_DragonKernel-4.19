#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "Documentation/dragonkernel/baseline.json"


def fail(message: str) -> None:
    raise SystemExit(f"baseline check failed: {message}")


data = json.loads(LOCK.read_text(encoding="utf-8"))
makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
parts = {}
for name in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
    match = re.search(rf"^{name}\s*=\s*(\d+)\s*$", makefile, re.MULTILINE)
    if not match:
        fail(f"Makefile has no {name}")
    parts[name] = match.group(1)

actual = f"{parts['VERSION']}.{parts['PATCHLEVEL']}.{parts['SUBLEVEL']}"
if actual != data["kernel"]["version"]:
    fail(f"kernel version is {actual}, lock says {data['kernel']['version']}")

tracked = set(
    subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True
    ).splitlines()
)
forbidden_files = {
    "agent.md",
    "agents.md",
    "plan.md",
    "plans.md",
    "superpower.md",
    "superpowers.md",
}
forbidden_prefixes = (
    ".dragonkernel-private/",
    "artifacts/",
    "build/",
    "dist/",
    "out/",
    "private/",
    "temp/",
    "tmp/",
)
forbidden_components = {
    ".agents",
    ".codex",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".superpowers",
    "__pycache__",
    "node_modules",
    "superpowers",
}
forbidden_suffixes = (
    ".bak",
    ".log",
    ".orig",
    ".pyc",
    ".pyo",
    ".rej",
    ".swo",
    ".swp",
    ".tmp",
    "~",
)
for path in tracked:
    normalized = path.casefold()
    if (
        normalized.rsplit("/", 1)[-1] in forbidden_files
        or normalized.startswith(forbidden_prefixes)
        or normalized.endswith(forbidden_suffixes)
        or forbidden_components.intersection(normalized.split("/")[:-1])
    ):
        fail(f"forbidden engineering or temporary file is tracked: {path}")

for path in data["kernel"]["config_fragments"]:
    if path not in tracked:
        fail(f"missing config fragment: {path}")
if "arch/arm64/configs/vendor/dragonkernel-kernelsu.config" not in tracked:
    fail("missing KernelSU config fragment")
if "arch/arm64/configs/vendor/dragonkernel-sukisu.config" not in tracked:
    fail("missing SukiSU config fragment")

devices = data["device_family"]["devices"]
if len({device["codename"] for device in devices}) != len(devices):
    fail("device codenames are not unique")
for device in devices:
    if device["config"] not in tracked:
        fail(f"missing device config: {device['config']}")

expected_capacity_mah = {
    "umi": 4780,
    "cmi": 4500,
    "cas": 4500,
    "thyme": 4780,
    "apollo": 5000,
}
if {
    device["codename"]: device.get("battery_capacity_mah")
    for device in devices
} != expected_capacity_mah:
    fail("device battery capacity contract changed")

expected_rom_profiles = {
    "umi": ("Hyper3", 1),
    "cmi": ("Hyper3", 1),
    "cas": ("Hyper3", 1),
    "thyme": ("Lineage_**Latest**", 1),
    "apollo": ("Lineage_**Latest**", 1),
}
if {
    device["codename"]: (
        device.get("validation_rom_reference"),
        device.get("validation_profiles"),
    )
    for device in devices
} != expected_rom_profiles:
    fail("device ROM validation profile contract changed")


def indexed_text(path: str) -> str:
    worktree_path = ROOT / path
    if worktree_path.exists():
        return worktree_path.read_text(encoding="utf-8")
    return subprocess.check_output(
        ["git", "show", f":{path}"], cwd=ROOT, text=True
    )


capacity_sources = {
    "arch/arm64/boot/dts/vendor/qcom/umi-sm8250.dtsi": (
        '"fg-gen4-batterydata-umi-gybm-4780mah.dtsi"',
        '"fg-gen4-batterydata-umi-NVTBM4N-4780mah.dtsi"',
    ),
    "arch/arm64/boot/dts/vendor/qcom/thyme-sm8250.dtsi": (
        '"fg-gen4-batterydata-umi-gybm-4780mah.dtsi"',
        '"fg-gen4-batterydata-umi-NVTBM4N-4780mah.dtsi"',
    ),
    "arch/arm64/boot/dts/vendor/qcom/cmi-sm8250.dtsi": (
        "bq,charge-full-design = <4500000>;",
    ),
    "arch/arm64/boot/dts/vendor/qcom/cas-sm8250.dtsi": (
        "bq,charge-full-design = <2250000>;",
    ),
    "arch/arm64/boot/dts/vendor/qcom/apollo-sm8250.dtsi": (
        '"fg-gen4-batterydata-apollo-sun-5000mah.dtsi"',
    ),
    "arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-umi-gybm-4780mah.dtsi": (
        "qcom,nom-batt-capacity-mah = <4780>;",
    ),
    "arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-umi-NVTBM4N-4780mah.dtsi": (
        "qcom,nom-batt-capacity-mah = <4780>;",
    ),
    "arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-apollo-sun-5000mah.dtsi": (
        "qcom,nom-batt-capacity-mah = <5000>;",
    ),
}
for path, required in capacity_sources.items():
    source = indexed_text(path)
    for token in required:
        if token not in source:
            fail(f"device battery capacity source changed: {path}")

expected_variants = {"original", "magisk", "kernelsu", "sukisu-kpm-susfs"}
if set(data["release_variants"]) != expected_variants:
    fail("release variant contract changed")

expected_release_naming = {
    "timezone": "Asia/Shanghai",
    "timestamp_format": "yyyyMMddHHmm",
    "tag_template": "UMI_{timestamp}_{variant}",
    "asset_base_template": "UMI_{timestamp}_{variant}_Build",
    "module_asset_template": "UMI_{timestamp}_DAC_Module_Build.zip",
    "variant_names": {
        "original": "Original",
        "magisk": "Magisk",
        "kernelsu": "KernelSU",
        "sukisu-kpm-susfs": "SukiSU_KPM_SUSFS",
    },
}
if data.get("release_naming") != expected_release_naming:
    fail("release naming contract changed")

expected_userspace_toolchain = {
    "name": "android-ndk-r27d",
    "revision": "27.3.13750724",
    "target": "aarch64-linux-android35",
    "linux_archive_sha1": "22105e410cf29afcf163760cc95522b9fb981121",
}
if data.get("userspace_toolchain") != expected_userspace_toolchain:
    fail("userspace toolchain contract changed")

expected_userspace_module = {
    "role": "optional-dac-and-vendor-cloud-control-layer",
    "kernel_variant": False,
    "root_manager_apis_required": False,
    "supported_installers": ["magisk", "kernelsu", "sukisu"],
    "joyose_policy": "block-remote-control-preserve-local-compatibility",
}
if data.get("userspace_module") != expected_userspace_module:
    fail("userspace DAC module contract changed")

for path in (
    "Documentation/dragonkernel/optimization/00_REPO_AUDIT.md",
    "Documentation/dragonkernel/optimization/01_RUNTIME_AUDIT.md",
    "Documentation/dragonkernel/optimization/02_BASELINE_METRICS.md",
    "Documentation/dragonkernel/optimization/03_DAC_ARCHITECTURE.md",
    "Documentation/dragonkernel/optimization/04_CPU_POLICY.md",
    "Documentation/dragonkernel/optimization/05_FREEZER.md",
    "Documentation/dragonkernel/optimization/06_GAME_CONTROLLER.md",
    "Documentation/dragonkernel/optimization/07_THERMAL.md",
    "Documentation/dragonkernel/optimization/08_VALIDATION.md",
    "scripts/dragonkernel/diagnostics/capture_runtime.py",
    "scripts/dragonkernel/package_dac_module.py",
    "scripts/dragonkernel/validate_dac_module.py",
    "tools/dragon-dac/src/main.cpp",
    "tools/dragon-dac/src/cpu_backend.h",
    "tools/dragon-dac/src/policy.h",
    "tools/dragon-dac/module/module.prop",
    "tools/dragon-dac/module/config/dac.conf",
    "tools/dragon-dac/module/customize.sh",
    "tools/dragon-dac/module/service.sh",
    "tools/dragon-dac/module/uninstall.sh",
    "tools/dragon-dac/module/action.sh",
    ".github/workflows/dac-module-validation.yml",
):
    if not (ROOT / path).is_file():
        fail(f"optimization contract file missing: {path}")

diagnostics_source = indexed_text("scripts/dragonkernel/diagnostics/capture_runtime.py")
for token in ("joyose_package", "joyose_runtime", "framework_freezer", "read_only", "--self-test"):
    if token not in diagnostics_source:
        fail("read-only runtime diagnostics contract changed")

dac_source = indexed_text("tools/dragon-dac/src/main.cpp")
for token in ("epoll_create1", "timerfd_create", "signalfd", "inotify_init1", "owned_resources"):
    if token not in dac_source:
        fail("DAC event-loop skeleton contract changed")
for token in (
    "BPF_PROG_TYPE_CGROUP_SKB",
    "BPF_CGROUP_INET_INGRESS",
    "BPF_CGROUP_INET_EGRESS",
    "BPF_LINK_CREATE",
    "cgroup_is_joyose_only",
    "BoostArbiter",
    "CpuBackend",
    "FreezeStateMachine",
    "kBinderGetFrozenInfo",
):
    if token not in dac_source:
        fail("Joyose cgroup BPF isolation contract changed")
kona_config = indexed_text("arch/arm64/configs/vendor/kona-perf_defconfig")
for token in ("CONFIG_CGROUP_BPF=y", "CONFIG_BPF_SYSCALL=y"):
    if token not in kona_config:
        fail("Joyose cgroup BPF kernel capability changed")
module_config = indexed_text("tools/dragon-dac/module/config/dac.conf")
for token in (
    "dac.enabled=false",
    "dac.cpu.enabled=false",
    "dac.dry_run=true",
    "dac.cloud_control.remote=block",
):
    if token not in module_config:
        fail("DAC safe default contract changed")

for name, upstream in data["upstreams"].items():
    if not re.fullmatch(r"[0-9a-f]{40}", upstream["commit"]):
        fail(f"{name} commit is not a full SHA-1")
    if not upstream["url"].startswith(("https://github.com/", "https://gitlab.com/")):
        fail(f"{name} URL is not an approved HTTPS source")

if data["upstreams"].get("kernelsu_non_gki") != {
    "url": "https://github.com/tiann/KernelSU.git",
    "ref": "v0.9.5",
    "commit": "b766b98513b5a7eb33bc1c4a76b5702bf1288f07",
}:
    fail("unexpected KernelSU non-GKI lock")
gitlink = subprocess.check_output(
    ["git", "ls-files", "--stage", "drivers/kernelsu"], cwd=ROOT, text=True
).split()
if gitlink[:2] != ["160000", data["upstreams"]["kernelsu_non_gki"]["commit"]]:
    fail("KernelSU submodule does not match its lock")

sukisu = data["upstreams"].get("sukisu_ultra", {})
if sukisu.get("url") != "https://github.com/SukiSU-Ultra/SukiSU-Ultra.git":
    fail("unexpected SukiSU source")
if sukisu.get("ref") != "v4.1.3" or sukisu.get("commit") != "0ca744a88835144c58d8256ebb32c279edabfcde":
    fail("unexpected SukiSU lock")
if not re.fullmatch(r"[0-9a-f]{64}", sukisu.get("compat_patch_sha256", "")):
    fail("invalid SukiSU compatibility patch hash")
sukisu_gitlink = subprocess.check_output(
    ["git", "ls-files", "--stage", "drivers/sukisu"], cwd=ROOT, text=True
).split()
if sukisu_gitlink[:2] != ["160000", sukisu["commit"]]:
    fail("SukiSU submodule does not match its lock")
sukisu_patch = "patches/sukisu/v4.1.3-kernel-4.19.patch"
if sukisu_patch not in tracked:
    fail("missing SukiSU compatibility patch")
if hashlib.sha256((ROOT / sukisu_patch).read_bytes()).hexdigest() != sukisu["compat_patch_sha256"]:
    fail("SukiSU compatibility patch hash mismatch")
sukisu_susfs_patch = "patches/sukisu/v4.1.3-susfs-v1.5.5.patch"
if sukisu_susfs_patch not in tracked:
    fail("missing SukiSU SUSFS patch")
if hashlib.sha256((ROOT / sukisu_susfs_patch).read_bytes()).hexdigest() != sukisu.get("susfs_patch_sha256"):
    fail("SukiSU SUSFS patch hash mismatch")

susfs = data["upstreams"].get("susfs_4_19", {})
if susfs.get("url") != "https://gitlab.com/simonpunk/susfs4ksu.git":
    fail("unexpected SUSFS source")
if susfs.get("ref") != "kernel-4.19" or susfs.get("commit") != "001e69919c6271f690fd00b17e4c721c9e599152":
    fail("unexpected SUSFS 4.19 lock")
for field in ("kernel_patch_sha256", "kernelsu_patch_sha256"):
    if not re.fullmatch(r"[0-9a-f]{64}", susfs.get(field, "")):
        fail(f"invalid SUSFS {field}")
susfs_patches = {
    "patches/susfs/kernel-4.19.patch": susfs["kernel_patch_sha256"],
    "patches/susfs/kernelsu-v0.9.5.patch": susfs["kernelsu_patch_sha256"],
}
for path, expected_hash in susfs_patches.items():
    if path not in tracked:
        fail(f"missing SUSFS patch: {path}")
    actual_hash = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        fail(f"SUSFS patch hash mismatch: {path}")

bbg = data["upstreams"].get("baseband_guard", {})
if bbg.get("url") != "https://github.com/vc-teahouse/Baseband-guard.git":
    fail("unexpected Baseband Guard source")
if bbg.get("ref") != "a54e0dc6cf0aff4dd87fec49644a02d2eb612905":
    fail("unexpected Baseband Guard ref")
if bbg.get("commit") != bbg.get("ref"):
    fail("Baseband Guard ref must be a pinned commit")
bbg_gitlink = subprocess.check_output(
    ["git", "ls-files", "--stage", "drivers/baseband-guard"], cwd=ROOT, text=True
).split()
if bbg_gitlink[:2] != ["160000", bbg["commit"]]:
    fail("Baseband Guard submodule does not match its lock")
bbg_patch = "patches/bbg/a54e0dc6-hardening.patch"
if bbg_patch not in tracked:
    fail("missing Baseband Guard hardening patch")
if hashlib.sha256((ROOT / bbg_patch).read_bytes()).hexdigest() != bbg.get(
    "hardening_patch_sha256"
):
    fail("Baseband Guard hardening patch hash mismatch")

common_config = indexed_text("arch/arm64/configs/vendor/xiaomi/sm8250-common.config")
for token in (
    "CONFIG_BBG=y",
    "CONFIG_BBG_BLOCK_BOOT=y",
    "# CONFIG_BBG_BLOCK_RECOVERY is not set",
    "baseband_guard",
):
    if token not in common_config:
        fail("BBG must remain a common anti-format feature")
for token in ("CONFIG_UCLAMP_TASK=y", "CONFIG_UCLAMP_TASK_GROUP=y"):
    if token not in common_config:
        fail("utilization clamping config contract changed")
schedutil = indexed_text("kernel/sched/cpufreq_schedutil.c")
for token in (
    "util = cpu_util_freq(sg_cpu->cpu, &sg_cpu->walt_load);",
    "util = uclamp_rq_util_with(rq, util, p);",
    "return uclamp_rq_util_with(rq, util, NULL);",
):
    if token not in schedutil:
        fail("WALT/schedutil utilization clamping contract changed")
cpu_boost = indexed_text("drivers/cpufreq/cpu-boost.c")
for token in (
    "sched_set_boost(-sched_boost_active)",
    "sched_boost_active = boost;",
):
    if token not in cpu_boost:
        fail("input scheduler boost ownership contract changed")
if "sched_set_boost(0)" in cpu_boost:
    fail("input boost must not clear unrelated scheduler boost owners")
sched_boost = indexed_text("kernel/sched/boost.c")
if "sched_boosts[sched_effective_boost()].exit();" not in sched_boost:
    fail("scheduler boost reset must exit only the effective boost")
if 'obj-$(CONFIG_BBG)' not in indexed_text("drivers/Makefile"):
    fail("BBG build integration missing")
if 'source "drivers/baseband-guard/Kconfig"' not in indexed_text("drivers/Kconfig"):
    fail("BBG Kconfig integration missing")

root_hiding = data.get("common_security", {}).get("root_hiding", {})
if set(root_hiding.get("required_variants", [])) != expected_variants - {"original"}:
    fail("root hiding must cover every Root variant")
if root_hiding.get("validation_layers") != ["kernel", "manager", "application"]:
    fail("root hiding validation layers changed")
if data.get("common_security", {}).get("bbg") != {
    "role": "common-anti-format-feature",
    "root_dependency": False,
    "separate_validation": True,
}:
    fail("BBG must not become a Root variant")

toolchain = data["toolchain"]
if not re.fullmatch(r"[0-9a-f]{40}", toolchain["commit"]):
    fail("toolchain commit is not a full SHA-1")
if toolchain["name"] != "clang-r416183b":
    fail("unexpected baseline toolchain")

magiskboot = data.get("boot_tools", {}).get("magiskboot", {})
if magiskboot.get("version") != "v30.7":
    fail("unexpected magiskboot version")
if magiskboot.get("url") != (
    "https://github.com/topjohnwu/Magisk/releases/download/v30.7/Magisk-v30.7.apk"
):
    fail("unexpected magiskboot URL")
for field in ("apk_sha256", "binary_sha256"):
    if not re.fullmatch(r"[0-9a-f]{64}", magiskboot.get(field, "")):
        fail(f"invalid magiskboot {field}")

payload_dumper = data.get("boot_tools", {}).get("payload_dumper", {})
if payload_dumper != {
    "version": "v0.1.6",
    "url": "https://github.com/xishang0128/payload-dumper-go/releases/download/v0.1.6/payload-dumper-linux-amd64-v3.tar.gz",
    "archive_sha256": "c2960706e7f8d6e5a7f9b42ec55b7997828120de47a3b8a9de93c2cb7dc44503",
}:
    fail("unexpected payload dumper lock")

avbtool = data.get("boot_tools", {}).get("avbtool", {})
if avbtool != {
    "url": "https://android.googlesource.com/platform/external/avb",
    "ref": "android-15.0.0_r1",
    "commit": "25a14f7e3e6493a7f1a42aa9f78209d4dbe848e9",
}:
    fail("unexpected avbtool lock")

anykernel3 = data.get("boot_tools", {}).get("anykernel3", {})
if anykernel3 != {
    "url": "https://github.com/osm0sis/AnyKernel3.git",
    "ref": "master",
    "commit": "e4b1bb25ca2aabcfd57f694a5998d87130701b71",
}:
    fail("unexpected AnyKernel3 lock")

magisk_validator = indexed_text("scripts/dragonkernel/validate_magisk_artifact.sh")
for token in (
    "CONFIG_DRAGONKERNEL_ROOT_NONE=y",
    "CONFIG_BBG=y",
    '[[ "$status" -eq 1 ]]',
    'cmp -s "$template_ramdisk" "$output_ramdisk"',
):
    if token not in magisk_validator:
        fail("Magisk artifact validation contract changed")

thermal_sources = {
    "drivers/thermal/thermal_core.c": ("thermal_message", "thermal-message"),
    "drivers/thermal/cpu_cooling.c": ("cpu_limits_set_level",),
    "include/linux/cpu_cooling.h": ("cpu_limits_set_level",),
    "arch/arm64/boot/dts/vendor/qcom/xiaomi-sm8250-common.dtsi": (
        "thermal-message",
    ),
}
for path, forbidden in thermal_sources.items():
    source = (ROOT / path).read_text(encoding="utf-8")
    for token in forbidden:
        if token in source:
            fail(f"Xiaomi thermal userspace control remains in {path}")

battery_sources = (
    "drivers/power/supply/qcom/qpnp-fg-gen4.c",
    "drivers/power/supply/qcom/bq27z561_fg.c",
    "drivers/power/supply/qcom_cas/bq27z561_fg.c",
)
for path in battery_sources:
    source = (ROOT / path).read_text(encoding="utf-8")
    if source.count("case POWER_SUPPLY_PROP_CHARGE_FULL_DESIGN:") != 1:
        fail(f"battery design capacity must remain read-only in {path}")
    if "design_cap_orig" in source or "batt_dc_orig" in source:
        fail(f"manual battery design capacity override remains in {path}")

cmi_fg_source = (ROOT / battery_sources[1]).read_text(encoding="utf-8")
if not re.search(
    r"case POWER_SUPPLY_PROP_CHARGE_FULL:\s+"
    r"if \(bq->old_hw\) \{\s+val->intval = bq->batt_dc;",
    cmi_fg_source,
):
    fail("cmi fuel-gauge fallback must use its model design capacity")

fg_gen4_source = (ROOT / battery_sources[0]).read_text(encoding="utf-8")
if "pval->intval > chip->cl->nom_cap_uah" not in fg_gen4_source:
    fail("FG Gen4 manual learned-capacity writes must remain stock-bounded")

fg_alg_path = ROOT / "drivers/power/supply/qcom/fg-alg.c"
fg_alg_source = (
    fg_alg_path.read_text(encoding="utf-8")
    if fg_alg_path.exists()
    else indexed_text("drivers/power/supply/qcom/fg-alg.c")
)
if "cl->learned_cap_uah < cl->nom_cap_uah" not in fg_alg_source:
    fail("capacity learning must retain the implausibly-low value repair")
if "abs(cl->learned_cap_uah - cl->nom_cap_uah)" in fg_alg_source:
    fail("persisted learned capacity is still reset above the stock value")
if "higher than expected, capping it to nominal" in fg_alg_source:
    fail("persisted learned capacity still has an upper stock-cap reset")

fast_workflow = ".github/workflows/fast-validation.yml"
if fast_workflow not in tracked:
    fail("missing targeted fast validation workflow")
fast_source = (ROOT / fast_workflow).read_text(encoding="utf-8")
if "actions/cache@v5" not in fast_source or 'USE_CCACHE: "1"' not in fast_source:
    fail("targeted fast validation must use the compiler cache")
if "options: [original, kernelsu, sukisu]" not in fast_source:
    fail("fast validation variants changed")
if "scripts/dragonkernel/prepare_bbg.sh" not in fast_source:
    fail("fast validation must include the common BBG feature")
if re.search(r"options:.*bbg|inputs\.variant.*bbg", fast_source):
    fail("BBG must not appear as a fast-build variant")

variant_workflows = (
    ".github/workflows/original-validation.yml",
    ".github/workflows/kernelsu-validation.yml",
    ".github/workflows/sukisu-validation.yml",
)
for workflow in variant_workflows:
    if "scripts/dragonkernel/prepare_bbg.sh" not in indexed_text(workflow):
        fail(f"variant workflow lacks common BBG preparation: {workflow}")

bbg_workflow_source = indexed_text(".github/workflows/bbg-validation.yml")
for token in (
    "scripts/dragonkernel/prepare_bbg.sh",
    "scripts/dragonkernel/build_original.sh",
    "bbg-feature-${{ matrix.device }}",
):
    if token not in bbg_workflow_source:
        fail("independent BBG feature workflow changed")
for forbidden in (
    "prepare_susfs.sh",
    "prepare_sukisu.sh",
    "build_bbg.sh",
    "OUT_ROOT }}/bbg/",
):
    if forbidden in bbg_workflow_source:
        fail("BBG feature workflow depends on a Root path")

package_source = indexed_text("scripts/dragonkernel/package_anykernel.py")
if '"bbg":' in package_source:
    fail("BBG must not be an AnyKernel variant")
if (ROOT / "scripts/dragonkernel/build_bbg.sh").exists():
    fail("BBG must not have a variant build wrapper")
if "scripts/dragonkernel/build_bbg.sh" in indexed_text(
    ".github/workflows/project-contract.yml"
):
    fail("project contract still exposes a BBG variant")

build_source = (ROOT / "scripts/dragonkernel/build_kernel.sh").read_text(
    encoding="utf-8"
)
if "original|kernelsu|sukisu)" not in build_source:
    fail("kernel variant contract changed")
for forbidden in ("original|kernelsu|sukisu|bbg", '"$variant" == bbg', "dragonkernel-bbg.config"):
    if forbidden in build_source:
        fail("BBG must not be a kernel variant")
for token in (
    "expected_bbg_commit=$(json_value upstreams baseband_guard commit)",
    "apply --reverse --check",
    "Baseband Guard hardening patch is not applied",
):
    if token not in build_source:
        fail("common BBG source gate changed")
if "SOURCE_DATE_EPOCH=$(git -C \"$root\" show -s --format=%ct HEAD)" not in build_source:
    fail("kernel builds must use the commit epoch")
for token in (
    "CONFIG_SCHED_WALT=y",
    "CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y",
    "CONFIG_UCLAMP_TASK=y",
    "CONFIG_UCLAMP_TASK_GROUP=y",
    "CONFIG_PSI=y",
    "CONFIG_ZRAM=y",
    "CONFIG_IOSCHED_BFQ=y",
    "CONFIG_BFQ_GROUP_IOSCHED=y",
    "CONFIG_F2FS_FS=y",
    "CONFIG_BLK_WBT=y",
    "CONFIG_BLK_WBT_SQ=y",
    "CONFIG_THERMAL=y",
    "CONFIG_CPU_THERMAL=y",
    "CONFIG_THERMAL_TSENS=y",
    "CONFIG_QTI_BCL_PMIC5=y",
    "CONFIG_QTI_BCL_SOC_DRIVER=y",
    "CONFIG_QTI_THERMAL_LIMITS_DCVS=y",
    "CONFIG_BBG=y",
    "CONFIG_BBG_BLOCK_BOOT=y",
    "# CONFIG_BBG_BLOCK_RECOVERY is not set",
    "baseband_guard",
    "bbg_init",
):
    if token not in build_source:
        fail("kernel build configuration gate changed")
for token in (
    "CONFIG_LN8282=y",
    "CONFIG_BQ2597X_CHARGE_PUMP=y",
    "CONFIG_BQ_PUMP_WIRELESS_CHARGE=y",
    "CONFIG_FUEL_GAUGE_BQ27Z561=y",
    "CONFIG_QPNP_SMB5_CAS=y",
    "CONFIG_SMB1398_CHARGER_CAS=y",
    "CONFIG_FUEL_GAUGE_BQ28Z610=y",
    "CONFIG_CHARGER_BQ25790=y",
):
    if token not in build_source:
        fail("device charging configuration gate changed")

rom_prepare_source = indexed_text("scripts/dragonkernel/prepare_rom_boot.sh")
for token in (
    'payload-dumper-v0.1.6/payload-dumper',
    'extract "$input" -p boot',
    '"$work/payload/boot.img"',
):
    if token not in rom_prepare_source:
        fail("OTA payload boot extraction contract changed")

kheaders_source = (ROOT / "kernel/gen_kheaders.sh").read_text(encoding="utf-8")
for token in (
    "--sort=name",
    '--mtime="@${SOURCE_DATE_EPOCH:-0}"',
    "--owner=0 --group=0 --numeric-owner",
):
    if token not in kheaders_source:
        fail("embedded kernel headers must be reproducible")

print(f"DragonKernel baseline OK: {len(devices)} devices / kernel {actual}")
