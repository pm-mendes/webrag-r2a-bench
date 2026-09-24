"""Defense interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from webrag_bench.core.tasks import Task


class UnspecifiedDefenseError(NotImplementedError):
    """The defense is part of the frozen protocol but its configuration is not imported."""


@dataclass(frozen=True)
class ToolCall:
    tool: str  # "<server>.<tool>"
    arguments: dict[str, Any]


class Defense:
    """Base class; on its own it is the `none` condition (lets everything through)."""

    name = "none"

    def filter_context(self, passages: list[str]) -> list[str]:
        return passages

    def authorize(self, call: ToolCall, task: Task) -> bool:
        return True


class NoDefense(Defense):
    name = "none"
