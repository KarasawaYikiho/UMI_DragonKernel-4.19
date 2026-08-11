#!/usr/bin/env python3
"""Deterministic preflight for the final security and conflict review."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_PATHS = (
    re.compile(r"(^|/)(AGENT|AGENTS)\.md$", re.IGNORECASE),
    re.compile(r"(^|/)\.dragonkernel-private(/|$)"),
    re.compile(r"(^|/)(__pycache__|\.pytest_cache|out|artifacts?)(/|$)"),
)
ADDED_LINE_RULES = {
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "selinux-off": re.compile(
        r"\bsetenforce\s+0\b|CONFIG_SECURITY_SELINUX_" + "DISABLE=y"
    ),
    "world-writable": re.compile(r"\bchmod\s+(?:-R\s+)?777\b"),
    "remote-shell": re.compile(
        r"\b(?:" + "cu" + "rl|wg" + "et" + r")\b[^\n|]*\|\s*(?:ba)?sh\b"
    ),
    "privileged-pr": re.compile(
        r"^\s*pull_request_" + "target" + r"\s*:|^\s*permissions\s*:\s*write-" + "all" + r"\s*$"
    ),
}
OWNER_SCOPES = {
    "scheduler": ("kernel/sched/", "drivers/cpufreq/", "kernel/cgroup/"),
    "thermal": ("drivers/thermal/", "arch/arm64/boot/dts/"),
    "battery": ("drivers/power/supply/",),
    "root": ("drivers/kernelsu/", "drivers/sukisu/", "patches/sukisu/", "patches/susfs/"),
    "bbg": ("drivers/baseband-guard/", "patches/bbg/"),
    "dac": ("tools/dragon-dac/",),
    "packaging": ("scripts/dragonkernel/package_", "scripts/dragonkernel/repack_"),
    "ci": (".github/workflows/",),
}


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace"
    )


def resolve_commit(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise SystemExit("candidate and base must be full lowercase commit SHAs")
    resolved = git("rev-parse", "--verify", f"{value}^{{commit}}").strip()
    if resolved != value:
        raise SystemExit("commit resolution mismatch")
    return resolved


def added_line_findings(diff: str) -> list[str]:
    findings: set[str] = set()
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        for name, pattern in ADDED_LINE_RULES.items():
            if pattern.search(line[1:]):
                findings.add(name)
    return sorted(findings)


def changed_paths(base: str, candidate: str) -> list[str]:
    return sorted(path for path in git("diff", "--name-only", "-z", base, candidate).split("\0") if path)


def unsafe_tree_paths(candidate: str) -> list[str]:
    unsafe: list[str] = []
    for record in git("ls-tree", "-r", "-z", candidate).split("\0"):
        if not record:
            continue
        metadata, path = record.split("\t", 1)
        mode = metadata.split(" ", 1)[0]
        if any(pattern.search(path) for pattern in FORBIDDEN_PATHS):
            unsafe.append(path)
            continue
        if mode == "120000":
            target = PurePosixPath(git("show", f"{candidate}:{path}").strip())
            resolved = posixpath.normpath(str(PurePosixPath(path).parent / target))
            if target.is_absolute() or resolved == ".." or resolved.startswith("../"):
                unsafe.append(path)
    return sorted(unsafe)


def owner_scopes(paths: list[str]) -> list[str]:
    return sorted(
        name
        for name, prefixes in OWNER_SCOPES.items()
        if any(path.startswith(prefix) for path in paths for prefix in prefixes)
    )


def self_test() -> None:
    assert added_line_findings("+chmod " + "777 /x\n context\n") == ["world-writable"]
    assert added_line_findings("+++ b/file\n+cu" + "rl x | sh\n") == ["remote-shell"]
    assert owner_scopes(["kernel/sched/core.c", "tools/dragon-dac/src/main.cpp"]) == [
        "dac",
        "scheduler",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--candidate")
    parser.add_argument("--output", type=Path, default=Path("release-preflight.json"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.base or not args.candidate:
        parser.error("--base and --candidate are required")
    base = resolve_commit(args.base)
    candidate = resolve_commit(args.candidate)
    if git("rev-parse", "HEAD").strip() != candidate:
        raise SystemExit("checked-out HEAD does not match candidate")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("tracked worktree is not clean")
    if subprocess.run(["git", "merge-base", "--is-ancestor", base, candidate], cwd=ROOT).returncode:
        raise SystemExit("base is not an ancestor of candidate")
    subprocess.check_call(["git", "diff", "--check", base, candidate], cwd=ROOT)
    paths = changed_paths(base, candidate)
    unsafe = unsafe_tree_paths(candidate)
    diff = git("diff", "--no-ext-diff", "--no-renames", "--unified=0", base, candidate)
    findings = added_line_findings(diff)
    if unsafe or findings:
        raise SystemExit(
            "release preflight blocked: "
            + json.dumps({"unsafe_paths": unsafe, "rules": findings}, sort_keys=True)
        )
    report = {
        "schema": 1,
        "base_sha": base,
        "candidate_sha": candidate,
        "changed_files": len(paths),
        "conflict_review_scopes": owner_scopes(paths),
        "known_hazard_findings": [],
        "manual_security_review_required": True,
        "manual_conflict_review_required": True,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
