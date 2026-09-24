"""Runner: builds the archive, fingerprints the freeze, runs the cells, writes JSONL.

Output goes to runs/<plan>/: `episodes.jsonl`, `transcripts.jsonl`,
`failures.jsonl`, `freeze.json`, `corpus.warc`. A rerun resumes where it stopped:
episode ids are deterministic and episodes already written are skipped.
"""

from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from webrag_bench import ROOT
from webrag_bench.attacks import load_templates
from webrag_bench.core.context import RunContext
from webrag_bench.core.episode import EpisodeResult, run_episode
from webrag_bench.core.plan import Cell, Plan, load_plan
from webrag_bench.core.versioning import bench_version
from webrag_bench.corpus import WarcReplay, build_adversarial_pages, load_benign_pages, write_warc
from webrag_bench.freeze import fingerprint
from webrag_bench.records import append_record, completed_ids
from webrag_bench.security import install_guard

_CTX: RunContext | None = None


@dataclass(frozen=True)
class Prepared:
    output_dir: Path
    warc: Path
    freeze_fingerprint: str


@dataclass(frozen=True)
class RunSummary:
    total_cells: int
    skipped: int
    written: int
    failed: int


def prepare(plan: Plan, output_dir: Path) -> Prepared:
    """Build the plan's WARC archive and compute the freeze fingerprint."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = plan.config
    benign = load_benign_pages(plan.resolve(cfg.corpus))
    templates = load_templates(plan.resolve(cfg.attacks_dir))
    families = {f for grid in cfg.subplans.values() for f in grid.families} - {"none"}
    missing = families - set(templates)
    if missing:
        raise ValueError(f"families without a template: {sorted(missing)}")
    adversarial = build_adversarial_pages(benign, plan.tasks(), templates, cfg.canary_salt)
    warc = output_dir / "corpus.warc"
    warc_sha = write_warc(benign + adversarial, warc)
    digest = fingerprint([*plan.frozen_paths(), warc], ROOT)
    freeze_fp = digest if plan.is_frozen else f"NOT-FROZEN:{digest}"
    (output_dir / "freeze.json").write_text(
        json.dumps(
            {
                "plan": plan.name,
                "empreinte_gel": freeze_fp,
                "sha256_warc": warc_sha,
                "version_banc": bench_version(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return Prepared(output_dir, warc, freeze_fp)


def allowed_hosts(plan: Plan) -> set[str]:
    urls = [g.base_url for g in plan.config.generators] + [plan.config.embedder.base_url]
    return {urllib.parse.urlparse(u).hostname or "" for u in urls if u} - {""}


def _init_worker(plan_path: str, warc: str, freeze_fp: str, version: str) -> None:
    global _CTX
    plan = load_plan(Path(plan_path))
    install_guard(allowed_hosts(plan))
    _CTX = RunContext(plan, WarcReplay(Path(warc)), freeze_fp, version)


def _run_one(cell: Cell) -> EpisodeResult | dict[str, Any]:
    if _CTX is None:
        raise RuntimeError("worker not initialised")
    try:
        return asyncio.run(run_episode(_CTX, cell))
    except Exception as e:  # one failing episode must not kill the worker
        return {"cell": cell.key(), "error": f"{type(e).__name__}: {e}"}


def _append_json(obj: dict[str, Any], path: Path) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def run_plan(
    plan_path: Path, workers: int = 1, limit: int | None = None, progress_every: int = 50
) -> RunSummary:
    plan = load_plan(plan_path)
    prepared = prepare(plan, ROOT / "runs" / plan.name)
    episodes = prepared.output_dir / "episodes.jsonl"
    transcripts = prepared.output_dir / "transcripts.jsonl"
    failures = prepared.output_dir / "failures.jsonl"

    cells = plan.cells()
    done = completed_ids(episodes)
    todo = [c for c in cells if plan.episode_id_and_seed(c)[0] not in done][:limit]
    print(
        f"plan {plan.name}: {len(cells)} cells, {len(done)} already done, {len(todo)} to run "
        f"- fingerprint {prepared.freeze_fingerprint[:24]}...",
        flush=True,
    )

    written = failed = 0
    init_args = (str(plan.path), str(prepared.warc), prepared.freeze_fingerprint, bench_version())
    with mp.get_context("spawn").Pool(workers, _init_worker, init_args) as pool:
        for result in pool.imap_unordered(_run_one, todo):
            if isinstance(result, EpisodeResult):
                # transcript first: a record never exists without its transcript
                _append_json(result.transcript, transcripts)
                append_record(result.record, episodes)
                written += 1
            else:
                _append_json(result, failures)
                failed += 1
            if (written + failed) % progress_every == 0:
                print(f"  {written + failed}/{len(todo)}", flush=True)
    return RunSummary(len(cells), len(done), written, failed)
