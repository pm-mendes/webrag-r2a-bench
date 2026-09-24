import pytest
from pydantic import ValidationError

from webrag_bench import ROOT
from webrag_bench.config import PlanConfig
from webrag_bench.core.plan import load_plan
from webrag_bench.freeze import IncompleteFreezeError


def test_cells_and_ids_are_deterministic(dry_run_plan_path):
    plan = load_plan(dry_run_plan_path)
    cells = plan.cells()
    assert len(cells) == 10
    ids = [plan.episode_id_and_seed(c) for c in cells]
    assert ids == [load_plan(dry_run_plan_path).episode_id_and_seed(c) for c in cells]
    assert len({i for i, _ in ids}) == len(ids)


@pytest.mark.parametrize("plan", ["campaign-p.yaml", "campaign-y.yaml", "pilot.yaml"])
def test_unresolved_plans_are_refused(plan):
    with pytest.raises(IncompleteFreezeError):
        load_plan(ROOT / "config/plans" / plan)


def test_undeclared_generator_is_rejected():
    with pytest.raises(ValidationError):
        PlanConfig.model_validate(
            {
                "name": "x",
                "status": "DEMO",
                "canary_salt": "s",
                "corpus": "c",
                "attacks_dir": "a",
                "tasks_dir": "t",
                "top_k": 1,
                "embedder": {"type": "stub"},
                "generators": [],
                "subplans": {
                    "m": {
                        "families": ["F1"],
                        "defenses": ["none"],
                        "generators": ["g"],
                        "indexes": ["bm25"],
                        "readers": ["bs4-text"],
                        "repetitions": 1,
                    }
                },
            }
        )


def test_missing_referenced_path_is_reported_not_raised(tmp_path):
    from webrag_bench.freeze import blocking_markers

    assert blocking_markers([tmp_path / "PENDING - later"]) == [
        f"{tmp_path / 'PENDING - later'}: missing path"
    ]
