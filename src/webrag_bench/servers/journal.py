"""Journal of the effects produced during one episode."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Journal:
    effects: list[dict[str, Any]] = field(default_factory=list)

    def record(self, tool: str, **arguments: Any) -> None:
        self.effects.append({"tool": tool, "arguments": arguments})
