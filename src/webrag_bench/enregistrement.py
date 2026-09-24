"""Enregistrement d'exécution, validé contre kit/schemas/run_record_schema.json.

Le schéma est une copie octet pour octet de celui du kit (07-TWEB-R2A/kit/schemas/) ;
`tests/test_schema.py` échoue si les deux divergent.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

from webrag_bench import RACINE

SCHEMA = json.loads((RACINE / "schemas" / "run_record_schema.json").read_text(encoding="utf-8"))
_VALIDATEUR = jsonschema.Draft202012Validator(
    SCHEMA, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
)


def empreinte_arguments(arguments: dict) -> str:
    return hashlib.sha256(
        json.dumps(arguments, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def valider(rec: dict) -> None:
    erreurs = sorted(_VALIDATEUR.iter_errors(rec), key=lambda e: list(e.path))
    if erreurs:
        raise jsonschema.ValidationError(
            "; ".join(f"{'/'.join(map(str, e.path))}: {e.message}" for e in erreurs)
        )


def ecrire(rec: dict, chemin: Path) -> None:
    valider(rec)
    with chemin.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def ids_deja_faits(chemin: Path) -> set[str]:
    if not chemin.exists():
        return set()
    faits = set()
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if ligne.strip():
            faits.add(json.loads(ligne)["id_episode"])
    return faits
