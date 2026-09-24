"""Version of the bench recorded in every run record (`version_banc`)."""

from __future__ import annotations

import os
import subprocess

from webrag_bench import ROOT

ENV_VAR = "WEBRAG_BENCH_VERSION"
"""Set at image build time, where there is no .git directory to describe."""


def bench_version() -> str:
    """Git tag (or commit) of the bench; `-dirty` if the tree has local changes.

    Inside a container image, the version captured at build time (`WEBRAG_BENCH_VERSION`)
    is used instead.
    """
    if os.environ.get(ENV_VAR):
        return os.environ[ENV_VAR]
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
