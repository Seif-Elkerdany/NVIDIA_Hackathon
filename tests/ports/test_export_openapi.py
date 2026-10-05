import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, Query
from pydantic import JsonValue, create_model

from benefitbridge.domain.base import DomainModel
from benefitbridge.domain.dto import Envelope, HealthLive
from benefitbridge.domain.schema import REQUEST_MODELS, RESPONSE_MODELS, build_openapi

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("export_openapi", ROOT / "scripts/export_openapi.py")
assert spec is not None and spec.loader is not None
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)
build_document = exporter.build_document
generate_types = exporter.generate_types
generated_files = exporter.generated_files


def test_export_keeps_shared_catalog_and_all_merged_routes():
    first = generated_files()
    assert first == generated_files()
    assert build_document(FastAPI()) == build_openapi()
    document = json.loads(first["openapi.json"])
    assert set(document["paths"]) == {
        "/api/v1/me",
        "/api/v1/profile",
        "/api/v1/profile/versions",
        "/api/v1/profile/versions/{profile_version_id}",
    }
    shared = build_openapi()["components"]["schemas"]
    assert all(document["components"]["schemas"][name] == schema for name, schema in shared.items())
    for name, content in first.items():
        assert (ROOT / "frontend/src/generated" / name).read_text(encoding="utf-8") == content


def test_route_components_merge_only_when_identical():
    app = FastAPI()

    @app.get("/api/v1/health/live", operation_id="health_live", response_model=Envelope[HealthLive])
    def live():
        return Envelope(data=HealthLive(status="ok"), request_id="synthetic")

    document = build_document(app)
    shared = build_openapi()["components"]["schemas"]
    assert document["components"]["schemas"] == shared
    assert set(document["paths"]) == {"/api/v1/health/live"}
    types = generate_types(document)
    assert 'readonly get: operations["health_live"]' in types
    assert 'components["schemas"]["Envelope_HealthLive_"]' in types


def test_conflicting_shared_schema_cannot_overwrite_catalog():
    wrong_health = create_model("HealthLive", __base__=DomainModel, status=(int, ...))
    app = FastAPI()
    app.get("/synthetic", operation_id="synthetic", response_model=wrong_health)(lambda: None)
    with pytest.raises(ValueError, match="Conflicting shared component: HealthLive"):
        build_document(app)


def test_shared_component_default_values_cannot_be_changed():
    app = FastAPI()
    app.openapi()
    app.openapi_schema["components"] = {
        "schemas": {
            "HealthLive": {
                **build_openapi()["components"]["schemas"]["HealthLive"],
                "default": "changed",
            }
        }
    }
    with pytest.raises(ValueError, match="Conflicting shared component: HealthLive"):
        build_document(app)


def test_every_domain_model_can_be_exported_with_the_shared_schema_mode():
    app = FastAPI(separate_input_output_schemas=False)
    for model in (*REQUEST_MODELS, *RESPONSE_MODELS):
        app.get(f"/synthetic/{model.__name__}", operation_id=model.__name__, response_model=model)(
            lambda: None
        )
    document = build_document(app)
    shared = build_openapi()["components"]["schemas"]
    assert all(document["components"]["schemas"][name] == schema for name, schema in shared.items())
    assert generate_types(document)


def test_optional_query_parameters_remain_optional_in_types():
    document = build_openapi()
    document["paths"] = {
        "/synthetic": {
            "get": {
                "operationId": "synthetic",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {"204": {"description": "No content"}},
            }
        }
    }
    types = generate_types(document)
    assert 'readonly parameters?: { readonly query?: { readonly "limit"?: number; }' in types
    assert 'readonly "204": { readonly content: Record<string, never>; }' in types


def test_unknown_transport_fields_do_not_widen_known_domain_types():
    app = FastAPI()

    @app.post("/synthetic", operation_id="synthetic", response_model=HealthLive)
    def post(body: HealthLive):
        return body

    types = generate_types(build_document(app))
    assert 'readonly "input"?: unknown;' in types
    assert '"HealthLive": { readonly "status": "ok"; }' in types
    assert "any" not in types.split()


