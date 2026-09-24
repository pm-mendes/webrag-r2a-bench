import asyncio

from webrag_bench import ROOT
from webrag_bench.core.context import RunContext
from webrag_bench.core.episode import run_episode
from webrag_bench.core.plan import load_plan
from webrag_bench.core.runner import prepare
from webrag_bench.corpus import WarcReplay


def test_signed_episodes_verify_every_page(tmp_path):
    plan = load_plan(ROOT / "config/plans/y-dry-run.yaml")
    prepared = prepare(plan, tmp_path)
    ctx = RunContext(plan, WarcReplay(prepared.warc), prepared.freeze_fingerprint, "test")
    for cell in [c for c in plan.cells() if c.fault_rate == 0][:4]:
        m = asyncio.run(run_episode(ctx, cell)).measures["provenance"]
        assert m["mode"] == cell.provenance
        if cell.provenance == "on":
            assert m["pages"]
            assert all(p["attested"] and p["verified"] for p in m["pages"])
            assert m["cost"]["attestations"] >= len(m["pages"])
            assert m["cost"]["meta_bytes"] > 0
        else:
            assert m["pages"] == []


def test_partial_failure_is_visible_to_the_agent(tmp_path):
    plan = load_plan(ROOT / "config/plans/y-dry-run.yaml")
    prepared = prepare(plan, tmp_path)
    ctx = RunContext(plan, WarcReplay(prepared.warc), prepared.freeze_fingerprint, "test")
    faulty_cells = [c for c in plan.cells() if c.fault_rate > 0]
    unverified = 0
    for cell in faulty_cells:
        m = asyncio.run(run_episode(ctx, cell)).measures["provenance"]
        assert m["fault_mode"] == "corrupt"
        assert len(m["faulty_parties"]) == round(0.5 * len(ctx.party_keys))
        for page in m["pages"]:
            assert page["verified"] == (page["origin"] not in m["faulty_parties"])
            unverified += not page["verified"]
    assert unverified > 0
