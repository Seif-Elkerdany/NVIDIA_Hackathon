import os

import pytest

from benefitbridge.config import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    """Do not load a developer's credentials into synthetic scaffold checks."""
    for name in os.environ:
        if name.lower() in Settings.model_fields:
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def production_values():
    return {
        "app_env": "production",
        "provider_mode": "real",
        "database_url": "postgresql+psycopg://synthetic:synthetic@localhost/fixture",
        "supabase_url": "https://synthetic.example.invalid",
        "jwt_issuer": "https://synthetic.example.invalid/auth/v1",
        "jwt_jwks_url": "https://synthetic.example.invalid/auth/v1/.well-known/jwks.json",
        "supabase_service_role_key": "synthetic-storage-key",
        "nebius_api_key": "synthetic-inference-key",
        "tavily_api_key": "synthetic-search-key",
        "deletion_hmac_key": "synthetic-deletion-key-00000000000",
        "receipt_encryption_key": "synthetic-receipt-key-000000000000",
    }
