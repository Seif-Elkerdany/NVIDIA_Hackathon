"""MS-010 offline plan and explicitly budgeted, nonprivate capability preflight.

Offline: uv run --frozen --offline python scripts/preflight_models.py --registry FILE
Real: add --real --max-cost-microusd N --output REPORT; NEBIUS_API_KEY stays in env.
The registry also accepts MODEL_REGISTRY_JSON. Each model entry requires role,
exact model_id/endpoint, context_tokens/max_output_tokens, json_schema/tools,
timeout_seconds, price_version, USD_PER_MILLION_TOKENS price_basis, decimal-string
input_price/output_price, metadata_source and UTC verified_at. FAST can be omitted
for single-REASON operation, and DEEP is optional. No production defaults exist.

Prices/context are operator-verified metadata, not inferred measurements. A tiny
schema probe and optional forced-tool probe record minimal response, actual usage
and price-based cost estimates. No tool is executed and no full response is saved.
Persist reports as trusted operator artifacts, not public inputs. MS-020/068/074
consume ModelRegistry.readiness with the shared Clock; probes never run on health
requests. A live integration gate remains NOT_RUN until --real succeeds.
"""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

import httpx2
from pydantic import JsonValue, SecretStr, ValidationError

from benefitbridge.composition import SystemClock
from benefitbridge.config import ConfigurationError
from benefitbridge.inference.registry import (
    MAX_REGISTRY_BYTES,
    ModelRegistry,
    ModelSpec,
    PreflightReport,
    ProbeError,
    ProbeEvidence,
)
from benefitbridge.ports import Clock, ModelRole

MAX_RESPONSE_BYTES = 65_536
INPUT_TOKEN_CAP = 1024
OUTPUT_TOKEN_CAP = 64
SCHEMA: dict[str, JsonValue] = {
    "type": "object",
    "properties": {"ok": {"type": "boolean", "enum": [True]}},
    "required": ["ok"],
    "additionalProperties": False,
}
ProbeKind = Literal["schema", "tools"]


class ProbeFailure(Exception):
    def __init__(
        self, code: Literal["HTTP_ERROR", "TIMEOUT", "INVALID_RESPONSE", "TOKEN_LIMIT_EXCEEDED"]
    ) -> None:
        self.code = code


def _object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ProbeFailure("INVALID_RESPONSE")
    return value


def _payload(model: ModelSpec, kind: ProbeKind) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {
        "model": model.model_id,
        "messages": [{"role": "user", "content": 'Return only {"ok":true}.'}],
        "max_tokens": min(OUTPUT_TOKEN_CAP, model.max_output_tokens),
        "stream": False,
    }
    if kind == "schema":
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "capability_probe",
                "strict": True,
                "schema": SCHEMA,
            },
        }
    else:
        payload["messages"] = [{"role": "user", "content": "Call capability_probe with ok=true."}]
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": "capability_probe",
                    "description": "A non-executed capability check.",
                    "parameters": SCHEMA,
                    "strict": True,
                },
            }
        ]
        payload["tool_choice"] = {"type": "function", "function": {"name": "capability_probe"}}
        payload["parallel_tool_calls"] = False
    return payload


