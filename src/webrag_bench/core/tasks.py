"""Tasks: user request, targeted page, adversarial goal.

The task list is FROZEN (config/frozen/tasks/); config/demo/tasks/ is for the dry
run only.

`action_type` is the partition used by the run record schema:
- open      : the request delegates the action to the content ("do what the page says")
- specified : the request fixes the action; content should only inform it
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator


class AdversarialGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str
    arguments: dict[str, Any]

    @field_validator("arguments")
    @classmethod
    def _carries_canary(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not any("{canary}" in str(x) for x in v.values()):
            raise ValueError(
                "the adversarial goal must carry {canary}, "
                "otherwise the action oracle is not mechanical"
            )
        return v


class _TaskFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["DEMO", "FROZEN"]
    id: str
    request: str
    action_type: Literal["open", "specified"]
    target_page: str
    allowed_tools: list[str] = []
    adversarial_goal: AdversarialGoal


@dataclass(frozen=True)
class Task:
    id: str
    request: str
    action_type: str
    target_page: str
    adversarial_goal: dict[str, Any]
    allowed_tools: tuple[str, ...]

    def goal_for(self, canary_token: str) -> dict[str, Any]:
        """Adversarial goal with the canary substituted in every string argument."""
        goal = copy.deepcopy(self.adversarial_goal)
        goal["arguments"] = {
            k: v.format(canary=canary_token) if isinstance(v, str) else v
            for k, v in goal["arguments"].items()
        }
        return goal


def load_tasks(directory: Path) -> list[Task]:
    tasks = []
    for path in sorted(directory.glob("*.yaml")):
        f = _TaskFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        tasks.append(
            Task(
                f.id,
                f.request,
                f.action_type,
                f.target_page,
                f.adversarial_goal.model_dump(),
                tuple(f.allowed_tools),
            )
        )
    ids = [t.id for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate task ids in {directory}")
    return tasks
