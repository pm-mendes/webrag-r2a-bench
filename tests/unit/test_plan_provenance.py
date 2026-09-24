import pytest
from pydantic import ValidationError

from webrag_bench import ROOT
from webrag_bench.config import PlanConfig
from webrag_bench.core.plan import Cell, load_plan

BASE = {
    "name": "x",
    "status": "DEMO",
    "canary_salt": "s",
    "corpus": "c",
    "attacks_dir": "a",
    "tasks_dir": "t",
    "top_k": 1,
    "embedder": {"type": "stub"},
    "generators": [{"name": "g", "type": "stub", "version_id": "g0"}],
}
GRID = {
    "families": ["F1"],
    "defenses": ["none"],
    "generators": ["g"],
    "indexes": ["bm25"],
    "readers": ["bs4-text"],
    "repetitions": 1,
}


def test_default_provenance_keeps_p_episode_ids_stable():
    cell = Cell("main", "T01", "F1", "none", "stub", "bm25", "bs4-text", 0)
    assert cell.key() == "main|T01|F1|none|stub|bm25|bs4-text|0"
    on = Cell("main", "T01", "F1", "none", "stub", "bm25", "bs4-text", 0, "on")
    assert on.key() == cell.key() + "|prov=on"


def test_provenance_on_requires_a_provenance_section():
    with pytest.raises(ValidationError, match="provenance section"):
        PlanConfig.model_validate({**BASE, "subplans": {"m": {**GRID, "provenance": ["on"]}}})
    PlanConfig.model_validate(
        {**BASE, "provenance": {"key_seed": "k"}, "subplans": {"m": {**GRID, "provenance": ["on"]}}}
    )


def test_y_dry_run_crosses_provenance():
    plan = load_plan(ROOT / "config/plans/y-dry-run.yaml")
    cells = plan.cells()
    assert len(cells) == 30  # off, on, on with half the parties failing
    assert {c.provenance for c in cells} == {"off", "on"}
