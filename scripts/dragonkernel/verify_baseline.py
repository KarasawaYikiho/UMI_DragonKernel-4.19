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


def indexed_text(path: str) -> str:
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
    "variant_names": {
        "original": "Original",
        "magisk": "Magisk",
        "kernelsu": "KernelSU",
        "sukisu-kpm-susfs": "SukiSU_KPM_SUSFS",
    },
}
if data.get("release_naming") != expected_release_naming:
    fail("release naming contract changed")

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

root_hiding = data.get("common_security", {}).get("root_hiding", {})
if set(root_hiding.get("required_variants", [])) != expected_variants - {"original"}:
    fail("root hiding must cover every Root variant")
if root_hiding.get("validation_layers") != ["kernel", "manager", "application"]:
    fail("root hiding validation layers changed")

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

avbtool = data.get("boot_tools", {}).get("avbtool", {})
if avbtool != {
    "url": "https://android.googlesource.com/platform/external/avb",
    "ref": "android-15.0.0_r1",
    "commit": "25a14f7e3e6493a7f1a42aa9f78209d4dbe848e9",
}:
    fail("unexpected avbtool lock")

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

print(f"DragonKernel baseline OK: {len(devices)} devices / kernel {actual}")
