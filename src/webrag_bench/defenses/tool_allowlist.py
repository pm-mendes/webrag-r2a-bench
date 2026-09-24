"""Per-task tool allowlist. DEMO condition, outside the frozen grid."""

from __future__ import annotations

from webrag_bench.core.tasks import Task
from webrag_bench.defenses.base import Defense, ToolCall


class ToolAllowlistDemo(Defense):
    name = "tool-allowlist-demo"

    def authorize(self, call: ToolCall, task: Task) -> bool:
        return call.tool in task.allowed_tools
