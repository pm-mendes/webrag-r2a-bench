"""Campaign monitoring: progress, measured throughput, projected end, anomalies.

Reads a plan and its run directory while the campaign runs (files are append-only,
so reading them concurrently is safe). The throughput is measured on the most recent
window of records, not assumed; the projection is what a checkpoint decides on.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from webrag_bench import ROOT
from webrag_bench.core.plan import load_plan

RECENT_WINDOW = timedelta(hours=1)
_ANOMALY_PREFIXES = (
    "model-substitution",
    "unknown-tool",
    "tool-error",
    "nesting-violated",
    "stub-component",
    "tool-arguments-not-json",
)


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@dataclass
class Status:
    plan: str
    total_cells: int
    done: int
    failed: int
    first: datetime | None
    last: datetime | None
    rate_per_hour: float | None
    anomalies: Counter[str] = field(default_factory=Counter)
    failure_kinds: Counter[str] = field(default_factory=Counter)
    stage_totals: dict[str, int] = field(default_factory=dict)

    @property
    def remaining(self) -> int:
        return self.total_cells - self.done

    def projected_end(self) -> datetime | None:
        if not self.remaining:
            return self.last
        if not self.rate_per_hour or self.last is None:
            return None
        return self.last + timedelta(hours=self.remaining / self.rate_per_hour)


def measure_rate(timestamps: list[datetime], window: timedelta = RECENT_WINDOW) -> float | None:
    """Episodes per hour over the most recent window (or the whole run if shorter)."""
    if len(timestamps) < 2:
        return None
    ts = sorted(timestamps)
    recent = [t for t in ts if t >= ts[-1] - window]
    if len(recent) < 2:
        recent = ts
    span = (recent[-1] - recent[0]).total_seconds()
    return (len(recent) - 1) / span * 3600 if span > 0 else None


def campaign_status(plan_path: Path, root: Path = ROOT) -> Status:
    plan = load_plan(plan_path)
    run_dir = root / "runs" / plan.name
    records = _read_jsonl(run_dir / "episodes.jsonl")
    failures = _read_jsonl(run_dir / "failures.jsonl")
    done_ids = {r["id_episode"] for r in records}
    stamps = [_parse(r["horodatage_utc"]) for r in records]

    anomalies: Counter[str] = Counter()
    for r in records:
        for e in r.get("erreurs", []):
            prefix = next((p for p in _ANOMALY_PREFIXES if e.startswith(p)), None)
            if prefix:
                anomalies[prefix] += 1
    return Status(
        plan=plan.name,
        total_cells=len(plan.cells()),
        done=len(done_ids),
        failed=len(failures),
        first=min(stamps, default=None),
        last=max(stamps, default=None),
        rate_per_hour=measure_rate(stamps),
        anomalies=anomalies,
        failure_kinds=Counter(f["error"].split(":", 1)[0] for f in failures),
        stage_totals={
            s: sum(r["etages"][s] for r in records)
            for s in ("exposition", "absorption", "effet", "action")
        },
    )


def render_report(status: Status, deadline: datetime | None, now: datetime) -> str:
    """Markdown checkpoint report."""
    end = status.projected_end()
    pct = 100 * status.done / status.total_cells if status.total_cells else 0.0
    lines = [
        f"# Checkpoint — {status.plan}",
        "",
        f"Generated {now:%Y-%m-%d %H:%M} UTC.",
        "",
        "| | |",
        "|---|---|",
        f"| progress | {status.done} / {status.total_cells} episodes ({pct:.1f} %) |",
        f"| remaining | {status.remaining} |",
        f"| failed (to retry) | {status.failed} |",
        f"| first / last record | {_fmt(status.first)} / {_fmt(status.last)} |",
        f"| measured throughput (last hour) | {_fmt_rate(status.rate_per_hour)} |",
        f"| projected end | {_fmt(end)} |",
    ]
    if deadline is not None:
        lines.append(f"| deadline | {_fmt(deadline)} |")
        lines.append(f"| verdict | **{verdict(end, deadline)}** |")
    lines += ["", "## Anomalies", ""]
    if status.anomalies or status.failure_kinds:
        lines += [f"- `{k}`: {n} episode(s)" for k, n in status.anomalies.most_common()]
        lines += [f"- failure `{k}`: {n}" for k, n in status.failure_kinds.most_common()]
        if status.anomalies.get("model-substitution"):
            lines += ["", "**Model substitution detected: record a deviation before continuing.**"]
    else:
        lines.append("None.")
    lines += [
        "",
        "## Stage totals so far",
        "",
        ", ".join(f"{k} {v}" for k, v in status.stage_totals.items()) or "—",
        "",
    ]
    return "\n".join(lines)


def verdict(end: datetime | None, deadline: datetime) -> str:
    if end is None:
        return "unknown (not enough records to measure throughput)"
    if end <= deadline:
        return f"on track ({(deadline - end).total_seconds() / 3600:.1f} h ahead)"
    return (
        f"LATE by {(end - deadline).total_seconds() / 3600:.1f} h "
        "-> apply the fallback rule in its declared order"
    )


def _fmt(t: datetime | None) -> str:
    return f"{t.astimezone(UTC):%Y-%m-%d %H:%M} UTC" if t else "—"


def _fmt_rate(r: float | None) -> str:
    return f"{r:.1f} episodes/h" if r else "— (fewer than two records)"
