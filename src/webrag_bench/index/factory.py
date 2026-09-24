"""Index construction by name."""

from __future__ import annotations

from webrag_bench.index.base import Doc, Index
from webrag_bench.index.bm25 import BM25Index
from webrag_bench.index.dense import DenseIndex
from webrag_bench.index.embedders import Embedder
from webrag_bench.index.hybrid import HybridIndex


def build_index(name: str, docs: list[Doc], embedder: Embedder, alpha: float) -> Index:
    if name == "bm25":
        return BM25Index(docs)
    if name == "dense":
        return DenseIndex(docs, embedder)
    if name == "hybrid":
        return HybridIndex(DenseIndex(docs, embedder), BM25Index(docs), alpha)
    raise ValueError(f"unknown index {name!r}")
