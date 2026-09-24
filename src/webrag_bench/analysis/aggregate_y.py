"""Aggregation of paper Y measures into 08-TWEB-PBD/kit/MASTER_VALUES.json.

Fills the EMPIRICAL keys only. The bounds (`borne_formelle_predite`) come from the
formal core and the measure-bound gaps (`ecart_mesure_borne`) are computed once the
bounds exist: neither is written here. The Y analysis plan (section 3) is explicit
that a bound met by the measure proves nothing more than the theorem already does.

- cout_delegation.surcout_latence_ms_median / _p99: signing + verification time per
  signed episode without failure (measured by the ProvenanceMeter). The end-to-end
  duration difference of off/on pairs is reported beside it, in `_provenance`, as a
  secondary figure: it is dominated by scheduling and model latency noise.
- cout_delegation.surcout_taille_message_octets: median attestation bytes per signed
  episode without failure.
- degradation_gracieuse.utilite_sans_provenance: utility, provenance off, no defense.
- degradation_gracieuse.utilite_avec_provenance: utility, provenance on, the policy,
  no failure.
- degradation_gracieuse.utilite_sous_defaillance_partielle: same, at the declared
  partial fault rate.
- egalite_inter_episodes.*: clean/attacked pairs, provenance on, the policy, no failure.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from webrag_bench.analysis.aggregate import AggregationError
from webrag_bench.analysis.equality import equality_report

PAIRING = ("subplan", "task", "family", "defense", "generator", "index", "reader", "repetition")


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise AggregationError(f"missing {path}")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _mean(values: list[bool]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def _p99(values: list[float]) -> float:
    return values[0] if len(values) == 1 else statistics.quantiles(values, n=100)[98]


def delegation_cost(
    measures: list[dict[str, Any]], durations: dict[str, float]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns the MASTER_VALUES keys and a secondary end-to-end figure."""
    signed = [
        m for m in measures if m["cell"]["provenance"] == "on" and m["cell"]["fault_rate"] == 0.0
    ]
    if not signed:
        raise AggregationError("no signed episode without failure: cost is not measurable")
    crypto_ms = [
        m["provenance"]["cost"]["sign_ms"] + m["provenance"]["cost"]["verify_ms"] for m in signed
    ]
    sizes = [m["provenance"]["cost"]["meta_bytes"] for m in signed]

    by_plan: dict[tuple[Any, ...], dict[str, str]] = {}
    for m in measures:
        if m["cell"]["fault_rate"] == 0.0:
            key = tuple(m["cell"][k] for k in PAIRING)
            by_plan.setdefault(key, {})[m["cell"]["provenance"]] = m["id_episode"]
    end_to_end = [
        (durations[p["on"]] - durations[p["off"]]) * 1000
        for p in by_plan.values()
        if "on" in p and "off" in p
    ]
    secondary = {
        "end_to_end_pairs": len(end_to_end),
        "end_to_end_overhead_ms_median": (
            round(statistics.median(end_to_end), 3) if end_to_end else None
        ),
    }
    costs = {
        "surcout_latence_ms_median": round(statistics.median(crypto_ms), 4),
        "surcout_latence_ms_p99": round(_p99(crypto_ms), 4),
        "surcout_taille_message_octets": int(statistics.median(sizes)),
    }
    return costs, secondary


def degradation(measures: list[dict[str, Any]], policy: str, partial_rate: float) -> dict[str, Any]:
    def utility(**where: Any) -> float | None:
        return _mean(
            [
                m["utility"]
                for m in measures
                if m["utility"] is not None and all(m["cell"][k] == v for k, v in where.items())
            ]
        )

    values = {
        "utilite_sans_provenance": utility(provenance="off", defense="none", fault_rate=0.0),
        "utilite_avec_provenance": utility(provenance="on", defense=policy, fault_rate=0.0),
        "utilite_sous_defaillance_partielle": utility(
            provenance="on", defense=policy, fault_rate=partial_rate
        ),
    }
    missing = [k for k, v in values.items() if v is None]
    if missing:
        raise AggregationError(f"no episode with a defined utility for {missing}")
    return values


def y_fragment(run_dir: Path, policy: str, partial_rate: float) -> dict[str, Any]:
    measures = _read(run_dir / "measures.jsonl")
    durations = {r["id_episode"]: r["duree_s"] for r in _read(run_dir / "episodes.jsonl")}
    equality = equality_report(
        measures, where={"provenance": "on", "defense": policy, "fault_rate": 0.0}
    )
    if not equality.pairs:
        raise AggregationError(f"no clean/attacked pair with provenance on and defense {policy}")
    cost, end_to_end = delegation_cost(measures, durations)
    return {
        "cout_delegation": cost,
        "degradation_gracieuse": degradation(measures, policy, partial_rate),
        "egalite_inter_episodes": {
            "n_paires_testees": equality.pairs,
            "taux_egalite_observe": round(equality.rate or 0.0, 6),
            "violations": len(equality.violations),
        },
        "_provenance": {
            "run": run_dir.name,
            "policy": policy,
            "partial_fault_rate": partial_rate,
            "delegation_cost_end_to_end": end_to_end,
            "violations": equality.violations,
        },
    }
