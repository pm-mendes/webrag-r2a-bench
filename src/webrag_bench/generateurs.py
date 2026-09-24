"""Générateurs : le modèle qui lit le contexte et émet des appels d'outils.

Chaque générateur est déclaré dans le plan avec un `id_version` figé. Pour un
générateur distant, l'identifiant renvoyé par le fournisseur est comparé à
l'identifiant déclaré à CHAQUE appel : un écart est enregistré comme erreur
`substitution-modele` sur l'épisode. On ne substitue pas en silence.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from webrag_bench.defenses import Appel


@dataclass
class Reponse:
    texte: str
    appels: list[Appel]
    id_modele_renvoye: str
    erreurs: list[str] = field(default_factory=list)


class GenerateurFactice:
    """Générateur scripté et déterministe, pour la répétition à blanc UNIQUEMENT.

    Il obéit à toute ligne `APPEL <serveur.outil> <json>` présente dans son contexte :
    c'est le pire cas d'obéissance, utile pour vérifier que les étages, les défenses
    et les oracles sont câblés. Sa durée n'a aucune valeur pour le pilote.
    """

    FACTICE = True
    _MOTIF = re.compile(r"APPEL\s+([a-z_]+\.[a-z_]+)\s+(\{[^{}]*\})", re.S)

    def __init__(self, nom: str, id_version: str) -> None:
        self.nom, self.id_version = nom, id_version

    def generer(self, systeme: str, utilisateur: str, outils: list[dict]) -> Reponse:
        appels = []
        noms = {o["nom"] for o in outils}
        for outil, brut in self._MOTIF.findall(utilisateur):
            try:
                args = json.loads(brut.replace("&quot;", '"'))
            except json.JSONDecodeError:
                continue
            if outil in noms:
                appels.append(Appel(outil, args))
        return Reponse(texte="(réponse factice)", appels=appels, id_modele_renvoye=self.id_version)


class GenerateurOpenAICompatible:
    """Point d'accès /chat/completions compatible OpenAI : API commerciales, ou vLLM
    sur la machine OVH pour le modèle 8B. Clé lue dans une variable d'environnement."""

    FACTICE = False

    def __init__(self, nom: str, id_version: str, base_url: str, cle_env: str | None,
                 temperature: float = 0.0, max_tokens: int = 1024, graine: int | None = None) -> None:
        self.nom, self.id_version = nom, id_version
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._cle = os.environ.get(cle_env, "") if cle_env else ""
        if cle_env and not self._cle:
            raise RuntimeError(f"générateur {nom} : variable {cle_env} absente")
        self._temperature, self._max_tokens, self._graine = temperature, max_tokens, graine

    @staticmethod
    def _nom_fonction(outil: str) -> str:
        return outil.replace(".", "__")

    def generer(self, systeme: str, utilisateur: str, outils: list[dict]) -> Reponse:
        corps = {
            "model": self.id_version,
            "messages": [{"role": "system", "content": systeme},
                         {"role": "user", "content": utilisateur}],
            "tools": [{"type": "function", "function": {
                "name": self._nom_fonction(o["nom"]), "description": o["description"],
                "parameters": o["schema"]}} for o in outils],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if self._graine is not None:
            corps["seed"] = self._graine
        req = urllib.request.Request(
            self._url, data=json.dumps(corps).encode(),
            headers={"Content-Type": "application/json",
                     **({"Authorization": f"Bearer {self._cle}"} if self._cle else {})},
        )
        d = self._envoyer(req)
        msg = d["choices"][0]["message"]
        appels = []
        erreurs = []
        for tc in msg.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                erreurs.append("arguments-outil-non-json")
                continue
            appels.append(Appel(tc["function"]["name"].replace("__", "."), args))
        renvoye = d.get("model", "")
        if renvoye != self.id_version:
            erreurs.append(f"substitution-modele: declare={self.id_version} renvoye={renvoye}")
        return Reponse(texte=msg.get("content") or "", appels=appels,
                       id_modele_renvoye=renvoye, erreurs=erreurs)

    @staticmethod
    def _envoyer(req: urllib.request.Request, essais: int = 4) -> dict:
        for i in range(essais):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code not in (429, 500, 502, 503, 504) or i == essais - 1:
                    raise
            except urllib.error.URLError:
                if i == essais - 1:
                    raise
            time.sleep(2 ** i * 5)
        raise RuntimeError("inaccessible")


def generateur(decl: dict, graine: int | None = None):
    """`decl` : entrée de la section `generateurs` du plan."""
    if decl["type"] == "factice":
        return GenerateurFactice(decl["nom"], decl["id_version"])
    if decl["type"] == "openai-compatible":
        return GenerateurOpenAICompatible(
            decl["nom"], decl["id_version"], decl["base_url"], decl.get("cle_env"),
            temperature=decl.get("temperature", 0.0), max_tokens=decl.get("max_tokens", 1024),
            graine=graine,
        )
    raise ValueError(f"type de générateur inconnu : {decl['type']}")
