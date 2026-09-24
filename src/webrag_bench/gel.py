"""Empreinte de gel et contrôle d'entrée en campagne.

L'empreinte SHA-256 couvre le plan, les gabarits, les tâches, les défenses, le juge
et l'archive WARC. Elle est écrite dans chaque enregistrement : un gabarit qui
bouge après le gel change l'empreinte, et c'est visible dans les données.

Un plan de campagne (statut GELE) refuse de démarrer tant qu'une marque PENDING ou
un élément DEMO subsiste dans ce qu'il référence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


class GelIncomplet(RuntimeError):
    pass


def empreinte(chemins: list[Path], racine: Path) -> str:
    h = hashlib.sha256()
    fichiers: list[Path] = []
    for c in chemins:
        fichiers += sorted(p for p in c.rglob("*") if p.is_file()) if c.is_dir() else [c]
    for f in sorted(set(fichiers)):
        nom = f.relative_to(racine) if f.is_relative_to(racine) else Path(f.name)
        h.update(str(nom).encode() + b"\0")
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def marques_bloquantes(chemins: list[Path]) -> list[str]:
    """Liste les fichiers qui contiennent encore PENDING ou `statut: DEMO`."""
    trouves = []
    for c in chemins:
        fichiers = sorted(p for p in c.rglob("*") if p.is_file()) if c.is_dir() else [c]
        for f in fichiers:
            try:
                t = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "PENDING" in t:
                trouves.append(f"{f} : PENDING")
            if "statut: DEMO" in t:
                trouves.append(f"{f} : élément DEMO")
    return trouves


def exiger_gel_complet(chemins: list[Path]) -> None:
    m = marques_bloquantes(chemins)
    if m:
        raise GelIncomplet(
            "campagne refusée : le gel n'est pas complet.\n  " + "\n  ".join(m)
        )