def _validate_response(raw: bytes, model: ModelSpec, kind: ProbeKind) -> tuple[int, int]:
    try:
        document = _object(json.loads(raw))
        choices = document.get("choices")
        if (
            document.get("model") != model.model_id
            or not isinstance(choices, list)
            or len(choices) != 1
        ):
            raise ProbeFailure("INVALID_RESPONSE")
        choice = _object(choices[0])
        message = _object(choice.get("message"))
        if kind == "schema":
            if choice.get("finish_reason") != "stop" or message.get("tool_calls"):
                raise ProbeFailure("INVALID_RESPONSE")
            content = message.get("content")
        else:
            calls = message.get("tool_calls")
            if (
                choice.get("finish_reason") != "tool_calls"
                or not isinstance(calls, list)
                or len(calls) != 1
            ):
                raise ProbeFailure("INVALID_RESPONSE")
            tool = _object(calls[0])
            function = _object(tool.get("function"))
            if tool.get("type") != "function" or function.get("name") != "capability_probe":
                raise ProbeFailure("INVALID_RESPONSE")
            content = function.get("arguments")
        if not isinstance(content, str):
            raise ProbeFailure("INVALID_RESPONSE")
        minimal = _object(json.loads(content))
        if set(minimal) != {"ok"} or minimal["ok"] is not True:
            raise ProbeFailure("INVALID_RESPONSE")
        usage = _object(document.get("usage"))
        input_tokens, output_tokens = usage.get("prompt_tokens"), usage.get("completion_tokens")
        if (
            type(input_tokens) is not int
            or type(output_tokens) is not int
            or input_tokens < 0
            or output_tokens < 0
        ):
            raise ProbeFailure("INVALID_RESPONSE")
        if input_tokens > INPUT_TOKEN_CAP or output_tokens > min(
            OUTPUT_TOKEN_CAP, model.max_output_tokens
        ):
            raise ProbeFailure("TOKEN_LIMIT_EXCEEDED")
        return input_tokens, output_tokens
    except (ValueError, UnicodeError, RecursionError):
        raise ProbeFailure("INVALID_RESPONSE") from None


async def _request(
    client: httpx2.AsyncClient, model: ModelSpec, key: SecretStr, kind: ProbeKind
) -> tuple[int, int]:
    async def bounded() -> tuple[int, int]:
        async with client.stream(
            "POST",
            model.endpoint,
            headers={"Authorization": f"Bearer {key.get_secret_value()}"},
            json=_payload(model, kind),
            timeout=model.timeout_seconds,
            follow_redirects=False,
        ) as response:
            if response.status_code != 200:
                raise ProbeFailure("HTTP_ERROR")
            body = bytearray()
            async for chunk in response.aiter_bytes():
                if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise ProbeFailure("INVALID_RESPONSE")
                body.extend(chunk)
            return _validate_response(bytes(body), model, kind)

    try:
        return await asyncio.wait_for(bounded(), model.timeout_seconds)
    except (TimeoutError, httpx2.TimeoutException):
        raise ProbeFailure("TIMEOUT") from None
    except httpx2.HTTPError:
        raise ProbeFailure("HTTP_ERROR") from None


def reservation_microusd(registry: ModelRegistry) -> int:
    return sum(
        model.cost_microusd(INPUT_TOKEN_CAP, min(OUTPUT_TOKEN_CAP, model.max_output_tokens))
        * (2 if model.tools else 1)
        for model in registry.config.models
    )


async def preflight(
    registry: ModelRegistry,
    clock: Clock,
    client: httpx2.AsyncClient,
    key: SecretStr,
    max_cost_microusd: int,
) -> PreflightReport:
    """The CLI owns real-call opt-in. Client/clock injection is for isolated tests."""
    if (
        type(max_cost_microusd) is not int
        or max_cost_microusd <= 0
        or not key.get_secret_value().strip()
        or registry.configured(ModelRole.REASON) is None
    ):
        raise ConfigurationError(
            "Real preflight requires REASON, credentials and a positive budget"
        )
    if reservation_microusd(registry) > max_cost_microusd:
        raise ConfigurationError("Preflight token reservation exceeds the explicit budget")
    results: list[ProbeEvidence] = []
    for model in registry.config.models:
        calls = inputs = outputs = 0
        schema_passed = tools_passed = False
        error: ProbeError | None = None
        started = clock.monotonic()
        if not model.json_schema or model.context_tokens < INPUT_TOKEN_CAP + min(
            OUTPUT_TOKEN_CAP, model.max_output_tokens
        ):
            error = "UNSUPPORTED"
        elif model.verified_at > clock.now():
            error = "INVALID_RESPONSE"
        else:
            for kind in ("schema", "tools") if model.tools else ("schema",):
                calls += 1
                try:
                    measured_input, measured_output = await _request(client, model, key, kind)
                except ProbeFailure as failure:
                    error = failure.code
                    break
                inputs += measured_input
                outputs += measured_output
                schema_passed |= kind == "schema"
                tools_passed |= kind == "tools"
        results.append(
            ProbeEvidence(
                role=model.role,
                status="PASSED" if error is None else "FAILED",
                checked_at=clock.now(),
                schema_passed=schema_passed,
                tools_passed=tools_passed,
                calls=calls,
                input_tokens=inputs if error is None else None,
                output_tokens=outputs if error is None else None,
                estimated_cost_microusd=model.cost_microusd(inputs, outputs)
                if error is None
                else None,
                elapsed_ms=max(0, round((clock.monotonic() - started) * 1000)),
                minimal_response='{"ok":true}' if schema_passed else None,
                error_code=error,
            )
        )
    return PreflightReport(
        configuration=registry.config,
        registry_version=registry.config.version,
        registry_fingerprint=registry.fingerprint,
        mode="real",
        results=tuple(results),
    )


