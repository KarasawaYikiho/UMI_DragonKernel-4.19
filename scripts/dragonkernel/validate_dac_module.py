#!/usr/bin/env python3
"""Validate a Dragon DAC root-manager module without installing it."""

from __future__ import annotations

import argparse
import hashlib
import tempfile
import zipfile
from pathlib import Path

from package_dac_module import REQUIRED, package


def fail(message: str) -> None:
    raise SystemExit(f"DAC module validation failed: {message}")


def validate(module_zip: Path, checksum: Path) -> None:
    expected_line = f"{hashlib.sha256(module_zip.read_bytes()).hexdigest()}  {module_zip.name}"
    if checksum.read_text(encoding="ascii").strip() != expected_line:
        fail("checksum mismatch or non-portable checksum entry")
    with zipfile.ZipFile(module_zip) as archive:
        expected_members = [*REQUIRED, "bin/dragon-dac"]
        if archive.namelist() != expected_members:
            fail("member order or inventory changed")
        for name in REQUIRED:
            expected_mode = 0o755 if name.endswith(".sh") else 0o644
            if (archive.getinfo(name).external_attr >> 16) & 0o777 != expected_mode:
                fail(f"invalid mode: {name}")
        if (archive.getinfo("bin/dragon-dac").external_attr >> 16) & 0o777 != 0o700:
            fail("invalid daemon mode")
        binary = archive.read("bin/dragon-dac")
        if len(binary) < 20 or binary[:6] != b"\x7fELF\x02\x01":
            fail("daemon is not a 64-bit little-endian ELF")
        if int.from_bytes(binary[18:20], "little") != 183:
            fail("daemon is not AArch64")
        if b"libc++_shared.so" in binary:
            fail("daemon has an unbundled libc++ dependency")
        properties = archive.read("module.prop").decode("utf-8").splitlines()
        if not {"id=dragon_dac", "version=0.2.0", "versionCode=2"} <= set(properties):
            fail("module identity changed")
        config = set(archive.read("config/dac.conf").decode("utf-8").splitlines())
        for token in ("dac.enabled=false", "dac.dry_run=true", "dac.cloud_control.remote=block"):
            if token not in config:
                fail("safe defaults changed")
        for name in ("customize.sh", "service.sh", "uninstall.sh", "action.sh"):
            script = archive.read(name)
            if not script.startswith(b"#!/system/bin/sh\n") or b"\r\n" in script:
                fail(f"invalid Android shell script: {name}")


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        binary = root / "dragon-dac"
        header = bytearray(64)
        header[:6] = b"\x7fELF\x02\x01"
        header[18:20] = (183).to_bytes(2, "little")
        binary.write_bytes(header)
        module_zip = package(binary, root, "202608111900", 1_786_400_000)
        validate(module_zip, root / f"{module_zip.name}.sha256")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--checksum", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.zip or not args.checksum:
        parser.error("--zip and --checksum are required")
    validate(args.zip, args.checksum)
    print("DAC module contract OK")


if __name__ == "__main__":
    main()
