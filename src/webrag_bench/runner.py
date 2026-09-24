"""Runner : construit l'archive, vérifie le gel, exécute les cellules, écrit un JSONL.

    webrag-bench config/plans/repetition-a-blanc.yaml --workers 4
    webrag-bench config/plans/campagne-P.yaml --workers 24     # refuse tant que le gel est incomplet

La sortie va dans runs/<plan>/episodes.jsonl. Une relance reprend là où elle s'est
arrêtée : les identifiants d'épisode sont déterministes et les épisodes déjà écrits
sont sautés.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import multiprocessing as mp
import sys
import urllib.parse
from pathlib import Path

from webrag_bench import RACINE
from webrag_bench.attaques import charger_gabarits
from webrag_bench.corpus import (RejeuWarc, charger_pages_benignes, construire_pages_adverses,
                                 ecrire_warc)
from webrag_bench.enregistrement import ecrire, ids_deja_faits
from webrag_bench.episode import Contexte, executer, version_banc
from webrag_bench.gel import GelIncomplet, empreinte, exiger_gel_complet
from webrag_bench.plan import Cellule, Plan
from webrag_bench.reseau import installer_garde

_CTX: Contexte | None = None


def preparer(plan: Plan, sortie: Path) -> tuple[Path, str]:
    """Construit l'archive WARC du plan et calcule l'empreinte de gel."""
    if plan.gele:
        exiger_gel_complet(plan.chemins_geles())
    benignes = charger_pages_benignes(plan.chemin_config("corpus"))
    gabarits = charger_gabarits(plan.chemin_config("config_attaques"))
    familles_plan = {f for sp in plan.sous_plans().values() for f in sp["familles"]} - {"aucune"}
    manquantes = familles_plan - set(gabarits)
    if manquantes:
        raise ValueError(f"familles sans gabarit : {sorted(manquantes)}")
    adverses = construire_pages_adverses(benignes, plan.taches(), gabarits, plan.d["sel_canari"])
    warc = sortie / "corpus.warc"
    h_warc = ecrire_warc(benignes + adverses, warc)
    h = empreinte(plan.chemins_geles() + [warc], RACINE)
    prefixe = "" if plan.gele else "NON-GELE:"
    (sortie / "gel.json").write_text(json.dumps(
        {"plan": plan.nom, "empreinte_gel": prefixe + h, "sha256_warc": h_warc,
         "version_banc": version_banc(RACINE)}, indent=2), encoding="utf-8")
    return warc, prefixe + h


def hotes_autorises(plan: Plan) -> set[str]:
    hotes = set(plan.d.get("hotes_autorises", []))
    for g in plan.d["generateurs"]:
        if "base_url" in g:
            hotes.add(urllib.parse.urlparse(g["base_url"]).hostname or "")
    emb = plan.d.get("embedder", {})
    if "base_url" in emb:
        hotes.add(urllib.parse.urlparse(emb["base_url"]).hostname or "")
    return hotes - {""}


def _init_worker(chemin_plan: str, warc: str, empreinte_gel: str, vbanc: str) -> None:
    global _CTX
    plan = Plan.charger(Path(chemin_plan))
    installer_garde(hotes_autorises(plan))
    _CTX = Contexte(plan, RejeuWarc(Path(warc)), empreinte_gel, vbanc)


def _un_episode(c: Cellule) -> dict:
    assert _CTX is not None
    try:
        return asyncio.run(executer(_CTX, c))
    except Exception as e:  # l'échec d'un épisode ne doit pas tuer le worker
        return {"_echec": True, "cellule": c.cle(), "erreur": f"{type(e).__name__}: {e}"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", type=Path)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limite", type=int, default=None, help="n'exécuter que les N premières cellules")
    a = ap.parse_args(argv)

    plan = Plan.charger(a.plan.resolve())
    sortie = RACINE / "runs" / plan.nom
    sortie.mkdir(parents=True, exist_ok=True)
    try:
        warc, h = preparer(plan, sortie)
    except GelIncomplet as e:
        print(e, file=sys.stderr)
        return 3

    cellules = plan.cellules()
    jsonl = sortie / "episodes.jsonl"
    faits = ids_deja_faits(jsonl)
    a_faire = [c for c in cellules if plan.id_et_graine(c)[0] not in faits][: a.limite]
    print(f"plan {plan.nom} : {len(cellules)} cellules, {len(faits)} déjà faites, "
          f"{len(a_faire)} à exécuter · empreinte {h[:24]}…", flush=True)

    echecs = sortie / "echecs.jsonl"
    n_ok = n_ko = 0
    initargs = (str(plan.chemin), str(warc), h, version_banc(RACINE))
    with mp.get_context("spawn").Pool(a.workers, _init_worker, initargs) as pool:
        for rec in pool.imap_unordered(_un_episode, a_faire):
            if rec.get("_echec"):
                n_ko += 1
                with echecs.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue
            ecrire(rec, jsonl)
            n_ok += 1
            if (n_ok + n_ko) % 50 == 0:
                print(f"  {n_ok + n_ko}/{len(a_faire)}", flush=True)
    print(f"terminé : {n_ok} épisodes écrits dans {jsonl.relative_to(RACINE)}, {n_ko} échecs"
          + (f" (voir {echecs.relative_to(RACINE)})" if n_ko else ""))
    return 1 if n_ko else 0


if __name__ == "__main__":
    sys.exit(main())
