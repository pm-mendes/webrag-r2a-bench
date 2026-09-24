"""Network guard: no third-party site is ever contacted.

Installed at the start of every worker. Any outbound connection to a host outside
the allowlist raises instead of being attempted. The allowlist holds only the
loopback interface and the endpoints of the generators and embedder declared in the
plan (API providers, the OVH machine).
"""

from __future__ import annotations

import contextlib
import ipaddress
import socket
from typing import Any

_ORIGINAL_CONNECT = socket.socket.connect
_ORIGINAL_CREATE_CONNECTION = socket.create_connection
_allowed_hosts: set[str] = set()


class ForbiddenConnectionError(RuntimeError):
    """Raised when code tries to reach a host that is not allowlisted."""


def _is_loopback(host: str) -> bool:
    if host in {"localhost", ""}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _check(address: object) -> None:
    if isinstance(address, tuple) and address:
        host = str(address[0])
        if _is_loopback(host) or host in _allowed_hosts:
            return
        raise ForbiddenConnectionError(
            f"outbound connection to {host!r} refused: not allowlisted "
            "(no third-party site is contacted; only declared model endpoints are)"
        )
    # Unix sockets and other families are local by construction.


def install_guard(allowed_hosts: set[str]) -> None:
    """Enable the guard. Host names are resolved once so that IPs match too."""
    resolved = set(allowed_hosts)
    for host in allowed_hosts:
        with contextlib.suppress(OSError):
            resolved.update(str(info[4][0]) for info in socket.getaddrinfo(host, None))
    _allowed_hosts.clear()
    _allowed_hosts.update(resolved)

    def connect(self: socket.socket, address: Any) -> None:
        _check(address)
        _ORIGINAL_CONNECT(self, address)

    def create_connection(address: Any, *args: Any, **kwargs: Any) -> socket.socket:
        _check(address)
        return _ORIGINAL_CREATE_CONNECTION(address, *args, **kwargs)

    socket.socket.connect = connect  # type: ignore[method-assign,assignment]
    socket.create_connection = create_connection


def remove_guard() -> None:
    socket.socket.connect = _ORIGINAL_CONNECT  # type: ignore[method-assign]
    socket.create_connection = _ORIGINAL_CREATE_CONNECTION
    _allowed_hosts.clear()
