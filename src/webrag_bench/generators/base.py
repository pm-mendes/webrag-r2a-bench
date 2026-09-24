"""Generator interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from webrag_bench.defenses import ToolCall


@dataclass
class Response:
    text: str
    calls: list[ToolCall]
    returned_model_id: str
    errors: list[str] = field(default_factory=list)


class Generator(Protocol):
    name: str
    version_id: str
    is_stub: bool

    def generate(self, system: str, user: str, tools: list[dict[str, Any]]) -> Response: ...
