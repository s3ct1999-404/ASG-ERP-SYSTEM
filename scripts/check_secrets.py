#!/usr/bin/env python3
"""Scan git-tracked text files for likely committed secrets.

A guard, not a guarantee: it catches common token shapes and quoted credential
assignments. Lines containing an allow-marker (placeholder / not-a-secret) are
skipped. Exit code 1 if anything is found; findings never print the matched value.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

PATTERNS: dict[str, re.Pattern[str]] = {
    "GitHub token": re.compile(
        r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|github_pat_[A-Za-z0-9_]{30,}"
    ),
    "AWS access key id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "API key (sk- style)": re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{20,}\b"),
    "Quoted credential assignment": re.compile(
        r"""(?i)(?<![a-z])(password|passwd|secret|token|api[_-]?key)\w*\s*[:=]\s*(['"])[^'"\s]{12,}\2"""
    ),
}
ALLOW_MARKERS = ("not-a-secret", "placeholder", "replace-with", "example")
SKIP_NAMES = {"package-lock.json"}
MAX_BYTES = 1_000_000


def tracked_files(root: Path) -> list[Path]:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable not found")
    out = subprocess.run(  # noqa: S603
        [git, "ls-files", "-z"], cwd=root, capture_output=True, check=True
    ).stdout
    return [root / name for name in out.decode().split("\0") if name]


def scan_text(text: str) -> list[tuple[int, str]]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        if any(marker in line.lower() for marker in ALLOW_MARKERS):
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append((number, label))
    return findings


def scan_repo(root: Path) -> list[tuple[str, int, str]]:
    results = []
    for path in tracked_files(root):
        if path.name in SKIP_NAMES or not path.is_file() or path.stat().st_size > MAX_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary file
        for number, label in scan_text(text):
            results.append((str(path.relative_to(root)), number, label))
    return results


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    findings = scan_repo(root)
    for name, number, label in findings:
        print(f"{name}:{number}: possible secret ({label})")
    if findings:
        print(f"FAIL: {len(findings)} possible secret(s). Remove them and rotate if real.")
        return 1
    print("OK: no likely secrets in tracked files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
