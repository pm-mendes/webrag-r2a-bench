"""Defense conditions.

A defense acts at two points: on the context (before generation) and on each tool
call (before execution). A refused call is recorded with `bloque_par`.

The six conditions of the manuscript — Progent included — are FROZEN elements. Until
their exact configuration and code version are imported into config/frozen/defenses/,
they raise `UnspecifiedDefense` instead of being approximated.
"""

from webrag_bench.defenses.base import Defense, NoDefense, ToolCall, UnspecifiedDefense
from webrag_bench.defenses.registry import PENDING_DEFENSES, get_defense

__all__ = ["PENDING_DEFENSES", "Defense", "NoDefense", "ToolCall", "UnspecifiedDefense", "get_defense"]
