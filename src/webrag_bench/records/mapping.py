"""Bench vocabulary (English) -> run record schema vocabulary (French, frozen)."""

from __future__ import annotations

_FAMILY = {"none": "aucune", "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4"}
_INDEX = {"dense": "dense", "bm25": "bm25", "hybrid": "hybride"}
_ACTION_TYPE = {"open": "action-open", "specified": "action-specifiee"}


def to_schema_family(family: str) -> str:
    return _FAMILY[family]


def to_schema_index(index: str) -> str:
    return _INDEX[index]


def to_schema_action_type(action_type: str) -> str:
    return _ACTION_TYPE[action_type]
