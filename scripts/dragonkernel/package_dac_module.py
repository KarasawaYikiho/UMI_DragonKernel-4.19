#!/usr/bin/env python3
"""Create a deterministic root-manager module ZIP for Dragon DAC."""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from release_name import module_asset_name


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/dragon-dac/module"
REQUIRED = (
    "module.prop",
    "customize.sh",
    "service.sh",
    "uninstall.sh",
    "action.sh",
    "config/dac.conf",
)


def zip_time(epoch: int) -> tuple[int, int, int, int, int, int]:
    value = datetime.fromtimestamp(max(epoch, 315532800), timezone.utc)
    return value.year, value.month, value.day, value.hour, value.minute, value.second // 2 * 2


def add_bytes(archive: zipfile.ZipFile, name: str, data: bytes, mode: int, epoch: int) -> None:
    info = zipfile.ZipInfo(name, zip_time(epoch))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, data)


def package(binary: Path, output_dir: Path, timestamp: str, epoch: int) -> Path:
    if not binary.is_file():
        raise SystemExit(f"missing DAC binary: {binary}")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / module_asset_name(timestamp)
    with zipfile.ZipFile(destination, "w", strict_timestamps=True) as archive:
        for relative in REQUIRED:
            source = MODULE / relative
            if not source.is_file():
                raise SystemExit(f"missing module member: {relative}")
            mode = 0o755 if relative.endswith(".sh") else 0o644
            add_bytes(archive, relative, source.read_bytes(), mode, epoch)
        add_bytes(archive, "bin/dragon-dac", binary.read_bytes(), 0o700, epoch)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    (output_dir / f"{destination.name}.sha256").write_text(
        f"{digest}  {destination.name}\n", encoding="ascii"
    )
    return destination


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        binary = root / "dragon-dac"
        binary.write_bytes(b"test-binary\n")
        first = package(binary, root / "a", "202608111800", 1_786_400_000)
        second = package(binary, root / "b", "202608111800", 1_786_400_000)
        assert first.read_bytes() == second.read_bytes()
        with zipfile.ZipFile(first) as archive:
            assert archive.namelist() == [*REQUIRED, "bin/dragon-dac"]
            assert (archive.getinfo("service.sh").external_attr >> 16) & 0o777 == 0o755
            assert (archive.getinfo("bin/dragon-dac").external_attr >> 16) & 0o777 == 0o700


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--timestamp")
    parser.add_argument("--source-date-epoch", type=int, default=int(os.environ.get("SOURCE_DATE_EPOCH", "0")))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.binary or not args.output_dir or not args.timestamp:
        parser.error("--binary, --output-dir and --timestamp are required")
    print(package(args.binary, args.output_dir, args.timestamp, args.source_date_epoch))


if __name__ == "__main__":
    main()
