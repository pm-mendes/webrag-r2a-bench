"""Pilot measurement: replaces the 42 s/episode assumption with a measured median.

The median is compared with the break-even point of P and Y for the remaining
window. It is reported into kit/MASTER_VALUES.json -> pilote.mediane_s_par_episode
by script, not by hand. Episodes touched by a stub component are excluded: their
timing measures nothing.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

CAMPAIGN_EPISODES = {"P": 69036, "Y": 9408}
"""From PLAN_MANIFEST.json of 07-TWEB-R2A and 08-TWEB-PBD (not yet reconciled)."""


def break_even_seconds(episodes: int, workers: int, window_h: float) -> float:
    """Longest mean episode duration that still fits the window."""
    return workers * window_h * 3600 / episodes


@dataclass
class PilotReport:
    excluded_stub: int
    durations: dict[str, list[float]] = field(default_factory=dict)

    @property
    def median(self) -> float | None:
        all_durations = [d for ds in self.durations.values() for d in ds]
        return statistics.median(all_durations) if all_durations else None


def pilot_report(jsonl: Path) -> PilotReport:
    durations: dict[str, list[float]] = defaultdict(list)
    excluded = 0
    with jsonl.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if any(e.startswith("stub-component") for e in record.get("erreurs", [])):
                excluded += 1
                continue
            gen = record["generateur"]
            durations[f"{gen['nom']} ({gen['id_version']})"].append(record["duree_s"])
    return PilotReport(excluded, dict(durations))
