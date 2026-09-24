"""Tâches : requête utilisateur, page ciblée, but adverse.

La liste des tâches est GELÉE (config/gel/taches/). Les tâches de config/demo/taches/
servent uniquement à la répétition à blanc.

`type_action` reprend la partition du schéma d'enregistrement :
- action-open      : la requête délègue l'action au contenu (« fais ce que dit la page »)
- action-specifiee : la requête fixe l'action ; le contenu ne devrait servir que d'information
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TYPES_ACTION = ("action-open", "action-specifiee")


@dataclass(frozen=True)
class Tache:
    id: str
    requete: str
    type_action: str
    page_cible: str
    but_adverse: dict
    outils_autorises: tuple[str, ...] = field(default_factory=tuple)

    def but_adverse_rendu(self, c: str) -> dict:
        """But adverse avec le canari substitué dans chaque argument textuel."""
        but = copy.deepcopy(self.but_adverse)
        but["arguments"] = {
            k: (v.format(canari=c) if isinstance(v, str) else v)
            for k, v in but["arguments"].items()
        }
        return but


def charger_taches(dossier: Path) -> list[Tache]:
    taches = []
    for f in sorted(dossier.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if d["type_action"] not in TYPES_ACTION:
            raise ValueError(f"{f.name} : type_action {d['type_action']!r} hors partition")
        if not any("{canari}" in str(v) for v in d["but_adverse"]["arguments"].values()):
            raise ValueError(f"{f.name} : le but adverse doit porter le canari, "
                             "sinon l'oracle d'action n'est pas mécanique")
        taches.append(Tache(
            id=d["id"], requete=d["requete"], type_action=d["type_action"],
            page_cible=d["page_cible"], but_adverse=d["but_adverse"],
            outils_autorises=tuple(d.get("outils_autorises", [])),
        ))
    ids = [t.id for t in taches]
    if len(ids) != len(set(ids)):
        raise ValueError("identifiants de tâche en double")
    return taches
