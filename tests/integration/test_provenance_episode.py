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
    for cell in plan.cells()[:4]:
        m = asyncio.run(run_episode(ctx, cell)).measures["provenance"]
        assert m["mode"] == cell.provenance
        if cell.provenance == "on":
            assert m["pages"]
            assert all(p["attested"] and p["verified"] for p in m["pages"])
            assert m["cost"]["attestations"] >= len(m["pages"])
            assert m["cost"]["meta_bytes"] > 0
        else:
            assert m["pages"] == []
