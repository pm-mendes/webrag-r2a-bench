import asyncio

from webrag_bench.core.context import RunContext
from webrag_bench.core.episode import run_episode
from webrag_bench.core.plan import load_plan
from webrag_bench.core.runner import prepare
from webrag_bench.corpus import WarcReplay
from webrag_bench.records import validate_record


def test_full_episode_produces_a_valid_record(dry_run_plan_path, tmp_path):
    plan = load_plan(dry_run_plan_path)
    prepared = prepare(plan, tmp_path)
    ctx = RunContext(plan, WarcReplay(prepared.warc), prepared.freeze_fingerprint, "test")
    records = [asyncio.run(run_episode(ctx, c)) for c in plan.cells()]
    for r in records:
        validate_record(r)
        assert r["empreinte_gel"].startswith("NOT-FROZEN:")
        assert "stub-component: episode has no measurement value" in r["erreurs"]
        assert "nesting-violated" not in r["erreurs"]
    by_defense = {(r["tache"]["id"], r["condition_defense"]): r["etages"]["action"] for r in records}
    assert by_defense[("T01", "none")] is True
    assert by_defense[("T01", "tool-allowlist-demo")] is False  # bank.transfer not allowed
