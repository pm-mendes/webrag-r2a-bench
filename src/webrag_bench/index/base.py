"""Shared index types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
import numpy.typing as npt

Scores = npt.NDArray[np.float64]


@dataclass(frozen=True)
class Doc:
    url: str
    text: str


class Index(Protocol):
    name: str

    def search(self, query: str, k: int) -> list[tuple[Doc, float]]: ...


def tokenize(text: str) -> list[str]:
    return "".join(c.lower() if c.isalnum() else " " for c in text).split()


def top_k(
    docs: list[Doc], scores: Scores, k: int, positive_only: bool = False
) -> list[tuple[Doc, float]]:
    order = np.argsort(-scores, kind="stable")[:k]
    return [(docs[i], float(scores[i])) for i in order if not positive_only or scores[i] > 0]
