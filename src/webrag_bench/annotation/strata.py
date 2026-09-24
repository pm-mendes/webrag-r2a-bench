"""Stratum keys, read from run records (schema field names)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Record = dict[str, Any]

STRATUM_KEYS: dict[str, Callable[[Record], str]] = {
    "family": lambda r: r["famille_attaque"],
    "defense": lambda r: r["condition_defense"],
    "defense_on": lambda r: "off" if r["condition_defense"] == "none" else "on",
    "generator": lambda r: r["generateur"]["nom"],
    "index": lambda r: r["index_recherche"],
    "reader": lambda r: r["lecteur"]["nom"],
    "action_type": lambda r: r["tache"]["type_action"],
    "task": lambda r: r["tache"]["id"],
}


def stratum_of(record: Record, keys: list[str]) -> tuple[str, ...]:
    return tuple(STRATUM_KEYS[k](record) for k in keys)
