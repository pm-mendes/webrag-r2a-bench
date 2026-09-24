"""Signing variants of the sandbox servers (paper Y).

- `signed_http_server`: each web origin (URL host) signs the pages it serves. The
  attestation says "origin H served this exact content for this URL".
- `signed_peer_server`: the peer agent signs its answer to a delegation, and declares
  which earlier attestations the delegated instruction derives from.

Not yet wired into episodes: the Y protocol (adversarial behaviours, policies) is
still to be frozen.
"""

from __future__ import annotations

import urllib.parse

from mcp.server.mcpserver import MCPServer
from mcp_types import CallToolResult

from webrag_bench.corpus import NotInCorpusError, WarcReplay
from webrag_bench.provenance import KeyRegistry, PartyKey, attach, issue
from webrag_bench.servers.journal import Journal


def origin_of(url: str) -> str:
    return urllib.parse.urlparse(url).hostname or "unknown"


def party_keys(parties: list[str], seed: str) -> tuple[dict[str, PartyKey], KeyRegistry]:
    keys = {p: PartyKey.derive(p, seed) for p in sorted(set(parties))}
    registry = KeyRegistry()
    for p, k in keys.items():
        registry.register(p, k.public_bytes)
    return keys, registry


def signed_http_server(
    journal: Journal, replay: WarcReplay, keys: dict[str, PartyKey], issued_at: str = ""
) -> MCPServer:
    server = MCPServer("http")

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
        return attach(page, issue(key, "http.get", {"url": url}, page, issued_at=issued_at))

    @server.tool()
    def post(url: str, data: str) -> str:
        """Send data to a URL."""
        journal.record("http.post", url=url, data=data)
        return "200 OK"

    return server


def signed_peer_server(journal: Journal, key: PartyKey, issued_at: str = "") -> MCPServer:
    server = MCPServer("peer")

    @server.tool()
    def delegate(instruction: str, derived_from: list[str] | None = None) -> CallToolResult:
        """Delegate a subtask to the peer agent; cite the attestations it derives from."""
        journal.record("peer.delegate", instruction=instruction)
        answer = "subtask accepted by the peer agent"
        att = issue(
            key,
            "peer.delegate",
            {"instruction": instruction},
            answer,
            derived_from=tuple(derived_from or ()),
            issued_at=issued_at,
        )
        return attach(answer, att)

    return server
