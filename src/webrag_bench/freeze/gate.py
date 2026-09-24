"""Campaign entry gate: a FROZEN plan refuses to start while anything is unresolved."""

from __future__ import annotations

from pathlib import Path

from webrag_bench.freeze.fingerprint import collect_files

MARKERS = {"PENDING": "PENDING value", "status: DEMO": "DEMO element"}


class IncompleteFreezeError(RuntimeError):
    pass


def blocking_markers(paths: list[Path]) -> list[str]:
    """Files that still contain a PENDING value or a DEMO element, and referenced paths
    that do not exist (e.g. a directory still named "PENDING - ..." in the plan)."""
    found = [f"{p}: missing path" for p in paths if not p.exists()]
    for f in collect_files([p for p in paths if p.exists()]):
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found += [f"{f}: {label}" for marker, label in MARKERS.items() if marker in text]
    return found


def require_complete_freeze(paths: list[Path], what: str = "campaign") -> None:
    markers = blocking_markers(paths)
    if markers:
        raise IncompleteFreezeError(
            f"{what} refused: unresolved elements.\n  " + "\n  ".join(markers)
        )
