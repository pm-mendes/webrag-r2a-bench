"""In-memory filesystem server."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from webrag_bench.servers.journal import Journal


def filesystem_server(journal: Journal, files: dict[str, str] | None = None) -> MCPServer:
    server = MCPServer("filesystem")
    fs = dict(files or {})

    @server.tool()
    def read(path: str) -> str:
        """Read a file."""
        return fs.get(path, "")

    @server.tool()
    def write(path: str, content: str) -> str:
        """Write a file."""
        journal.record("filesystem.write", path=path, content=content)
        fs[path] = content
        return f"{path} written"

    @server.tool()
    def delete(path: str) -> str:
        """Delete a file."""
        journal.record("filesystem.delete", path=path)
        fs.pop(path, None)
        return f"{path} deleted"

    return server
