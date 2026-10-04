"""Export installed routes plus the shared Pydantic catalog, deterministically.

Run with `uv run --frozen --offline python scripts/export_openapi.py [--check]`.
No .env file, production readiness probe or provider call is needed for generation.
"""

import argparse
import json
from pathlib import Path
from typing import cast

from fastapi import FastAPI
from fastapi.openapi.models import OpenAPI
from pydantic import JsonValue, TypeAdapter

from benefitbridge.config import Settings
from benefitbridge.domain.schema import _ts_type, build_openapi, typescript_from_openapi
from benefitbridge.main import create_app

ROOT = Path(__file__).resolve().parents[1]
HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


def _object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError("Expected an OpenAPI object")
    return value


def _check_references(value: JsonValue, document: dict[str, JsonValue]) -> None:
    if isinstance(value, dict):
        reference = value.get("$ref")
        if reference is not None:
            if not isinstance(reference, str) or not reference.startswith("#/components/"):
                raise ValueError("Only local component references are supported")
            target: JsonValue = document
            for segment in reference[2:].split("/"):
                key = segment.replace("~1", "/").replace("~0", "~")
                mapping = _object(target)
                if key not in mapping:
                    raise ValueError(f"Unresolved OpenAPI reference: {reference}")
                target = mapping[key]
        for child in value.values():
            _check_references(child, document)
    elif isinstance(value, list):
        for child in value:
            _check_references(child, document)


def _wire_schema(value: JsonValue) -> JsonValue:
    """Normalize only omitted null-default annotations from Pydantic serialization.

    `default` is metadata, not requiredness. exclude_if=None can remove this
    annotation even when FastAPI uses a single schema mode. All constraints,
    required fields and non-null defaults must still match the shared catalog.
    """
    if isinstance(value, dict):
        return {
            key: _wire_schema(child)
            for key, child in value.items()
            if key != "default" or child is not None
        }
    if isinstance(value, list):
        return [_wire_schema(child) for child in value]
    return value


def build_document(app: FastAPI | None = None) -> dict[str, JsonValue]:
    """Shared component collisions must be identical; no override wins silently."""
    if app is None:
        # Export every merged optional feature, independently of an operator's .env.
        app = create_app(
            Settings(
                _env_file=None,
                app_env="development",
                provider_mode="disabled",
                demo_enabled=True,
                watch_enabled=True,
            )
        )
    shared = build_openapi()
    routes = TypeAdapter(dict[str, JsonValue]).validate_python(app.openapi())
    document = dict(shared)
    components = dict(_object(shared["components"]))
    schemas = dict(_object(components["schemas"]))
    for section, content in _object(routes.get("components", {})).items():
        if section == "schemas":
            for name, definition in _object(content).items():
                if name in schemas:
                    if _wire_schema(schemas[name]) != _wire_schema(definition):
                        raise ValueError(f"Conflicting shared component: {name}")
                    # Always retain the canonical Pydantic catalog definition.
                else:
                    schemas[name] = definition
        else:
            components[section] = content
    components["schemas"] = schemas
    document["components"] = components
    document["paths"] = routes.get("paths", {})
    for key in ("tags", "security", "servers", "webhooks"):
        if key in routes:
            document[key] = routes[key]
    _check_references(document, document)
    OpenAPI.model_validate(document)
    return document


def _resolve(value: JsonValue, document: dict[str, JsonValue]) -> dict[str, JsonValue]:
    mapping = _object(value)
    visited: set[str] = set()
    while "$ref" in mapping:
        reference = mapping["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/components/"):
            raise ValueError("Unsupported OpenAPI object reference")
        if reference in visited:
            raise ValueError("Cyclic OpenAPI object reference")
        visited.add(reference)
        target: JsonValue = document
        for segment in reference[2:].split("/"):
            target = _object(target)[segment.replace("~1", "/").replace("~0", "~")]
        mapping = _object(target)
    return mapping


def _route_type(schema: dict[str, JsonValue]) -> str:
    """Extend the strict domain renderer for untyped framework transport metadata."""
    try:
        return _ts_type(schema)
    except ValueError:
        if not schema or set(schema) <= {"title", "description", "default", "examples"}:
            return "unknown"
        for union in ("anyOf", "oneOf"):
            if union in schema:
                variants = schema[union]
                if not isinstance(variants, list):
                    raise ValueError("Invalid route union") from None
                return "(" + " | ".join(_route_type(_object(item)) for item in variants) + ")"
        if schema.get("type") == "array":
            return "ReadonlyArray<" + _route_type(_object(schema.get("items", {}))) + ">"
        if schema.get("type") == "object":
            properties = _object(schema.get("properties", {}))
            required = schema.get("required", [])
            if not isinstance(required, list):
                raise ValueError("Invalid required route fields") from None
            fields = [
                f"readonly {json.dumps(name)}{'' if name in required else '?'}: "
                f"{_route_type(_object(value))};"
                for name, value in sorted(properties.items())
            ]
            additional = schema.get("additionalProperties", True)
            if additional is not False:
                if fields and isinstance(additional, dict):
                    raise ValueError(
                        "Mixed route properties and typed index signatures are unsupported"
                    ) from None
                value_type = _route_type(additional) if isinstance(additional, dict) else "unknown"
                fields.append(f"readonly [key: string]: {value_type};")
            return "{ " + " ".join(fields) + " }" if fields else "Record<string, never>"
        # Unsupported semantic shapes still fail; there is no blanket unknown fallback.
        raise


