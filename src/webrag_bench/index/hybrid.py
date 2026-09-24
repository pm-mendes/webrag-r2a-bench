"""Hybrid index: linear fusion alpha * dense + (1 - alpha) * BM25, as in WI-IAT."""

from __future__ import annotations

from webrag_bench.index.base import Doc, top_k
from webrag_bench.index.bm25 import BM25Index
from webrag_bench.index.dense import DenseIndex


class HybridIndex:
    name = "hybrid"

    def __init__(self, dense: DenseIndex, bm25: BM25Index, alpha: float) -> None:
        if dense.docs != bm25.docs:
            raise ValueError("dense and BM25 indexes must cover the same documents")
        self.docs = dense.docs
        self._dense, self._bm25, self._alpha = dense, bm25, alpha

    def search(self, query: str, k: int) -> list[tuple[Doc, float]]:
        scores = self._alpha * self._dense.scores(query) + (1 - self._alpha) * self._bm25.scores(
            query
        )
        return top_k(self.docs, scores, k)
