"""The real-generator client, exercised against a local fake endpoint (loopback only)."""

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from webrag_bench.generators import OpenAICompatibleGenerator

TOOLS = [{"name": "mail.send", "description": "Send", "schema": {"type": "object"}}]


def _fake_endpoint(model_returned: str) -> tuple[HTTPServer, list[dict[str, Any]]]:
    seen: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            seen.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            body = json.dumps(
                {
                    "model": model_returned,
                    "choices": [
                        {
                            "message": {
                                "content": "ok",
                                "tool_calls": [
                                    {
                                        "function": {
                                            "name": "mail__send",
                                            "arguments": '{"to": "x"}',
                                        }
                                    },
                                    {"function": {"name": "mail__send", "arguments": "not json"}},
                                ],
                            }
                        }
                    ],
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: Any) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, seen


@pytest.fixture
def endpoint() -> Iterator[Any]:
    servers: list[HTTPServer] = []

    def make(model_returned: str) -> tuple[str, list[dict[str, Any]]]:
        server, seen = _fake_endpoint(model_returned)
        servers.append(server)
        return f"http://127.0.0.1:{server.server_port}/v1", seen

    yield make
    for s in servers:
        s.shutdown()


def test_calls_are_parsed_and_names_mapped_back(endpoint):
    url, seen = endpoint("model-2026-01")
    g = OpenAICompatibleGenerator("G1", "model-2026-01", url, None, seed=7)
    r = g.generate("sys", "user", TOOLS)
    assert [(c.tool, c.arguments) for c in r.calls] == [("mail.send", {"to": "x"})]
    assert r.errors == ["tool-arguments-not-json"]
    assert seen[0]["tools"][0]["function"]["name"] == "mail__send"
    assert seen[0]["seed"] == 7
    assert seen[0]["model"] == "model-2026-01"


def test_model_substitution_is_recorded(endpoint):
    url, _ = endpoint("model-2026-02")
    r = OpenAICompatibleGenerator("G1", "model-2026-01", url, None).generate("s", "u", TOOLS)
    assert "model-substitution: declared=model-2026-01 returned=model-2026-02" in r.errors


def test_missing_api_key_fails_early(monkeypatch):
    monkeypatch.delenv("WEBRAG_TEST_KEY", raising=False)
    with pytest.raises(RuntimeError, match="WEBRAG_TEST_KEY"):
        OpenAICompatibleGenerator("G1", "m", "http://127.0.0.1:1/v1", "WEBRAG_TEST_KEY")
