#!/usr/bin/env python3
import re
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def value(text: str, label: str) -> str:
    matches = re.findall(rf"^{re.escape(label)}\s*(\S+)\s*(?:bytes)?$", text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(label)
    return matches[0]


def footer_options(info: str) -> list[str]:
    header, descriptors = info.split("Descriptors:\n", 1)
    if re.findall(r"^    (.+ descriptor):$", descriptors, re.MULTILINE) != ["Hash descriptor"]:
        raise ValueError("descriptors")
    if value(header, "Algorithm:") != "NONE":
        raise ValueError("signed footer")

    descriptor_flags = int(value(descriptors, "      Flags:"))
    if descriptor_flags & ~1:
        raise ValueError("descriptor flags")
    options = [
        "--partition_size", value(header, "Image size:"),
        "--partition_name", value(descriptors, "      Partition Name:"),
        "--hash_algorithm", value(descriptors, "      Hash Algorithm:"),
        "--salt", value(descriptors, "      Salt:"),
        "--algorithm", "NONE",
        "--rollback_index", value(header, "Rollback Index:"),
        "--rollback_index_location", value(header, "Rollback Index Location:"),
        "--flags", value(header, "Flags:"),
    ]
    if descriptor_flags == 1:
        options.append("--do_not_use_ab")
    return options


def refresh(avbtool: Path, template: Path, image: Path) -> None:
    try:
        info = subprocess.run(
            [sys.executable, avbtool, "info_image", "--image", template],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except subprocess.CalledProcessError as error:
        raise ValueError("inspect") from error
    try:
        options = footer_options(info)
    except (ValueError, IndexError) as error:
        raise ValueError("parse") from error
    try:
        subprocess.run(
            [sys.executable, avbtool, "add_hash_footer", "--image", image, *options],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        raise ValueError("generate") from error
    try:
        partition_name = options[options.index("--partition_name") + 1]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", partition_name):
            raise ValueError("partition name")
        with tempfile.TemporaryDirectory(dir=image.parent) as directory:
            verification_image = Path(directory) / f"{partition_name}{image.suffix}"
            os.link(image, verification_image)
            subprocess.run(
                [sys.executable, avbtool, "verify_image", "--image", verification_image],
                check=True,
                capture_output=True,
            )
    except subprocess.CalledProcessError as error:
        raise ValueError("verify") from error


def self_test() -> None:
    sample = """Image size:               67108864 bytes
Algorithm:                NONE
Rollback Index:           0
Flags:                    0
Rollback Index Location:  0
Descriptors:
    Hash descriptor:
      Image Size:            1 bytes
      Hash Algorithm:        sha256
      Partition Name:        boot
      Salt:                  00
      Digest:                00
      Flags:                 0
"""
    options = footer_options(sample)
    assert options[:6] == ["--partition_size", "67108864", "--partition_name", "boot", "--hash_algorithm", "sha256"]


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["--self-test"]:
            self_test()
        elif len(sys.argv) == 4:
            refresh(*(Path(arg).resolve() for arg in sys.argv[1:]))
        else:
            raise ValueError("usage")
    except ValueError as error:
        raise SystemExit(f"AVB footer refresh failed: {error}")
