import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from benefitbridge.api import registry
from benefitbridge.composition import Dependencies, HandlerBinding
from benefitbridge.config import ConfigurationError, Settings
from benefitbridge.domain.dto import Envelope, HealthLive
from benefitbridge.domain.enums import RunKind
from benefitbridge.main import create_app
from benefitbridge.ports import JobScope

from .fakes import FakeStage

ROOT = Path(__file__).resolve().parents[2]


def health_router():
    router = APIRouter()

    @router.get(
        "/api/v1/health/live", operation_id="health_live", response_model=Envelope[HealthLive]
    )
    def live():
        return Envelope(data=HealthLive(status="ok"), request_id="synthetic")

    return router


def install_modules(monkeypatch, modules):
    calls = []

    def load(name):
        calls.append(name)
        if name not in modules:
            raise ModuleNotFoundError("Not implemented", name=name)
        return modules[name]

    monkeypatch.setattr(registry, "import_module", load)
    return calls


def test_allowlist_covers_exact_documented_operation_ids_once():
    text = (ROOT / "API.md").read_text(encoding="utf-8")
    table = text.split("## Endpoint index")[1].split("## Endpoint details")[0]
    expected = re.findall(r"^\| ([a-z_]+) \| (?:GET|POST|PUT|PATCH|DELETE) /api/v1/", table, re.M)
    actual = [operation for spec in registry.ROUTER_SPECS for operation in spec.operations]
    assert sorted(actual) == sorted(expected)
    assert len(actual) == len(set(actual))
    transports = re.findall(
        r"^\| ([a-z_]+) \| (GET|POST|PUT|PATCH|DELETE) (/api/v1/[^ ]+) \|", table, re.M
    )
    assert registry.OPERATION_CONTRACTS == {
        operation: (method, path) for operation, method, path in transports
    }
    assert len({spec.module for spec in registry.ROUTER_SPECS}) == len(registry.ROUTER_SPECS)
    writes = (ROOT / "sprints.md").read_text(encoding="utf-8")
    assert all(f"api/{spec.module}.py" in writes for spec in registry.ROUTER_SPECS)


def test_development_mounts_only_installed_allowlisted_routers(monkeypatch):
    router = health_router()
    calls = install_modules(
        monkeypatch, {"benefitbridge.api.health": SimpleNamespace(router=router)}
    )
    app = create_app(Settings(_env_file=None))
    assert app.separate_input_output_schemas is False
    expected = [
        f"benefitbridge.api.{spec.module}" for spec in registry.ROUTER_SPECS if spec.feature is None
    ]
    assert calls == expected
    assert list(app.openapi()["paths"]) == ["/api/v1/health/live"]
    with TestClient(app) as client:
        assert client.get("/api/v1/health/live").json()["data"] == {"status": "ok"}
    assert "benefitbridge.api.demo" not in calls
    assert "benefitbridge.api.watch" not in calls


def test_enabled_feature_routers_are_loaded_only_via_fixed_hooks(monkeypatch):
    calls = install_modules(monkeypatch, {})
    create_app(Settings(_env_file=None, demo_enabled=True, watch_enabled=True))
    assert calls[-2:] == ["benefitbridge.api.demo", "benefitbridge.api.watch"]


def test_missing_import_inside_installed_module_is_not_optional(monkeypatch):
    def load(name):
        raise ModuleNotFoundError("Broken adapter dependency", name="missing_sdk")

    monkeypatch.setattr(registry, "import_module", load)
    with pytest.raises(ModuleNotFoundError, match="Broken adapter"):
        create_app(Settings(_env_file=None))


def test_module_initialization_error_is_not_swallowed(monkeypatch):
    def load(name):
        raise RuntimeError("Synthetic initialization failure")

    monkeypatch.setattr(registry, "import_module", load)
    with pytest.raises(RuntimeError, match="initialization"):
        create_app(Settings(_env_file=None))


def test_missing_p0_router_prevents_production_startup(monkeypatch, production_settings):
    install_modules(monkeypatch, {})
    with pytest.raises(ConfigurationError, match="Missing required P0/feature routers"):
        create_app(production_settings)


def test_installed_but_incomplete_p0_router_prevents_production(monkeypatch, production_settings):
    install_modules(
        monkeypatch, {"benefitbridge.api.accounts": SimpleNamespace(router=APIRouter())}
    )
    with pytest.raises(ConfigurationError, match="Incomplete required P0/feature router: accounts"):
        create_app(production_settings)


def test_missing_handler_prevents_production_even_if_routers_are_present(production_settings):
    bindings = {
        kind.value: HandlerBinding(FakeStage()) for kind in RunKind if kind != RunKind.DEMO_RESET
    }
    del bindings[RunKind.EVALUATE.value]
    with pytest.raises(ConfigurationError, match="Missing required stage handlers: EVALUATE"):
        registry.validate_handlers((), Dependencies(handlers=bindings), production_settings)
    bindings[RunKind.EVALUATE.value] = HandlerBinding(FakeStage())
    registry.validate_handlers((), Dependencies(handlers=bindings), production_settings)


