"""Text embedders for the dense index."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from typing import Protocol

import numpy as np

from webrag_bench.config import EmbedderConfig
from webrag_bench.index.base import Scores, tokenize


class Embedder(Protocol):
    identifier: str
    is_stub: bool

    def encode(self, texts: list[str]) -> Scores: ...


class StubEmbedder:
    """Hashed bag of tokens. For dry runs ONLY: it carries no semantics and must
    never produce a reported result."""

    identifier = "stub-hashing-256"
    is_stub = True

    def encode(self, texts: list[str]) -> Scores:
        m = np.zeros((len(texts), 256))
        for i, text in enumerate(texts):
            for token in tokenize(text):
                m[i, int(hashlib.md5(token.encode()).hexdigest(), 16) % 256] += 1.0
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.where(norms == 0, 1, norms)


class HttpEmbedder:
    """Embedder behind an OpenAI-compatible /embeddings endpoint (e.g. on the OVH machine)."""

    is_stub = False

    def __init__(self, base_url: str, model: str, key_env: str | None = None) -> None:
        self._url = base_url.rstrip("/") + "/embeddings"
        self._model = model
        self._key = os.environ.get(key_env, "") if key_env else ""
        self.identifier = model

    def encode(self, texts: list[str]) -> Scores:
        request = urllib.request.Request(
            self._url,
            data=json.dumps({"model": self._model, "input": texts}).encode(),
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self._key}"} if self._key else {}),
            },
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.load(response)
        rows = sorted(payload["data"], key=lambda e: e["index"])
        m = np.array([e["embedding"] for e in rows], dtype=np.float64)
        return m / np.linalg.norm(m, axis=1, keepdims=True)


def build_embedder(config: EmbedderConfig) -> Embedder:
    if config.type == "stub":
        return StubEmbedder()
    if not (config.base_url and config.model):  # also enforced by EmbedderConfig
        raise ValueError("an openai-compatible embedder needs base_url and model")
    return HttpEmbedder(config.base_url, config.model, config.key_env)
