"""Command-line interface: `webrag-bench <command>`.

webrag-bench run config/plans/dry-run.yaml --workers 2
webrag-bench pilot runs/pilot/episodes.jsonl --window-h 72
webrag-bench freeze-check config/plans/campaign-p.yaml
webrag-bench annotation build config/annotation/demo-batch.yaml
webrag-bench annotation verify runs/demo-factors/annotation/demo-batch
webrag-bench aggregate runs/campaign-p --master <kit>/MASTER_VALUES.json
"""

from __future__ import annotations

import argparse
import json
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
    if args.master:
        from webrag_bench.analysis import (
            AggregationError,
            load_run,
            merge_into_master,
            pilot_values,
        )

        try:
            values = pilot_values(load_run(args.jsonl.parent), args.window_h, args.workers)
        except AggregationError as e:
            print(e, file=sys.stderr)
            return 3
        written = merge_into_master(args.master, {"pilote": values})
        print(f"wrote {len(written)} pilot value(s) into {args.master}")
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


def _cmd_aggregate(args: argparse.Namespace) -> int:
    from webrag_bench.analysis import (
        AggregationError,
        campaign_fragment,
        check_publishable,
        load_run,
        merge_into_master,
    )

    try:
        run = load_run(args.run)
        fragment = campaign_fragment(run, args.run, args.cells.split(","))
    except AggregationError as e:
        print(e, file=sys.stderr)
        return 3
    out = args.run / "master_values_fragment.json"
    out.write_text(json.dumps(fragment, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    prov = fragment["_provenance"]
    print(
        f"{prov['episodes']} episodes aggregated ({prov['excluded_nesting_violations']} "
        f"nesting violation(s) excluded) -> {out}"
    )
    for name, cell in fragment["entonnoir"]["cellules"].items():
        print(
            f"  {name:40s} N={cell['N']:5d} E={cell['n_E']:5d} A={cell['n_A']:5d} "
            f"F={cell['n_F']:5d} X={cell['n_X']:5d}"
        )
    if args.master:
        try:
            check_publishable(run)
        except AggregationError as e:
            print(e, file=sys.stderr)
            return 3
        written = merge_into_master(args.master, fragment)
        print(f"wrote {', '.join(written)} into {args.master}")
    return 0


def _cmd_annotation_build(args: argparse.Namespace) -> int:
    from webrag_bench.annotation import BatchError, build_batch, load_batch_config

    try:
        config = load_batch_config(args.config)
        out = build_batch(config, args.config)
    except (IncompleteFreezeError, BatchError) as e:
        print(e, file=sys.stderr)
        return 3
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    print(f"batch {config.name}: {manifest['total_items']} items in {out}")
    for row in manifest["strata"]:
        short = f"  SHORTFALL {row['shortfall']}" if row["shortfall"] else ""
        print(
            f"  {row['stratum']}  available {row['available']:5d}  drawn {row['drawn']:4d}{short}"
        )
    print(
        "give items.jsonl, sheet.csv and instructions.md to each annotator; keep key.jsonl sealed"
    )
    return 0


def _cmd_annotation_verify(args: argparse.Namespace) -> int:
    from webrag_bench.annotation import verify_batch

    problems = verify_batch(args.directory)
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    print("batch intact" if not problems else f"batch ALTERED: {len(problems)} problem(s)")
    return 1 if problems else 0


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
    pilot.add_argument(
        "--master", type=Path, help="write the pilote section of this MASTER_VALUES.json"
    )
    pilot.set_defaults(func=_cmd_pilot)

    aggregate = sub.add_parser(
        "aggregate", help="per-cell counts in the kit's MASTER_VALUES format"
    )
    aggregate.add_argument("run", type=Path, help="run directory, e.g. runs/campaign-p")
    aggregate.add_argument(
        "--cells",
        default="family,defense",
        help="grouping keys of a funnel cell (default: family,defense)",
    )
    aggregate.add_argument(
        "--master", type=Path, help="merge into this MASTER_VALUES.json (frozen, tagged runs only)"
    )
    aggregate.set_defaults(func=_cmd_aggregate)

    check = sub.add_parser("freeze-check", help="check that a plan can enter the campaign")
    check.add_argument("plan", type=Path)
    check.set_defaults(func=_cmd_freeze_check)

    annotation = sub.add_parser("annotation", help="build or verify an annotation batch")
    annotation_sub = annotation.add_subparsers(dest="annotation_command", required=True)
    build = annotation_sub.add_parser("build", help="build and freeze a batch")
    build.add_argument("config", type=Path)
    build.set_defaults(func=_cmd_annotation_build)
    verify = annotation_sub.add_parser("verify", help="check that a batch is unchanged")
    verify.add_argument("directory", type=Path)
    verify.set_defaults(func=_cmd_annotation_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