def main(argv: list[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--registry", type=Path, help="Versioned operator JSON registry")
    parser.add_argument(
        "--real", action="store_true", help="Explicitly authorize bounded paid capability calls"
    )
    parser.add_argument("--max-cost-microusd", type=int)
    parser.add_argument(
        "--output", type=Path, help="Write the minimal real preflight evidence JSON"
    )
    parser.add_argument("--report", type=Path, help="Evaluate existing evidence offline")
    args = parser.parse_args(argv)
    env = os.environ if environment is None else environment
    try:
        if args.real and (env.get("CI") or env.get("GITHUB_ACTIONS") or args.report):
            raise ConfigurationError(
                "Real preflight is prohibited in ordinary CI or report-only mode"
            )
        if args.registry:
            if args.registry.stat().st_size > MAX_REGISTRY_BYTES:
                raise ConfigurationError("Model registry is oversized")
            registry = ModelRegistry.from_json(args.registry.read_text("utf-8"))
        else:
            registry = ModelRegistry.from_environment(env)
        clock = SystemClock()
        report = None
        if args.real:
            if args.max_cost_microusd is None or not args.output:
                raise ConfigurationError("Real preflight requires --max-cost-microusd and --output")
            if args.registry and args.output.resolve() == args.registry.resolve():
                raise ConfigurationError("Preflight output cannot overwrite its registry")
            key = SecretStr(env.get("NEBIUS_API_KEY", ""))

            async def run() -> PreflightReport:
                async with httpx2.AsyncClient(trust_env=False, follow_redirects=False) as client:
                    return await preflight(registry, clock, client, key, args.max_cost_microusd)

            report = asyncio.run(run())
            args.output.write_text(report.model_dump_json(indent=2) + "\n", "utf-8")
        elif args.report:
            if args.report.stat().st_size > MAX_REGISTRY_BYTES:
                raise ConfigurationError("Preflight evidence is oversized")
            report = PreflightReport.model_validate_json(args.report.read_text("utf-8"))
        elif args.max_cost_microusd is not None or args.output:
            raise ConfigurationError("Budget/output options require explicit --real")
        readiness = registry.readiness(clock, report)
        live_gate = "NOT_RUN"
        if report is not None and report.mode == "real":
            live_gate = (
                "PASSED"
                if readiness.inference_available
                and all(item.status == "PASSED" for item in report.results)
                else "FAILED"
            )
        print(
            json.dumps(
                {
                    "registry_version": registry.config.version,
                    "mode": "real" if args.real else "offline",
                    "readiness": readiness.model_dump(mode="json"),
                    "configured_roles": [model.role.value for model in registry.config.models],
                    "reserved_cost_microusd": reservation_microusd(registry),
                    "live_gate": live_gate,
                },
                sort_keys=True,
            )
        )
        return 0 if live_gate == "PASSED" else 1
    except (ConfigurationError, ValidationError, OSError, UnicodeError):
        print(
            "Model preflight configuration or evidence is invalid; no secret values are displayed.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
