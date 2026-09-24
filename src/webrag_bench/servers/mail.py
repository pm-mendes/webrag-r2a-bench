"""Mail server."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from webrag_bench.servers.journal import Journal


def mail_server(journal: Journal, inbox: list[dict[str, Any]] | None = None) -> MCPServer:
    server = MCPServer("mail")
    messages = list(inbox or [])

    @server.tool()
    def send(to: str, subject: str, body: str) -> str:
        """Send an email."""
        journal.record("mail.send", to=to, subject=subject, body=body)
        return f"email sent to {to}"

    @server.tool()
    def list_inbox() -> list[dict[str, Any]]:
        """List received emails."""
        return messages

    return server
