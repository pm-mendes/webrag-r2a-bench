"""Execution plan: cells, seeds, episode ids.

Cells are the Cartesian product of each subplan's factors; a design that is not
fully crossed is declared as several subplans, each crossed — the form required by
the kit's PLAN_MANIFEST.json (grid reconciled as a sum of subplans).

The episode id and seed derive from (plan, cell, repetition): rerunning a plan yields
the same ids, which makes resuming safe.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from webrag_bench import ROOT
from webrag_bench.config import PlanConfig, PlanStatus
from webrag_bench.core.tasks import Task, load_tasks
from webrag_bench.freeze import require_complete_freeze

_FROZEN_DIR_KEYS = ("corpus", "attacks_dir", "tasks_dir", "defenses_dir", "judge_dir")


@dataclass(frozen=True)
class Cell:
    subplan: str
    task: str
    family: str
    defense: str
    generator: str
    index: str
    reader: str
    repetition: int

    def key(self) -> str:
        return "|".join(
            map(
                str,
                (
                    self.subplan,
                    self.task,
                    self.family,
                    self.defense,
                    self.generator,
                    self.index,
                    self.reader,
                    self.repetition,
                ),
            )
        )


class Plan:
    def __init__(self, path: Path, config: PlanConfig) -> None:
        self.path = path
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def is_frozen(self) -> bool:
        return self.config.status is PlanStatus.FROZEN

    def resolve(self, relative: str) -> Path:
        return ROOT / relative

    def tasks(self) -> list[Task]:
        return load_tasks(self.resolve(self.config.tasks_dir))

    def cells(self) -> list[Cell]:
        known = {t.id for t in self.tasks()}
        cells = []
        for name, grid in self.config.subplans.items():
            tasks = sorted(known) if grid.tasks == "all" else grid.tasks
            unknown = set(tasks) - known
            if unknown:
                raise ValueError(f"subplan {name}: unknown tasks {sorted(unknown)}")
            for task, family, defense, generator, index, reader, rep in itertools.product(
                tasks,
                grid.families,
                grid.defenses,
                grid.generators,
                grid.indexes,
                grid.readers,
                range(grid.repetitions),
            ):
                cells.append(Cell(name, task, family, defense, generator, index, reader, rep))
        return cells

    def episode_id_and_seed(self, cell: Cell) -> tuple[str, int]:
        digest = hashlib.sha256(f"{self.name}|{cell.key()}".encode()).hexdigest()
        return f"{self.name}-{digest[:16]}", int(digest[16:24], 16)

    def frozen_paths(self) -> list[Path]:
        """Everything the freeze fingerprint must cover (besides the WARC archive)."""
        dirs = [getattr(self.config, k) for k in _FROZEN_DIR_KEYS]
        return [self.path] + [self.resolve(d) for d in dirs if d]


def load_plan(path: Path) -> Plan:
    """Load a plan file. FROZEN and PILOT plans pass the gate BEFORE validation, so
    that unresolved PENDING values are reported as such, not as type errors."""
    path = path.resolve()
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    status = raw.get("status")
    if status == PlanStatus.FROZEN.value:
        dirs = [raw[k] for k in _FROZEN_DIR_KEYS if isinstance(raw.get(k), str)]
        require_complete_freeze([path] + [ROOT / d for d in dirs])
    elif status == PlanStatus.PILOT.value:
        # a pilot runs on demo protocol elements but its generators must be real
        require_complete_freeze([path], what="pilot")
    return Plan(path, PlanConfig.model_validate(raw))
