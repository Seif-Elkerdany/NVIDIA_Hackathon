"""Isolated configuration and network denial for MS-003 checks."""

import socket

import pytest

from benefitbridge.config import Settings


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch):
    original_connect = socket.socket.connect

    def guarded_connect(connection, address):
        # Windows implements asyncio's socketpair through a loopback TCP pair.
        if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            return original_connect(connection, address)
        raise AssertionError("MS-003 checks must not call external providers")

    def blocked(*args, **kwargs):
        raise AssertionError("MS-003 checks must not call external providers")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", blocked)


@pytest.fixture
def production_settings():
    return Settings(
        _env_file=None,
        app_env="production",
        provider_mode="real",
        database_url="postgresql+psycopg://synthetic:synthetic@localhost/fixture",
        supabase_url="https://synthetic.example.invalid",
        jwt_issuer="https://synthetic.example.invalid/auth/v1",
        jwt_jwks_url="https://synthetic.example.invalid/auth/v1/.well-known/jwks.json",
        supabase_service_role_key="synthetic-storage-key",
        nebius_api_key="synthetic-inference-key",
        tavily_api_key="synthetic-search-key",
        deletion_hmac_key="synthetic-deletion-key-00000000000",
        receipt_encryption_key="synthetic-receipt-key-000000000000",
    )
