"""Campaign entry gate: a FROZEN plan refuses to start while anything is unresolved."""

from __future__ import annotations

from pathlib import Path

from webrag_bench.freeze.fingerprint import collect_files

MARKERS = {"PENDING": "PENDING value", "status: DEMO": "DEMO element"}


class IncompleteFreeze(RuntimeError):
    pass


def blocking_markers(paths: list[Path]) -> list[str]:
    """Files that still contain a PENDING value or a DEMO element."""
    found = []
    for f in collect_files(paths):
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found += [f"{f}: {label}" for marker, label in MARKERS.items() if marker in text]
    return found


def require_complete_freeze(paths: list[Path], what: str = "campaign") -> None:
    markers = blocking_markers(paths)
    if markers:
        raise IncompleteFreeze(f"{what} refused: unresolved elements.\n  " + "\n  ".join(markers))
