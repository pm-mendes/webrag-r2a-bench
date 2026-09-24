"""JSONL persistence of run records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from webrag_bench.records.schema import validate_record


def append_record(record: dict[str, Any], path: Path) -> None:
    """Validate, then append one record. An invalid record is never written."""
    validate_record(record)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as f:
        return {json.loads(line)["id_episode"] for line in f if line.strip()}
