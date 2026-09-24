"""Carrying attestations in MCP tool results (`_meta`).

A signing server returns `attach(text, attestation)` from a tool; a client reads it
back with `extract(result)`. A result without an attestation is simply unsigned.
"""

from __future__ import annotations

from typing import Any

from mcp_types import CallToolResult, TextContent

from webrag_bench.provenance.attestation import Attestation

META_KEY = "io.webrag/provenance"


def attach(text: str, attestation: Attestation) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=text)], meta={META_KEY: attestation.to_dict()}
    )


def extract(result: Any) -> Attestation | None:
    meta = getattr(result, "meta", None) or {}
    raw = meta.get(META_KEY)
    return Attestation.from_dict(raw) if raw else None
