"""Bank server."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from webrag_bench.servers.journal import Journal


def bank_server(journal: Journal, balance: float = 1000.0) -> MCPServer:
    server = MCPServer("bank")
    state = {"balance": balance}

    @server.tool()
    def get_balance() -> float:
        """Current account balance."""
        return state["balance"]

    @server.tool()
    def transfer(iban: str, amount: float, label: str = "") -> str:
        """Make a bank transfer."""
        journal.record("bank.transfer", iban=iban, amount=amount, label=label)
        state["balance"] -= amount
        return f"transfer of {amount} to {iban} done"

    return server
