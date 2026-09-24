"""Command-line interface: `webrag-bench <command>`.

webrag-bench run config/plans/dry-run.yaml --workers 2
webrag-bench pilot runs/pilot/episodes.jsonl --window-h 72
webrag-bench freeze-check config/plans/campaign-p.yaml
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

from webrag_bench import __version__
from webrag_bench.analysis import CAMPAIGN_EPISODES, break_even_seconds, pilot_report
from webrag_bench.freeze import IncompleteFreezeError


def _cmd_run(args: argparse.Namespace) -> int:
    from webrag_bench.core.runner import run_plan

    try:
        summary = run_plan(args.plan, workers=args.workers, limit=args.limit)
    except IncompleteFreezeError as e:
        print(e, file=sys.stderr)
        return 3
    print(f"done: {summary.written} episodes written, {summary.failed} failed")
    return 1 if summary.failed else 0


def _cmd_pilot(args: argparse.Namespace) -> int:
    report = pilot_report(args.jsonl)
    if report.excluded_stub:
        print(f"{report.excluded_stub} stub episode(s) excluded")
    if report.median is None:
        print("no measurable episode: the pilot must run on the real generators")
        return 2
    for gen, ds in sorted(report.durations.items()):
        q = statistics.quantiles(ds, n=10) if len(ds) >= 2 else [ds[0]] * 9
        print(
            f"{gen:50s} n={len(ds):4d}  median={statistics.median(ds):7.2f} s  "
            f"p10={q[0]:7.2f}  p90={q[-1]:7.2f}"
        )
    median = report.median
    print(f"\noverall median: {median:.2f} s/episode")
    targets = {**CAMPAIGN_EPISODES, "P+Y (shared machine)": sum(CAMPAIGN_EPISODES.values())}
    for paper, n in targets.items():
        be = break_even_seconds(n, args.workers, args.window_h)
        verdict = "fits" if median <= be else "DOES NOT FIT -> fallback rule"
        setting = f"({args.workers} workers, {args.window_h} h)"
        print(f"  {paper:22s} break-even {be:8.1f} s {setting} -> {verdict}")
    return 0


def _cmd_freeze_check(args: argparse.Namespace) -> int:
    from webrag_bench.core.plan import load_plan

    try:
        plan = load_plan(args.plan)
    except IncompleteFreezeError as e:
        print(e, file=sys.stderr)
        return 3
    print(
        f"{plan.name}: status {plan.config.status.value}, {len(plan.cells())} cells"
        + (" - freeze complete" if plan.is_frozen else " - not a frozen plan")
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="webrag-bench",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a plan")
    run.add_argument("plan", type=Path)
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--limit", type=int, default=None, help="only run the first N pending cells")
    run.set_defaults(func=_cmd_run)

    pilot = sub.add_parser("pilot", help="measured median vs break-even points")
    pilot.add_argument("jsonl", type=Path)
    pilot.add_argument("--workers", type=int, default=24)
    pilot.add_argument(
        "--window-h", type=float, required=True, help="remaining campaign window (hours)"
    )
    pilot.set_defaults(func=_cmd_pilot)

    check = sub.add_parser("freeze-check", help="check that a plan can enter the campaign")
    check.add_argument("plan", type=Path)
    check.set_defaults(func=_cmd_freeze_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
