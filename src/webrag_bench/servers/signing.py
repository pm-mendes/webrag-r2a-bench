"""Signing variants of the sandbox servers (paper Y).

- `signed_http_server`: each web origin (URL host) signs the pages it serves. The
  attestation says "origin H served this exact content for this URL".
- `signed_peer_server`: the peer agent signs its answer to a delegation, and declares
  which earlier attestations the delegated instruction derives from.

Partial failure (degradation experiments): a party listed in `faulty` misbehaves
according to `fault_mode` — `missing` (no attestation), `corrupt` (signature
altered), `unknown-key` (signed with a key absent from the registry).
"""

from __future__ import annotations

import base64
import dataclasses
import urllib.parse

from mcp.server.mcpserver import MCPServer
from mcp_types import CallToolResult, TextContent

from webrag_bench.corpus import NotInCorpusError, WarcReplay
from webrag_bench.provenance import (
    Attestation,
    KeyRegistry,
    PartyKey,
    ProvenanceMeter,
    attach,
    canonical_json,
    issue,
)
from webrag_bench.servers.journal import Journal


def origin_of(url: str) -> str:
    return urllib.parse.urlparse(url).hostname or "unknown"


def party_keys(parties: list[str], seed: str) -> tuple[dict[str, PartyKey], KeyRegistry]:
    keys = {p: PartyKey.derive(p, seed) for p in sorted(set(parties))}
    registry = KeyRegistry()
    for p, k in keys.items():
        registry.register(p, k.public_bytes)
    return keys, registry


@dataclasses.dataclass(frozen=True)
class Faults:
    """Which parties misbehave in this episode, and how."""

    faulty: frozenset[str] = frozenset()
    mode: str = "missing"

    def apply(self, party: str, text: str, attestation: Attestation) -> CallToolResult:
        """Result as sent by `party`, degraded if the party is faulty."""
        if party not in self.faulty:
            return attach(text, attestation)
        if self.mode == "missing":
            return CallToolResult(content=[TextContent(type="text", text=text)])
        if self.mode == "corrupt":
            sig = attestation.signature
            altered = ("A" if sig[0] != "A" else "B") + sig[1:]
            return attach(text, dataclasses.replace(attestation, signature=altered))
        if self.mode == "unknown-key":
            # same payload, signed with a key the registry does not hold for `party`
            rogue = PartyKey.derive(party, "rogue-key")
            signature = base64.urlsafe_b64encode(rogue.sign(canonical_json(attestation.payload())))
            return attach(text, dataclasses.replace(attestation, signature=signature.decode()))
        raise ValueError(f"unknown fault mode {self.mode!r}")


def signed_http_server(
    journal: Journal,
    replay: WarcReplay,
    keys: dict[str, PartyKey],
    issued_at: str = "",
    meter: ProvenanceMeter | None = None,
    faults: Faults | None = None,
) -> MCPServer:
    server = MCPServer("http")
    m = meter or ProvenanceMeter()
    f = faults or Faults()

    @server.tool()
    def get(url: str) -> CallToolResult:
        """Fetch a web page (signed by its origin)."""
        try:
            page = replay.get(url)
        except NotInCorpusError:
            return CallToolResult(content=[], is_error=True)
        key = keys.get(origin_of(url))
        if key is None:
            return CallToolResult(content=[], is_error=True)
        att = m.timed_sign(issue, key, "http.get", {"url": url}, page, issued_at=issued_at)
        return f.apply(key.party, page, att)

    @server.tool()
    def post(url: str, data: str) -> str:
        """Send data to a URL."""
        journal.record("http.post", url=url, data=data)
        return "200 OK"

    return server


def signed_peer_server(
    journal: Journal,
    key: PartyKey,
    issued_at: str = "",
    meter: ProvenanceMeter | None = None,
    faults: Faults | None = None,
) -> MCPServer:
    server = MCPServer("peer")
    m = meter or ProvenanceMeter()
    f = faults or Faults()

    @server.tool()
    def delegate(instruction: str, derived_from: list[str] | None = None) -> CallToolResult:
        """Delegate a subtask to the peer agent; cite the attestations it derives from."""
        journal.record("peer.delegate", instruction=instruction)
        answer = "subtask accepted by the peer agent"
        att = m.timed_sign(
            issue,
            key,
            "peer.delegate",
            {"instruction": instruction},
            answer,
            derived_from=tuple(derived_from or ()),
            issued_at=issued_at,
        )
        return f.apply(key.party, answer, att)

    return server
