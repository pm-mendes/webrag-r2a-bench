"""Deterministic SHA-256 over a set of files and directories."""

from __future__ import annotations

import hashlib
from pathlib import Path


def collect_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        out += sorted(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else [p]
    return sorted(set(out))


def fingerprint(paths: list[Path], root: Path) -> str:
    h = hashlib.sha256()
    for f in collect_files(paths):
        name = f.relative_to(root) if f.is_relative_to(root) else Path(f.name)
        h.update(str(name).encode() + b"\0")
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()
