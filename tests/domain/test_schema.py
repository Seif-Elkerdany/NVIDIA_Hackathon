import json
import subprocess
import sys

import pytest
from fastapi.openapi.models import OpenAPI

from benefitbridge.domain.schema import build_openapi, typescript_from_openapi

from .conftest import ROOT


def test_components_only_document_has_resolved_references():
    document = build_openapi()
    OpenAPI.model_validate(document)
    assert document["openapi"] == "3.1.0"
    assert document["paths"] == {}
    schemas = document["components"]["schemas"]
    assert {
        "FactValue",
        "RuleNode",
        "RequirementSet",
        "Problem",
        "PatchProfile",
        "Evaluation",
    } <= schemas.keys()

    def walk(value):
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str) and value.startswith("#/components/schemas/"):
            assert value.removeprefix("#/components/schemas/") in schemas

    walk(document)


def test_all_business_objects_reject_unknown_properties():
    for schema in build_openapi()["components"]["schemas"].values():
        if schema.get("type") == "object":
            assert schema["additionalProperties"] is False


def test_decimal_union_and_required_nullable_schema():
    schemas = build_openapi()["components"]["schemas"]
    assert schemas["GpaValue"]["properties"]["number"]["type"] == "string"
    assert schemas["FactValue"]["discriminator"]["propertyName"] == "type"
    assert "profile_version_id" in schemas["Run"]["required"]
    assert {"type": "null"} in schemas["Run"]["properties"]["profile_version_id"]["anyOf"]
    assert "reference_date" not in schemas["PredicateNode"]["required"]


def test_generation_is_deterministic_and_checked_in_outputs_match():
    from scripts.export_openapi import generated_files as merged_generated_files

    first = merged_generated_files()
    assert first == merged_generated_files()
    for name, content in first.items():
        assert (ROOT / "frontend/src/generated" / name).read_text(encoding="utf-8") == content
    assert "any" not in first["api.ts"].split()


def test_generation_cli_detects_drift_without_overwriting_it(tmp_path):
    command = [sys.executable, "-m", "benefitbridge.domain.schema", "--output-dir", str(tmp_path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    output = tmp_path / "api.ts"
    output.write_text("// deliberate synthetic drift\n", encoding="utf-8")
    result = subprocess.run(
        [*command, "--check"], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 1
    assert "api.ts" in result.stderr
    assert output.read_text(encoding="utf-8") == "// deliberate synthetic drift\n"


def test_type_generation_fails_for_unsupported_schema_shapes():
    with pytest.raises(ValueError, match="Unsupported"):
        typescript_from_openapi({"components": {"schemas": {"Unknown": {}}}})


def test_schema_changes_drive_types_without_a_parallel_field_catalog():
    document = json.loads(json.dumps(build_openapi()))
    document["components"]["schemas"]["HealthLive"]["properties"]["synthetic"] = {"type": "boolean"}
    generated = typescript_from_openapi(document)
    assert 'readonly "synthetic"?: boolean' in generated
