#!/usr/bin/env python3
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

VARIANTS = {
    "original": "Original",
    "magisk": "Magisk",
    "kernelsu": "KernelSU",
    "sukisu-kpm-susfs": "SukiSU_KPM_SUSFS",
}


def release_names(variant: str, timestamp: str | None = None) -> tuple[str, str]:
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant: {variant}")
    timestamp = timestamp or datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d%H%M")
    if datetime.strptime(timestamp, "%Y%m%d%H%M").strftime("%Y%m%d%H%M") != timestamp:
        raise ValueError(f"invalid timestamp: {timestamp}")
    stem = f"UMI_{timestamp}_{VARIANTS[variant]}"
    return stem, f"{stem}_Build"


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        assert release_names("kernelsu", "202608052353") == (
            "UMI_202608052353_KernelSU",
            "UMI_202608052353_KernelSU_Build",
        )
    elif len(sys.argv) in (2, 3):
        tag, asset_base = release_names(*sys.argv[1:])
        print(f"tag={tag}")
        print(f"asset_base={asset_base}")
    else:
        raise SystemExit(f"usage: {sys.argv[0]} <variant> [yyyyMMddHHmm]")
