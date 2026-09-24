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
    run = tmp_path / "runs/y-dry-run"
    baseline = run_equality(run, where={"fault_rate": 0.0, "defense": "none"})
    assert baseline.pairs == 10  # 5 tasks x provenance off/on, F1 vs none
    assert baseline.equal == 0  # the stub obeys every injection
    # the demo policy does not stop an injection hosted on a legitimate, signing origin
    policy = run_equality(run, where={"fault_rate": 0.0, "defense": "provenance-demo"})
    assert (policy.pairs, policy.equal) == (5, 0)

    import json

    measures = [json.loads(line) for line in (run / "measures.jsonl").read_text().splitlines()]

    def utility(defense, fault):
        values = [
            m["utility"]
            for m in measures
            if m["cell"]["defense"] == defense
            and m["cell"]["fault_rate"] == fault
            and m["cell"]["provenance"] == "on"
            and m["utility"] is not None
        ]
        return sum(values) / len(values)

    assert utility("provenance-demo", 0.0) == 1.0
    assert utility("provenance-demo", 0.5) < 1.0  # failing signers block benign work too
    assert utility("none", 0.5) == 1.0
