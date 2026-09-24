"""Per-task tool allowlist. DEMO condition, outside the frozen grid."""

from __future__ import annotations

from webrag_bench.core.tasks import Task
from webrag_bench.defenses.base import DecisionContext, Defense, ToolCall


class ToolAllowlistDemo(Defense):
    name = "tool-allowlist-demo"

    def authorize(self, call: ToolCall, task: Task, context: DecisionContext) -> bool:
        return call.tool in task.allowed_tools
