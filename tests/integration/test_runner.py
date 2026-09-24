import json

from webrag_bench.core import runner


def test_run_plan_writes_valid_records_and_resumes(dry_run_plan_path, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    first = runner.run_plan(dry_run_plan_path, workers=2, limit=4)
    assert (first.written, first.failed, first.skipped) == (4, 0, 0)
    second = runner.run_plan(dry_run_plan_path, workers=2)
    assert (second.written, second.skipped) == (6, 4)
    lines = (tmp_path / "runs/dry-run/episodes.jsonl").read_text().splitlines()
    ids = [json.loads(line)["id_episode"] for line in lines]
    assert len(ids) == len(set(ids)) == 10
