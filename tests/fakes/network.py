"""Python network denial for collection and execution; CI also isolates subprocesses."""

import socket
from collections.abc import Callable
from typing import Any

import pytest


def install_network_guard(patch: pytest.MonkeyPatch) -> None:
    """Permit numeric loopback/Unix IPC only, including Windows asyncio socketpairs."""
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    sendto = socket.socket.sendto
    getaddrinfo = socket.getaddrinfo

    def allowed(address: object) -> bool:
        return isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}

    def check(connection: socket.socket, address: object) -> None:
        if connection.family == getattr(socket, "AF_UNIX", None) or allowed(address):
            return
        raise AssertionError("Ordinary tests cannot contact external or paid endpoints")

    def guarded_connect(connection: socket.socket, address: Any) -> None:
        check(connection, address)
        connect(connection, address)

    def guarded_connect_ex(connection: socket.socket, address: Any) -> int:
        check(connection, address)
        return connect_ex(connection, address)

    def guarded_sendto(connection: socket.socket, data: bytes, *args: Any) -> int:
        check(connection, args[-1])
        return sendto(connection, data, *args)

    def guarded_lookup(host: Any, *args: Any, **kwargs: Any) -> Any:
        if host not in {None, "localhost", "127.0.0.1", "::1"}:
            raise AssertionError("Ordinary tests cannot resolve external provider names")
        return getaddrinfo(host, *args, **kwargs)

    replacements: tuple[tuple[object, str, Callable[..., Any]], ...] = (
        (socket.socket, "connect", guarded_connect),
        (socket.socket, "connect_ex", guarded_connect_ex),
        (socket.socket, "sendto", guarded_sendto),
        (socket, "getaddrinfo", guarded_lookup),
    )
    for target, name, value in replacements:
        patch.setattr(target, name, value)
