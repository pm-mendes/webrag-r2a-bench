"""Batch configuration (config/annotation/*.yaml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from webrag_bench.freeze import require_complete_freeze


class Allocation(BaseModel):
    """Exactly one of: a fixed count per stratum, or a sampling fraction per stratum."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    per_stratum: int | None = Field(None, ge=1)
    fraction: float | None = Field(None, gt=0.0, le=1.0)

    @model_validator(mode="after")
    def _exactly_one(self) -> Allocation:
        if (self.per_stratum is None) == (self.fraction is None):
            raise ValueError("allocation needs exactly one of per_stratum or fraction")
        return self


class BatchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    status: Literal["DEMO", "FROZEN"]
    source_run: str = Field(description="run directory under runs/")
    seed: int
    strata: list[str] = Field(min_length=1)
    allocation: Allocation
    max_items: int = Field(ge=1, description="calendar ceiling of the annotation window")
    exclude_stub_episodes: bool = True
    question: str
    labels: list[str] = Field(min_length=2)

    @model_validator(mode="after")
    def _known_strata(self) -> BatchConfig:
        from webrag_bench.annotation.strata import STRATUM_KEYS

        unknown = set(self.strata) - set(STRATUM_KEYS)
        if unknown:
            raise ValueError(
                f"unknown stratum keys {sorted(unknown)}; known: {sorted(STRATUM_KEYS)}"
            )
        return self


def load_batch_config(path: Path) -> BatchConfig:
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw.get("status") == "FROZEN":
        require_complete_freeze([path], what="annotation batch")
    return BatchConfig.model_validate(raw)
