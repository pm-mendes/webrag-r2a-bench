"""Index de recherche : dense, BM25, hybride.

Repris et simplifié du code WI-IAT (agentic-rag-ipi/src/agentic_rag/retrieval),
sans ChromaDB : l'index tient en mémoire et se reconstruit à l'identique.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from rank_bm25 import BM25Okapi


@dataclass(frozen=True)
class Doc:
    url: str
    texte: str


def _tokens(s: str) -> list[str]:
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in s).split() if t]


class Index(Protocol):
    nom: str

    def chercher(self, requete: str, k: int) -> list[tuple[Doc, float]]: ...


class IndexBM25:
    nom = "bm25"

    def __init__(self, docs: list[Doc]) -> None:
        self._docs = docs
        self._bm25 = BM25Okapi([_tokens(d.texte) for d in docs])

    def scores(self, requete: str) -> np.ndarray:
        s = np.asarray(self._bm25.get_scores(_tokens(requete)), dtype=float)
        m = s.max() if len(s) else 0.0
        return s / m if m > 0 else s

    def chercher(self, requete: str, k: int) -> list[tuple[Doc, float]]:
        s = self.scores(requete)
        ordre = np.argsort(-s, kind="stable")[:k]
        return [(self._docs[i], float(s[i])) for i in ordre if s[i] > 0]


class Embedder(Protocol):
    identifiant: str

    def encoder(self, textes: list[str]) -> np.ndarray: ...


class EmbedderFactice:
    """Plongement par hachage de tokens. Pour la répétition à blanc UNIQUEMENT :
    il n'a aucune valeur sémantique et ne doit jamais produire un résultat publié."""

    identifiant = "factice-hachage-256"

    def encoder(self, textes: list[str]) -> np.ndarray:
        m = np.zeros((len(textes), 256))
        for i, t in enumerate(textes):
            for tok in _tokens(t):
                m[i, int(hashlib.md5(tok.encode()).hexdigest(), 16) % 256] += 1.0
        n = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.where(n == 0, 1, n)


class EmbedderHTTP:
    """Embedder derrière un point d'accès compatible OpenAI (/v1/embeddings),
    p. ex. l'embedder servi sur la machine OVH."""

    def __init__(self, base_url: str, modele: str, cle_env: str | None = None) -> None:
        self._url = base_url.rstrip("/") + "/embeddings"
        self._modele = modele
        self._cle = os.environ.get(cle_env, "") if cle_env else ""
        self.identifiant = modele

    def encoder(self, textes: list[str]) -> np.ndarray:
        req = urllib.request.Request(
            self._url, data=json.dumps({"model": self._modele, "input": textes}).encode(),
            headers={"Content-Type": "application/json",
                     **({"Authorization": f"Bearer {self._cle}"} if self._cle else {})},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.load(r)
        m = np.array([e["embedding"] for e in sorted(d["data"], key=lambda e: e["index"])])
        return m / np.linalg.norm(m, axis=1, keepdims=True)


class IndexDense:
    nom = "dense"

    def __init__(self, docs: list[Doc], embedder: Embedder) -> None:
        self._docs = docs
        self._emb = embedder
        self._m = embedder.encoder([d.texte for d in docs]) if docs else np.zeros((0, 1))

    def scores(self, requete: str) -> np.ndarray:
        q = self._emb.encoder([requete])[0]
        return self._m @ q

    def chercher(self, requete: str, k: int) -> list[tuple[Doc, float]]:
        s = self.scores(requete)
        ordre = np.argsort(-s, kind="stable")[:k]
        return [(self._docs[i], float(s[i])) for i in ordre]


class IndexHybride:
    """Fusion linéaire α·dense + (1-α)·BM25, comme dans WI-IAT. α est une constante du plan."""

    nom = "hybride"

    def __init__(self, dense: IndexDense, bm25: IndexBM25, alpha: float) -> None:
        self._d, self._b, self._alpha = dense, bm25, alpha
        self._docs = dense._docs

    def chercher(self, requete: str, k: int) -> list[tuple[Doc, float]]:
        s = self._alpha * self._d.scores(requete) + (1 - self._alpha) * self._b.scores(requete)
        ordre = np.argsort(-s, kind="stable")[:k]
        return [(self._docs[i], float(s[i])) for i in ordre]


def construire_index(nom: str, docs: list[Doc], embedder: Embedder, alpha: float) -> Index:
    if nom == "bm25":
        return IndexBM25(docs)
    if nom == "dense":
        return IndexDense(docs, embedder)
    if nom == "hybride":
        return IndexHybride(IndexDense(docs, embedder), IndexBM25(docs), alpha)
    raise ValueError(f"index inconnu : {nom}")
