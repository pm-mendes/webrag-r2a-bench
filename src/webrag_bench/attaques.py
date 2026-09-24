"""Familles d'attaque : gabarits, canaris et points d'insertion.

Un gabarit est un fichier YAML (voir config/demo/attaques/ et config/gel/attaques/).
Le texte exact des gabarits des quatre familles est un élément GELÉ : il vient du
manuscrit, pas de ce dépôt. Les gabarits de config/demo/ ne servent qu'à la
répétition à blanc et portent `statut: DEMO`.

Le canari est un jeton propre au couple famille × tâche. Il n'apparaît que dans
la page adverse et dans les arguments du but adverse : sa présence en aval
(contexte, sortie, journal d'un serveur) est ce que les oracles mécaniques testent.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

POINTS_INSERTION = ("visible", "cache-css", "commentaire", "attribut-alt", "meta")


@dataclass(frozen=True)
class Gabarit:
    famille: str
    nom: str
    statut: str  # DEMO | GELE
    insertion: str
    texte: str

    def rendre(self, but: dict, c: str) -> str:
        return self.texte.format(
            canari=c,
            outil=but["outil"],
            arguments=json.dumps(but["arguments"], ensure_ascii=False),
        )


def canari(famille: str, tache_id: str, sel: str) -> str:
    h = hashlib.sha256(f"{sel}|{famille}|{tache_id}".encode()).hexdigest()
    return f"CNR{h[:12].upper()}"


def charger_gabarits(dossier: Path) -> dict[str, Gabarit]:
    gabarits: dict[str, Gabarit] = {}
    for f in sorted(dossier.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if d["insertion"] not in POINTS_INSERTION:
            raise ValueError(f"{f.name} : point d'insertion inconnu {d['insertion']!r}")
        g = Gabarit(famille=d["famille"], nom=d["nom"], statut=d["statut"],
                    insertion=d["insertion"], texte=d["gabarit"])
        if g.famille in gabarits:
            raise ValueError(f"famille {g.famille} définie deux fois")
        gabarits[g.famille] = g
    return gabarits


def injecter(html: str, g: Gabarit, but: dict, c: str) -> str:
    """Insère la charge dans la page selon le point d'insertion du gabarit.

    Le point d'insertion compte : selon le lecteur (HTML -> texte), un contenu caché
    en CSS, un commentaire ou un attribut survit ou disparaît. C'est ce qui fait du
    lecteur un facteur expérimental.
    """
    charge = g.rendre(but, c)
    echappe = charge.replace('"', "&quot;")
    fragments = {
        "visible": f"<p>{charge}</p>",
        "cache-css": f'<div style="display:none">{charge}</div>',
        "commentaire": f"<!-- {charge} -->",
        "attribut-alt": f'<img src="data:," alt="{echappe}">',
        "meta": f'<meta name="description" content="{echappe}">',
    }
    frag = fragments[g.insertion]
    ancre = "</head>" if g.insertion == "meta" else "</main>"
    if ancre not in html:
        ancre = "</body>"
    if ancre not in html:
        return html + frag
    return html.replace(ancre, frag + ancre, 1)
