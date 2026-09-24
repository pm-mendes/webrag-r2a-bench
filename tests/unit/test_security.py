import socket

import pytest

from webrag_bench.security import ForbiddenConnectionError, install_guard, remove_guard


def test_guard_refuses_third_party_host():
    install_guard(set())
    try:
        with pytest.raises(ForbiddenConnectionError):
            socket.create_connection(("93.184.216.34", 80), timeout=1)
    finally:
        remove_guard()


def test_guard_allows_loopback():
    install_guard(set())
    try:
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen()
        socket.create_connection(server.getsockname(), timeout=1).close()
        server.close()
    finally:
        remove_guard()
