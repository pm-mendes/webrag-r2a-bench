"""Attestations: signed statements of origin and derivation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from webrag_bench.provenance.canonical import canonical_json, digest
from webrag_bench.provenance.keys import KeyRegistry, PartyKey

VERSION = "webrag-attestation/0"


@dataclass(frozen=True)
class Attestation:
    issuer: str
    activity: dict[str, Any]  # {"tool": ..., "arguments_digest": ...}
    output_digest: str
    derived_from: tuple[str, ...]  # ids of earlier attestations
    issued_at: str
    signature: str  # base64url, over the canonical payload

    def payload(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "issuer": self.issuer,
            "activity": self.activity,
            "output_digest": self.output_digest,
            "derived_from": list(self.derived_from),
            "issued_at": self.issued_at,
        }

    @property
    def id(self) -> str:
        return digest(self.payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "id": self.id, "signature": self.signature}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Attestation:
        if d.get("version") != VERSION:
            raise ValueError(f"unsupported attestation version {d.get('version')!r}")
        return cls(
            d["issuer"],
            d["activity"],
            d["output_digest"],
            tuple(d["derived_from"]),
            d["issued_at"],
            d["signature"],
        )


def issue(
    key: PartyKey,
    tool: str,
    arguments: dict[str, Any],
    output: Any,
    derived_from: tuple[str, ...] = (),
    issued_at: str = "",
) -> Attestation:
    unsigned = Attestation(
        key.party,
        {"tool": tool, "arguments_digest": digest(arguments)},
        digest(output),
        tuple(derived_from),
        issued_at,
        "",
    )
    signature = key.sign(canonical_json(unsigned.payload()))
    return Attestation(
        unsigned.issuer,
        unsigned.activity,
        unsigned.output_digest,
        unsigned.derived_from,
        issued_at,
        base64.urlsafe_b64encode(signature).decode(),
    )


def verify(att: Attestation, registry: KeyRegistry, output: Any = None) -> list[str]:
    """Problems with one attestation; empty means valid. With `output`, also checks
    that the attestation covers exactly that output."""
    problems = []
    if not registry.knows(att.issuer):
        problems.append(f"unknown issuer {att.issuer!r}")
    else:
        try:
            signature = base64.urlsafe_b64decode(att.signature)
        except ValueError:
            signature = b""
        if not registry.verify(att.issuer, signature, canonical_json(att.payload())):
            problems.append(f"invalid signature for issuer {att.issuer!r}")
    if output is not None and digest(output) != att.output_digest:
        problems.append("output does not match the attested digest")
    return problems


def verify_chain(
    root: Attestation, store: dict[str, Attestation], registry: KeyRegistry
) -> list[str]:
    """Verify an attestation and, transitively, everything it derives from."""
    problems: list[str] = []
    seen: set[str] = set()
    stack: list[tuple[Attestation, tuple[str, ...]]] = [(root, ())]
    while stack:
        att, path = stack.pop()
        if att.id in path:
            problems.append(f"derivation cycle through {att.id}")
            continue
        if att.id in seen:
            continue
        seen.add(att.id)
        problems += [f"{att.id}: {p}" for p in verify(att, registry)]
        for parent_id in att.derived_from:
            parent = store.get(parent_id)
            if parent is None:
                problems.append(f"{att.id}: derives from unknown attestation {parent_id}")
            else:
                stack.append((parent, (*path, att.id)))
    return problems
