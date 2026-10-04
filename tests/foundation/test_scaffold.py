import json
import re
import tomllib
from pathlib import Path

import yaml

from benefitbridge.config import Settings

ROOT = Path(__file__).resolve().parents[2]


def test_example_environment_is_loadable_and_has_no_credentials(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    settings = Settings(_env_file=ROOT / ".env.example")
    assert settings.provider_mode == "disabled"
    assert settings.database_url is None
    assert settings.postgres_password is None
    assert settings.nebius_api_key is None
    assert settings.supabase_service_role_key is None


def test_postgres_is_pinned_persistent_and_local_only():
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    postgres = compose["services"]["postgres"]
    assert re.fullmatch(r"postgres:17-bookworm@sha256:[0-9a-f]{64}", postgres["image"])
    assert postgres["ports"] == ["127.0.0.1:${POSTGRES_PORT:-5432}:5432"]
    assert "postgres-data:/var/lib/postgresql/data" in postgres["volumes"]
    assert "POSTGRES_PASSWORD:?" in postgres["environment"]["POSTGRES_PASSWORD"]
    assert postgres["healthcheck"]["test"][1].startswith("pg_isready ")


def test_python_lock_covers_exact_direct_dependencies():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked = {package["name"]: package["version"] for package in lock["package"]}
    dependencies = project["project"]["dependencies"] + project["dependency-groups"]["dev"]
    for dependency in dependencies:
        name, version = dependency.split("==")
        assert locked[name] == version
    assert project["project"]["requires-python"] == ">=3.12,<3.13"


def test_frontend_lock_and_strict_typescript_configuration():
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    lock = yaml.safe_load((ROOT / "frontend/pnpm-lock.yaml").read_text(encoding="utf-8"))
    for group in ("dependencies", "devDependencies"):
        for name, version in package[group].items():
            assert lock["importers"]["."][group][name]["specifier"] == version
    assert "--strict" in package["scripts"]["typecheck"]
    assert package["private"] is True
