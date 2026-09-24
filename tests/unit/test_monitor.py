import json
from datetime import UTC, datetime, timedelta

from webrag_bench.analysis.monitor import campaign_status, measure_rate, render_report, verdict

T0 = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)


def test_rate_uses_the_recent_window():
    # slow start (1/h for 5 h), then 60/h in the last hour
    slow = [T0 + timedelta(hours=h) for h in range(5)]
    fast = [T0 + timedelta(hours=5, minutes=m) for m in range(1, 61)]
    assert round(measure_rate(slow + fast)) == 60


def test_rate_needs_two_records():
    assert measure_rate([T0]) is None


def test_verdict():
    assert verdict(T0, T0 + timedelta(hours=2)).startswith("on track (2.0 h ahead)")
    assert verdict(T0 + timedelta(hours=3), T0).startswith("LATE by 3.0 h")
    assert verdict(None, T0).startswith("unknown")


def test_status_of_a_partial_run(dry_run_plan_path, tmp_path):
    run = tmp_path / "runs/dry-run"
    run.mkdir(parents=True)
    records = [
        {
            "id_episode": f"ep-{i}",
            "horodatage_utc": f"2026-09-26T10:{i:02d}:00Z",
            "erreurs": ["model-substitution: declared=a returned=b"] if i == 0 else [],
            "etages": {"exposition": True, "absorption": True, "effet": False, "action": False},
        }
        for i in range(4)
    ]
    (run / "episodes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    (run / "failures.jsonl").write_text(
        json.dumps({"cell": "c", "error": "TimeoutError: x"}) + "\n"
    )

    status = campaign_status(dry_run_plan_path, root=tmp_path)
    assert (status.total_cells, status.done, status.remaining, status.failed) == (10, 4, 6, 1)
    assert round(status.rate_per_hour) == 60
    assert status.projected_end() == datetime(2026, 9, 26, 10, 9, tzinfo=UTC)

    report = render_report(status, T0 + timedelta(hours=1), T0)
    assert "on track" in report
    assert "`model-substitution`: 1" in report
    assert "failure `TimeoutError`: 1" in report
    assert "record a deviation" in report
