"""Lexical index (Okapi BM25)."""

from __future__ import annotations

import numpy as np
from rank_bm25 import BM25Okapi

from webrag_bench.index.base import Doc, Scores, tokenize, top_k


class BM25Index:
    name = "bm25"

    def __init__(self, docs: list[Doc]) -> None:
        self.docs = docs
        self._bm25 = BM25Okapi([tokenize(d.text) for d in docs])

    def scores(self, query: str) -> Scores:
        """BM25 scores normalised by their maximum, in [0, 1]."""
        s = np.asarray(self._bm25.get_scores(tokenize(query)), dtype=np.float64)
        peak = float(s.max()) if len(s) else 0.0
        return s / peak if peak > 0 else s

    def search(self, query: str, k: int) -> list[tuple[Doc, float]]:
        return top_k(self.docs, self.scores(query), k, positive_only=True)
