"""Cost of signed provenance within one episode.

Signing happens in the servers and verification in the agent; both run in the same
process, so one meter per episode collects them. Together with the paired off/on
episode durations, this feeds the confrontation with the irreducible-cost bound.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar

from webrag_bench.provenance.attestation import Attestation
from webrag_bench.provenance.canonical import canonical_json

T = TypeVar("T")
P = ParamSpec("P")


@dataclass
class ProvenanceMeter:
    sign_s: float = 0.0
    verify_s: float = 0.0
    attestations: int = 0
    meta_bytes: int = 0

    def timed_sign(
        self, fn: Callable[P, Attestation], *args: P.args, **kwargs: P.kwargs
    ) -> Attestation:
        start = time.perf_counter()
        attestation = fn(*args, **kwargs)
        self.sign_s += time.perf_counter() - start
        self.attestations += 1
        self.meta_bytes += len(canonical_json(attestation.to_dict()))
        return attestation

    def timed_verify(self, fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        self.verify_s += time.perf_counter() - start
        return result

    def summary(self) -> dict[str, float | int]:
        return {
            "sign_ms": round(self.sign_s * 1000, 4),
            "verify_ms": round(self.verify_s * 1000, 4),
            "attestations": self.attestations,
            "meta_bytes": self.meta_bytes,
        }
