"""Scripted, deterministic generator for dry runs ONLY."""

from __future__ import annotations

import json
import re
from typing import Any

from webrag_bench.defenses import ToolCall
from webrag_bench.generators.base import Response


class StubGenerator:
    """Obeys every `CALL <server.tool> <json>` line in its context.

    This is the worst case of compliance, useful to check that stages, defenses and
    oracles are wired. Its timing is meaningless for the pilot.
    """

    is_stub = True
    _PATTERN = re.compile(r"CALL\s+([a-z_]+\.[a-z_]+)\s+(\{[^{}]*\})", re.S)

    def __init__(self, name: str, version_id: str) -> None:
        self.name, self.version_id = name, version_id

    def generate(self, system: str, user: str, tools: list[dict[str, Any]]) -> Response:
        known = {t["name"] for t in tools}
        calls = []
        for tool, raw in self._PATTERN.findall(user):
            try:
                arguments = json.loads(raw.replace("&quot;", '"'))
            except json.JSONDecodeError:
                continue
            if tool in known:
                calls.append(ToolCall(tool, arguments))
        return Response(text="(stub response)", calls=calls, returned_model_id=self.version_id)
