"""Regression checks for reproducible migration setup and safe configuration errors."""

import os
import subprocess
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[2]


def test_migration_chain_has_one_sources_head():
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert scripts.get_heads() == ["0002_sources"]
    assert scripts.get_revision("0001_identity").down_revision is None
    assert scripts.get_revision("0002_sources").down_revision == "0001_identity"


def test_missing_database_configuration_fails_without_connecting():
    environment = {**os.environ, "DATABASE_URL": "", "APP_ENV": "test"}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ROOT / "alembic.ini"), "upgrade", "head"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "DATABASE_URL is required to run migrations" in result.stderr


def test_invalid_database_configuration_does_not_echo_credentials():
    secret = "synthetic-secret-that-must-not-be-printed"
    environment = {**os.environ, "DATABASE_URL": f"invalid://{secret}", "APP_ENV": "test"}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ROOT / "alembic.ini"), "upgrade", "head"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Invalid migration configuration" in result.stderr
    assert secret not in result.stdout + result.stderr
