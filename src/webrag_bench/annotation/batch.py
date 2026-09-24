"""Build and verify an annotation batch.

Output directory: runs/<source_run>/annotation/<batch name>/

- `items.jsonl`     (both annotators) blinded, shuffled items: request, context,
                    response, proposed calls
- `sheet.csv`       (both annotators) empty label sheet: item_id, label, comment
- `instructions.md` (both annotators) the question and the allowed labels
- `key.jsonl`       (sealed) item -> episode and stratum
- `manifest.json`   (the paper) configuration, per-stratum counts and shortfalls,
                    SHA-256 of every file

Blinding covers metadata: condition, generator and family never appear in an item.
Content-level cues remain (an injected instruction is visible in the context); this
is inherent to the task and is stated in the manifest.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from webrag_bench import ROOT
from webrag_bench.annotation.config import BatchConfig
from webrag_bench.core.versioning import bench_version
from webrag_bench.records.fields import key_of as stratum_of

ANNOTATOR_FILES = ("items.jsonl", "sheet.csv", "instructions.md")
SEALED_FILES = ("key.jsonl",)
BLINDING_NOTE = (
    "Items carry no condition, generator or family metadata. Content-level cues "
    "(e.g. an injected instruction visible in the context) are inherent to the task."
)


class BatchError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _eligible(record: dict[str, Any], exclude_stub: bool) -> bool:
    errors = record.get("erreurs", [])
    if "nesting-violated" in errors:  # a bench defect, not data (analysis plan §2)
        return False
    return not (exclude_stub and any(e.startswith("stub-component") for e in errors))


def _target(available: int, config: BatchConfig) -> int:
    alloc = config.allocation
    if alloc.per_stratum is not None:
        return min(alloc.per_stratum, available)
    assert alloc.fraction is not None
    return min(available, math.floor(alloc.fraction * available + 0.5))


def _stratum_rng(seed: int, stratum: tuple[str, ...]) -> random.Random:
    # one generator per stratum: adding a stratum never changes the draw of another
    digest = hashlib.sha256(f"{seed}|{'|'.join(stratum)}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def batch_dir(config: BatchConfig) -> Path:
    return ROOT / "runs" / config.source_run / "annotation" / config.name


def build_batch(config: BatchConfig, config_path: Path | None = None) -> Path:
    out = batch_dir(config)
    if out.exists():
        raise BatchError(
            f"{out} already exists. A built batch is frozen and never rebuilt; "
            "a new batch needs a new name."
        )
    run = ROOT / "runs" / config.source_run
    episodes_path, transcripts_path = run / "episodes.jsonl", run / "transcripts.jsonl"
    for p in (episodes_path, transcripts_path):
        if not p.exists():
            raise BatchError(f"missing {p}")

    records = [r for r in _read_jsonl(episodes_path) if _eligible(r, config.exclude_stub_episodes)]
    transcripts = {t["id_episode"]: t for t in _read_jsonl(transcripts_path)}
    missing = [r["id_episode"] for r in records if r["id_episode"] not in transcripts]
    if missing:
        raise BatchError(f"{len(missing)} eligible episodes have no transcript, e.g. {missing[0]}")

    by_stratum: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for r in records:
        by_stratum[stratum_of(r, config.strata)].append(r["id_episode"])

    table, drawn = [], []
    for stratum in sorted(by_stratum):
        ids = sorted(by_stratum[stratum])
        n = _target(len(ids), config)
        chosen = _stratum_rng(config.seed, stratum).sample(ids, n)
        drawn += [(stratum, i) for i in chosen]
        requested = config.allocation.per_stratum
        table.append(
            {
                "stratum": dict(zip(config.strata, stratum, strict=True)),
                "available": len(ids),
                "drawn": n,
                "shortfall": max(0, requested - len(ids)) if requested is not None else 0,
            }
        )
    if not drawn:
        raise BatchError("no eligible episode: nothing to annotate")
    if len(drawn) > config.max_items:
        raise BatchError(
            f"the allocation draws {len(drawn)} items, above max_items={config.max_items}. "
            "Change the allocation or the partition before the freeze; the batch is not truncated."
        )

    items = []
    for stratum, episode_id in drawn:
        item_id = "I" + hashlib.sha256(f"{config.seed}|{episode_id}".encode()).hexdigest()[:10]
        t = transcripts[episode_id]
        items.append(
            (
                item_id,
                stratum,
                episode_id,
                {
                    "item_id": item_id,
                    "request": t["request"],
                    "context": t["context"],
                    "response_text": t["response_text"],
                    "proposed_calls": t["proposed_calls"],
                },
            )
        )
    random.Random(config.seed).shuffle(items)

    out.mkdir(parents=True)
    with (out / "items.jsonl").open("w", encoding="utf-8") as f:
        for _, _, _, item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    with (out / "key.jsonl").open("w", encoding="utf-8") as f:
        for item_id, stratum, episode_id, _ in items:
            f.write(
                json.dumps(
                    {
                        "item_id": item_id,
                        "id_episode": episode_id,
                        "stratum": dict(zip(config.strata, stratum, strict=True)),
                    }
                )
                + "\n"
            )
    with (out / "sheet.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["item_id", "label", "comment"])
        writer.writerows([item_id, "", ""] for item_id, *_ in items)
    (out / "instructions.md").write_text(
        f"# Annotation batch {config.name}\n\n"
        f"For each item in `items.jsonl`, answer:\n\n> {config.question}\n\n"
        f"Allowed labels: {', '.join(f'`{label}`' for label in config.labels)}.\n\n"
        "Fill a copy of `sheet.csv` named after you (one row per item) and hand it back; "
        "do not edit the files of this batch. Work alone: do not discuss items with the "
        "other annotator before both sheets are handed in.\n",
        encoding="utf-8",
    )

    manifest = {
        "batch": config.name,
        "status": config.status,
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bench_version": bench_version(),
        "config": config.model_dump(),
        "config_sha256": _sha256(config_path) if config_path else None,
        "source": {
            "episodes_sha256": _sha256(episodes_path),
            "transcripts_sha256": _sha256(transcripts_path),
            "eligible_episodes": len(records),
        },
        "strata": table,
        "total_items": len(items),
        "blinding": BLINDING_NOTE,
        "files": {name: _sha256(out / name) for name in (*ANNOTATOR_FILES, *SEALED_FILES)},
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return out


def verify_batch(directory: Path) -> list[str]:
    """Return the list of problems; empty means the batch is intact."""
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        return [f"{manifest_path} is missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems = []
    for name, expected in manifest["files"].items():
        path = directory / name
        if not path.exists():
            problems.append(f"{name} is missing")
        elif _sha256(path) != expected:
            problems.append(f"{name} changed since the batch was frozen")
    extra = {p.name for p in directory.iterdir()} - set(manifest["files"]) - {"manifest.json"}
    problems += [f"unexpected file {name}" for name in sorted(extra)]
    return problems
