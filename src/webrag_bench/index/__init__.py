"""Retrieval indexes: dense, BM25, hybrid.

Adapted from the WI-IAT code base (agentic-rag-ipi), without ChromaDB: indexes are
held in memory and rebuilt identically from the corpus.
"""

from webrag_bench.index.base import Doc, Index
from webrag_bench.index.bm25 import BM25Index
from webrag_bench.index.dense import DenseIndex
from webrag_bench.index.embedders import Embedder, HttpEmbedder, StubEmbedder, build_embedder
from webrag_bench.index.hybrid import HybridIndex
from webrag_bench.index.factory import build_index

__all__ = [
    "BM25Index",
    "DenseIndex",
    "Doc",
    "Embedder",
    "HttpEmbedder",
    "HybridIndex",
    "Index",
    "StubEmbedder",
    "build_embedder",
    "build_index",
]
