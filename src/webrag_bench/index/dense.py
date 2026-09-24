"""Dense index (cosine similarity over normalised embeddings)."""

from __future__ import annotations

import numpy as np

from webrag_bench.index.base import Doc, Scores, top_k
from webrag_bench.index.embedders import Embedder


class DenseIndex:
    name = "dense"

    def __init__(self, docs: list[Doc], embedder: Embedder) -> None:
        self.docs = docs
        self._embedder = embedder
        self._matrix = embedder.encode([d.text for d in docs]) if docs else np.zeros((0, 1))

    def scores(self, query: str) -> Scores:
        return self._matrix @ self._embedder.encode([query])[0]

    def search(self, query: str, k: int) -> list[tuple[Doc, float]]:
        return top_k(self.docs, self.scores(query), k)
