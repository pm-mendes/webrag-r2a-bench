"""Plan d'exécution : facteurs, cellules, graines, identifiants d'épisode.

Un plan est un YAML dans config/plans/. Les cellules sont le produit cartésien des
facteurs déclarés ; un plan non entièrement croisé se déclare comme plusieurs
sous-plans (clé `sous_plans`), chacun croisé — c'est la forme exigée par
`PLAN_MANIFEST.json` (grille réconciliée par somme de sous-plans).

L'identifiant d'épisode et la graine se déduisent de (plan, cellule, répétition) :
relancer un plan reproduit les mêmes identifiants, ce qui rend la reprise sûre.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from pathlib import Path

import yaml

from webrag_bench import RACINE
from webrag_bench.taches import Tache, charger_taches

FACTEURS = ("familles", "defenses", "generateurs", "index", "lecteurs")


@dataclass(frozen=True)
class Cellule:
    sous_plan: str
    tache: str
    famille: str
    defense: str
    generateur: str
    index: str
    lecteur: str
    repetition: int

    def cle(self) -> str:
        return "|".join(map(str, (self.sous_plan, self.tache, self.famille, self.defense,
                                  self.generateur, self.index, self.lecteur, self.repetition)))


@dataclass
class Plan:
    chemin: Path
    d: dict

    @classmethod
    def charger(cls, chemin: Path) -> "Plan":
        return cls(chemin, yaml.safe_load(chemin.read_text(encoding="utf-8")))

    @property
    def nom(self) -> str:
        return self.d["nom"]

    @property
    def gele(self) -> bool:
        return self.d["statut"] == "GELE"

    def chemin_config(self, cle: str) -> Path:
        return RACINE / self.d[cle]

    def taches(self) -> list[Tache]:
        return charger_taches(self.chemin_config("config_taches"))

    def generateur_decl(self, nom: str) -> dict:
        for g in self.d["generateurs"]:
            if g["nom"] == nom:
                return g
        raise KeyError(f"générateur {nom} non déclaré dans le plan")

    def sous_plans(self) -> dict[str, dict]:
        return self.d.get("sous_plans") or {"principal": self.d["facteurs"]}

    def cellules(self) -> list[Cellule]:
        toutes = {t.id for t in self.taches()}
        out = []
        for nom_sp, f in self.sous_plans().items():
            taches = sorted(toutes) if f.get("taches", "toutes") == "toutes" else f["taches"]
            inconnues = set(taches) - toutes
            if inconnues:
                raise ValueError(f"sous-plan {nom_sp} : tâches inconnues {sorted(inconnues)}")
            for combo in itertools.product(taches, *(f[k] for k in FACTEURS),
                                           range(f["repetitions"])):
                out.append(Cellule(nom_sp, *combo))
        return out

    def id_et_graine(self, c: Cellule) -> tuple[str, int]:
        h = hashlib.sha256(f"{self.nom}|{c.cle()}".encode()).hexdigest()
        return f"{self.nom}-{h[:16]}", int(h[16:24], 16)

    def chemins_geles(self) -> list[Path]:
        """Tout ce que l'empreinte de gel doit couvrir."""
        cles = ("config_attaques", "config_taches", "config_defenses", "config_juge", "corpus")
        return [self.chemin] + [self.chemin_config(k) for k in cles if k in self.d]
