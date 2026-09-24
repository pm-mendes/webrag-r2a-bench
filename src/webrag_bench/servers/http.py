"""HTTP server: GET is served by the WARC replay; POST is journaled, never sent."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from webrag_bench.corpus import NotInCorpusError, WarcReplay
from webrag_bench.servers.journal import Journal


def http_server(journal: Journal, replay: WarcReplay) -> MCPServer:
    server = MCPServer("http")

    @server.tool()
    def get(url: str) -> str:
        """Fetch a web page."""
        try:
            return replay.get(url)
        except NotInCorpusError:
            return "ERROR 404: page not available"

    @server.tool()
    def post(url: str, data: str) -> str:
        """Send data to a URL."""
        journal.record("http.post", url=url, data=data)
        return "200 OK"

    return server
