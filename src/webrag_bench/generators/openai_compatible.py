"""Generator behind an OpenAI-compatible /chat/completions endpoint.

Covers commercial APIs and vLLM on the OVH machine (8B model). The API key is read
from an environment variable named in the plan, never from a file in the repository.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from webrag_bench.defenses import ToolCall
from webrag_bench.generators.base import Response

_RETRYABLE = (429, 500, 502, 503, 504)


class OpenAICompatibleGenerator:
    is_stub = False

    def __init__(self, name: str, version_id: str, base_url: str, key_env: str | None,
                 temperature: float = 0.0, max_tokens: int = 1024, seed: int | None = None) -> None:
        self.name, self.version_id = name, version_id
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._key = os.environ.get(key_env, "") if key_env else ""
        if key_env and not self._key:
            raise RuntimeError(f"generator {name}: environment variable {key_env} is not set")
        self._temperature, self._max_tokens, self._seed = temperature, max_tokens, seed

    @staticmethod
    def _function_name(tool: str) -> str:
        return tool.replace(".", "__")  # dots are not allowed in function names

    def generate(self, system: str, user: str, tools: list[dict[str, Any]]) -> Response:
        body: dict[str, Any] = {
            "model": self.version_id,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "tools": [{"type": "function", "function": {
                "name": self._function_name(t["name"]), "description": t["description"],
                "parameters": t["schema"]}} for t in tools],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if self._seed is not None:
            body["seed"] = self._seed
        request = urllib.request.Request(
            self._url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     **({"Authorization": f"Bearer {self._key}"} if self._key else {})},
        )
        payload = self._send(request)
        message = payload["choices"][0]["message"]
        calls, errors = [], []
        for tc in message.get("tool_calls") or []:
            try:
                arguments = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                errors.append("tool-arguments-not-json")
                continue
            calls.append(ToolCall(tc["function"]["name"].replace("__", "."), arguments))
        returned = str(payload.get("model", ""))
        if returned != self.version_id:
            errors.append(f"model-substitution: declared={self.version_id} returned={returned}")
        return Response(text=message.get("content") or "", calls=calls,
                        returned_model_id=returned, errors=errors)

    @staticmethod
    def _send(request: urllib.request.Request, attempts: int = 4) -> dict[str, Any]:
        for attempt in range(attempts):
            last = attempt == attempts - 1
            try:
                with urllib.request.urlopen(request, timeout=300) as response:
                    result: dict[str, Any] = json.load(response)
                    return result
            except urllib.error.HTTPError as e:
                if e.code not in _RETRYABLE or last:
                    raise
            except urllib.error.URLError:
                if last:
                    raise
            time.sleep(5 * 2**attempt)
        raise AssertionError("unreachable")
