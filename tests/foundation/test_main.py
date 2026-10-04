from types import SimpleNamespace

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from benefitbridge import main
from benefitbridge.config import ConfigurationError, Settings


def test_development_app_exposes_no_public_endpoints():
    app = main.create_app(Settings())
    assert app.routes == []
    assert app.openapi()["paths"] == {}
    with TestClient(app) as client:
        assert client.get("/api/v1/health/live").status_code == 404
        assert client.get("/docs").status_code == 404


def test_production_requires_registry_even_with_all_secrets(production_values):
    with pytest.raises(ConfigurationError, match="MS-003 API registry"):
        main.create_app(Settings(**production_values))


def test_registry_is_called_once_and_mounts_its_router(monkeypatch):
    settings = Settings(app_env="test", provider_mode="fixture")
    router = APIRouter()

    @router.get("/synthetic", operation_id="syntheticFixture")
    def synthetic():
        return {"fixture": True}

    calls = []

    def register_routers(app, received_settings):
        calls.append((app, received_settings))
        app.include_router(router)

    def load_registry(name):
        assert name == "benefitbridge.api.registry"
        return SimpleNamespace(register_routers=register_routers)

    monkeypatch.setattr(main, "import_module", load_registry)
    app = main.create_app(settings)
    assert calls == [(app, settings)]
    with TestClient(app) as client:
        assert client.get("/synthetic").json() == {"fixture": True}


def test_registry_internal_missing_dependency_is_not_swallowed(monkeypatch):
    def broken_registry(name):
        raise ModuleNotFoundError("Missing registry dependency", name="required_dependency")

    monkeypatch.setattr(main, "import_module", broken_registry)
    with pytest.raises(ModuleNotFoundError, match="Missing registry dependency"):
        main.create_app(Settings())


def test_registry_startup_failure_propagates(monkeypatch):
    def register_routers(app, settings):
        raise ConfigurationError("Required P0 router or handler is missing")

    monkeypatch.setattr(
        main, "import_module", lambda name: SimpleNamespace(register_routers=register_routers)
    )
    with pytest.raises(ConfigurationError, match="Required P0"):
        main.create_app(Settings())


def test_registry_must_implement_explicit_interface(monkeypatch):
    monkeypatch.setattr(main, "import_module", lambda name: SimpleNamespace())
    with pytest.raises(ConfigurationError, match="register_routers"):
        main.create_app(Settings())
