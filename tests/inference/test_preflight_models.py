import asyncio
import json
from pathlib import Path

import httpx2
import pytest
from pydantic import SecretStr
from scripts import preflight_models as cli
from scripts.preflight_models import INPUT_TOKEN_CAP, main, preflight, reservation_microusd
from tests.fakes.providers import FakeClock
from tests.inference.test_registry import model, registry, report

from benefitbridge.config import ConfigurationError
from benefitbridge.ports import ModelRole


def response(model_id: str, tools: bool = False) -> dict[str, object]:
    message: dict[str, object] = {"role": "assistant", "content": '{"ok":true}'}
    if tools:
        message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "synthetic-call",
                    "type": "function",
                    "function": {"name": "capability_probe", "arguments": '{"ok":true}'},
                }
            ],
        }
    return {
        "model": model_id,
        "choices": [{"message": message, "finish_reason": "tool_calls" if tools else "stop"}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 8},
    }


def test_real_wire_probes_are_bounded_tiny_nonprivate_and_record_verified_metadata() -> None:
    current = registry(model(tools=True), model(ModelRole.DEEP))
    calls: list[httpx2.Request] = []
    clock = FakeClock()

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(request)
        body = json.loads(request.content)
        assert body["stream"] is False and body["max_tokens"] == 64
        assert "profile" not in request.content.decode()
        assert request.headers["Authorization"] == "Bearer synthetic-key"
        clock.advance(0.125)
        return httpx2.Response(200, json=response(body["model"], "tools" in body))

    async def run() -> None:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
            evidence = await preflight(current, clock, client, SecretStr("synthetic-key"), 100)
        assert len(calls) == 3
        assert current.readiness(clock, evidence).inference_available
        assert current.readiness(clock, evidence).deep_available
        assert evidence.configuration == current.config
        assert evidence.results[0].elapsed_ms == 250
        assert evidence.results[0].input_tokens == 40
        assert evidence.results[0].tools_passed
        assert evidence.results[0].billed_microusd is None
        assert "synthetic-key" not in evidence.model_dump_json()
        assert evidence.results[0].minimal_response == '{"ok":true}'

    asyncio.run(run())


@pytest.mark.parametrize(
    "case",
    [
        "redirect",
        "timeout",
        "html",
        "oversize",
        "wrong_model",
        "bad_schema",
        "truncated",
        "missing_usage",
        "token_overrun",
        "wrong_tool",
    ],
)
def test_failed_probes_are_safe_and_never_make_reason_ready(case: str) -> None:
    current = registry(model(tools=case == "wrong_tool"))

    def handler(request: httpx2.Request) -> httpx2.Response:
        if case == "redirect":
            return httpx2.Response(302, headers={"Location": "https://secret.invalid"})
        if case == "timeout":
            raise httpx2.ReadTimeout("secret-provider-body", request=request)
        if case == "html":
            return httpx2.Response(200, text="<html>secret-body</html>")
        if case == "oversize":
            return httpx2.Response(200, content=b"x" * 65_537)
        data = response(model().model_id, "tools" in json.loads(request.content))
        if case == "wrong_model":
            data["model"] = "foreign"
        if case == "bad_schema":
            data["choices"][0]["message"]["content"] = '{"ok":true,"extra":"secret"}'
        if case == "truncated":
            data["choices"][0]["finish_reason"] = "length"
        if case == "missing_usage":
            del data["usage"]
        if case == "token_overrun":
            data["usage"]["prompt_tokens"] = INPUT_TOKEN_CAP + 1
        if case == "wrong_tool" and "tools" in json.loads(request.content):
            data["choices"][0]["message"]["tool_calls"][0]["function"]["name"] = "untrusted_action"
        return httpx2.Response(200, json=data)

    async def run() -> None:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
            evidence = await preflight(
                current, FakeClock(), client, SecretStr("synthetic-key"), 100
            )
        assert evidence.results[0].status == "FAILED"
        assert not current.readiness(FakeClock(), evidence).inference_available
        assert evidence.results[0].input_tokens is None
        assert evidence.results[0].billed_microusd is None
        assert "secret" not in evidence.model_dump_json()

    asyncio.run(run())


def test_reservation_and_missing_reason_fail_before_any_provider_call() -> None:
    def forbidden(request: httpx2.Request) -> httpx2.Response:
        raise AssertionError("No provider request was authorized")

    async def run() -> None:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(forbidden)) as client:
            expensive = registry(model(input_price="100"))
            assert reservation_microusd(expensive) > 1
            for current, key, budget in [
                (expensive, "key", 1),
                (registry(), "key", 100),
                (registry(model()), "", 100),
                (registry(model()), "key", 0),
            ]:
                with pytest.raises(ConfigurationError):
                    await preflight(current, FakeClock(), client, SecretStr(key), budget)

    asyncio.run(run())


