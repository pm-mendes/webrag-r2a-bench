"""Canonical JSON serialisation for signing and digests.

Keys sorted, no insignificant whitespace, UTF-8, and no floating-point values: floats
have no single canonical text form, so signed content must use integers or strings.
This is close to RFC 8785 (JCS) for the values accepted here, but conformance with JCS
is not claimed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _reject_floats(obj: Any) -> None:
    if isinstance(obj, float):
        raise TypeError("floats are not allowed in signed content (no canonical form)")
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError("object keys must be strings")
            _reject_floats(v)
    elif isinstance(obj, list | tuple):
        for v in obj:
            _reject_floats(v)


def canonical_json(obj: Any) -> bytes:
    _reject_floats(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(obj: Any) -> str:
    """SHA-256 of the canonical form, as `sha256:<hex>`. Bytes and str are hashed as is."""
    if isinstance(obj, bytes):
        data = obj
    elif isinstance(obj, str):
        data = obj.encode()
    else:
        data = canonical_json(obj)
    return "sha256:" + hashlib.sha256(data).hexdigest()
