"""Defense lookup by name."""

from __future__ import annotations

from webrag_bench.defenses.base import Defense, NoDefense, UnspecifiedDefenseError
from webrag_bench.defenses.tool_allowlist import ToolAllowlistDemo

_DEFENSES: dict[str, type[Defense]] = {
    "none": NoDefense,
    "tool-allowlist-demo": ToolAllowlistDemo,
}

PENDING_DEFENSES = ("progent", "PENDING-D2", "PENDING-D3", "PENDING-D4", "PENDING-D5")


def get_defense(name: str) -> Defense:
    if name in _DEFENSES:
        return _DEFENSES[name]()
    if name in PENDING_DEFENSES:
        raise UnspecifiedDefenseError(
            f"defense {name!r}: exact configuration and code version must be imported from "
            "the manuscript into config/frozen/defenses/; it is not approximated here"
        )
    raise ValueError(f"unknown defense condition {name!r}")
