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
    transcripts = (tmp_path / "runs/dry-run/transcripts.jsonl").read_text().splitlines()
    assert sorted(json.loads(t)["id_episode"] for t in transcripts) == sorted(ids)


def test_equality_on_the_y_dry_run(tmp_path, monkeypatch):
    from webrag_bench import ROOT
    from webrag_bench.analysis.equality import run_equality

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    runner.run_plan(ROOT / "config/plans/y-dry-run.yaml", workers=2)
    report = run_equality(tmp_path / "runs/y-dry-run", where={"fault_rate": 0.0})
    assert report.pairs == 10  # 5 tasks x provenance off/on, F1 vs none
    # the stub obeys every injection and no policy is active yet: all pairs differ
    assert report.equal == 0
