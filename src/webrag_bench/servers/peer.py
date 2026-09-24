"""Peer agent.

For paper P: a delegation channel whose effect is journaled. For paper Y
(08-TWEB-PBD) it is to be extended into a signing peer (PROV-O / Verifiable
Credentials) — not done yet.
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from webrag_bench.servers.journal import Journal


def peer_server(journal: Journal) -> MCPServer:
    server = MCPServer("peer")

    @server.tool()
    def delegate(instruction: str) -> str:
        """Delegate a subtask to the peer agent."""
        journal.record("peer.delegate", instruction=instruction)
        return "subtask accepted by the peer agent"

    return server