def test_missing_operation_id_cannot_create_implicit_client_contract():
    document = build_openapi()
    document["paths"] = {"/synthetic": {"get": {"responses": {"200": {"description": "fixture"}}}}}
    with pytest.raises(ValueError, match="explicit operationId"):
        generate_types(document)


def test_duplicate_operation_id_fails_generation():
    document = build_openapi()
    operation: dict[str, JsonValue] = {
        "operationId": "synthetic",
        "responses": {"200": {"description": "fixture"}},
    }
    document["paths"] = {"/one": {"get": operation}, "/two": {"get": operation}}
    with pytest.raises(ValueError, match="Duplicate operationId"):
        generate_types(document)


def test_unresolved_route_reference_fails_export():
    app = FastAPI()
    # Prime FastAPI's cache so its route-version invalidation preserves this fixture.
    app.openapi()
    app.openapi_schema = {
        "openapi": "3.1.0",
        "info": {"title": "fixture", "version": "1"},
        "paths": {
            "/synthetic": {
                "get": {
                    "operationId": "synthetic",
                    "responses": {
                        "200": {
                            "description": "fixture",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/DoesNotExist"},
                                }
                            },
                        }
                    },
                }
            }
        },
    }
    with pytest.raises(ValueError, match="Unresolved OpenAPI reference"):
        build_document(app)


def test_generated_route_types_compile_and_enforce_body_parameter_and_response(tmp_path):
    app = FastAPI()

    @app.post(
        "/synthetic/{resource_id}",
        operation_id="synthetic_write",
        response_model=Envelope[HealthLive],
    )
    def write(resource_id: str, body: HealthLive, limit: int = Query(1)):
        return Envelope(data=body, request_id="synthetic")

    types = generate_types(build_document(app))
    (tmp_path / "api.ts").write_text(types, encoding="utf-8")
    (tmp_path / "contract.ts").write_text(
        """
import type { paths, operations } from "./api";
type Write = paths["/synthetic/{resource_id}"]["post"];
const request: Write["requestBody"]["content"]["application/json"] = { status: "ok" };
const parameters: Write["parameters"] = { path: { resource_id: "fixture" }, query: { limit: 1 } };
type Response = operations["synthetic_write"]["responses"]["200"]["content"]["application/json"];
const response: Response = { data: request, request_id: "fixture" };
// @ts-expect-error Wire enum values remain closed.
const wrongBody: Write["requestBody"]["content"]["application/json"] = { status: "broken" };
// @ts-expect-error Required path parameters cannot disappear.
const missing: Write["parameters"] = {};
// @ts-expect-error Query integers cannot silently become strings.
const wrong: Write["parameters"] = { path: { resource_id: "fixture" }, query: { limit: "one" } };
// @ts-expect-error The implemented operation has no GET method.
type Invalid = paths["/synthetic/{resource_id}"]["get"];
void parameters; void response;
""",
        encoding="utf-8",
    )
    node = shutil.which("node")
    assert node is not None, "Node is required by the frozen frontend setup"
    result = subprocess.run(
        [
            node,
            str(ROOT / "frontend/node_modules/typescript/bin/tsc"),
            "--noEmit",
            "--strict",
            "--target",
            "ES2022",
            "--module",
            "ESNext",
            "--moduleResolution",
            "bundler",
            str(tmp_path / "contract.ts"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_export_command_detects_drift_without_overwriting(tmp_path):
    command = [
        sys.executable,
        str(ROOT / "scripts/export_openapi.py"),
        "--output-dir",
        str(tmp_path),
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=30, check=False, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr
    result = subprocess.run(
        [*command, "--check"], capture_output=True, text=True, timeout=30, check=False, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr
    output = tmp_path / "api.ts"
    output.write_text("// synthetic drift\n", encoding="utf-8")
    result = subprocess.run(
        [*command, "--check"], capture_output=True, text=True, timeout=30, check=False, cwd=ROOT
    )
    assert result.returncode == 1
    assert "api.ts" in result.stderr
    assert output.read_text(encoding="utf-8") == "// synthetic drift\n"