def test_complete_router_installation_still_fails_before_mounting_when_handler_missing(
    monkeypatch, production_settings
):
    modules = {}
    for spec in registry.ROUTER_SPECS:
        if spec.feature is not None:
            continue
        router = APIRouter()
        for operation in spec.operations:
            method, path = registry.OPERATION_CONTRACTS[operation]
            router.add_api_route(path, lambda: {}, methods=[method], operation_id=operation)
        modules[f"benefitbridge.api.{spec.module}"] = SimpleNamespace(router=router)
    install_modules(monkeypatch, modules)
    bindings = {
        kind.value: HandlerBinding(FakeStage()) for kind in RunKind if kind != RunKind.EVALUATE
    }
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.dependencies = Dependencies(provider_mode="real", handlers=bindings)
    with pytest.raises(ConfigurationError, match="Missing required stage handlers: EVALUATE"):
        registry.register_routers(app, production_settings)
    assert app.routes == []


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/v1/incorrect", "GET"),
        ("/api/v1/health/live", "POST"),
    ],
)
def test_operation_id_cannot_mask_a_wrong_transport(monkeypatch, path, method):
    router = APIRouter()
    router.add_api_route(path, lambda: {}, methods=[method], operation_id="health_live")
    install_modules(monkeypatch, {"benefitbridge.api.health": SimpleNamespace(router=router)})
    with pytest.raises(ConfigurationError, match="method/path differs"):
        create_app(Settings(_env_file=None))


def test_demo_requires_its_reset_handler_when_enabled(production_settings):
    bindings = {
        kind.value: HandlerBinding(FakeStage()) for kind in RunKind if kind != RunKind.DEMO_RESET
    }
    enabled = production_settings.model_copy(update={"demo_enabled": True})
    with pytest.raises(ConfigurationError, match="DEMO_RESET"):
        registry.validate_handlers((), Dependencies(handlers=bindings), enabled)


def test_referenced_intermediate_handler_cannot_be_missing(production_settings):
    item = registry.LoadedRouter(registry.ROUTER_SPECS[0], APIRouter(), ("VALIDATE_INPUTS",))
    bindings = {kind.value: HandlerBinding(FakeStage()) for kind in RunKind}
    with pytest.raises(ConfigurationError, match="VALIDATE_INPUTS"):
        registry.validate_handlers((item,), Dependencies(handlers=bindings), production_settings)


def test_private_entrypoint_cannot_bind_public_maintenance(production_settings):
    bindings = {kind.value: HandlerBinding(FakeStage()) for kind in RunKind}
    bindings[RunKind.EVALUATE.value] = HandlerBinding(FakeStage(), JobScope.PUBLIC)
    with pytest.raises(ConfigurationError, match="private stage bindings"):
        registry.validate_handlers((), Dependencies(handlers=bindings), production_settings)


@pytest.mark.parametrize("module", [SimpleNamespace(), SimpleNamespace(router=object())])
def test_invalid_router_export_fails_in_development(monkeypatch, module):
    install_modules(monkeypatch, {"benefitbridge.api.health": module})
    with pytest.raises(ConfigurationError, match="APIRouter"):
        create_app(Settings(_env_file=None))


def test_undeclared_operations_fail_in_development(monkeypatch):
    router = APIRouter()
    router.add_api_route("/api/v1/hidden", lambda: {}, operation_id="undeclared")
    install_modules(monkeypatch, {"benefitbridge.api.health": SimpleNamespace(router=router)})
    with pytest.raises(ConfigurationError, match="Undocumented"):
        create_app(Settings(_env_file=None))


def test_duplicate_operations_are_rejected(monkeypatch):
    router = health_router()
    router.add_api_route("/api/v1/health/duplicate", lambda: {}, operation_id="health_live")
    install_modules(monkeypatch, {"benefitbridge.api.health": SimpleNamespace(router=router)})
    with pytest.raises(ConfigurationError, match="Duplicate API operation"):
        create_app(Settings(_env_file=None))


def test_invalid_handler_declaration_is_not_silently_ignored(monkeypatch):
    module = SimpleNamespace(router=health_router(), required_handlers=["EVALUATE"])
    install_modules(monkeypatch, {"benefitbridge.api.health": module})
    with pytest.raises(ConfigurationError, match="required_handlers"):
        create_app(Settings(_env_file=None))


def test_registry_cannot_be_installed_twice(monkeypatch):
    install_modules(monkeypatch, {})
    app = create_app(Settings(_env_file=None))
    with pytest.raises(ConfigurationError, match="already been installed"):
        registry.register_routers(app, app.state.settings)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/watches",
        "/api/v1/watches/synthetic",
        "/api/v1/notifications",
        "/api/v1/notifications/synthetic/read",
    ],
)
def test_watch_gate_precedes_missing_router_and_returns_problem(monkeypatch, path):
    install_modules(monkeypatch, {})
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get(path, headers={"X-Request-ID": "synthetic-request"})
    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["X-Request-ID"] == "synthetic-request"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["code"] == "FEATURE_DISABLED"
    assert response.json()["request_id"] == "synthetic-request"


def test_watch_prefix_gate_does_not_match_unrelated_paths(monkeypatch):
    install_modules(monkeypatch, {})
    with TestClient(create_app(Settings(_env_file=None))) as client:
        assert client.get("/api/v1/watches-other").status_code == 404
    with TestClient(create_app(Settings(_env_file=None, watch_enabled=True))) as client:
        assert client.get("/api/v1/watches").status_code == 404


@pytest.mark.parametrize("request_id", ["bad request", "x" * 65])
def test_gate_replaces_invalid_request_id_without_echoing_it(monkeypatch, request_id):
    install_modules(monkeypatch, {})
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get("/api/v1/watches", headers={"X-Request-ID": request_id})
    assert response.headers["X-Request-ID"] != request_id
    assert len(response.headers["X-Request-ID"]) == 36
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
