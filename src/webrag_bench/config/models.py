"""Pydantic models of the plan file (config/plans/*.yaml)."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Family = Literal["none", "F1", "F2", "F3", "F4"]
ProvenanceMode = Literal["off", "on"]
FaultMode = Literal["missing", "corrupt", "unknown-key"]
IndexName = Literal["dense", "bm25", "hybrid"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PlanStatus(StrEnum):
    DEMO = "DEMO"  # wiring checks; stub components allowed; never reported
    PILOT = "PILOT"  # real generators, demo protocol elements; timing only
    FROZEN = "FROZEN"  # campaign; refuses to start unless the freeze is complete


class EmbedderConfig(_Strict):
    type: Literal["stub", "openai-compatible"]
    base_url: str | None = None
    model: str | None = None
    key_env: str | None = None

    @model_validator(mode="after")
    def _endpoint_required(self) -> EmbedderConfig:
        if self.type == "openai-compatible" and not (self.base_url and self.model):
            raise ValueError("an openai-compatible embedder needs base_url and model")
        return self


class GeneratorConfig(_Strict):
    name: str
    type: Literal["stub", "openai-compatible"]
    version_id: str = Field(description="exact model snapshot; checked on every call")
    base_url: str | None = None
    key_env: str | None = None
    temperature: float = 0.0
    max_tokens: int = 1024

    @model_validator(mode="after")
    def _endpoint_required(self) -> GeneratorConfig:
        if self.type == "openai-compatible" and not self.base_url:
            raise ValueError(f"generator {self.name}: base_url is required")
        return self


class FactorGrid(_Strict):
    """One fully crossed grid. A non-crossed design is a sum of several grids."""

    tasks: Literal["all"] | list[str] = "all"
    families: list[Family]
    defenses: list[str]
    generators: list[str]
    indexes: list[IndexName]
    readers: list[str]
    repetitions: int = Field(ge=1)
    provenance: list[ProvenanceMode] = ["off"]
    fault_rates: list[float] = [0.0]

    @model_validator(mode="after")
    def _fault_rates_in_range(self) -> FactorGrid:
        if any(not 0.0 <= r <= 1.0 for r in self.fault_rates):
            raise ValueError("fault rates must be in [0, 1]")
        return self


class ProvenanceConfig(_Strict):
    """Signed provenance (paper Y): who signs, with keys derived from a frozen seed."""

    key_seed: str
    peer_party: str = "peer"
    fault_mode: FaultMode = "missing"


class PlanConfig(_Strict):
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    status: PlanStatus
    canary_salt: str
    corpus: str
    attacks_dir: str
    tasks_dir: str
    defenses_dir: str | None = None
    judge_dir: str | None = None
    top_k: int = Field(ge=1)
    hybrid_alpha: float = Field(0.5, ge=0.0, le=1.0)
    embedder: EmbedderConfig
    generators: list[GeneratorConfig]
    subplans: dict[str, FactorGrid]
    provenance: ProvenanceConfig | None = None

    @model_validator(mode="after")
    def _generators_declared(self) -> PlanConfig:
        declared = {g.name for g in self.generators}
        for name, grid in self.subplans.items():
            missing = set(grid.generators) - declared
            if missing:
                raise ValueError(f"subplan {name}: undeclared generators {sorted(missing)}")
        return self

    @model_validator(mode="after")
    def _provenance_configured(self) -> PlanConfig:
        uses = any("on" in grid.provenance for grid in self.subplans.values())
        if uses and self.provenance is None:
            raise ValueError(
                "a subplan uses provenance 'on' but the plan has no provenance section"
            )
        return self

    def generator(self, name: str) -> GeneratorConfig:
        return next(g for g in self.generators if g.name == name)
