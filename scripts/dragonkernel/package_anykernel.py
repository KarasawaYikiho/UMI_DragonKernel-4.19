#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "Documentation/dragonkernel/baseline.json"
DEVICES = ("umi", "cmi", "cas", "thyme", "apollo")
VARIANT_CONFIG = {
    "original": "CONFIG_DRAGONKERNEL_ROOT_NONE=y",
    "kernelsu": "CONFIG_DRAGONKERNEL_KERNELSU=y",
    "sukisu": "CONFIG_DRAGONKERNEL_SUKISU=y",
}
VARIANT_LABEL = {
    "original": "Original",
    "kernelsu": "KernelSU",
    "sukisu": "SukiSU_KPM_SUSFS",
}
DEVICE_CONFIG = {
    device: f"CONFIG_MACH_XIAOMI_{device.upper()}=y" for device in DEVICES
}
ZIP_TIME = (2020, 1, 1, 0, 0, 0)


def fail(message: str) -> None:
    raise SystemExit(f"package check failed: {message}")


def template_script(device: str, variant: str) -> bytes:
    android = json.loads(BASELINE.read_text(encoding="utf-8"))["device_family"][
        "android"
    ]
    return f"""### UMI DragonKernel AnyKernel3 install

properties() {{ '
kernel.string=UMI DragonKernel 4.19 {VARIANT_LABEL[variant]} ({device})
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=1
device.name1={device}
supported.versions={android}
supported.patchlevels=
supported.vendorpatchlevels=
'; }}

BLOCK=boot;
IS_SLOT_DEVICE=auto;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=0;
NO_VBMETA_PARTITION_PATCH=1;
SLOT_SELECT=active;

. tools/ak3-core.sh;
split_boot;
flash_boot;
""".encode()


def add_bytes(archive: zipfile.ZipFile, name: str, content: bytes, mode: int) -> None:
    info = zipfile.ZipInfo(name, ZIP_TIME)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o100000 | mode) << 16
    archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def add_file(archive: zipfile.ZipFile, source: Path, name: str, mode: int) -> None:
    info = zipfile.ZipInfo(name, ZIP_TIME)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o100000 | mode) << 16
    with source.open("rb") as source_file, archive.open(info, "w", force_zip64=True) as target:
        shutil.copyfileobj(source_file, target, length=1024 * 1024)


def write_package(template: Path, image: Path, device: str, variant: str, output: Path) -> None:
    required = (
        template / "LICENSE",
        template / "META-INF/com/google/android/update-binary",
        template / "META-INF/com/google/android/updater-script",
        template / "tools/ak3-core.sh",
    )
    if any(not path.is_file() for path in required):
        fail("AnyKernel3 template is incomplete")
    if not image.is_file() or image.stat().st_size < 64:
        fail("kernel Image is missing")

    entries = [(template / "LICENSE", "LICENSE", 0o644)]
    for directory in (template / "META-INF", template / "tools"):
        for path in sorted(item for item in directory.rglob("*") if item.is_file()):
            relative = path.relative_to(template).as_posix()
            mode = 0o755 if relative.endswith("update-binary") or relative.startswith("tools/") else 0o644
            entries.append((path, relative, mode))

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", allowZip64=True) as archive:
        for source, name, mode in entries:
            add_file(archive, source, name, mode)
        add_bytes(archive, "anykernel.sh", template_script(device, variant), 0o755)
        add_file(archive, image, "Image", 0o644)


def validate_inputs(template: Path, artifact: Path, device: str, variant: str) -> Path:
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    expected = data["boot_tools"]["anykernel3"]["commit"]
    try:
        actual = subprocess.check_output(
            ["git", "-C", template, "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        fail("AnyKernel3 template is not a Git checkout")
    if actual != expected:
        fail("AnyKernel3 template commit mismatch")
    if subprocess.run(["git", "-C", template, "diff", "--quiet"]).returncode:
        fail("AnyKernel3 template has tracked changes")

    config_path = artifact / ".config"
    image = artifact / "arch/arm64/boot/Image"
    if not config_path.is_file():
        fail("artifact config is missing")
    config = set(config_path.read_text(encoding="utf-8").splitlines())
    for token in (DEVICE_CONFIG[device], VARIANT_CONFIG[variant], "CONFIG_BBG=y"):
        if token not in config:
            fail(f"artifact config missing {token}")
    with image.open("rb") as image_file:
        image_file.seek(56)
        magic = image_file.read(4)
    if magic != b"ARMd":
        fail("artifact is not an ARM64 Image")
    return image


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        template = root / "template"
        artifact = root / "artifact"
        for relative in (
            "LICENSE",
            "META-INF/com/google/android/update-binary",
            "META-INF/com/google/android/updater-script",
            "tools/ak3-core.sh",
            "tools/magiskboot",
        ):
            path = template / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode())
        image = artifact / "arch/arm64/boot/Image"
        image.parent.mkdir(parents=True)
        content = bytearray(64)
        content[56:60] = b"ARMd"
        image.write_bytes(content)
        first, second = root / "first.zip", root / "second.zip"
        write_package(template, image, "umi", "original", first)
        write_package(template, image, "umi", "original", second)
        if hashlib.sha256(first.read_bytes()).digest() != hashlib.sha256(second.read_bytes()).digest():
            fail("package is not reproducible")
        with zipfile.ZipFile(first) as archive:
            names = archive.namelist()
            script = archive.read("anykernel.sh")
            modes = {
                name: (archive.getinfo(name).external_attr >> 16) & 0o777
                for name in names
            }
        if names != [
            "LICENSE",
            "META-INF/com/google/android/update-binary",
            "META-INF/com/google/android/updater-script",
            "tools/ak3-core.sh",
            "tools/magiskboot",
            "anykernel.sh",
            "Image",
        ]:
            fail("package member contract changed")
        for token in (b"device.name1=umi", b"BLOCK=boot", b"split_boot", b"flash_boot"):
            if token not in script:
                fail("installer contract changed")
        if modes["anykernel.sh"] != 0o755 or modes["Image"] != 0o644:
            fail("package permissions changed")
    print("AnyKernel3 packaging contract OK.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("device", nargs="?", choices=DEVICES)
    parser.add_argument("variant", nargs="?", choices=tuple(VARIANT_CONFIG))
    parser.add_argument("template", nargs="?", type=Path)
    parser.add_argument("artifact", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if None in (args.device, args.variant, args.template, args.artifact, args.output):
        parser.error("device, variant, template, artifact and output are required")
    image = validate_inputs(args.template, args.artifact, args.device, args.variant)
    write_package(args.template, image, args.device, args.variant, args.output)
    print(f"Packaged {VARIANT_LABEL[args.variant]} candidate for {args.device}.")


if __name__ == "__main__":
    main()
