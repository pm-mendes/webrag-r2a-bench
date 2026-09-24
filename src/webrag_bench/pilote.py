"""Mesure du pilote : remplace l'hypothèse de 42 s par épisode par une médiane mesurée.

    python -m webrag_bench.pilote runs/pilote-P/episodes.jsonl

Affiche la médiane (et les quantiles) de `duree_s` par générateur, et la compare aux
points d'équilibre de P et Y pour la fenêtre restante. Le résultat se reporte dans
kit/MASTER_VALUES.json -> pilote.mediane_s_par_episode (par script, pas à la main).
Les épisodes d'un générateur factice sont exclus : leur durée ne mesure rien.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

EPISODES = {"P": 69036, "Y": 9408}  # PLAN_MANIFEST.json des chantiers 07 et 08


def point_equilibre(episodes: int, workers: int, fenetre_h: float) -> float:
    return workers * fenetre_h * 3600 / episodes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--fenetre-h", type=float, required=True,
                    help="fenêtre de campagne restante, en heures")
    a = ap.parse_args(argv)

    par_gen: dict[str, list[float]] = defaultdict(list)
    factices = 0
    for ligne in a.jsonl.read_text(encoding="utf-8").splitlines():
        r = json.loads(ligne)
        if any(e.startswith("generateur-factice") for e in r.get("erreurs", [])):
            factices += 1
            continue
        par_gen[f"{r['generateur']['nom']} ({r['generateur']['id_version']})"].append(r["duree_s"])
    if factices:
        print(f"{factices} épisode(s) à générateur factice exclus")
    if not par_gen:
        print("aucun épisode mesurable : le pilote doit tourner sur les vrais générateurs")
        return 2

    toutes = [d for v in par_gen.values() for d in v]
    for g, v in sorted(par_gen.items()):
        q = statistics.quantiles(v, n=10) if len(v) >= 2 else [v[0]] * 9
        print(f"{g:50s} n={len(v):4d}  médiane={statistics.median(v):7.2f} s  "
              f"p10={q[0]:7.2f}  p90={q[-1]:7.2f}")
    med = statistics.median(toutes)
    print(f"\nmédiane globale : {med:.2f} s/épisode (n={len(toutes)})")
    for p, n in EPISODES.items():
        pe = point_equilibre(n, a.workers, a.fenetre_h)
        verdict = "tient" if med <= pe else "NE TIENT PAS -> règle de repli"
        print(f"  {p} : point d'équilibre {pe:8.1f} s ({a.workers} workers, {a.fenetre_h} h) -> {verdict}")
    pe_conj = point_equilibre(sum(EPISODES.values()), a.workers, a.fenetre_h)
    print(f"  P+Y sur machine partagée : {pe_conj:.1f} s -> "
          + ("tient" if med <= pe_conj else "NE TIENT PAS -> règle de repli"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
