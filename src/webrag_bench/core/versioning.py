"""Version of the bench recorded in every run record (`version_banc`)."""

from __future__ import annotations

import subprocess

from webrag_bench import ROOT


def bench_version() -> str:
    """Git tag (or commit) of the bench; `-dirty` if the tree has local changes."""
    try:
        out = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "untagged"
    return out or "untagged"
