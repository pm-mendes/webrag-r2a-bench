"""Schema loading and validation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import jsonschema

from webrag_bench import ROOT

SCHEMA_PATH = ROOT / "schemas" / "run_record_schema.json"
_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
_VALIDATOR = jsonschema.Draft202012Validator(
    _SCHEMA, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
)


def arguments_digest(arguments: dict[str, Any]) -> str:
    canonical = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_record(record: dict[str, Any]) -> None:
    errors = sorted(_VALIDATOR.iter_errors(record), key=lambda e: list(e.path))
    if errors:
        raise jsonschema.ValidationError(
            "; ".join(f"{'/'.join(map(str, e.path))}: {e.message}" for e in errors)
        )