def test_unsupported_schema_is_not_probed_or_misrepresented_as_ready() -> None:
    async def run() -> None:
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(lambda _: pytest.fail("Unexpected call"))
        ) as client:
            evidence = await preflight(
                registry(model(json_schema=False)), FakeClock(), client, SecretStr("key"), 100
            )
        assert evidence.results[0].error_code == "UNSUPPORTED"
        assert evidence.results[0].calls == 0

    asyncio.run(run())


def test_offline_cli_does_not_probe_and_missing_reason_is_visible(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "registry.json"
    path.write_text(registry(model()).config.model_dump_json(), "utf-8")
    assert main(["--registry", str(path)], {}) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["readiness"]["reason"] == "PREFLIGHT_REQUIRED"
    assert output["live_gate"] == "NOT_RUN" and output["mode"] == "offline"
    assert main([], {}) == 1
    assert json.loads(capsys.readouterr().out)["readiness"]["reason"] == "MISSING_REASON"


@pytest.mark.parametrize(
    "options,env",
    [
        (["--real"], {}),
        (["--max-cost-microusd", "1"], {}),
        (["--real", "--max-cost-microusd", "1", "--output", "report.json"], {"CI": "true"}),
        (
            ["--real", "--max-cost-microusd", "1", "--output", "report.json"],
            {"GITHUB_ACTIONS": "true"},
        ),
    ],
)
def test_cli_requires_opt_in_budget_and_refuses_ci(
    options: list[str], env: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(options, env) == 2
    assert "invalid" in capsys.readouterr().err


def test_tampered_report_and_secret_config_fail_safely(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    current = registry(model())
    path = tmp_path / "report.json"
    values = report(current).model_dump(mode="json")
    values["configuration"]["models"][0]["input_price"] = "900"
    path.write_text(json.dumps(values), "utf-8")
    assert main(["--report", str(path)], {}) == 2
    path.write_text('{"secret":"sensitive-value"}', "utf-8")
    assert main(["--registry", str(path)], {}) == 2
    assert "sensitive-value" not in capsys.readouterr().err


@pytest.mark.parametrize("deep_fails", [False, True])
def test_cli_real_path_with_mocked_http_writes_evidence_and_offline_reuses_it(
    deep_fails: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    current = registry(model(), model(ModelRole.DEEP))
    path, output = tmp_path / "registry.json", tmp_path / "report.json"
    path.write_text(current.config.model_dump_json(), "utf-8")

    def handler(request: httpx2.Request) -> httpx2.Response:
        configured_id = json.loads(request.content)["model"]
        if deep_fails and configured_id == current.resolve(ModelRole.DEEP).model_id:
            return httpx2.Response(503, text="secret-provider-error")
        return httpx2.Response(200, json=response(configured_id))

    original_client = httpx2.AsyncClient

    def mock_client(**options: object) -> httpx2.AsyncClient:
        assert options == {"trust_env": False, "follow_redirects": False}
        return original_client(transport=httpx2.MockTransport(handler))

    monkeypatch.setattr(cli, "SystemClock", FakeClock)
    monkeypatch.setattr(httpx2, "AsyncClient", mock_client)
    result = main(
        ["--registry", str(path), "--real", "--max-cost-microusd", "100", "--output", str(output)],
        {"NEBIUS_API_KEY": "synthetic-private-key"},
    )
    assert result == (1 if deep_fails else 0)
    summary = json.loads(capsys.readouterr().out)
    assert summary["readiness"]["inference_available"]
    assert summary["live_gate"] == ("FAILED" if deep_fails else "PASSED")
    assert "synthetic-private-key" not in output.read_text("utf-8")
    assert main(["--registry", str(path), "--report", str(output)], {}) == result
    assert json.loads(capsys.readouterr().out)["mode"] == "offline"


def test_real_output_cannot_overwrite_registry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "registry.json"
    before = registry(model()).config.model_dump_json()
    path.write_text(before, "utf-8")
    assert (
        main(
            [
                "--registry",
                str(path),
                "--real",
                "--max-cost-microusd",
                "100",
                "--output",
                str(path),
            ],
            {"NEBIUS_API_KEY": "synthetic-key"},
        )
        == 2
    )
    assert path.read_text("utf-8") == before
    assert "invalid" in capsys.readouterr().err
