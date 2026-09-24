"""Defense interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from webrag_bench.core.tasks import Task


class UnspecifiedDefenseError(NotImplementedError):
    """The defense is part of the frozen protocol but its configuration is not imported."""


@dataclass(frozen=True)
class ToolCall:
    tool: str  # "<server>.<tool>"
    arguments: dict[str, Any]


@dataclass(frozen=True)
class DecisionContext:
    """What a defense may look at when authorising a call, besides the call and the task.

    `pages` is the per-page provenance of the context (origin, attested, verified) when
    the episode runs with signed provenance; empty otherwise.
    """

    signed: bool = False
    pages: tuple[dict[str, Any], ...] = field(default_factory=tuple)


class Defense:
    """Base class; on its own it is the `none` condition (lets everything through)."""

    name = "none"

    def filter_context(self, passages: list[str]) -> list[str]:
        return passages

    requires_provenance = False

    def authorize(self, call: ToolCall, task: Task, context: DecisionContext) -> bool:
        return True


class NoDefense(Defense):
    name = "none"
