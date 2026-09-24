"""Conditions de défense.

Une défense agit à deux endroits : sur le contexte (avant génération) et sur chaque
appel d'outil (avant exécution). Un appel refusé est enregistré avec `bloque_par`.

Les six conditions du manuscrit — dont Progent — sont un élément GELÉ. Leur
configuration exacte et la version de leur code viennent du manuscrit : tant qu'elle
n'est pas versée, elles lèvent `DefenseNonSpecifiee` au lieu d'être approximées.
`garde-outils-squelette` ne sert qu'à la répétition à blanc.
"""

from __future__ import annotations

from dataclasses import dataclass

from webrag_bench.taches import Tache


class DefenseNonSpecifiee(NotImplementedError):
    pass


@dataclass(frozen=True)
class Appel:
    outil: str  # "serveur.outil"
    arguments: dict


class Defense:
    nom = "aucune"

    def filtrer_contexte(self, passages: list[str]) -> list[str]:
        return passages

    def autoriser(self, appel: Appel, tache: Tache) -> bool:
        return True


class GardeOutilsSquelette(Defense):
    """Liste blanche d'outils par tâche. Condition de DÉMONSTRATION, hors grille gelée."""

    nom = "garde-outils-squelette"

    def autoriser(self, appel: Appel, tache: Tache) -> bool:
        return appel.outil in tache.outils_autorises


class _EnAttente(Defense):
    def __init__(self, nom: str) -> None:
        self.nom = nom
        raise DefenseNonSpecifiee(
            f"défense {nom!r} : configuration exacte et version du code à verser depuis le "
            "manuscrit (config/gel/defenses/) — elle n'est pas approximée ici"
        )


_DEFENSES: dict[str, type[Defense]] = {
    "aucune": Defense,
    "garde-outils-squelette": GardeOutilsSquelette,
}
EN_ATTENTE = ("progent", "PENDING-D2", "PENDING-D3", "PENDING-D4", "PENDING-D5")


def defense(nom: str) -> Defense:
    if nom in _DEFENSES:
        return _DEFENSES[nom]()
    if nom in EN_ATTENTE:
        return _EnAttente(nom)
    raise ValueError(f"condition de défense inconnue : {nom}")
