"""Aggregation of run records into the kit's MASTER_VALUES.json format.

Implements step 2 of the analysis plan (kit/PLAN-ANALYSE.md): records -> per-cell
counts -> MASTER_VALUES. It stores COUNTS (N, n_E, n_A, n_F, n_X) and the three
conditionals computed from them, and the end-to-end action rate as n_X / n_E — never
n_X / N, which is the false identity the kit's `verifier_entonnoir.py` rejects.

A conditional whose denominator is zero is `None` (not emitted into the manuscript;
the reporting rule applies). Effect sizes, intervals and multiplicity corrections are
NOT computed here: their estimands are still PENDING in the analysis plan.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from webrag_bench.analysis.pilot import CAMPAIGN_EPISODES, break_even_seconds
from webrag_bench.records.fields import key_of

Record = dict[str, Any]
STAGES = ("exposition", "absorption", "effet", "action")
PRECISION = 6


class AggregationError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoadedRun:
    records: list[Record]
    excluded_nesting: int
    stub: int
    fingerprints: frozenset[str]
    bench_versions: frozenset[str]


def load_run(run_dir: Path) -> LoadedRun:
    """Records of a run, minus nesting violations (a bench defect, not data)."""
    path = run_dir / "episodes.jsonl"
    if not path.exists():
        raise AggregationError(f"missing {path}")
    kept, excluded, stub = [], 0, 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if "nesting-violated" in r.get("erreurs", []):
                excluded += 1
                continue
            stub += any(e.startswith("stub-component") for e in r.get("erreurs", []))
            kept.append(r)
    return LoadedRun(
        kept,
        excluded,
        stub,
        frozenset(r["empreinte_gel"] for r in kept),
        frozenset(r["version_banc"] for r in kept),
    )


def _ratio(num: int, den: int) -> float | None:
    return round(num / den, PRECISION) if den else None


def _counts(records: list[Record]) -> dict[str, int]:
    return {
        "N": len(records),
        "n_E": sum(r["etages"]["exposition"] for r in records),
        "n_A": sum(r["etages"]["absorption"] for r in records),
        "n_F": sum(r["etages"]["effet"] for r in records),
        "n_X": sum(r["etages"]["action"] for r in records),
    }


def funnel_cell(records: list[Record]) -> dict[str, Any]:
    c = _counts(records)
    return {
        **c,
        "p_A_sachant_E": _ratio(c["n_A"], c["n_E"]),
        "p_F_sachant_A": _ratio(c["n_F"], c["n_A"]),
        "p_X_sachant_F": _ratio(c["n_X"], c["n_F"]),
        "taux_action_bout_en_bout": _ratio(c["n_X"], c["n_E"]),
    }


def _group(records: list[Record], keys: list[str]) -> dict[str, list[Record]]:
    groups: dict[str, list[Record]] = defaultdict(list)
    for r in records:
        groups["__".join(key_of(r, keys))].append(r)
    return dict(sorted(groups.items()))


def funnel_cells(records: list[Record], keys: list[str]) -> dict[str, dict[str, Any]]:
    """One funnel per cell. Unattacked episodes (family `aucune`) are left out: no stage
    can be reached without an attack, so they would only inflate N."""
    attacked = [r for r in records if r["famille_attaque"] != "aucune"]
    return {name: funnel_cell(group) for name, group in _group(attacked, keys).items()}


def reader_factor(records: list[Record]) -> dict[str, dict[str, Any]]:
    """Per (family, reader): how much exposed adversarial content survives the reader."""
    attacked = [r for r in records if r["famille_attaque"] != "aucune"]
    out = {}
    for name, group in _group(attacked, ["family", "reader"]).items():
        c = _counts(group)
        out[name] = {
            "N": c["N"],
            "n_E": c["n_E"],
            "n_A": c["n_A"],
            "p_A_sachant_E": _ratio(c["n_A"], c["n_E"]),
        }
    return out


def defense_counts(records: list[Record]) -> dict[str, dict[str, int]]:
    """Per defense condition: stage counts over attacked episodes. Counts only — the
    effect estimand is PENDING in the analysis plan."""
    attacked = [r for r in records if r["famille_attaque"] != "aucune"]
    return {name: _counts(group) for name, group in _group(attacked, ["defense"]).items()}


def pilot_values(run: LoadedRun, window_h: float, workers: int) -> dict[str, Any]:
    if run.stub:
        raise AggregationError(
            f"{run.stub} stub episode(s): the pilot must run on the real generators"
        )
    durations = [r["duree_s"] for r in run.records]
    if len(durations) < 2:
        raise AggregationError("a pilot needs at least two episodes")
    q1, _, q3 = statistics.quantiles(durations, n=4)
    median = statistics.median(durations)
    break_even = break_even_seconds(sum(CAMPAIGN_EPISODES.values()), workers, window_h)
    fits = median <= break_even
    days = sorted({r["horodatage_utc"][:10] for r in run.records})
    return {
        "mediane_s_par_episode": round(median, 2),
        "q1_s_par_episode": round(q1, 2),
        "q3_s_par_episode": round(q3, 2),
        "n_episodes_pilote": len(durations),
        "date_pilote": days[0] if len(days) == 1 else f"{days[0]}/{days[-1]}",
        "verdict_faisabilite": (
            f"{'fits' if fits else 'does not fit'}: median {median:.1f} s "
            f"{'<=' if fits else '>'} break-even {break_even:.1f} s "
            f"(P+Y, {workers} workers, {window_h:g} h)"
        ),
    }


def campaign_fragment(run: LoadedRun, run_dir: Path, cell_keys: list[str]) -> dict[str, Any]:
    freeze = json.loads((run_dir / "freeze.json").read_text(encoding="utf-8"))
    return {
        "entonnoir": {"cellules": funnel_cells(run.records, cell_keys)},
        "effets_defense": {"entrees": defense_counts(run.records)},
        "facteur_lecteur": {"entrees": reader_factor(run.records)},
        "reproductibilite": {"empreinte_corpus_warc": freeze["sha256_warc"]},
        "_provenance": {
            "run": run_dir.name,
            "episodes": len(run.records),
            "excluded_nesting_violations": run.excluded_nesting,
            "stub_episodes": run.stub,
            "empreinte_gel": sorted(run.fingerprints),
            "version_banc": sorted(run.bench_versions),
        },
    }


def check_publishable(run: LoadedRun) -> None:
    """Guards before any number reaches the manuscript."""
    problems = []
    if run.stub:
        problems.append(f"{run.stub} episode(s) used a stub component")
    unfrozen = [f for f in run.fingerprints if f.startswith("NOT-FROZEN:")]
    if unfrozen:
        problems.append("the run is not frozen (fingerprint NOT-FROZEN)")
    if len(run.fingerprints) > 1:
        problems.append(f"{len(run.fingerprints)} different freeze fingerprints in one run")
    if any(v.endswith("-dirty") or v == "untagged" for v in run.bench_versions):
        problems.append("records come from an untagged or dirty bench version")
    if problems:
        raise AggregationError("refusing to write into MASTER_VALUES: " + "; ".join(problems))


def merge_into_master(master_path: Path, fragment: dict[str, Any]) -> list[str]:
    """Replace only the sections produced by the bench; keep every other key and comment."""
    master = json.loads(master_path.read_text(encoding="utf-8"))
    written = []
    for section, content in fragment.items():
        if section.startswith("_"):
            continue
        target = master.setdefault(section, {})
        for key, value in content.items():
            target[key] = value
            written.append(f"{section}.{key}")
    master_path.write_text(
        json.dumps(master, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return written
