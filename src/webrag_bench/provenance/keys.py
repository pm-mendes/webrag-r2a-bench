"""Party keys and the registry of public keys.

Keys are derived deterministically from (seed, party id) so that a run is
reproducible; the seed is part of the frozen configuration. Deterministic derivation
is for a closed benchmark only — a deployment would generate keys randomly.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


@dataclass(frozen=True)
class PartyKey:
    party: str
    private: Ed25519PrivateKey

    @classmethod
    def derive(cls, party: str, seed: str) -> PartyKey:
        material = hashlib.sha256(f"webrag-provenance|{seed}|{party}".encode()).digest()
        return cls(party, Ed25519PrivateKey.from_private_bytes(material))

    @property
    def public_bytes(self) -> bytes:
        return self.private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def sign(self, data: bytes) -> bytes:
        return self.private.sign(data)


@dataclass
class KeyRegistry:
    """Public keys by party id. Who may issue attestations, and with which key."""

    _keys: dict[str, Ed25519PublicKey] = field(default_factory=dict)

    def register(self, party: str, public_bytes: bytes) -> None:
        if party in self._keys:
            raise ValueError(f"party {party!r} is already registered")
        self._keys[party] = Ed25519PublicKey.from_public_bytes(public_bytes)

    def knows(self, party: str) -> bool:
        return party in self._keys

    def verify(self, party: str, signature: bytes, data: bytes) -> bool:
        key = self._keys.get(party)
        if key is None:
            return False
        try:
            key.verify(signature, data)
        except InvalidSignature:
            return False
        return True