def _content(value: JsonValue) -> str:
    fields = []
    for media_type, item in sorted(_object(value).items()):
        schema = _object(item).get("schema", {})
        # An unspecified transport body (e.g. an SSE stream) is unknown, not any.
        rendered = _route_type(_object(schema))
        fields.append(f"readonly {json.dumps(media_type)}: {rendered};")
    return "{ " + " ".join(fields) + " }" if fields else "Record<string, never>"


def _operation(
    operation: dict[str, JsonValue],
    path_parameters: list[JsonValue],
    document: dict[str, JsonValue],
) -> str:
    own_parameters = operation.get("parameters", [])
    if not isinstance(own_parameters, list):
        raise ValueError("Operation parameters must be an array")
    # OpenAPI operation parameters override path-item parameters by (in, name).
    parameters: dict[tuple[str, str], dict[str, JsonValue]] = {}
    for item in (*path_parameters, *own_parameters):
        parameter = _resolve(item, document)
        location, name = parameter.get("in"), parameter.get("name")
        if not isinstance(location, str) or not isinstance(name, str):
            raise ValueError("Invalid OpenAPI parameter")
        if location not in {"path", "query", "header", "cookie"}:
            raise ValueError("Unsupported OpenAPI parameter location")
        parameters[location, name] = parameter
    fields: list[str] = []
    locations: list[str] = []
    for location in ("path", "query", "header", "cookie"):
        group = [
            (name, parameter)
            for (kind, name), parameter in sorted(parameters.items())
            if kind == location
        ]
        if not group:
            continue
        entries = []
        for name, parameter in group:
            if "schema" not in parameter:
                raise ValueError("Content-based OpenAPI parameters require explicit support")
            optional = "" if parameter.get("required", False) else "?"
            value_type = _route_type(_object(parameter["schema"]))
            entries.append(f"readonly {json.dumps(name)}{optional}: {value_type};")
        optional_group = (
            "" if any(parameter.get("required", False) for _, parameter in group) else "?"
        )
        locations.append(f"readonly {location}{optional_group}: {{ {' '.join(entries)} }};")
    if locations:
        optional = "" if any(item.get("required", False) for item in parameters.values()) else "?"
        fields.append(f"readonly parameters{optional}: {{ " + " ".join(locations) + " };")
    if "requestBody" in operation:
        body = _resolve(operation["requestBody"], document)
        optional = "" if body.get("required", False) else "?"
        content = _content(body.get("content", {}))
        fields.append(f"readonly requestBody{optional}: {{ readonly content: {content}; }};")
    responses = []
    for status, value in sorted(_object(operation.get("responses", {})).items()):
        response = _resolve(value, document)
        content = _content(response.get("content", {}))
        responses.append(f"readonly {json.dumps(status)}: {{ readonly content: {content}; }};")
    fields.append("readonly responses: { " + " ".join(responses) + " };")
    return "{ " + " ".join(fields) + " }"


def generate_types(document: dict[str, JsonValue]) -> str:
    """Reuse MS-002's schema renderer; add paths/operations from implemented routes."""
    schemas = _object(_object(document["components"])["schemas"])
    strict: dict[str, JsonValue] = {}
    extended: list[str] = []
    for name, value in sorted(schemas.items()):
        try:
            _ts_type(_object(value))
        except ValueError:
            extended.append(f"    {json.dumps(name)}: {_route_type(_object(value))};")
        else:
            strict[name] = value
    base = typescript_from_openapi({"components": {"schemas": strict}})
    if extended:
        base = base.removesuffix("  };\n}\n") + "\n".join(extended) + "\n  };\n}\n"
    paths: list[str] = []
    operations: dict[str, str] = {}
    for path, value in sorted(_object(document["paths"]).items()):
        item = _object(value)
        path_parameters = item.get("parameters", [])
        if not isinstance(path_parameters, list):
            raise ValueError("Path parameters must be an array")
        methods = []
        for method in HTTP_METHODS:
            if method not in item:
                continue
            operation = _object(item[method])
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                raise ValueError("Every implemented operation requires an explicit operationId")
            if operation_id in operations:
                raise ValueError(f"Duplicate operationId: {operation_id}")
            operations[operation_id] = _operation(operation, path_parameters, document)
            methods.append(f"readonly {method}: operations[{json.dumps(operation_id)}];")
        paths.append(f"  readonly {json.dumps(path)}: {{ {' '.join(methods)} }};")
    if not paths:
        return base
    path_type = "export interface paths {\n" + "\n".join(paths) + "\n}"
    base = base.replace("export type paths = Record<string, never>;", path_type)
    base = base.replace(
        "// Generated by python -m benefitbridge.domain.schema. Do not edit.",
        "// Generated by python scripts/export_openapi.py. Do not edit.",
    )
    lines = ["export interface operations {"]
    lines.extend(
        f"  readonly {json.dumps(name)}: {content};" for name, content in sorted(operations.items())
    )
    lines.extend(["}", ""])
    return base + "\n" + "\n".join(lines)


def generated_files(app: FastAPI | None = None) -> dict[str, str]:
    document = build_document(app)
    return {
        "openapi.json": json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "api.ts": generate_types(document),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "frontend/src/generated")
    parser.add_argument(
        "--check", action="store_true", help="Detect drift without changing any files"
    )
    args = parser.parse_args()
    output = cast(Path, args.output_dir)
    generated = generated_files()
    if args.check:
        drifted = [
            name
            for name, content in generated.items()
            if not (output / name).is_file()
            or (output / name).read_text(encoding="utf-8") != content
        ]
        if drifted:
            parser.exit(1, "Generated contract drift: " + ", ".join(drifted) + "\n")
    else:
        output.mkdir(parents=True, exist_ok=True)
        for name, content in generated.items():
            (output / name).write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
