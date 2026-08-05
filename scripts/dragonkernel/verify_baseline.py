#!/usr/bin/env python3
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
forbidden_files = {"AGENT.md", "AGENTS.md", "Agent.md", "Agents.md"}
forbidden_prefixes = (".dragonkernel-private/", "artifacts/", "private/", "temp/", "tmp/")
forbidden_suffixes = (".log", ".tmp")
for path in tracked:
    if (
        path in forbidden_files
        or path.startswith(forbidden_prefixes)
        or path.endswith(forbidden_suffixes)
    ):
        fail(f"forbidden engineering or temporary file is tracked: {path}")

for path in data["kernel"]["config_fragments"]:
    if path not in tracked:
        fail(f"missing config fragment: {path}")

devices = data["device_family"]["devices"]
if len({device["codename"] for device in devices}) != len(devices):
    fail("device codenames are not unique")
for device in devices:
    if device["config"] not in tracked:
        fail(f"missing device config: {device['config']}")

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
    if not upstream["url"].startswith("https://github.com/"):
        fail(f"{name} URL is not HTTPS GitHub")

toolchain = data["toolchain"]
if not re.fullmatch(r"[0-9a-f]{40}", toolchain["commit"]):
    fail("toolchain commit is not a full SHA-1")
if toolchain["name"] != "clang-r416183b":
    fail("unexpected baseline toolchain")

print(f"DragonKernel baseline OK: {len(devices)} devices / kernel {actual}")
