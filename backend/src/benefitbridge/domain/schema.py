"""Deterministic, components-only OpenAPI and TypeScript generation for MS-002.

Run `python -m benefitbridge.domain.schema [--check]` from the repository root.
MS-003 can reuse build_openapi() when adding the allowlisted implemented routes.
"""

import argparse
import json
from pathlib import Path
from typing import cast

from pydantic import JsonValue, TypeAdapter
from pydantic.json_schema import models_json_schema

from . import dto, facts, requests, rules
from .base import DomainModel

CONTRACT_VERSION = "1.0.0"
RESPONSE_MODELS: tuple[type[DomainModel], ...] = (
    dto.Account,
    facts.Fact,
    dto.Profile,
    dto.Document,
    dto.Evidence,
    facts.FactCandidate,
    dto.RunReceipt,
    dto.Run,
    dto.Deadline,
    dto.Opportunity,
    dto.Source,
    rules.RequirementSet,
    dto.Evaluation,
    dto.ClarificationSet,
    dto.Saved,
    dto.ChecklistItem,
    dto.Application,
    dto.Draft,
    dto.Watch,
    dto.Notification,
    dto.Usage,
    dto.Capabilities,
    dto.UploadIntent,
    dto.DocumentDownload,
    dto.DeletionAccepted,
    dto.DeletionReceipt,
    dto.HealthLive,
    dto.HealthReady,
    dto.RunEvent,
    dto.DraftEditReceipt,
)
REQUEST_MODELS: tuple[type[DomainModel], ...] = (
    requests.EmptyCommand,
    requests.PatchMe,
    requests.PatchProfile,
    requests.CreateDocumentUpload,
    requests.CompleteDocumentUpload,
    requests.ReviewFactCandidates,
    requests.StartDiscovery,
    requests.ImportOpportunity,
    requests.AnswerClarifications,
    requests.StartEvaluation,
    requests.CreateApplication,
    requests.PatchChecklistItem,
    requests.StartDraft,
    requests.EditDraft,
    requests.AcceptDraft,
    requests.DeleteAccount,
    requests.ResetDemo,
    requests.CreateWatch,
    requests.PatchWatch,
)
PAGE_MODELS: tuple[type[DomainModel], ...] = (
    dto.Profile,
    dto.Document,
    facts.FactCandidate,
    dto.Run,
    dto.Opportunity,
    dto.Saved,
    dto.Application,
    dto.Watch,
    dto.Notification,
)


def _object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON schema object")
    return value


def build_openapi() -> dict[str, JsonValue]:
    """No paths are invented. Every component comes from a Pydantic model/union."""
    pages = [cast(type[DomainModel], dto.Page.__class_getitem__(model)) for model in PAGE_MODELS]
    envelopes = [
        cast(type[DomainModel], dto.Envelope.__class_getitem__(model))
        for model in (*RESPONSE_MODELS, *pages)
        if model is not dto.RunEvent
    ]
    models: tuple[type[DomainModel], ...] = (
        *RESPONSE_MODELS,
        *REQUEST_MODELS,
        dto.Problem,
        *pages,
        *envelopes,
    )
    _, combined = models_json_schema(
        [(model, "validation") for model in models], ref_template="#/components/schemas/{model}"
    )
    components = cast(dict[str, JsonValue], combined["$defs"])
    aliases: dict[str, TypeAdapter[object]] = {
        "FactValue": TypeAdapter(facts.FactValue),
        "RuleNode": TypeAdapter(rules.RuleNode),
        "ExpectedValue": TypeAdapter(rules.ExpectedValue),
        "CandidateDecision": TypeAdapter(requests.CandidateDecision),
    }
    for name, adapter in aliases.items():
        schema = adapter.json_schema(ref_template="#/components/schemas/{model}")
        for key, definition in schema.pop("$defs", {}).items():
            if key in components and components[key] != definition:
                raise ValueError(f"Conflicting shared component: {key}")
            components[key] = definition
        components[name] = schema
    return {
        "openapi": "3.1.0",
        "info": {"title": "BenefitBridge", "version": CONTRACT_VERSION},
        "paths": {},
        "components": {"schemas": components},
    }


def _ts_type(schema: dict[str, JsonValue]) -> str:
    """Render our emitted JSON Schema subset; unknown shapes fail generation.

    Numerical/string/cross-field constraints remain server validation. This is a
    mechanical projection, never a second source of domain fields or enums.
    """
    reference = schema.get("$ref")
    if isinstance(reference, str):
        prefix = "#/components/schemas/"
        if not reference.startswith(prefix):
            raise ValueError("Only local component references are supported")
        return f'components["schemas"][{json.dumps(reference.removeprefix(prefix))}]'
    if "const" in schema:
        return json.dumps(schema["const"], ensure_ascii=False)
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return " | ".join(json.dumps(value, ensure_ascii=False) for value in enum)
    for key, operator in (("oneOf", " | "), ("anyOf", " | "), ("allOf", " & ")):
        variants = schema.get(key)
        if isinstance(variants, list) and variants:
            return "(" + operator.join(_ts_type(_object(value)) for value in variants) + ")"
    kind = schema.get("type")
    if kind in ("string", "number", "boolean", "null"):
        return str(kind)
    if kind == "integer":
        return "number"
    if kind == "array":
        return "ReadonlyArray<" + _ts_type(_object(schema["items"])) + ">"
    if kind == "object":
        properties = _object(schema.get("properties", {}))
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise ValueError("Invalid required field list")
        fields = [
            f"readonly {json.dumps(name)}{'' if name in required else '?'}: "
            f"{_ts_type(_object(value))};"
            for name, value in sorted(properties.items())
        ]
        additional = schema.get("additionalProperties", False)
        if isinstance(additional, dict):
            if fields:
                raise ValueError("Mixed properties and index signatures require explicit support")
            return "Readonly<Record<string, " + _ts_type(additional) + ">>"
        if additional is not False:
            raise ValueError("Unbounded object schemas are not domain contracts")
        return "{ " + " ".join(fields) + " }" if fields else "Record<string, never>"
    raise ValueError("Unsupported JSON schema shape; update the generator explicitly")


def typescript_from_openapi(document: dict[str, JsonValue]) -> str:
    schemas = _object(_object(document["components"])["schemas"])
    lines = [
        "// Generated by python -m benefitbridge.domain.schema. Do not edit.",
        "// Runtime constraints are enforced by the Python models; this file contains wire types.",
        "export type paths = Record<string, never>;",
        "export interface components {",
        "  schemas: {",
    ]
    for name, schema in sorted(schemas.items()):
        lines.append(f"    {json.dumps(name)}: {_ts_type(_object(schema))};")
    lines.extend(["  };", "}", ""])
    return "\n".join(lines)


def generated_files() -> dict[str, str]:
    document = build_openapi()
    return {
        "openapi.json": json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "api.ts": typescript_from_openapi(document),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("frontend/src/generated"))
    parser.add_argument(
        "--check", action="store_true", help="Fail if generated artifacts have drifted"
    )
    args = parser.parse_args()
    generated = generated_files()
    if args.check:
        drifted = [
            name
            for name, content in generated.items()
            if not (args.output_dir / name).is_file()
            or (args.output_dir / name).read_text(encoding="utf-8") != content
        ]
        if drifted:
            parser.exit(1, "Generated contract drift: " + ", ".join(drifted) + "\n")
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in generated.items():
            (args.output_dir / name).write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
