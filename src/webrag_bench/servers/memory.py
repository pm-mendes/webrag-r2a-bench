"""Persistent-memory server (a channel for stored injections)."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from webrag_bench.servers.journal import Journal


def memory_server(journal: Journal) -> MCPServer:
    server = MCPServer("memory")
    notes: dict[str, str] = {}

    @server.tool()
    def store(key: str, value: str) -> str:
        """Store a persistent note."""
        journal.record("memory.store", key=key, value=value)
        notes[key] = value
        return "stored"

    @server.tool()
    def recall(key: str) -> str:
        """Read a note back."""
        return notes.get(key, "")

    return server
