"""Sandbox MCP servers: mail, bank, filesystem, http, memory, peer.

Every episode gets fresh servers (empty state), exposed through the MCP SDK and
connected in memory. None has any effect outside the process: a "transfer" or a
"sent mail" is a line in the episode journal, which is the only source of the action
oracle.
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from webrag_bench.corpus import WarcReplay
from webrag_bench.servers.bank import bank_server
from webrag_bench.servers.filesystem import filesystem_server
from webrag_bench.servers.http import http_server
from webrag_bench.servers.journal import Journal
from webrag_bench.servers.mail import mail_server
from webrag_bench.servers.memory import memory_server
from webrag_bench.servers.peer import peer_server

EFFECTFUL_TOOLS = frozenset(
    {
        "mail.send",
        "bank.transfer",
        "filesystem.write",
        "filesystem.delete",
        "http.post",
        "memory.store",
        "peer.delegate",
    }
)
"""Tools whose call produces a real effect, and can therefore reach the action stage."""


def episode_servers(journal: Journal, replay: WarcReplay) -> dict[str, MCPServer]:
    return {
        "mail": mail_server(journal),
        "bank": bank_server(journal),
        "filesystem": filesystem_server(journal),
        "http": http_server(journal, replay),
        "memory": memory_server(journal),
        "peer": peer_server(journal),
    }


__all__ = ["EFFECTFUL_TOOLS", "Journal", "episode_servers"]
